import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from thefuzz import process


class Normalization:
    _CORRECT_CITIES = (
        "Анапа",
        "Краснодар",
        "Сочи",
        "Новороссийск",
        "Ростов-на-Дону",
    )

    _COMPLETED_STATUSES = {
        "выполнен": "Выполнен",
        "завершен": "Выполнен",
        "закрыт": "Выполнен",
    }
    _CANCELED_STATUSES = {
        "отменен": "Отменен",
        "отмена": "Отменен",
        "отказ клиента": "Отменен",
    }

    _POSITIVE_VALUES = {"да", "yes", "1", "истина", "true"}
    _NEGATIVE_VALUES = {"нет", "no", "0", "ложь", "false"}

    _DATE_FORMATS = (
        # .
        "%d.%m.%y",
        "%m.%d.%Y",
        "%m.%d.%y",
        "%Y.%m.%d",
        "%y.%m.%d",
        # -
        "%d-%m-%Y",
        "%d-%m-%y",
        "%m-%d-%Y",
        "%m-%d-%y",
        "%Y-%m-%d",
        "%y-%m-%d",
        # /
        "%d/%m/%Y",
        "%d/%m/%y",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y/%m/%d",
        "%y/%m/%d",
    )

    _MONTHS = {
        "января": 1,
        "январь": 1,
        "янв": 1,
        "февраля": 2,
        "февраль": 2,
        "фев": 2,
        "марта": 3,
        "март": 3,
        "мар": 3,
        "апреля": 4,
        "апрель": 4,
        "апр": 4,
        "мая": 5,
        "май": 5,
        "июня": 6,
        "июнь": 6,
        "июн": 6,
        "июля": 7,
        "июль": 7,
        "июл": 7,
        "августа": 8,
        "август": 8,
        "авг": 8,
        "сентября": 9,
        "сентябрь": 9,
        "сен": 9,
        "октября": 10,
        "октябрь": 10,
        "окт": 10,
        "ноября": 11,
        "ноябрь": 11,
        "ноя": 11,
        "декабря": 12,
        "декабрь": 12,
        "дек": 12,
    }

    def normalize_data(self, data: dict):
        return {
            "id": data.get("ID заказа"),
            "date": self._normalize_date(value=data.get("Дата")),
            "city": self._normalize_city(value=data.get("Город")),
            "contractor": data.get("Исполнитель"),
            "master": self._normalize_master(value=data.get("Мастер")),
            "status": self._normalize_status(value=data.get("Статус заказа")),
            "amount": self._normalize_amount(value=data.get("Сумма")),
            "complaint": self._normalize_yes_no(value=data.get("Рекламация")),
            "photo": self._normalize_yes_no(value=data.get("Фото загружено")),
            "service_type": (data.get("Тип услуги")),
            "source": data.get("Источник"),
            "comment": data.get("Комментарий"),
            "row_number": data.get("Номер строки"),
        }

    def _parse_text_date(self, date_str: str) -> str | None:
        parts = date_str.split()
        if len(parts) != 3:
            return None
        if parts[0].lower() in self._MONTHS:
            month_name = parts[0].lower()
            day_str = parts[1]
        elif parts[1].lower() in self._MONTHS:
            month_name = parts[1].lower()
            day_str = parts[0]
        else:
            return None
        if not day_str.isdigit():
            return None
        day = int(day_str)
        year_str = parts[2]
        if not year_str.isdigit() or (len(year_str) != 2 and len(year_str) != 4):
            return None
        year = int(year_str)
        if len(year_str) == 2:
            year += 2000
        month_num = self._MONTHS[month_name]
        try:
            dt = datetime(year, month_num, day)
            return dt.strftime("%d.%m.%Y")
        except ValueError:
            return None

    def _normalize_date(self, value: Any) -> str | None:
        if not value:
            return None
        date = str(value).strip()
        try:
            datetime.strptime(date, "%d.%m.%Y")
            return date
        except ValueError:
            pass
        for format in self._DATE_FORMATS:
            try:
                dt = datetime.strptime(date, format)
                return dt.strftime("%d.%m.%Y")
            except ValueError:
                continue
        return self._parse_text_date(date)

    def _normalize_city(self, value: str | None) -> str | None:
        if not value:
            return None
        city = value.strip()
        if city in self._CORRECT_CITIES:
            return city
        match = process.extractOne(city, self._CORRECT_CITIES, score_cutoff=80)
        if match:
            return match[0]
        else:
            return None

    def _normalize_master(self, value: str | None):
        if value is not None:
            master = value.strip().split()
            if not master:
                return None
            return " ".join(part.capitalize() for part in master)
        return None

    def _normalize_status(self, value: str) -> str | None:
        if not value:
            return None
        status = value.strip().lower()
        if not status:
            return None
        status_map = {**self._COMPLETED_STATUSES, **self._CANCELED_STATUSES}
        return status_map.get(status, status)

    def _normalize_amount(self, value: Any) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        raw = str(value).strip()
        cleaned = re.sub(r"[^\d.,\-]", "", raw)
        if not cleaned:
            return None
        cleaned = cleaned.replace(",", ".")
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    def _normalize_yes_no(self, value: str | None) -> bool | None:
        if value is not None:
            normalized_value = str(value).strip().lower()
            if normalized_value in self._POSITIVE_VALUES:
                return True
            if normalized_value in self._NEGATIVE_VALUES:
                return False
        return None
