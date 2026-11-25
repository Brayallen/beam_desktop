import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from beam_designer import BeamLoads, STEEL_SECTIONS, UniformLoad, analyze
from csv_export import CSV_HEADERS, write_results_csv
from main import BeamDesignerApp


class CsvExportTests(unittest.TestCase):
    def test_export_contains_headers_samples_and_exact_values(self):
        loads = BeamLoads((), (UniformLoad(1.0, 0.0, 20.0),))
        result = analyze("simple", 20.0, loads, STEEL_SECTIONS[0])

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "beam-results.csv"
            write_results_csv(path, result)

            contents = path.read_bytes()
            self.assertTrue(contents.startswith(b"\xef\xbb\xbf"))
            self.assertNotIn(b"\n", contents.replace(b"\r\n", b""))

            with path.open(encoding="utf-8-sig", newline="") as file:
                rows = list(csv.reader(file))

        self.assertEqual(rows[0], list(CSV_HEADERS))
        self.assertEqual(len(rows), len(result["x"]) + 1)
        self.assertEqual(len(rows[0]), 4)
        self.assertEqual(rows[1], ["0.000000", "10.000000", "0.000000", "0.000000"])
        self.assertEqual(rows[-1][0], "20.000000")
        self.assertEqual(rows[-1][1], "-10.000000")
        self.assertEqual(rows[-1][2], "0.000000")
        self.assertEqual(rows[-1][3], "0.000000")

        midpoint = rows[len(rows) // 2]
        self.assertEqual(midpoint, ["10.000000", "0.000000", "50.000000", "0.608515"])
        for row_index, row in enumerate(rows[1:]):
            self.assertEqual(len(row), 4)
            self.assertEqual(
                row,
                [
                    f"{result['x'][row_index]:.6f}",
                    f"{result['shear'][row_index]:.6f}",
                    f"{result['moment'][row_index]:.6f}",
                    f"{result['deflection'][row_index]:.6f}",
                ],
            )

    def test_inconsistent_samples_do_not_create_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad-results.csv"
            with self.assertRaisesRegex(ValueError, "inconsistent diagram samples"):
                write_results_csv(
                    path,
                    {
                        "x": [0.0, 1.0],
                        "shear": [1.0],
                        "moment": [0.0, 0.0],
                        "deflection_x": [0.0, 1.0],
                        "deflection": [0.0, 0.0],
                    },
                )
            self.assertFalse(path.exists())

    def test_unanalyzed_results_are_rejected_with_helpful_message(self):
        app = object.__new__(BeamDesignerApp)
        app.master = None
        app.result = None

        with patch("main.messagebox.showerror") as showerror, patch(
            "main.filedialog.asksaveasfilename"
        ) as save_dialog:
            app.export_results_dialog()

        showerror.assert_called_once()
        self.assertIn("analyze the beam", showerror.call_args.args[1])
        save_dialog.assert_not_called()

    def test_cancelled_save_dialog_does_not_export(self):
        app = object.__new__(BeamDesignerApp)
        app.master = None
        app.result = {"x": [0.0]}

        with patch("main.filedialog.asksaveasfilename", return_value=""), patch(
            "main.write_results_csv"
        ) as export, patch("main.messagebox.showinfo") as showinfo:
            app.export_results_dialog()

        export.assert_not_called()
        showinfo.assert_not_called()


if __name__ == "__main__":
    unittest.main()
