from fastapi import FastAPI

from .api.files import router
from .db import Base, engine


Base.metadata.create_all(engine)


app = FastAPI(
    title="Geospatial Measurement API",
    version="1.0.0"
)


app.include_router(router)