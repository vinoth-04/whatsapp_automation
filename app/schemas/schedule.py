from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime, timezone
import re


class ScheduleCreate(BaseModel):

    phone_number: str
    message: str = Field(min_length=1, max_length=4096)
    scheduled_at: datetime

    recipient_opted_in: bool = False

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value):

        if not re.fullmatch(r"\+[1-9]\d{7,14}", value):
            raise ValueError("Invalid phone number")

        return value

    @field_validator("scheduled_at")
    @classmethod
    def validate_datetime(cls, value):

        if value.tzinfo is None:
            raise ValueError("Timezone required")

        if value <= datetime.now(timezone.utc):
            raise ValueError("Schedule must be in future")

        return value

    @field_validator("recipient_opted_in")
    @classmethod
    def validate_consent(cls, value):

        if not value:
            raise ValueError("Recipient consent required")

        return value


class ScheduleResponse(BaseModel):

    id: int
    client_id: str
    phone_number: str
    message: str
    scheduled_at: datetime
    status: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
