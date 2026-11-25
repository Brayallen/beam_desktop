# Beam Designer

## Purpose
A desktop application written in Python using Tkinter that analyzes a simply
supported or cantilever beam and checks whether a selected steel or lumber
section is strong and stiff enough.

The app is educational and preliminary-design focused. It must show the
assumptions and section-property basis used for every result.

## Platform and implementation

- Python desktop application using Tkinter
- Cross-platform windowing with native Tk widgets
- Standard-library modules should be preferred for the initial implementation
- The engineering calculations and data tables should be separate from the
  Tkinter presentation code
- Matplotlib or another plotting library may be used for the beam sketch and
  diagrams if it is available without requiring a server
- No web server or browser-based UI is required

## Inputs

- Beam support:
  - Simply supported
  - Cantilever
- Beam span in feet
- Loads:
  - One or more point loads, each with magnitude and location from the left end
  - One or more uniformly distributed loads, each with magnitude and
    start/end locations from the left end
- Section:
  - Steel W-shape selected from a built-in section table
  - Lumber size, species, and grade selected from a built-in section table
- Display units:
  - Imperial units (kips, pounds, feet, inches, ksi, and psi)

By default, do not include beam self-weight. If self-weight is added later, it
must be a separate calculated uniform load and clearly distinguishable from
user-entered loads.

## Beam and section properties

Each steel W-shape record must include:

- Shape designation
- Weight per foot
- Area
- Depth
- Strong-axis moment of inertia, \(I_x\)
- Strong-axis elastic section modulus, \(S_x\)

Each lumber record must include:

- Nominal and actual dressed dimensions
- Species
- Grade or reference grade
- Modulus of elasticity, \(E\)
- Strong-axis bending stress, \(F_b\)
- Strong-axis moment of inertia, \(I\)
- Strong-axis section modulus, \(S\)

The lumber orientation must be explicit: edgewise or flatwise.

Record the source and revision of any section-property and lumber-property
table used by the app. Do not infer section properties or allowable stresses
from nominal size alone.

## Calculation assumptions

- Prismatic, homogeneous, linearly elastic beam
- Loads are vertical and perpendicular to the beam
- Major-axis bending only
- Deflection is caused only by bending; shear deformation is ignored
- No axial load or torsion
- Simply supported or cantilever boundary conditions only
- Small-deflection theory
- Steel modulus of elasticity: \(E = 29{,}000\) ksi
- No buckling, lateral-torsional buckling, web yielding, or shear check
- No load combinations or safety-factor/load-duration combinations
- Segment and diagram sign conventions are documented in the interface

## Calculations

- Reactions from static equilibrium
- Shear force and bending moment along the beam
- Maximum absolute shear
- Maximum absolute bending moment and its location
- Bending stress \(f_b = M/S\)
- Maximum bending stress and bending utilization \(f_b/F_b\)
- Elastic deflection along the beam
- Maximum absolute deflection and its location
- Deflection limit: \(L/360\) by default
- Deflection utilization: maximum deflection divided by the selected limit

For steel, use the selected \(S_x\) for bending stress and \(I_x\) for
deflection. For lumber, use the selected orientation-specific \(I\) and \(S\).

Point-load positions and distributed-load endpoints must lie within the beam
span. Zero-length distributed loads are invalid. Support and load values must
be positive or meaningful at the documented sign convention.

## Outputs

- Beam sketch with supports, span, and all loads
- Reaction values
- Shear, moment, and deflection diagrams
- Maximum shear, moment, and deflection values with locations
- Selected section properties
- Allowable bending stress and deflection limit
- Separate bending and deflection pass/fail results
- Overall result that is:
  - Pass only if both checks pass
  - Fail if either check fails
- Utilization percentages for bending and deflection
- Expandable assumption and calculation-summary sections

## Look and feel

- Clean, professional, engineering-tool interface
- Example beam loaded when the app opens
- Clear distinction between inputs, diagrams, and results
- Inline validation near the affected input
- Responsive layout within resizable desktop windows
- Accessible labels, contrast, and keyboard navigation
- Numerical and diagram units shown next to values
- Diagrams use consistent signs and adaptive scales

## Validation

The baseline W12x26 example is:

- 20 ft simply supported beam
- 1 kip/ft full-span uniform load
- \(E = 29{,}000\) ksi
- \(I_x = 204\) in4
- Maximum moment: 50.0 kip-ft
- Maximum deflection: approximately 0.609 in

This example should also verify:

- Reactions: 10 kip at each support
- Maximum moment location: midspan
- Maximum deflection location: midspan
- Deflection limit: \(20 ft / 360 = 0.667 in\)

Additional hand-calculation cases must cover:

- Center point load on a simply supported beam
- End point load on a cantilever
- Full-span uniform load on a cantilever
- Multiple point loads
- Mixed point and uniform loads
- Steel and lumber sections
- Invalid spans, load locations, and load values

## Out of scope

- Continuous beams
- Fixed-end beams
- Frames or trusses
- Buckling and lateral-torsional buckling
- Shear and connection design
- Concrete design
- Load combinations
- Live-load patterns
- Seismic or wind analysis
- Beam self-weight, unless separately implemented and tested later
- Metric unit entry
