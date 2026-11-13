
from contextlib import asynccontextmanager

from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler

from app.routes.schedules import router as schedule_router
from app.storage.csv_storage import initialize_storage
from app.services.scheduler_service import check_due_messages


scheduler = BackgroundScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(app: FastAPI):

    initialize_storage()

    scheduler.add_job(
        check_due_messages,
        trigger="interval",
        seconds=10,
        id="message_scheduler",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )

    scheduler.start()

    print("WhatsApp scheduler started.")

    yield

    scheduler.shutdown(wait=False)

    print("WhatsApp scheduler stopped.")


app = FastAPI(
    title="WhatsApp Automation",
    description="Scheduled WhatsApp Messaging System",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(schedule_router)


@app.get("/")
def home():

    return {
        "application": "WhatsApp Automation",
        "storage": "CSV",
        "scheduler": "running"
    }


@app.get("/health")
def health():

    return {"status": "healthy"}
