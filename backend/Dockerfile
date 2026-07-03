# backend/Dockerfile

# 1. Use an official lightweight Python image
FROM python:3.11-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy only the requirements file first (this caches the installation step and makes future builds faster)
COPY requirements.txt .

# 4. Install all the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your backend code (main.py, monitor.py, etc.) into the container
COPY . .

# 6. Expose port 8000 so the frontend can talk to it
EXPOSE 8000

# 7. Start the FastAPI server using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]