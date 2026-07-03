import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from models import URLStatus


class URLCreate(BaseModel):
    url: HttpUrl
    check_interval_seconds: int = Field(default=60, ge=10, le=3600)
    expected_status_code: Optional[int] = None  # None -> treat any code < 400 as success
    webhook_url: Optional[HttpUrl] = None


class URLOut(BaseModel):
    id: int
    url: str
    check_interval_seconds: int
    expected_status_code: Optional[int]
    current_status: URLStatus
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class PingOut(BaseModel):
    id: int
    status_code: Optional[int]
    response_time_ms: Optional[float]
    is_success: bool
    timestamp: datetime.datetime

    class Config:
        from_attributes = True


class IncidentOut(BaseModel):
    id: int
    started_at: datetime.datetime
    ended_at: Optional[datetime.datetime]
    duration_seconds: Optional[float] = None

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    url_id: int
    window_hours: int
    total_pings: int
    successful_pings: int
    uptime_percentage: float
    avg_response_time_ms: Optional[float]
    open_incidents: int
    current_status: URLStatus
