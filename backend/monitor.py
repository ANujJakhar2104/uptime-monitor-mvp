import asyncio
import httpx
import time
from sqlalchemy.orm import Session
from database import SessionLocal
import models

class MonitorManager:
    def __init__(self):
        self.running = False
        self.task = None

    async def start_all(self):
        self.running = True
        async with httpx.AsyncClient() as client:
            while self.running:
                db: Session = SessionLocal()
                try:
                    urls = db.query(models.MonitoredURL).all()
                    for url in urls:
                        try:
                            # ⏱️ Start Stopwatch
                            start_time = time.time()
                            
                            response = await client.get(url.url, timeout=5.0)
                            
                            # ⏱️ Stop Stopwatch
                            end_time = time.time()

                            is_success = response.status_code < 400
                            url.current_status = models.URLStatus.UP if is_success else models.URLStatus.DOWN
                            
                            # Time calculate karke DB mein save karna (in milliseconds)
                            url.response_time = round((end_time - start_time) * 1000, 2)
                            
                        except Exception as e:
                            # Agar website fail/timeout ho jaye
                            url.current_status = models.URLStatus.DOWN
                            url.response_time = None
                    
                    db.commit()
                finally:
                    db.close()
                
                # Agle check ke liye 10 seconds wait karega
                await asyncio.sleep(10)

    async def stop_all(self):
        self.running = False

manager = MonitorManager()