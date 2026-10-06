import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, JSON, ForeignKey, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


class UploadedFile(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=_new_id
    )

    filename: Mapped[str] = mapped_column(String)

    status: Mapped[str] = mapped_column(
        String,
        default="PROCESSING"
    )

    crs: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    feature_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    error: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    features: Mapped[list["Feature"]] = relationship(
        back_populates="file",
        cascade="all, delete-orphan"
    )


class Feature(Base):
    __tablename__ = "features"

    pk: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    file_id: Mapped[str] = mapped_column(
        ForeignKey("files.id")
    )

    index: Mapped[int] = mapped_column(Integer)

    geometry_type: Mapped[str] = mapped_column(String)

    geometry: Mapped[dict] = mapped_column(JSON)

    crs: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    properties: Mapped[dict] = mapped_column(JSON)

    measurement_type: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    measurement_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    measurement_unit: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    projected_crs: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    note: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    file: Mapped["UploadedFile"] = relationship(
        back_populates="features"
    )