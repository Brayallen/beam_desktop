import csv
from pathlib import Path


CSV_HEADERS = (
    "Position, x (ft)",
    "Shear force, V (kip)",
    "Bending moment, M (kip-ft)",
    "Deflection (in)",
)


def write_results_csv(path: str | Path, result: dict) -> None:
    positions = result["x"]
    shears = result["shear"]
    moments = result["moment"]
    deflection_positions = result["deflection_x"]
    deflections = result["deflection"]
    sample_count = len(positions)
    if not sample_count or any(
        len(values) != sample_count
        for values in (shears, moments, deflection_positions, deflections)
    ):
        raise ValueError("The analyzed beam result has inconsistent diagram samples.")

    with Path(path).open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file, lineterminator="\r\n")
        writer.writerow(CSV_HEADERS)
        for index in range(sample_count):
            writer.writerow(
                (
                    f"{positions[index]:.6f}",
                    f"{shears[index]:.6f}",
                    f"{moments[index]:.6f}",
                    f"{deflections[index]:.6f}",
                )
            )
