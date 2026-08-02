import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from report.report_build import ReportBuilder

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = Path("uploads")
REPORT_FOLDER = Path("reports")
UPLOAD_FOLDER.mkdir(exist_ok=True)
REPORT_FOLDER.mkdir(exist_ok=True)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"error": None},
    )


@router.post("/", response_class=HTMLResponse)
async def upload_and_build(request: Request, file: UploadFile = File(...)):
    if not file.filename:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"error": "Файл не выбран"},
        )

    if not file.filename.endswith((".xlsx", ".xls")):
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"error": "Поддерживаются только файлы Excel (.xlsx, .xls)"},
        )

    try:
        logger.info("Загружен файл: %s", file.filename)

        input_path = UPLOAD_FOLDER / file.filename
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        report_filename = f"report_{file.filename}"
        output_path = REPORT_FOLDER / report_filename

        builder = ReportBuilder()
        builder.build_report(input_file=str(input_path), output_file=str(output_path))
        logger.info("Отчёт создан: %s", report_filename)

        return FileResponse(
            path=str(output_path),
            filename=report_filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        logger.error("Ошибка обработки: %s", str(e))
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"error": f"Ошибка при обработке файла: {str(e)}"},
        )
