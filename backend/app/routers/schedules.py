from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Schedule

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


@router.get("")
async def list_schedules(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Schedule).order_by(Schedule.start_time.asc())

    if start_date:
        query = query.where(Schedule.start_time >= start_date)
    if end_date:
        query = query.where(Schedule.end_time <= end_date)

    result = await db.execute(query)
    schedules = result.scalars().all()

    return [
        {
            "id": s.id,
            "log_id": s.log_id,
            "title": s.title,
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat(),
            "location": s.location,
            "description": s.description,
            "is_synced_to_calendar": s.is_synced_to_calendar,
        }
        for s in schedules
    ]
