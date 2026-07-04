# Uptime Monitor MVP

A lightweight, full-stack application for monitoring website health in real time. Register a URL through the dashboard and it automatically tracks operational status (**UP** / **DOWN**) and response times in the background.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Testing the Monitoring Logic](#testing-the-monitoring-logic)
- [API Reference](#api-reference)
- [Deployment Sketch](#deployment-sketch)
- [AI Collaboration Log](#ai-collaboration-log)

## Features

- Register any URL from the dashboard with one click
- Background worker pings every registered URL on a schedule and records status code + response time
- Live UP / DOWN status, color-coded on the dashboard
- Fully containerized — one command to run the whole stack locally

## Tech Stack

| Layer         | Choice                                   |
|---------------|-------------------------------------------|
| Backend       | FastAPI (Python), SQLAlchemy              |
| Background jobs | Async worker (asyncio)                 |
| Database      | SQLite (dev) — swappable for Postgres in prod |
| Frontend      | Static dashboard served alongside the API |
| Local dev     | Docker Compose                            |
| Prod target   | AWS ECS Fargate, provisioned via Terraform |

## Quick Start

**Prerequisite:** Docker and Docker Compose installed locally.

```bash
docker compose up --build
```

Once the containers are up, open the dashboard at **http://localhost**.

## Testing the Monitoring Logic

**1. Add a working URL**

1. Enter `https://httpbin.org/status/200` into the dashboard input field.
2. Click **Monitor**.
3. Wait ~10 seconds — the status should turn **green (UP)**.

**2. Add a broken URL**

1. Enter `https://httpbin.org/status/500` into the dashboard input field.
2. Click **Monitor**.
3. The background worker detects the failure on its next check, and the status turns **red (DOWN)**.

## API Reference

The backend is a FastAPI service, so full interactive API docs are available for free once the stack is running:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Deployment Sketch

For production, this would run on **AWS ECS with Fargate** for serverless container management.

- **Frontend:** delivered via CloudFront CDN for low-latency static asset delivery
- **Backend:** runs in a private VPC, reachable only through an internal load balancer / API gateway
- **IaC:** provisioned with Terraform

```hcl
resource "aws_ecs_task_definition" "uptime_monitor" {
  family = "uptime-monitor-task"

  container_definitions = jsonencode([{
    name          = "monitor-api"
    image         = "your-docker-repo/uptime-monitor:latest"
    portMappings  = [{ containerPort = 8000 }]
  }])

  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
}
```

## AI Collaboration Log

See [`AI_LOG.md`](./AI_LOG.md) for a full breakdown of the tools used, the prompts that shipped each feature, and the technical hurdles hit during development.