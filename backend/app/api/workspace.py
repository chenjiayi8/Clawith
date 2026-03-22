"""Public workspace API routes (bug reports, project listing)."""

import logging
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.workspace import WorkspaceBugReport, WorkspaceProject
from app.services.workspace_tools import approve_container_deploy, reject_container_deploy

logger = logging.getLogger(__name__)

# Public router — no auth required, registered without API prefix
public_router = APIRouter(tags=["workspace-public"])

# Authenticated router — under /api/workspace
router = APIRouter(prefix="/workspace", tags=["workspace"])

# Simple in-memory rate limiter: {ip: [timestamps]}
_rate_limit: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 3600  # 1 hour


class BugReportRequest(BaseModel):
    description: str
    website: str = ""  # honeypot field


def _check_rate_limit(ip: str) -> bool:
    """Return True if request is within rate limit."""
    now = time.time()
    _rate_limit[ip] = [t for t in _rate_limit[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit[ip]) >= RATE_LIMIT_MAX:
        return False
    _rate_limit[ip].append(now)
    return True


@public_router.post("/api/workspace/projects/{slug}/report-bug")
async def report_bug(
    slug: str,
    body: BugReportRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint for reporting bugs on workspace projects."""
    # Honeypot check
    if body.website:
        # Bot detected — return 200 silently to not reveal the trap
        return {"status": "ok"}

    # Rate limit
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Too many reports. Try again later.")

    # Find project
    result = await db.execute(
        select(WorkspaceProject).where(
            WorkspaceProject.slug == slug,
            WorkspaceProject.status == "deployed",
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Create bug report
    report = WorkspaceBugReport(
        project_id=project.id,
        source="user_report",
        description=body.description[:2000],  # cap length
    )
    db.add(report)
    await db.commit()

    logger.info("Bug report created for project '%s' from %s", slug, client_ip)
    return {"status": "ok", "message": "Report submitted. Thank you!"}


class ApproveRequest(BaseModel):
    memory: str = ""
    cpus: str = ""


@router.post("/projects/{slug}/approve")
async def approve_deploy(slug: str, body: ApproveRequest | None = None):
    """Approve a container deployment (authenticated, under /api/workspace)."""
    limits = {}
    if body:
        if body.memory:
            limits["memory"] = body.memory
        if body.cpus:
            limits["cpus"] = body.cpus
    result = await approve_container_deploy(slug, limits if limits else None)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/projects/{slug}/reject")
async def reject_deploy(slug: str):
    """Reject a container deployment (authenticated, under /api/workspace)."""
    result = await reject_container_deploy(slug)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/projects")
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all workspace projects."""
    result = await db.execute(
        select(WorkspaceProject).order_by(WorkspaceProject.created_at.desc())
    )
    projects = result.scalars().all()
    return [
        {
            "slug": p.slug,
            "name": p.name,
            "status": p.status,
            "deploy_type": p.deploy_type,
            "container_port": p.container_port,
            "url": f"/workspace/{p.slug}/" if p.status == "deployed" else None,
        }
        for p in projects
    ]
