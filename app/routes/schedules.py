from fastapi import APIRouter, HTTPException
from pathlib import Path

from app.storage.csv_storage import (
    read_messages,
    add_message,
    update_message,
    get_message
)

from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleResponse
)

from app.services.whatsapp_service import SESSION_DIR

router = APIRouter(
    prefix="/api/schedules",
    tags=["Message Scheduling"]
)


@router.get("/whatsapp/status")
def whatsapp_status():
    has_session = SESSION_DIR.exists() and any(SESSION_DIR.iterdir())
    return {
        "linked": has_session,
        "status": "connected" if has_session else "not_linked",
        "session_directory": str(SESSION_DIR),
        "instructions": (
            "Run 'python link_whatsapp.py' to open the QR code and link your phone."
            if not has_session
            else "WhatsApp session is ready to dispatch scheduled messages."
        )
    }


@router.post("/", response_model=ScheduleResponse)
def create_schedule(data: ScheduleCreate):

    record = add_message(data)

    return {
        **record,
        "id": int(record["id"]),
        "scheduled_at": record["scheduled_at"],
        "created_at": record["created_at"]
    }


@router.get("/", response_model=list[ScheduleResponse])
def get_schedules():

    messages = read_messages()

    return [
        {
            **message,
            "id": int(message["id"])
        }
        for message in messages
    ]


@router.delete("/{schedule_id}")
def cancel_schedule(schedule_id: int):

    message = get_message(schedule_id)

    if not message:

        raise HTTPException(
            status_code=404,
            detail="Schedule not found"
        )

    if message["status"] != "scheduled":

        raise HTTPException(
            status_code=400,
            detail="Only scheduled messages can be cancelled"
        )

    update_message(
        schedule_id,
        {"status": "cancelled"}
    )

    return {
        "status": "success",
        "message": "Schedule cancelled"
    }
