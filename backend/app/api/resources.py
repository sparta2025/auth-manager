"""
Mock business-resource endpoints: Reports, Documents, Settings.

No real database tables are used.  In-process dicts simulate persistence
for demonstration purposes.  Each endpoint is protected by the appropriate
permission using `require_permission()`.

In a production system these would be replaced with proper repositories
backed by real tables.
"""
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import require_permission
from app.models.models import User
from app.schemas.resources import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
    ReportCreate,
    ReportResponse,
    ReportUpdate,
    SettingsResponse,
    SettingsUpdate,
)

router = APIRouter(tags=["Business Resources"])

# ── In-memory stores (mock persistence) ──────────────────────────────────────
_reports: dict[str, dict[str, Any]] = {}
_documents: dict[str, dict[str, Any]] = {}
_settings: dict[str, Any] = {
    "site_name": "My Application",
    "maintenance_mode": False,
    "max_upload_size_mb": 10,
}


# ── Reports ───────────────────────────────────────────────────────────────────

@router.get(
    "/reports",
    response_model=list[ReportResponse],
    summary="List all reports",
)
def list_reports(current_user: User = Depends(require_permission("reports:read"))):
    return list(_reports.values())


@router.post(
    "/reports",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a report",
)
def create_report(
    payload: ReportCreate,
    current_user: User = Depends(require_permission("reports:create")),
):
    report_id = str(uuid.uuid4())
    record = {"id": report_id, "title": payload.title, "content": payload.content, "created_by": current_user.id}
    _reports[report_id] = record
    return record


@router.put(
    "/reports/{report_id}",
    response_model=ReportResponse,
    summary="Update a report",
)
def update_report(
    report_id: str,
    payload: ReportUpdate,
    current_user: User = Depends(require_permission("reports:update")),
):
    report = _reports.get(report_id)
    if not report:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Report not found.")
    if payload.title is not None:
        report["title"] = payload.title
    if payload.content is not None:
        report["content"] = payload.content
    return report


@router.delete(
    "/reports/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a report",
)
def delete_report(
    report_id: str,
    current_user: User = Depends(require_permission("reports:delete")),
):
    if report_id not in _reports:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Report not found.")
    del _reports[report_id]


# ── Documents ─────────────────────────────────────────────────────────────────

@router.get(
    "/documents",
    response_model=list[DocumentResponse],
    summary="List all documents",
)
def list_documents(current_user: User = Depends(require_permission("documents:read"))):
    return list(_documents.values())


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a document",
)
def create_document(
    payload: DocumentCreate,
    current_user: User = Depends(require_permission("documents:create")),
):
    doc_id = str(uuid.uuid4())
    record = {"id": doc_id, "name": payload.name, "body": payload.body, "created_by": current_user.id}
    _documents[doc_id] = record
    return record


@router.put(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Update a document",
)
def update_document(
    document_id: str,
    payload: DocumentUpdate,
    current_user: User = Depends(require_permission("documents:update")),
):
    doc = _documents.get(document_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found.")
    if payload.name is not None:
        doc["name"] = payload.name
    if payload.body is not None:
        doc["body"] = payload.body
    return doc


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
)
def delete_document(
    document_id: str,
    current_user: User = Depends(require_permission("documents:delete")),
):
    if document_id not in _documents:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found.")
    del _documents[document_id]


# ── Settings ─────────────────────────────────────────────────────────────────

@router.get(
    "/settings",
    response_model=SettingsResponse,
    summary="Read application settings",
)
def get_settings(current_user: User = Depends(require_permission("settings:read"))):
    return _settings


@router.put(
    "/settings",
    response_model=SettingsResponse,
    summary="Update application settings",
)
def update_settings(
    payload: SettingsUpdate,
    current_user: User = Depends(require_permission("settings:update")),
):
    if payload.site_name is not None:
        _settings["site_name"] = payload.site_name
    if payload.maintenance_mode is not None:
        _settings["maintenance_mode"] = payload.maintenance_mode
    if payload.max_upload_size_mb is not None:
        _settings["max_upload_size_mb"] = payload.max_upload_size_mb
    return _settings
