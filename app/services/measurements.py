from dataclasses import dataclass

import shapely
from pyproj import CRS, Transformer
from shapely.ops import transform


AREA_TYPES = {"Polygon", "MultiPolygon"}
LENGTH_TYPES = {"LineString", "MultiLineString"}


@dataclass
class Measurement:
    type: str | None = None
    value: float | None = None
    unit: str | None = None
    projected_crs: str | None = None
    note: str | None = None


def utm_crs_for(geom, src_crs: CRS) -> CRS:
    """Pick the UTM zone from the geometry's centroid."""

    to_wgs84 = Transformer.from_crs(
        src_crs,
        "EPSG:4326",
        always_xy=True
    )

    c = geom.centroid

    lon, lat = to_wgs84.transform(c.x, c.y)

    zone = int((lon + 180) // 6) + 1

    return CRS.from_epsg(
        (32600 if lat >= 0 else 32700) + zone
    )


def _is_metric_projected(crs: CRS) -> bool:
    return (
        crs.is_projected
        and crs.axis_info[0].unit_name.lower()
        in ("metre", "meter")
    )


def measure(geom, src_crs: CRS) -> Measurement:

    if geom is None or geom.is_empty:
        return Measurement(
            note="Empty or missing geometry"
        )

    gtype = geom.geom_type

    if gtype not in AREA_TYPES | LENGTH_TYPES:
        return Measurement(
            note=f"No measurement defined for {gtype}"
        )

    try:
        # Ignore altitude / Z coordinate.
        geom = shapely.force_2d(geom)

        if _is_metric_projected(src_crs):
            projected, target = geom, src_crs

        else:
            target = utm_crs_for(
                geom,
                src_crs
            )

            fn = Transformer.from_crs(
                src_crs,
                target,
                always_xy=True
            ).transform

            projected = transform(
                fn,
                geom
            )

    except Exception as e:
        return Measurement(
            note=f"Projection failed: {e}"
        )

    if gtype in AREA_TYPES:
        return Measurement(
            "area",
            projected.area,
            "sq_m",
            target.to_string()
        )

    return Measurement(
        "length",
        projected.length,
        "m",
        target.to_string()
    )