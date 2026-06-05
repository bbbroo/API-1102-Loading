from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_name: Mapped[str] = mapped_column(String(255), default="")
    project_number: Mapped[str] = mapped_column(String(100), default="")
    client: Mapped[str] = mapped_column(String(255), default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="Active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    calculations: Mapped[list["Calculation"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Calculation(Base):
    __tablename__ = "calculations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    calc_number: Mapped[str] = mapped_column(String(100), default="")
    crossing_name: Mapped[str] = mapped_column(String(255), default="")
    calculation_type: Mapped[str] = mapped_column(String(50), default="Highway")
    road_highway: Mapped[str] = mapped_column(String(255), default="")
    railroad_route: Mapped[str] = mapped_column(String(255), default="")
    prepared_by: Mapped[str] = mapped_column(String(255), default="")
    checked_by: Mapped[str] = mapped_column(String(255), default="")
    reviewer: Mapped[str] = mapped_column(String(255), default="")
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    revision: Mapped[str] = mapped_column(String(50), default="0")
    status: Mapped[str] = mapped_column(String(50), default="Draft")
    review_comments: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    overall_result: Mapped[str] = mapped_column(String(50), default="Not Calculated")
    controlling_check: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    project: Mapped[Project] = relationship(back_populates="calculations")
    scenarios: Mapped[list["Scenario"]] = relationship(back_populates="calculation", cascade="all, delete-orphan")


class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    calculation_id: Mapped[int] = mapped_column(ForeignKey("calculations.id", ondelete="CASCADE"))
    scenario_name: Mapped[str] = mapped_column(String(255), default="Base Case")
    description: Mapped[str] = mapped_column(Text, default="")
    shared_inputs_json: Mapped[str] = mapped_column(Text, default="{}")
    highway_inputs_json: Mapped[str] = mapped_column(Text, default="{}")
    railroad_inputs_json: Mapped[str] = mapped_column(Text, default="{}")
    results_json: Mapped[str] = mapped_column(Text, default="{}")
    intermediate_values_json: Mapped[str] = mapped_column(Text, default="{}")
    warnings_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    calculation: Mapped[Calculation] = relationship(back_populates="scenarios")


class ExportRecord(Base):
    __tablename__ = "export_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    calculation_id: Mapped[int] = mapped_column(ForeignKey("calculations.id", ondelete="CASCADE"))
    scenario_id: Mapped[int | None] = mapped_column(ForeignKey("scenarios.id", ondelete="SET NULL"), nullable=True)
    export_type: Mapped[str] = mapped_column(String(20))
    file_name: Mapped[str] = mapped_column(String(255))
    exported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
