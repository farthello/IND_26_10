import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import ifcopenshell
import ifcopenshell.guid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from daylight.src.main import analyse
from daylight.src.analysis_formatted import make_tables
from runall import run_analyses, save_result


class DaylightTests(unittest.TestCase):
    def test_model_is_preserved_and_result_is_json_serializable(self):
        model = ifcopenshell.file(schema="IFC4")
        guid = ifcopenshell.guid.new()
        model.create_entity("IfcSpace", GlobalId=guid, Name="Office")
        before = model.to_string()
        with patch("analyse_model.src.analyse_model.get_element_bbox", return_value=None):
            result = analyse(model)
        json.dumps(result, allow_nan=False)
        self.assertEqual(model.to_string(), before)
        self.assertEqual(result["rooms"][0]["Room GlobalId"], guid)
        self.assertEqual(result["rooms"][0]["Screening status"], "MISSING AREA")
        self.assertEqual(result["summary"]["total_rooms"], 1)
        with tempfile.TemporaryDirectory() as directory:
            output = save_result(result, directory)
            self.assertEqual({k: v for k, v in json.loads(output.read_text()).items() if k not in ("run_id", "function_results")}, result)
            self.assertEqual(list(output.parent.iterdir()), [output])

    def test_empty_model_runner_writes_only_json(self):
        result = analyse(ifcopenshell.file(schema="IFC4"))
        self.assertEqual(result["summary"]["total_rooms"], 0)
        with tempfile.TemporaryDirectory() as directory:
            run_analyses(ifcopenshell.file(schema="IFC4"), directory)
            output = next(Path(directory).glob("daylight/run-*/result.json"))
            self.assertEqual({k: v for k, v in json.loads(output.read_text()).items() if k not in ("run_id", "function_results")}, result)
            self.assertEqual(list(output.parent.iterdir()), [output])

    def test_threshold_and_missing_area_statuses(self):
        base = dict(global_id="room-guid", name="Office", long_name="Office",
                    floor_area=20.0, total_window_area=2.0, storey="Ground",
                    is_relevant=True, windows=[{"area": 2.0}])
        cases = [({}, "OK"), ({"total_window_area": 1.9}, "FAIL"),
                 ({"windows": [{"area": None}]}, "MISSING AREA"),
                 ({"long_name": "Corridor"}, "N/A"),
                 ({"is_relevant": False}, "REVIEW USE")]
        for updates, expected in cases:
            with self.subTest(expected=expected):
                rows, _ = make_tables({"rooms": [{**base, **updates}]})
                self.assertEqual(rows[0]["Screening status"], expected)


if __name__ == "__main__":
    unittest.main()
