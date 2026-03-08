"""
Resume management routes: upload, list, get.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import ResumeListResponse, ResumeResponse

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Resume:
    """
    Upload a resume PDF. Automatically parses text, extracts entities,
    generates embedding, and handles versioning.
    """
    import asyncio

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    settings = get_settings()
    upload_dir = settings.upload_dir / str(user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    file_path = upload_dir / file.filename
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse resume in thread pool (sync spaCy + embedding are CPU-heavy)
    from app.services.resume_parser import ResumeParser

    parser = ResumeParser.get_instance()
    parsed = await asyncio.to_thread(parser.parse_resume, str(file_path))

    # Handle versioning: find latest version for this user
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == user.id)
        .order_by(Resume.version.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()

    version = 1
    parent_id = None
    if latest:
        version = latest.version + 1
        parent_id = latest.id

    resume = Resume(
        user_id=user.id,
        file_path=str(file_path),
        file_name=file.filename,
        version=version,
        parent_id=parent_id,
        raw_text=parsed["raw_text"],
        structured_data=parsed["structured_data"],
        embedding=parsed["embedding"],
    )
    db.add(resume)
    await db.flush()
    await db.refresh(resume)
    return resume


@router.get("/", response_model=ResumeListResponse)
async def list_resumes(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """List all resumes for the current user."""
    query = select(Resume).where(Resume.user_id == user.id).offset(skip).limit(limit)
    result = await db.execute(query)
    items = list(result.scalars().all())

    count_result = await db.execute(
        select(func.count(Resume.id)).where(Resume.user_id == user.id)
    )
    total = count_result.scalar() or 0

    return {"items": items, "total": total}


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Resume:
    """Get a specific resume by ID."""
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    resume = result.scalar_one_or_none()

    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    return resume
