from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime, timedelta

# Your local imports
from database import engine, Base, get_db
import models
import schemas
from monitor import manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize database tables
    Base.metadata.create_all(bind=engine)
    
    # 2. Start the background monitor loop. 
    # If your manager.start_all() is async, we use create_task. 
    # If it is a normal sync function (using threads), we just call it directly.
    if asyncio.iscoroutinefunction(manager.start_all):
        asyncio.create_task(manager.start_all())
    else:
        manager.start_all()
        
    yield
    
    # 3. Safely shut down background loops when stopping server
    if asyncio.iscoroutinefunction(manager.stop_all):
        await manager.stop_all()
    else:
        manager.stop_all()

# INITIALIZE APP FIRST
app = FastAPI(lifespan=lifespan)

# CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # <--- Crucial for vanilla HTML frontend
    allow_methods=["*"],
    allow_headers=["*"],
)

# ROUTES
@app.post("/urls", response_model=schemas.URLOut)
def create_url(url_data: schemas.URLCreate, db: Session = Depends(get_db)):
    """Register a new URL to monitor."""
    # Check if URL already exists
    existing = db.query(models.MonitoredURL).filter(models.MonitoredURL.url == str(url_data.url)).first()
    if existing:
        raise HTTPException(status_code=400, detail="URL is already being monitored")
    
    # Create new URL entry
    new_url = models.MonitoredURL(
        url=str(url_data.url),
        check_interval_seconds=url_data.check_interval_seconds,
        expected_status_code=url_data.expected_status_code,
        webhook_url=str(url_data.webhook_url) if url_data.webhook_url else None
    )
    db.add(new_url)
    db.commit()
    db.refresh(new_url)
    
    # Add to the running monitor loop
    #manager.add_monitor(new_url.id, new_url.url, new_url.check_interval_seconds)
    
    return new_url

@app.get("/urls", response_model=list[schemas.URLOut])
def get_urls(db: Session = Depends(get_db)):
    """Fetch all monitored URLs for the dashboard."""
    return db.query(models.MonitoredURL).all()

@app.get("/urls/{url_id}/stats", response_model=schemas.StatsOut)
def get_url_stats(url_id: int, hours: int = 24, db: Session = Depends(get_db)):
    """Fetch aggregated uptime statistics for a specific URL."""
    url = db.query(models.MonitoredURL).filter(models.MonitoredURL.id == url_id).first()
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    # Time window for stats
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    pings = db.query(models.PingResult).filter(
        models.PingResult.url_id == url_id,
        models.PingResult.timestamp >= cutoff_time
    ).all()
    
    total_pings = len(pings)
    successful_pings = sum(1 for p in pings if p.is_success)
    uptime_percentage = (successful_pings / total_pings * 100.0) if total_pings > 0 else 0.0
    
    response_times = [p.response_time_ms for p in pings if p.response_time_ms is not None]
    avg_response = (sum(response_times) / len(response_times)) if response_times else None
    
    open_incidents = db.query(models.Incident).filter(
        models.Incident.url_id == url_id,
        models.Incident.ended_at.is_(None)
    ).count()
    
    return schemas.StatsOut(
        url_id=url.id,
        window_hours=hours,
        total_pings=total_pings,
        successful_pings=successful_pings,
        uptime_percentage=uptime_percentage,
        avg_response_time_ms=avg_response,
        open_incidents=open_incidents,
        current_status=url.current_status
    )