import unittest

from beam_designer import (
    BeamLoads,
    LUMBER_SECTIONS,
    PointLoad,
    STEEL_SECTIONS,
    UniformLoad,
    analyze,
    validate_inputs,
)


class BeamDesignerTests(unittest.TestCase):
    def test_baseline_uniform_load(self):
        loads = BeamLoads(
            point=(),
            uniform=(UniformLoad(1.0, 0.0, 20.0),),
        )
        result = analyze("simple", 20.0, loads, STEEL_SECTIONS[0])
        self.assertAlmostEqual(result["reaction"]["RA"], 10.0, places=8)
        self.assertAlmostEqual(result["reaction"]["RB"], 10.0, places=8)
        self.assertAlmostEqual(abs(result["max_moment"]), 50.0, places=6)
        self.assertAlmostEqual(result["moment_location"], 10.0, delta=0.05)
        self.assertAlmostEqual(abs(result["max_deflection"]), 0.609, delta=0.003)
        self.assertAlmostEqual(result["deflection_limit"], 0.667, delta=0.001)

    def test_center_point_load(self):
        loads = BeamLoads(point=(PointLoad(10.0, 10.0),), uniform=())
        result = analyze("simple", 20.0, loads, STEEL_SECTIONS[0])
        self.assertAlmostEqual(result["reaction"]["RA"], 5.0, places=8)
        self.assertAlmostEqual(result["reaction"]["RB"], 5.0, places=8)
        self.assertAlmostEqual(abs(result["max_moment"]), 50.0, places=6)

    def test_cantilever_end_point_load(self):
        loads = BeamLoads(point=(PointLoad(10.0, 20.0),), uniform=())
        result = analyze("cantilever", 20.0, loads, STEEL_SECTIONS[0])
        self.assertAlmostEqual(result["reaction"]["RA"], 10.0, places=8)
        self.assertAlmostEqual(result["reaction"]["MA"], -200.0, places=8)
        self.assertAlmostEqual(abs(result["max_deflection"]), 7.7890466531, delta=0.001)

    def test_cantilever_full_uniform_load(self):
        loads = BeamLoads(point=(), uniform=(UniformLoad(1.0, 0.0, 20.0),))
        result = analyze("cantilever", 20.0, loads, STEEL_SECTIONS[0])
        self.assertAlmostEqual(result["reaction"]["RA"], 20.0, places=8)
        self.assertAlmostEqual(result["reaction"]["MA"], -200.0, places=8)
        self.assertAlmostEqual(abs(result["max_deflection"]), 5.8417849899, delta=0.001)

    def test_multiple_point_loads(self):
        loads = BeamLoads(
            point=(PointLoad(8.0, 5.0), PointLoad(6.0, 15.0)),
            uniform=(),
        )
        result = analyze("simple", 20.0, loads, STEEL_SECTIONS[0])
        self.assertAlmostEqual(result["reaction"]["RA"], 7.5, places=8)
        self.assertAlmostEqual(result["reaction"]["RB"], 6.5, places=8)
        self.assertAlmostEqual(abs(result["max_moment"]), 37.5, places=6)
        self.assertAlmostEqual(abs(result["max_deflection"]), 0.4687226383, delta=0.001)

    def test_mixed_point_and_uniform_loads(self):
        loads = BeamLoads(
            point=(PointLoad(10.0, 10.0),),
            uniform=(UniformLoad(1.0, 0.0, 20.0),),
        )
        result = analyze("simple", 20.0, loads, STEEL_SECTIONS[0])
        self.assertAlmostEqual(result["reaction"]["RA"], 15.0, places=8)
        self.assertAlmostEqual(result["reaction"]["RB"], 15.0, places=8)
        self.assertAlmostEqual(abs(result["max_moment"]), 100.0, places=6)
        self.assertAlmostEqual(abs(result["max_deflection"]), 1.0953283469, delta=0.001)

    def test_lumber_edgewise_and_flatwise_sections(self):
        loads = BeamLoads(point=(), uniform=(UniformLoad(1.0, 0.0, 20.0),))

        edge = analyze("simple", 20.0, loads, LUMBER_SECTIONS[0], "edgewise")
        self.assertAlmostEqual(edge["I"], 20.797, delta=0.001)
        self.assertAlmostEqual(edge["S"], 7.5625, delta=0.001)
        self.assertAlmostEqual(abs(edge["max_deflection"]), 108.1886811, delta=0.01)

        flat = analyze("simple", 20.0, loads, LUMBER_SECTIONS[0], "flatwise")
        self.assertAlmostEqual(flat["I"], 1.546875, delta=0.000001)
        self.assertAlmostEqual(flat["S"], 2.0625, delta=0.000001)
        self.assertAlmostEqual(abs(flat["max_deflection"]), 1454.5454545, delta=0.011)

    def test_invalid_span_and_uniform_load(self):
        with self.assertRaises(ValueError):
            analyze("simple", 0.0, BeamLoads((), ()), STEEL_SECTIONS[0])
        loads = BeamLoads((), (UniformLoad(1.0, 10.0, 10.0),))
        with self.assertRaises(ValueError):
            analyze("simple", 20.0, loads, STEEL_SECTIONS[0])

    def test_invalid_point_load_position_and_value(self):
        invalid_position = BeamLoads((PointLoad(5.0, 21.0),), ())
        invalid_value = BeamLoads((PointLoad(0.0, 10.0),), ())
        self.assertEqual(
            validate_inputs(20.0, invalid_position),
            "Point-load positions must be within the beam span.",
        )
        self.assertEqual(
            validate_inputs(20.0, invalid_value),
            "Point loads must be greater than zero.",
        )

    def test_invalid_uniform_load_ranges_and_values(self):
        invalid_range = BeamLoads((), (UniformLoad(1.0, 12.0, 10.0),))
        invalid_position = BeamLoads((), (UniformLoad(1.0, -1.0, 10.0),))
        invalid_value = BeamLoads((), (UniformLoad(0.0, 0.0, 10.0),))
        self.assertEqual(
            validate_inputs(20.0, invalid_range),
            "Uniform-load start and end must be in order and within the beam span.",
        )
        self.assertEqual(
            validate_inputs(20.0, invalid_position),
            "Uniform-load start and end must be in order and within the beam span.",
        )
        self.assertEqual(
            validate_inputs(20.0, invalid_value),
            "Uniform loads must be greater than zero.",
        )


if __name__ == "__main__":
    unittest.main()
