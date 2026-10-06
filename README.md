# Geospatial File Measurement API

A FastAPI service that accepts a zipped Shapefile or KML file, extracts
geospatial features, and calculates area or length measurements using
an appropriate projected coordinate reference system (CRS).

The API stores uploaded file information, feature geometry, properties,
CRS information, and calculated measurements in SQLite.

---

## Features

- Upload KML files
- Upload zipped Shapefiles
- Support KML files containing multiple layers/folders
- Extract feature properties
- Support 3D KML coordinates (Z values)
- Calculate polygon and multipolygon area
- Calculate linestring and multilinestring length
- Automatically select a suitable UTM projection
- Preserve source CRS information
- Store results in SQLite
- Validate uploaded file type
- Enforce a 50 MB upload limit
- Protect against ZIP path traversal (zip-slip)
- Handle invalid/corrupt files without crashing
- Automated tests using pytest

---

## Project Structure

```text
geo-measure-api/
│
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── files.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── measurements.py
│   │   └── parser.py
│   │
│   ├── __init__.py
│   ├── db.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
│
├── tests/
│   ├── data/
│   │   └── sample.kml
│   ├── conftest.py
│   ├── test_api.py
│   └── test_measurements.py
│
├── uploads/
├── .gitignore
├── README.md
└── requirements.txt