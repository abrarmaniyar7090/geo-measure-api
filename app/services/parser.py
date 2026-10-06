import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio
from pyproj import CRS


class ParseError(Exception):
    pass


def _safe_extract(zip_path: Path, dest: Path) -> None:
    dest = dest.resolve()

    try:
        with zipfile.ZipFile(zip_path) as z:
            for member in z.infolist():
                target = (dest / member.filename).resolve()

                if dest not in target.parents and target != dest:
                    raise ParseError("Unsafe path in zip archive")

            z.extractall(dest)

    except zipfile.BadZipFile:
        raise ParseError("Invalid zip file")


def _read_kml(path: Path) -> gpd.GeoDataFrame:
    frames = []

    # A KML can contain multiple layers/folders.
    for name, _ in pyogrio.list_layers(path):
        layer = gpd.read_file(
            path,
            layer=name,
            engine="pyogrio"
        )

        if len(layer):
            frames.append(layer)

    if not frames:
        raise ParseError("KML contains no features")

    gdf = pd.concat(
        frames,
        ignore_index=True
    )

    return gpd.GeoDataFrame(
        gdf,
        geometry="geometry",
        crs="EPSG:4326"
    )


def read_geodata(path: Path) -> gpd.GeoDataFrame:
    suffix = path.suffix.lower()

    try:

        if suffix == ".zip":
            tmp = Path(tempfile.mkdtemp())

            _safe_extract(path, tmp)

            shps = list(tmp.rglob("*.shp"))

            if not shps:
                raise ParseError(
                    "No .shp file found in the zip"
                )

            gdf = gpd.read_file(
                shps[0],
                engine="pyogrio"
            )

            if gdf.crs is None:
                raise ParseError(
                    "Shapefile has no CRS (.prj file missing)"
                )

            return gdf

        if suffix == ".kml":
            return _read_kml(path)

    except ParseError:
        raise

    except Exception as e:
        raise ParseError(
            f"Could not read file: {e}"
        )

    raise ParseError(
        "Unsupported file type; use .zip (Shapefile) or .kml"
    )


def crs_label(crs: CRS) -> str:
    epsg = crs.to_epsg()

    return f"EPSG:{epsg}" if epsg else crs.name