import logging

from report.report_build import ReportBuilder

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    builder = ReportBuilder()
    builder.build_report(input_file="Тестовое_задание.xlsx")
