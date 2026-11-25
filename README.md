# Beam Designer Desktop

Beam Designer is a Python/Tkinter desktop app for preliminary beam analysis. It evaluates simply supported and cantilever beams with steel or lumber sections under point and uniform loads, and displays the beam, shear, moment, and deflection diagrams with bending and deflection checks.

## Requirements

- Python 3.10 or newer with Tkinter
- ReportLab, installed from `requirements.txt` for PDF export

NumPy and Matplotlib are not required by this implementation: calculations use Python's standard library, and diagrams are drawn with Tkinter and ReportLab.

## Install and run

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main.py
```

## Features

- Save and open beam designs as JSON files.
- Export analyzed results to CSV.
- Export a two-page, US Letter PDF calculation sheet with inputs, diagrams, reactions, design checks, and assumptions.

The original browser-based assignment reference is included in [`index.html`](./index.html).

## Intended use

This application is for preliminary educational engineering analysis. Its section properties and assumptions should be verified; results are not a substitute for applicable design codes or review by a qualified engineer.
