from pydantic import BaseModel, ConfigDict


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    feature_count: int
    crs: str | None
    status: str
    error: str | None = None


class MeasurementOut(BaseModel):
    type: str | None
    value: float | None
    unit: str | None
    projected_crs: str | None
    note: str | None


class FeatureOut(BaseModel):
    index: int
    geometry_type: str
    geometry: dict
    crs: str | None
    properties: dict
    measurement: MeasurementOut


class MeasurementsResponse(BaseModel):
    file_id: str
    features: list[FeatureOut]