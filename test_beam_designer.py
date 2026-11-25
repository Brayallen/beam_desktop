import unittest

from beam_designer import (
    BeamLoads,
    PointLoad,
    STEEL_SECTIONS,
    UniformLoad,
    analyze,
    reactions,
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

    def test_invalid_span_and_uniform_load(self):
        with self.assertRaises(ValueError):
            analyze("simple", 0.0, BeamLoads((), ()), STEEL_SECTIONS[0])
        loads = BeamLoads((), (UniformLoad(1.0, 10.0, 10.0),))
        with self.assertRaises(ValueError):
            analyze("simple", 20.0, loads, STEEL_SECTIONS[0])


if __name__ == "__main__":
    unittest.main()
