"""Reusable daylight screening entry point; no model loading or file writes."""

from .daylight_analysis import analyse_model
from .analysis_formatted import make_tables


def analyse(model):
    results = analyse_model(model)
    rows, summary = make_tables(results)
    return {
        "threshold_percent": 10.0,
        "assessment": "Window-to-floor-area screening, not daylight compliance verification",
        "limitations": [
            "Window areas may include frames; they are not verified glass areas.",
            "Window assignment uses bounding boxes and heuristic storey elevations.",
            "Missing geometry or unassigned windows may cause misleading zero-area results.",
            "Room use is classified using name keywords and requires review.",
        ],
        "rooms": rows,
        "summary": summary,
        "room_details": results["rooms"],
    }
