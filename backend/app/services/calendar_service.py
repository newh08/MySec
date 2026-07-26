from datetime import datetime
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import settings

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_credentials() -> Credentials:
    creds = Credentials(
        token=None,
        refresh_token=settings.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_calendar_client_id,
        client_secret=settings.google_calendar_client_secret,
        scopes=SCOPES,
    )
    if creds.expired:
        creds.refresh(Request())
    return creds


async def sync_schedules_to_google(
    schedules: list[dict[str, Any]]
) -> bool:
    if not settings.google_refresh_token:
        print("[Calendar] No refresh token configured. Skipping sync.")
        return False

    try:
        creds = await _async_get_credentials()
        service = build("calendar", "v3", credentials=creds)

        for sched in schedules:
            event = {
                "summary": sched.get("title", "제목 없음"),
                "description": sched.get("description", ""),
                "location": sched.get("location", ""),
                "start": {
                    "dateTime": sched.get("start_time"),
                    "timeZone": settings.timezone,
                },
                "end": {
                    "dateTime": sched.get("end_time"),
                    "timeZone": settings.timezone,
                },
            }
            try:
                created = (
                    service.events()
                    .insert(calendarId=settings.google_calendar_id, body=event)
                    .execute()
                )
                print(f"[Calendar] Event created: {created.get('htmlLink')}")
            except Exception as e:
                print(f"[Calendar] Failed to create event '{event['summary']}': {e}")

        return True

    except Exception as e:
        print(f"[Calendar] Sync error: {e}")
        return False


async def _async_get_credentials():
    import asyncio

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _get_credentials)
