"""Tabular presentation and CSV export for the daylight analysis."""

import csv

from A3.daylight_analysis import EXCLUDED_TYPES


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
