from fastapi import FastAPI

from routers.report import router as report_router

app = FastAPI(title="Report Builder", version="1.0")

app.include_router(report_router)
