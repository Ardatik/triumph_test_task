import logging
from pathlib import Path

import aiofiles
from fastapi import APIRouter, BackgroundTasks, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from report.report_build import ReportBuilder

from .message import send_telegram_notification

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = Path("/tmp/uploads")
REPORT_FOLDER = Path("/tmp/reports")
UPLOAD_FOLDER.mkdir(exist_ok=True, parents=True)
REPORT_FOLDER.mkdir(exist_ok=True, parents=True)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"error": None, "success": False},
    )


@router.post("/", response_class=HTMLResponse)
async def upload_and_build(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    telegram_id: str = Form(default=""),
):
    if not file.filename:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"error": "Файл не выбран", "success": False},
        )
    if not file.filename.endswith((".xlsx", ".xls")):
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": "Поддерживаются только файлы Excel (.xlsx, .xls)",
                "success": False,
            },
        )
    try:
        logger.info("Загружен файл: %s", file.filename)
        content = await file.read()
        input_path = UPLOAD_FOLDER / file.filename
        async with aiofiles.open(input_path, "wb") as f:
            await f.write(content)
        report_filename = f"report_{file.filename}"
        output_path = REPORT_FOLDER / report_filename
        builder = ReportBuilder()
        builder.build_report(input_file=str(input_path), output_file=str(output_path))
        logger.info("Отчёт создан: %s", report_filename)
        telegram_id = telegram_id.strip()
        if telegram_id:
            background_tasks.add_task(send_telegram_notification, telegram_id)
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": None,
                "success": True,
                "report_filename": report_filename,
                "download_url": f"/download/{report_filename}",
                "telegram_id": telegram_id,
            },
        )
    except Exception as e:
        logger.error("Ошибка обработки: %s", e)
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"error": f"Ошибка при обработке файла: {e}", "success": False},
        )


@router.get("/download/{filename}")
async def download_report(filename: str):
    file_path = REPORT_FOLDER / filename
    if not file_path.exists():
        return HTMLResponse(status_code=404, content="Файл не найден")
    return FileResponse(path=str(file_path), filename=filename)
