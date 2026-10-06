from shapely.geometry import Polygon, LineString, Point
from pyproj import CRS

from app.services.measurements import measure


WGS84 = CRS.from_epsg(4326)


def test_polygon_area_is_in_square_metres_not_degrees():

    poly = Polygon([
        (77.59, 12.97),
        (77.599, 12.97),
        (77.599, 12.979),
        (77.59, 12.979)
    ])

    m = measure(poly, WGS84)

    assert m.type == "area"
    assert m.unit == "sq_m"

    assert 900_000 < m.value < 1_100_000

    assert m.projected_crs == "EPSG:32643"


def test_line_length_in_metres():

    m = measure(
        LineString([
            (77.59, 12.97),
            (77.59, 12.979)
        ]),
        WGS84
    )

    assert m.type == "length"
    assert 900 < m.value < 1100


def test_point_is_handled_gracefully():

    m = measure(
        Point(77.59, 12.97),
        WGS84
    )

    assert m.value is None
    assert m.note


def test_already_projected_crs_is_not_reprojected():

    m = measure(
        Polygon([
            (0, 0),
            (100, 0),
            (100, 100),
            (0, 100)
        ]),
        CRS.from_epsg(32643)
    )

    assert round(m.value) == 10_000


def test_empty_geometry():

    assert measure(
        Polygon(),
        WGS84
    ).note