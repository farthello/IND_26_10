"""Tabular presentation and CSV/XLSX export for the daylight analysis."""

import csv
from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

if __package__:
    from .daylight_analysis import EXCLUDED_TYPES
else:
    from A4.Analysis.daylight_analysis import EXCLUDED_TYPES


def make_tables(results, threshold=10.0):
    rows = []
    for room in results["rooms"]:
        area = room["floor_area"]
        window_area = room["total_window_area"]
        ratio = 100 * window_area / area if area and area > 0 else None
        use = (room["long_name"] or room["name"]).lower()
        if any(keyword in use for keyword in EXCLUDED_TYPES):
            status = "N/A"
        elif not room["is_relevant"]:
            status = "REVIEW USE"
        elif ratio is None or any(w["area"] is None for w in room["windows"]):
            status = "MISSING AREA"
        else:
            status = "OK" if ratio >= threshold else "FAIL"
        rows.append({
            "Storey": room["storey"],
            "Room": room["name"],
            "Use": room["long_name"],
            "Floor area (m²)": area,
            "Window area (m²)": window_area,
            "Windows": len(room["windows"]),
            "Window-to-floor ratio (%)": ratio,
            "Screening status": status,
        })
    summary = {key: value for key, value in results.items() if key != "rooms"}
    for status in ("OK", "FAIL", "REVIEW USE", "MISSING AREA", "N/A"):
        summary[status] = sum(row["Screening status"] == status for row in rows)
    return rows, summary


def export_csv(rows, path):
    if not rows:
        raise ValueError("No room rows to export.")
    with open(path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export_xlsx(rows, path):
    """Export room results with banded rows and screening status highlights."""
    if not rows:
        raise ValueError("No room rows to export.")

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Results"
    sheet.freeze_panes = "A2"
    sheet.sheet_view.showGridLines = False

    columns = list(rows[0])
    status_column = "Screening status"
    widths = {
        "Storey": 13,
        "Room": 10,
        "Use": 39,
        "Floor area (m²)": 17,
        "Window area (m²)": 19,
        "Windows": 11,
        "Window-to-floor ratio (%)": 28,
        status_column: 22,
    }
    number_formats = {
        "Floor area (m²)": "#,##0.00",
        "Window area (m²)": "#,##0.00",
        "Windows": "#,##0",
        "Window-to-floor ratio (%)": '0.0"%"',
    }

    header_font = Font(name="Arial", size=10, bold=True, color="FF1D4542")
    body_font = Font(name="Arial", size=10, color="FF263242")
    header_fill = PatternFill("solid", fgColor="FFE2EFED")
    band_fill = PatternFill("solid", fgColor="FFF1F7F6")
    header_border = Border(bottom=Side(style="thin", color="FFAAC5C1"))
    centered = Alignment(horizontal="center", vertical="center")
    right_aligned = Alignment(horizontal="right", vertical="center")
    middle = Alignment(vertical="center")

    sheet.append(columns)
    sheet.row_dimensions[1].height = 28.5
    for cell, column in zip(sheet[1], columns):
        cell.font = header_font
        cell.fill = header_fill
        cell.border = header_border
        cell.alignment = centered
        sheet.column_dimensions[cell.column_letter].width = widths.get(
            column, max(12, len(str(column)) + 3)
        )

    for row_index, row in enumerate(rows, start=2):
        sheet.append([row.get(column) for column in columns])
        sheet.row_dimensions[row_index].height = 21
        for cell, column in zip(sheet[row_index], columns):
            cell.font = body_font
            cell.alignment = middle
            if row_index % 2 == 1:
                cell.fill = band_fill
            if column in number_formats:
                cell.number_format = number_formats[column]
                cell.alignment = right_aligned
            if column == status_column:
                cell.alignment = centered

    if status_column in columns:
        letter = get_column_letter(columns.index(status_column) + 1)
        status_range = f"{letter}2:{letter}{sheet.max_row}"
        status_styles = {
            "OK": ("FFE2F1E7", "FF24563A"),
            "FAIL": ("FFFBE6E5", "FF8D252A"),
            "REVIEW USE": ("FFFFF0CC", "FF764900"),
            "N/A": (None, "FF566373"),
        }
        for status, (background, text) in status_styles.items():
            fill = None
            if background:
                fill = PatternFill("solid", fgColor=background, bgColor=background)
            sheet.conditional_formatting.add(
                status_range,
                FormulaRule(
                    formula=[f'${letter}2="{status}"'],
                    font=Font(color=text, bold=background is not None),
                    fill=fill,
                ),
            )

    workbook.save(path)
