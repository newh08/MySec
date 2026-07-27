from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import DailyLog, Schedule

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
async def list_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: date | None = None,
    end_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(DailyLog).order_by(DailyLog.date.desc())

    if start_date:
        query = query.where(DailyLog.date >= start_date)
    if end_date:
        query = query.where(DailyLog.date <= end_date)

    total = len((await db.execute(select(DailyLog.id))).scalars().all())
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    logs_data = []
    for log in logs:
        sched_result = await db.execute(
            select(Schedule).where(Schedule.log_id == log.id)
        )
        schedules = sched_result.scalars().all()
        logs_data.append({
            "id": log.id,
            "date": str(log.date),
            "summary_markdown": log.summary_markdown,
            "schedules": [
                {
                    "id": s.id,
                    "title": s.title,
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat(),
                    "location": s.location,
                    "is_synced_to_calendar": s.is_synced_to_calendar,
                }
                for s in schedules
            ],
            "created_at": log.created_at.isoformat(),
        })

    return {
        "items": logs_data,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/{log_id}")
async def get_log(log_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DailyLog).where(DailyLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    sched_result = await db.execute(
        select(Schedule).where(Schedule.log_id == log.id)
    )
    schedules = sched_result.scalars().all()

    return {
        "id": log.id,
        "date": str(log.date),
        "summary_markdown": log.summary_markdown,
        "raw_conversation_json": log.raw_conversation_json,
        "schedules": [
            {
                "id": s.id,
                "title": s.title,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat(),
                "location": s.location,
                "description": s.description,
                "is_synced_to_calendar": s.is_synced_to_calendar,
            }
            for s in schedules
        ],
        "created_at": log.created_at.isoformat(),
    }


@router.delete("/{log_id}")
async def delete_log(log_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DailyLog).where(DailyLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    await db.execute(delete(Schedule).where(Schedule.log_id == log_id))
    await db.delete(log)
    await db.commit()
    return {"status": "deleted"}
