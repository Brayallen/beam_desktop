import json
import tempfile
import unittest
from pathlib import Path

from beam_designer import PointLoad, UniformLoad
from design_io import SavedDesign, open_design, save_design


class DesignIoTests(unittest.TestCase):
    def test_save_and_reopen_restores_all_steel_inputs_and_loads(self):
        design = SavedDesign(
            support="cantilever",
            span_ft=18.5,
            material="steel",
            section="W16x40",
            lumber_orientation=None,
            deflection_limit_in=0.42,
            point_loads=(PointLoad(4.5, 3.25), PointLoad(7.0, 18.5)),
            uniform_loads=(
                UniformLoad(0.75, 0.0, 12.0),
                UniformLoad(1.25, 12.0, 18.5),
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "steel-design.json"
            save_design(path, design)
            reopened = open_design(path)

            self.assertEqual(reopened, design)
            saved_json = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved_json["support"], "cantilever")
            self.assertEqual(saved_json["span_ft"], 18.5)
            self.assertEqual(saved_json["material"], "steel")
            self.assertEqual(saved_json["section"], "W16x40")
            self.assertIsNone(saved_json["lumber_orientation"])
            self.assertEqual(saved_json["deflection_limit_in"], 0.42)
            self.assertEqual(
                saved_json["point_loads"],
                [
                    {"magnitude_kip": 4.5, "position_ft": 3.25},
                    {"magnitude_kip": 7.0, "position_ft": 18.5},
                ],
            )
            self.assertEqual(
                saved_json["uniform_loads"],
                [
                    {"magnitude_kip_per_ft": 0.75, "start_ft": 0.0, "end_ft": 12.0},
                    {"magnitude_kip_per_ft": 1.25, "start_ft": 12.0, "end_ft": 18.5},
                ],
            )

    def test_save_and_reopen_restores_lumber_orientation(self):
        design = SavedDesign(
            support="simple",
            span_ft=10.0,
            material="lumber",
            section="2x8",
            lumber_orientation="flatwise",
            deflection_limit_in=0.25,
            point_loads=(PointLoad(2.0, 5.0),),
            uniform_loads=(UniformLoad(0.3, 1.0, 9.0),),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lumber-design.json"
            save_design(path, design)
            self.assertEqual(open_design(path), design)

    def test_invalid_json_has_helpful_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text('{"support": ', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid JSON at line"):
                open_design(path)

    def test_incompatible_design_is_rejected(self):
        incompatible = {
            "support": "simple",
            "span_ft": 20,
            "material": "steel",
            "section": "W999x999",
            "lumber_orientation": None,
            "deflection_limit_in": 0.5,
            "point_loads": [],
            "uniform_loads": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "incompatible.json"
            path.write_text(json.dumps(incompatible), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not available for steel"):
                open_design(path)

    def test_invalid_loads_are_rejected_before_restore(self):
        invalid = {
            "support": "simple",
            "span_ft": 10,
            "material": "steel",
            "section": "W12x26",
            "lumber_orientation": None,
            "deflection_limit_in": 0.5,
            "point_loads": [{"magnitude_kip": 2, "position_ft": 11}],
            "uniform_loads": [],
        }
        with self.assertRaisesRegex(ValueError, "within the beam span"):
            SavedDesign.from_json_value(invalid)

    def test_non_finite_or_overflowing_numbers_are_rejected(self):
        invalid = {
            "support": "simple",
            "span_ft": 10**10000,
            "material": "steel",
            "section": "W12x26",
            "lumber_orientation": None,
            "deflection_limit_in": 0.5,
            "point_loads": [],
            "uniform_loads": [],
        }
        with self.assertRaisesRegex(ValueError, "span_ft.*finite"):
            SavedDesign.from_json_value(invalid)


if __name__ == "__main__":
    unittest.main()
