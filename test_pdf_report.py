import tempfile
import unittest
from pathlib import Path
import re
from unittest.mock import patch

from beam_designer import (
    BeamLoads,
    LUMBER_SECTIONS,
    PointLoad,
    STEEL_SECTIONS,
    UniformLoad,
    analyze,
)
from design_io import SavedDesign
from main import BeamDesignerApp
from pdf_report import create_calculation_sheet


class PdfReportTests(unittest.TestCase):
    def setUp(self):
        self.loads = BeamLoads((), (UniformLoad(1.0, 0.0, 20.0),))
        self.limit = 20.0 * 12.0 / 360.0
        self.section = STEEL_SECTIONS[0]
        self.design = SavedDesign(
            "simple",
            20.0,
            "steel",
            "W12x26",
            None,
            self.limit,
            (),
            self.loads.uniform,
        )
        self.result = analyze(
            "simple",
            20.0,
            self.loads,
            self.section,
            deflection_limit_in=self.limit,
        )

    def test_baseline_pdf_is_created_with_letter_page_layout(self):
        from pypdf import PdfReader

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "baseline.pdf"
            create_calculation_sheet(path, self.design, self.result)

            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 10_000)
            reader = PdfReader(str(path))

        self.assertEqual(len(reader.pages), 2)
        for page in reader.pages:
            self.assertAlmostEqual(float(page.mediabox.width), 612.0)
            self.assertAlmostEqual(float(page.mediabox.height), 792.0)

        page_text = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(page_text)
        self.assertIn("Deflection Diagram", page_text[0])
        self.assertIn("Engineering Assumptions and Limitations", page_text[0])
        self.assertIn("Shear Force Diagram", page_text[1])
        self.assertIn("Bending Moment Diagram", page_text[1])
        for required in (
            "Beam Designer Calculation Sheet",
            "Report date",
            "OVERALL DESIGN STATUS: PASS",
            "Simply supported",
            "20.000 ft",
            "W12x26",
            "1.000 kip/ft",
            "R_A = 10.000 kip",
            "R_B = 10.000 kip",
            "Maximum shear",
            "10.000 kip",
            "Maximum bending moment",
            "50.000 kip-ft",
            "Maximum deflection",
            "0.6085 in",
            "17.964 / 24.000 ksi",
            "Bending Moment Diagram",
            "Deflection Diagram",
            "Engineering Assumptions and Limitations",
            "shear deformation ignored",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)
        self.assertRegex(text, re.compile(r"[A-Z][a-z]+ \d{1,2}, \d{4}"))

    def test_mismatched_results_are_rejected_without_writing(self):
        mismatched_design = SavedDesign(
            "simple",
            15.0,
            "steel",
            "W12x26",
            None,
            self.limit,
            (),
            self.loads.uniform,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stale.pdf"
            with self.assertRaisesRegex(ValueError, "do not match the current inputs"):
                create_calculation_sheet(path, mismatched_design, self.result)
            self.assertFalse(path.exists())

    def test_lumber_cantilever_inputs_and_loads_are_reported(self):
        from pypdf import PdfReader

        loads = BeamLoads(
            (PointLoad(2.0, 5.0), PointLoad(3.0, 10.0)),
            (UniformLoad(0.25, 0.0, 10.0),),
        )
        limit = 10.0 * 12.0 / 360.0
        design = SavedDesign(
            "cantilever",
            10.0,
            "lumber",
            "2x8",
            "flatwise",
            limit,
            loads.point,
            loads.uniform,
        )
        result = analyze(
            "cantilever",
            10.0,
            loads,
            LUMBER_SECTIONS[1],
            orientation="flatwise",
            deflection_limit_in=limit,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lumber-cantilever.pdf"
            create_calculation_sheet(path, design, result)
            text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)

        for required in (
            "Cantilever",
            "Lumber",
            "2x8",
            "Douglas Fir-Larch",
            "flatwise",
            "Point load P1",
            "Point load P2",
            "Uniform load w1",
            "Fixed-end moment M_A",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_missing_results_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.pdf"
            with self.assertRaisesRegex(ValueError, "Analyze the current beam inputs"):
                create_calculation_sheet(path, self.design, None)
            self.assertFalse(path.exists())

    def test_unanalyzed_dialog_shows_helpful_message_without_save_dialog(self):
        app = object.__new__(BeamDesignerApp)
        app.master = None
        app.result = None

        with patch("main.messagebox.showerror") as showerror, patch(
            "main.filedialog.asksaveasfilename"
        ) as save_dialog:
            app.export_pdf_dialog()

        showerror.assert_called_once()
        self.assertIn("analyze the beam", showerror.call_args.args[1])
        save_dialog.assert_not_called()

    def test_canceled_pdf_save_dialog_creates_no_file(self):
        app = object.__new__(BeamDesignerApp)
        app.master = None
        app.result = self.result

        with patch("main.filedialog.asksaveasfilename", return_value=""), patch(
            "main.create_calculation_sheet"
        ) as create_pdf, patch("main.messagebox.showinfo") as showinfo:
            app.export_pdf_dialog()

        create_pdf.assert_not_called()
        showinfo.assert_not_called()


if __name__ == "__main__":
    unittest.main()
