from datetime import date, datetime
from typing import Any

from .models import ReportOrder, ValidationError


class OrderValidator:
    _REQUIRED_FIELDS = {
        "id": "ID заказа",
        "date": "Дата",
        "city": "Город",
        "master": "Мастер",
        "status": "Статус заказа",
        "amount": "Сумма",
        "complaint": "Рекламация",
        "photo": "Фото загружено",
    }

    _ERROR_MESSAGES = {
        "id": "Дубликат или отсутствует ID заказа",
        "date": "Некорректная дата",
        "city": "Город не указан или не распознан",
        "master": "Мастер не указан",
        "status": "Статус заказа не распознан",
        "amount": "Сумма не является числом",
        "complaint": "Рекламация не распознана",
        "photo": "Фото загружено не распознано",
    }

    _VALID_STATUSES = {"Выполнен", "Отменен"}

    _DATE_FORMAT = "%d.%m.%Y"

    def __init__(self, normalizer):
        self.normalizer = normalizer

    def validate(
        self, data: list[dict[str, Any]]
    ) -> tuple[list[ReportOrder], list[ValidationError]]:
        valid_orders: list[ReportOrder] = []
        validation_errors: list[ValidationError] = []
        seen_order_ids: set[str] = set()
        for row in data:
            normalized_row = self.normalizer.normalize_data(data=row)
            row_number: int = normalized_row["row_number"]
            order_id: str = normalized_row["id"]
            norm_status = normalized_row.get("status")
            if norm_status is not None and norm_status not in self._VALID_STATUSES:
                continue
            row_errors: list[ValidationError] = []
            self._validate_required_fields(
                normalized_row=normalized_row, data=row, errors=row_errors
            )
            parsed_date = self._validate_date_field(
                data=normalized_row, errors=row_errors
            )
            self._validate_duplicate_id(
                order_id=order_id,
                row_number=row_number,
                raw_row=row,
                errors=row_errors,
                seen_order_id=seen_order_ids,
            )
            if row_errors:
                validation_errors.extend(row_errors)
                continue
            valid_orders.append(
                self._build_report_order(
                    order_id=order_id,
                    parsed_date=parsed_date,
                    data=normalized_row,
                )
            )
        return valid_orders, validation_errors

    def _validate_required_fields(
        self,
        normalized_row: dict,
        data: dict,
        errors: list[ValidationError],
    ) -> None:
        row_number = normalized_row["row_number"]
        order_id = normalized_row.get("id")

        for field_key, source_column in self._REQUIRED_FIELDS.items():
            if normalized_row.get(field_key) is None:
                errors.append(
                    ValidationError(
                        row_number=row_number,
                        order_id=order_id,
                        field=source_column,
                        message=self._ERROR_MESSAGES[field_key],
                        value=data.get(source_column),
                    )
                )

    def _validate_date_field(
        self,
        data: dict,
        errors: list[ValidationError],
    ) -> date | None:
        row_number = data["row_number"]
        order_id = data.get("id")
        date = data.get("date")
        if date is None:
            return None
        try:
            return datetime.strptime(date, self._DATE_FORMAT).date()
        except ValueError:
            errors.append(
                ValidationError(
                    row_number=row_number,
                    order_id=order_id,
                    field="Дата",
                    message="Некорректная дата",
                    value=date,
                )
            )
            return None

    def _validate_duplicate_id(
        self,
        order_id: str,
        row_number: int,
        raw_row: dict,
        errors: list[ValidationError],
        seen_order_id: set[str],
    ) -> None:
        if order_id in seen_order_id:
            errors.append(
                ValidationError(
                    row_number=row_number,
                    order_id=order_id,
                    field="ID заказа",
                    message="Дубликат ID заказа, строка исключена",
                    value=raw_row.get("ID заказа"),
                )
            )
        else:
            seen_order_id.add(order_id)

    def _build_report_order(
        self,
        order_id: str,
        parsed_date: date,
        data: dict,
    ) -> ReportOrder:
        return ReportOrder(
            id=order_id,
            date=parsed_date,
            city=data["city"],
            contractor=data.get("contractor", ""),
            master=data["master"],
            status=data["status"],
            amount=data["amount"],
            complaint=data["complaint"],
            photo=data["photo"],
            service_type=data.get("service_type", ""),
            source=data.get("source", ""),
            comment=data.get("comment"),
            row_number=data["row_number"],
        )
