import json
from pathlib import Path

import shapely
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Feature, UploadedFile
from ..schemas import (
    FeatureOut,
    FileOut,
    MeasurementOut,
    MeasurementsResponse,
)
from ..services.measurements import measure
from ..services.parser import (
    ParseError,
    crs_label,
    read_geodata,
)


router = APIRouter(
    prefix="/api/files",
    tags=["files"]
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_BYTES = 50 * 1024 * 1024


@router.post(
    "/",
    response_model=FileOut,
    status_code=201
)
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    name = Path(file.filename or "").name

    if not name.lower().endswith((".zip", ".kml")):
        raise HTTPException(
            400,
            "Only .zip (Shapefile) or .kml files are accepted"
        )

    record = UploadedFile(filename=name)

    db.add(record)
    db.commit()

    saved = UPLOAD_DIR / f"{record.id}_{name}"

    size = 0

    with saved.open("wb") as out:

        while chunk := file.file.read(1024 * 1024):

            size += len(chunk)

            if size > MAX_BYTES:
                break

            out.write(chunk)

    if size > MAX_BYTES:

        saved.unlink(missing_ok=True)

        record.status = "FAILED"
        record.error = "File exceeds 50 MB limit"

        db.commit()

        raise HTTPException(
            413,
            "File exceeds 50 MB limit"
        )

    try:

        gdf = read_geodata(saved)

        crs_str = crs_label(gdf.crs)

        props_list = json.loads(
            gdf.drop(
                columns=gdf.geometry.name
            ).to_json(
                orient="records",
                date_format="iso"
            )
        )

        for i, geom in enumerate(gdf.geometry):

            m = measure(
                geom,
                gdf.crs
            )

            has_geom = (
                geom is not None
                and not geom.is_empty
            )

            db.add(
                Feature(
                    file_id=record.id,
                    index=i,
                    geometry_type=(
                        geom.geom_type
                        if geom is not None
                        else "None"
                    ),
                    geometry=(
                        json.loads(
                            shapely.to_geojson(geom)
                        )
                        if has_geom
                        else {}
                    ),
                    crs=crs_str,
                    properties=props_list[i],
                    measurement_type=m.type,
                    measurement_value=m.value,
                    measurement_unit=m.unit,
                    projected_crs=m.projected_crs,
                    note=m.note,
                )
            )

        record.crs = crs_str
        record.feature_count = len(gdf)
        record.status = "COMPLETED"

    except ParseError as e:

        db.rollback()

        record = db.get(
            UploadedFile,
            record.id
        )

        record.status = "FAILED"
        record.error = str(e)

    except Exception as e:

        db.rollback()

        record = db.get(
            UploadedFile,
            record.id
        )

        record.status = "FAILED"
        record.error = f"Processing error: {e}"

    db.commit()
    db.refresh(record)

    return record


def _get_or_404(
    file_id: str,
    db: Session
) -> UploadedFile:

    record = db.get(
        UploadedFile,
        file_id
    )

    if record is None:
        raise HTTPException(
            404,
            "File not found"
        )

    return record


@router.get(
    "/{file_id}/",
    response_model=FileOut
)
def get_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    return _get_or_404(
        file_id,
        db
    )


@router.get(
    "/{file_id}/measurements/",
    response_model=MeasurementsResponse
)
def get_measurements(
    file_id: str,
    db: Session = Depends(get_db)
):

    record = _get_or_404(
        file_id,
        db
    )

    if record.status != "COMPLETED":
        raise HTTPException(
            409,
            f"File status is {record.status}: "
            f"{record.error or 'not ready'}"
        )

    features = sorted(
        record.features,
        key=lambda f: f.index
    )

    return MeasurementsResponse(
        file_id=record.id,
        features=[
            FeatureOut(
                index=f.index,
                geometry_type=f.geometry_type,
                geometry=f.geometry,
                crs=f.crs,
                properties=f.properties,
                measurement=MeasurementOut(
                    type=f.measurement_type,
                    value=f.measurement_value,
                    unit=f.measurement_unit,
                    projected_crs=f.projected_crs,
                    note=f.note,
                ),
            )
            for f in features
        ],
    )