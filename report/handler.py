from openpyxl import load_workbook


class ExcelHandler:
    @staticmethod
    def read_file(filename: str, sheet_name: str = "Заказы_сырье") -> list[dict]:
        wb = load_workbook(filename=filename, read_only=True)
        sheet = wb[sheet_name]
        rows = sheet.iter_rows(values_only=True)
        headers = next(rows)
        orders = []
        for row, value in enumerate(rows, start=2):
            data = dict(zip(headers, value))
            data["Номер строки"] = row
            orders.append(data)

        wb.close()
        return orders
