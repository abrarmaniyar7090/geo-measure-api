import shutil
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon


SAMPLE_KML = (
    Path(__file__).parent
    / "data"
    / "sample.kml"
)


def _upload(client, path, name=None):

    with open(path, "rb") as f:

        return client.post(
            "/api/files/",
            files={
                "file": (
                    name or Path(path).name,
                    f
                )
            }
        )


def test_upload_kml_and_get_info(client):

    r = _upload(
        client,
        SAMPLE_KML
    )

    assert r.status_code == 201

    body = r.json()

    assert body["status"] == "COMPLETED"

    assert body["feature_count"] == 3

    assert body["crs"] == "EPSG:4326"

    info = client.get(
        f"/api/files/{body['id']}/"
    )

    assert info.status_code == 200

    assert info.json()["filename"] == "sample.kml"


def test_measurements_for_kml(client):

    file_id = _upload(
        client,
        SAMPLE_KML
    ).json()["id"]

    response = client.get(
        f"/api/files/{file_id}/measurements/"
    )

    assert response.status_code == 200

    feats = response.json()["features"]

    by_type = {
        f["geometry_type"]: f
        for f in feats
    }

    assert (
        900_000
        < by_type["Polygon"]["measurement"]["value"]
        < 1_100_000
    )

    assert (
        900
        < by_type["LineString"]["measurement"]["value"]
        < 1100
    )

    assert (
        by_type["Point"]["measurement"]["value"]
        is None
    )

    assert (
        by_type["Point"]["measurement"]["note"]
    )


def test_upload_zipped_shapefile(
    client,
    tmp_path
):

    gdf = gpd.GeoDataFrame(
        {"name": ["plot"]},
        geometry=[
            Polygon([
                (77.59, 12.97),
                (77.599, 12.97),
                (77.599, 12.979),
                (77.59, 12.979)
            ])
        ],
        crs="EPSG:4326"
    )

    shp_dir = tmp_path / "shp"

    shp_dir.mkdir()

    gdf.to_file(
        shp_dir / "plot.shp"
    )

    zip_path = shutil.make_archive(
        str(tmp_path / "plot"),
        "zip",
        shp_dir
    )

    r = _upload(
        client,
        zip_path
    )

    assert r.json()["status"] == "COMPLETED"

    feats = client.get(
        f"/api/files/{r.json()['id']}/measurements/"
    ).json()["features"]

    assert feats[0]["properties"]["name"] == "plot"

    assert (
        feats[0]["measurement"]["type"]
        == "area"
    )


def test_rejects_unsupported_extension(
    client,
    tmp_path
):

    bad = tmp_path / "notes.txt"

    bad.write_text("hi")

    response = _upload(
        client,
        bad
    )

    assert response.status_code == 400


def test_corrupt_zip_marked_failed_not_crash(
    client,
    tmp_path
):

    bad = tmp_path / "broken.zip"

    bad.write_bytes(
        b"not a zip"
    )

    r = _upload(
        client,
        bad
    )

    assert r.status_code == 201

    assert (
        r.json()["status"]
        == "FAILED"
    )

    response = client.get(
        f"/api/files/{r.json()['id']}/measurements/"
    )

    assert response.status_code == 409


def test_unknown_id_returns_404(client):

    response = client.get(
        "/api/files/doesnotexist/"
    )

    assert response.status_code == 404