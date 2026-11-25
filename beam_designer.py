from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Sequence


@dataclass(frozen=True)
class PointLoad:
    value: float
    position: float


@dataclass(frozen=True)
class UniformLoad:
    value: float
    start: float
    end: float


@dataclass(frozen=True)
class BeamLoads:
    point: tuple[PointLoad, ...]
    uniform: tuple[UniformLoad, ...]


@dataclass(frozen=True)
class SteelSection:
    designation: str
    area: float
    depth: float
    weight: float
    Ix: float
    Sx: float
    E: float = 29000000.0
    Fb: float = 24.0


@dataclass(frozen=True)
class LumberSection:
    designation: str
    species: str
    grade: str
    actual_width: float
    actual_depth: float
    E: float
    Fb: float


STEEL_SECTIONS = (
    SteelSection("W12x26", 7.65, 12.22, 26.0, 204.0, 33.4),
    SteelSection("W12x30", 8.79, 12.34, 30.0, 238.0, 38.6),
    SteelSection("W14x30", 8.85, 13.84, 30.0, 291.0, 42.0),
    SteelSection("W16x40", 11.8, 16.01, 40.0, 518.0, 64.7),
)

LUMBER_SECTIONS = (
    LumberSection("2x6", "Douglas Fir-Larch", "No. 2", 1.5, 5.5, 1_600_000.0, 900.0),
    LumberSection("2x8", "Douglas Fir-Larch", "No. 2", 1.5, 7.25, 1_600_000.0, 900.0),
    LumberSection("2x10", "Douglas Fir-Larch", "No. 2", 1.5, 9.25, 1_600_000.0, 900.0),
)

SECTION_SOURCES = {
    "steel": "Approximate section properties — verify against the project-approved AISC shape table",
    "lumber": "Representative Douglas Fir-Larch No. 2 values — verify against the project-approved lumber reference",
}


def validate_inputs(span: float, loads: BeamLoads) -> str:
    if not isfinite(span) or span <= 0:
        return "Span must be greater than zero."
    for load in loads.point:
        if not isfinite(load.value) or load.value <= 0:
            return "Point loads must be greater than zero."
        if not isfinite(load.position) or load.position < 0 or load.position > span:
            return "Point-load positions must be within the beam span."
    for load in loads.uniform:
        if not isfinite(load.value) or load.value <= 0:
            return "Uniform loads must be greater than zero."
        if (
            not isfinite(load.start)
            or not isfinite(load.end)
            or load.start < 0
            or load.end > span
            or load.end <= load.start
        ):
            return "Uniform-load start and end must be in order and within the beam span."
    return ""


def reactions(support: str, span: float, loads: BeamLoads) -> dict[str, float]:
    total_point = sum(load.value for load in loads.point)
    total_uniform = sum(load.value * (load.end - load.start) for load in loads.uniform)
    total = total_point + total_uniform
    point_moment = sum(load.value * load.position for load in loads.point)
    uniform_moment = sum(
        load.value * (load.end * load.end - load.start * load.start) / 2
        for load in loads.uniform
    )

    if support == "cantilever":
        return {"RA": total, "RB": 0.0, "MA": -(point_moment + uniform_moment)}

    rb = (point_moment + uniform_moment) / span
    return {"RA": total - rb, "RB": rb, "MA": 0.0}


def shear_at(support: str, x: float, span: float, loads: BeamLoads, reaction: dict[str, float]) -> float:
    value = reaction["RA"]
    for load in loads.point:
        value -= load.value * (1.0 if x >= load.position else 0.0)
    for load in loads.uniform:
        value -= load.value * (
            max(0.0, x - load.start) - max(0.0, x - load.end)
        )
    return value


def moment_at(support: str, x: float, span: float, loads: BeamLoads, reaction: dict[str, float]) -> float:
    del span
    if support == "cantilever":
        value = 0.0
        for load in loads.point:
            value -= load.value * max(0.0, load.position - x)
        for load in loads.uniform:
            value -= load.value * (
                (max(0.0, load.end - x) ** 2 - max(0.0, load.start - x) ** 2) / 2.0
            )
        return value

    value = reaction["RA"] * x
    for load in loads.point:
        value -= load.value * max(0.0, x - load.position)
    for load in loads.uniform:
        value -= load.value * (
            0.5 * max(0.0, x - load.start) ** 2
            - 0.5 * max(0.0, x - load.end) ** 2
        )
    return value


