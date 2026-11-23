import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.guid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from daylight.src.main import analyse
from function_outputs import collect_results, write_function_results
from common.registry import FUNCTION_NAMES
from common._recording import ACTIVE_RECORDS
from runall import save_result


class StructureTests(unittest.TestCase):
    def test_each_function_has_its_own_module(self):
        self.assertEqual(len(FUNCTION_NAMES), 13)
        for name in FUNCTION_NAMES:
            path = ROOT / name / 'src' / (name + '.py')
            functions = [n.name for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef)]
            self.assertEqual(functions, [name])

    def test_calls_are_saved_and_combined_without_changing_analysis(self):
        model = ifcopenshell.file(schema='IFC4')
        for _ in range(2):
            model.create_entity('IfcSpace', GlobalId=ifcopenshell.guid.new(), Name='Office')
        original = model.to_string()
        expected = analyse(model)
        result = collect_results(analyse, model)
        self.assertEqual(model.to_string(), original)
        self.assertEqual({k: result[k] for k in expected}, expected)
        records = result['function_results']
        self.assertEqual(records['get_space_area']['call_count'], 2)
        self.assertEqual(records['run_ifc_analysis']['status'], 'not_called')
        self.assertIsNone(ACTIVE_RECORDS.get())
        with tempfile.TemporaryDirectory() as directory:
            output = save_result(result, Path(directory) / 'results')
            write_function_results(result, Path(directory))
            combined = json.loads(output.read_text())
            for name in FUNCTION_NAMES:
                individual = Path(directory) / name / 'results' / f'result_{name}.json'
                self.assertEqual(json.loads(individual.read_text()), combined['function_results'][name])
            second = collect_results(analyse, ifcopenshell.file(schema='IFC4'))
            write_function_results(second, Path(directory))
            self.assertEqual(second['function_results']['get_space_area']['call_count'], 0)
            self.assertNotEqual(second['run_id'], result['run_id'])
            self.assertTrue(output.exists())

    def test_cli_from_another_directory_and_input_preservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'small model.ifc'
            model = ifcopenshell.file(schema='IFC4')
            model.write(str(source))
            before = source.read_bytes()
            process = subprocess.run([sys.executable, '-B', str(ROOT / 'runall.py'), str(source),
                                      '--results-dir', str(root / 'output')], cwd=root,
                                     capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            files = list((root / 'output').rglob('*.*'))
            self.assertEqual(len(files), 14)
            self.assertTrue(all(p.suffix == '.json' for p in files))
            self.assertEqual(before, source.read_bytes())

    def test_import_does_not_create_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            process = subprocess.run([sys.executable, '-B', '-c',
                f'import sys; sys.path.insert(0, {str(ROOT)!r}); import runall'],
                cwd=directory, capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
