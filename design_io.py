import json
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any

from beam_designer import (
    BeamLoads,
    LUMBER_SECTIONS,
    PointLoad,
    STEEL_SECTIONS,
    UniformLoad,
    validate_inputs,
)


@dataclass(frozen=True)
class SavedDesign:
    support: str
    span_ft: float
    material: str
    section: str
    lumber_orientation: str | None
    deflection_limit_in: float
    point_loads: tuple[PointLoad, ...]
    uniform_loads: tuple[UniformLoad, ...]

    def to_json_value(self) -> dict[str, Any]:
        return {
            "support": self.support,
            "span_ft": self.span_ft,
            "material": self.material,
            "section": self.section,
            "lumber_orientation": self.lumber_orientation,
            "deflection_limit_in": self.deflection_limit_in,
            "point_loads": [
                {"magnitude_kip": load.value, "position_ft": load.position}
                for load in self.point_loads
            ],
            "uniform_loads": [
                {
                    "magnitude_kip_per_ft": load.value,
                    "start_ft": load.start,
                    "end_ft": load.end,
                }
                for load in self.uniform_loads
            ],
        }

    @classmethod
    def from_json_value(cls, value: Any) -> "SavedDesign":
        if not isinstance(value, dict):
            raise ValueError("The design file must contain a JSON object.")

        required_fields = {
            "support",
            "span_ft",
            "material",
            "section",
            "lumber_orientation",
            "deflection_limit_in",
            "point_loads",
            "uniform_loads",
        }
        missing = required_fields - value.keys()
        extra = value.keys() - required_fields
        if missing:
            raise ValueError("The design file is missing required fields: " + ", ".join(sorted(missing)))
        if extra:
            raise ValueError("The design file contains unsupported fields: " + ", ".join(sorted(extra)))

        support = value["support"]
        if support not in ("simple", "cantilever"):
            raise ValueError("Support must be 'simple' or 'cantilever'.")

        material = value["material"]
        if material not in ("steel", "lumber"):
            raise ValueError("Material must be 'steel' or 'lumber'.")

        section = value["section"]
        if not isinstance(section, str):
            raise ValueError("Section must be a section designation.")
        available_sections = (
            {item.designation for item in STEEL_SECTIONS}
            if material == "steel"
            else {item.designation for item in LUMBER_SECTIONS}
        )
        if section not in available_sections:
            raise ValueError(f"Section '{section}' is not available for {material}.")

        orientation = value["lumber_orientation"]
        if material == "steel":
            if orientation is not None:
                raise ValueError("Steel designs must have a null lumber_orientation.")
        elif orientation not in ("edgewise", "flatwise"):
            raise ValueError("Lumber orientation must be 'edgewise' or 'flatwise'.")

        span = _number(value["span_ft"], "span_ft")
        limit = _number(value["deflection_limit_in"], "deflection_limit_in")
        if span <= 0:
            raise ValueError("Beam span must be greater than zero.")
        if limit <= 0:
            raise ValueError("Deflection limit must be greater than zero.")

        points = _load_array(value["point_loads"], "point_loads")
        uniform = _load_array(value["uniform_loads"], "uniform_loads")
        loads = BeamLoads(points, uniform)
        input_error = validate_inputs(span, loads)
        if input_error:
            raise ValueError(input_error)

        return cls(
            support=support,
            span_ft=span,
            material=material,
            section=section,
            lumber_orientation=orientation,
            deflection_limit_in=limit,
            point_loads=points,
            uniform_loads=uniform,
        )


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"'{field}' must be a number.")
    try:
        number = float(value)
    except OverflowError as error:
        raise ValueError(f"'{field}' must be a finite number.") from error
    if not isfinite(number):
        raise ValueError(f"'{field}' must be a finite number.")
    return number


def _load_array(value: Any, field: str) -> tuple:
    if not isinstance(value, list):
        raise ValueError(f"'{field}' must be a JSON array.")

    result = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"'{field}[{index}]' must be a JSON object.")
        if field == "point_loads":
            expected = {"magnitude_kip", "position_ft"}
            if item.keys() != expected:
                raise ValueError(
                    f"'{field}[{index}]' must contain magnitude_kip and position_ft."
                )
            result.append(
                PointLoad(
                    _number(item["magnitude_kip"], f"{field}[{index}].magnitude_kip"),
                    _number(item["position_ft"], f"{field}[{index}].position_ft"),
                )
            )
        else:
            expected = {"magnitude_kip_per_ft", "start_ft", "end_ft"}
            if item.keys() != expected:
                raise ValueError(
                    f"'{field}[{index}]' must contain magnitude_kip_per_ft, start_ft, and end_ft."
                )
            result.append(
                UniformLoad(
                    _number(
                        item["magnitude_kip_per_ft"],
                        f"{field}[{index}].magnitude_kip_per_ft",
                    ),
                    _number(item["start_ft"], f"{field}[{index}].start_ft"),
                    _number(item["end_ft"], f"{field}[{index}].end_ft"),
                )
            )
    return tuple(result)


def save_design(path: str | Path, design: SavedDesign) -> None:
    destination = Path(path)
    with destination.open("w", encoding="utf-8") as file:
        json.dump(design.to_json_value(), file, indent=2, allow_nan=False)
        file.write("\n")


def open_design(path: str | Path) -> SavedDesign:
    source = Path(path)
    try:
        with source.open("r", encoding="utf-8") as file:
            value = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON at line {error.lineno}, column {error.colno}.") from error
    except UnicodeDecodeError as error:
        raise ValueError("The design file is not valid UTF-8 text.") from error
    except RecursionError as error:
        raise ValueError("The design file is nested too deeply to read.") from error
    return SavedDesign.from_json_value(value)