def section_properties(
    section: SteelSection | LumberSection, orientation: str = "edgewise"
) -> tuple[float, float, float, float]:
    if isinstance(section, SteelSection):
        return section.Ix, section.Sx, section.E, section.Fb
    if orientation == "flatwise":
        inertia = section.actual_depth * section.actual_width ** 3 / 12.0
        modulus = section.actual_depth * section.actual_width ** 2 / 6.0
    else:
        inertia = section.actual_width * section.actual_depth ** 3 / 12.0
        modulus = section.actual_width * section.actual_depth ** 2 / 6.0
    return inertia, modulus, section.E, section.Fb


def slope_and_deflection(
    support: str,
    span: float,
    loads: BeamLoads,
    reaction: dict[str, float],
    E_psi: float,
    I_in4: float,
    samples: int = 481,
) -> tuple[list[float], list[float]]:
    dx = span * 12.0 / (samples - 1)
    x_ft = []
    moment_values = []
    for index in range(samples):
        x_in = index * dx
        x = x_in / 12.0
        x_ft.append(x)
        moment_values.append(moment_at(support, x, span, loads, reaction))

    E = E_psi / 1000.0
    curvature = [moment * 12.0 / (E * I_in4) for moment in moment_values]
    slope = [0.0] * samples
    deflection = [0.0] * samples
    for index in range(1, samples):
        slope[index] = slope[index - 1] - (curvature[index - 1] + curvature[index]) * dx / 2.0
        deflection[index] = (
            deflection[index - 1] + (slope[index - 1] + slope[index]) * dx / 2.0
        )

    if support == "simple":
        slope_correction = deflection[-1] / (span * 12.0)
        deflection = [
            value - slope_correction * index * dx
            for index, value in enumerate(deflection)
        ]
    return x_ft, deflection


def analyze(
    support: str,
    span: float,
    loads: BeamLoads,
    section: SteelSection | LumberSection,
    orientation: str = "edgewise",
    samples: int = 481,
    deflection_limit_in: float | None = None,
) -> dict:
    error = validate_inputs(span, loads)
    if error:
        raise ValueError(error)

    I, S, E_psi, Fb = section_properties(section, orientation)
    reaction = reactions(support, span, loads)
    x = [span * index / (samples - 1) for index in range(samples)]
    shear = [shear_at(support, point, span, loads, reaction) for point in x]
    moment = [moment_at(support, point, span, loads, reaction) for point in x]
    deflection_x, deflection = slope_and_deflection(
        support, span, loads, reaction, E_psi, I, samples
    )

    max_moment = max(moment, key=abs)
    max_shear = max(shear, key=abs)
    max_deflection = max(deflection, key=abs)
    moment_location = x[moment.index(max_moment)]
    shear_location = x[shear.index(max_shear)]
    deflection_location = deflection_x[deflection.index(max_deflection)]

    moment_in_kip_in = max_moment * 12.0
    bending_stress_ksi = abs(moment_in_kip_in / S)
    if isinstance(section, LumberSection):
        allowable_ksi = Fb / 1000.0
    else:
        allowable_ksi = section.Fb
    bending_ratio = bending_stress_ksi / allowable_ksi
    if deflection_limit_in is None:
        deflection_limit = span * 12.0 / 360.0
    elif not isfinite(deflection_limit_in) or deflection_limit_in <= 0:
        raise ValueError("Deflection limit must be greater than zero.")
    else:
        deflection_limit = deflection_limit_in
    deflection_ratio = abs(max_deflection) / deflection_limit

    bending_pass = bending_ratio <= 1.0
    deflection_pass = deflection_ratio <= 1.0
    return {
        "span": span,
        "support": support,
        "loads": loads,
        "section": section,
        "orientation": orientation,
        "I": I,
        "S": S,
        "E": E_psi,
        "Fb": allowable_ksi,
        "reaction": reaction,
        "x": x,
        "shear": shear,
        "moment": moment,
        "deflection_x": deflection_x,
        "deflection": deflection,
        "max_moment": max_moment,
        "moment_location": moment_location,
        "max_shear": max_shear,
        "shear_location": shear_location,
        "max_deflection": max_deflection,
        "deflection_location": deflection_location,
        "bending_stress": bending_stress_ksi,
        "allowable": allowable_ksi,
        "bending_ratio": bending_ratio,
        "deflection_limit": deflection_limit,
        "deflection_ratio": deflection_ratio,
        "bending_pass": bending_pass,
        "deflection_pass": deflection_pass,
        "overall_pass": bending_pass and deflection_pass,
    }
