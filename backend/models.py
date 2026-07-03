import datetime
import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class URLStatus(str, enum.Enum):
    UNKNOWN = "UNKNOWN"
    UP = "UP"
    DOWN = "DOWN"


class MonitoredURL(Base):
    __tablename__ = "monitored_urls"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)

    check_interval_seconds = Column(Integer, default=60, nullable=False)
    expected_status_code = Column(Integer, nullable=True)  # None -> any code < 400 counts as success
    webhook_url = Column(String, nullable=True)  # optional POST target on status change

    current_status = Column(Enum(URLStatus), default=URLStatus.UNKNOWN, nullable=False)
    consecutive_failures = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    pings = relationship("PingResult", back_populates="url", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="url", cascade="all, delete-orphan")


class PingResult(Base):
    __tablename__ = "ping_results"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("monitored_urls.id"), nullable=False)
    status_code = Column(Integer, nullable=True)  # null if the request errored/timed out
    response_time_ms = Column(Float, nullable=True)
    is_success = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    url = relationship("MonitoredURL", back_populates="pings")


class Incident(Base):
    """An open->closed window of downtime for one URL, derived from consecutive failures."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("monitored_urls.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)  # null while still ongoing

    url = relationship("MonitoredURL", back_populates="incidents")
