import asyncio
import httpx
from database import SessionLocal
import models

class MonitorManager:
    def __init__(self):
        self.is_running = False

    async def start_all(self):
        """The infinite background loop that pings URLs."""
        self.is_running = True
        print("🚀 Background monitor loop started!")
        
        # 1. Create fake browser headers to bypass firewalls (like Swiggy/Zomato)
        fake_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        
        # 2. Inject headers into the async client
        async with httpx.AsyncClient(headers=fake_headers) as client:
            while self.is_running:
                # Open a new database session for this sweep
                db = SessionLocal()
                try:
                    # Fetch ALL URLs directly from the database
                    urls = db.query(models.MonitoredURL).all()
                    
                    for url in urls:
                        try:
                            # Request now looks like a real Chrome browser!
                            response = await client.get(url.url, timeout=5.0)
                            is_success = response.status_code < 400
                            
                            url.current_status = models.URLStatus.UP if is_success else models.URLStatus.DOWN
                            
                        except Exception:
                            # If the request times out or fails (like a bad URL)
                            url.current_status = models.URLStatus.DOWN
                        
                        # Save the updated status back to the database
                        db.commit()
                
                finally:
                    # Always close the DB session so it doesn't lock up
                    db.close()
                
                # Wait 10 seconds before sweeping the database again
                await asyncio.sleep(10)

    async def stop_all(self):
        """Gracefully shuts down the infinite loop."""
        self.is_running = False
        print("🛑 Background monitor loop stopped.")

    def add_monitor(self, url_id: int, url: str, interval: int):
        """
        Prevents the 'AttributeError' in main.py. 
        We don't need to do anything here because the start_all() loop 
        automatically pulls fresh URLs from the database every 10 seconds!
        """
        print(f"New monitor registered in DB: {url}")

# Create the single instance that main.py imports
manager = MonitorManager()