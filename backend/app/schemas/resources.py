"""Schemas for mock business resources (reports, documents, settings)."""
from pydantic import BaseModel, Field


# ── Reports ──────────────────────────────────────────────────────────────────

class ReportCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)


class ReportUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = None


class ReportResponse(BaseModel):
    id: str
    title: str
    content: str
    created_by: str


# ── Documents ─────────────────────────────────────────────────────────────────

class DocumentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)


class DocumentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    body: str | None = None


class DocumentResponse(BaseModel):
    id: str
    name: str
    body: str
    created_by: str


# ── Settings ─────────────────────────────────────────────────────────────────

class SettingsUpdate(BaseModel):
    site_name: str | None = Field(None, max_length=255)
    maintenance_mode: bool | None = None
    max_upload_size_mb: int | None = Field(None, ge=1, le=1024)


class SettingsResponse(BaseModel):
    site_name: str
    maintenance_mode: bool
    max_upload_size_mb: int
