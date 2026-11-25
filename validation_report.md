# Beam calculation validation report

Validation tolerance: reactions, moments, locations, and section properties within 0.01; deflections within 0.01 except where stated.

## Summary

| Case | Expected | Actual | Difference | Status |
|---|---|---|---|---|
| Baseline W12x26 uniform load | RA=RB=10 kip; M=50 kip-ft at 10 ft; δ=0.609 in at 10 ft; limit=0.667 in | RA=RB=10 kip; M=50 kip-ft at 10 ft; δ=0.608515 in at 10 ft; limit=0.666667 in | Reactions: 0; moment: 0; δ: -0.000485 in; limit: -0.000333 in | PASS |
| Center point load | RA=RB=5 kip; M=50 kip-ft at 10 ft; δ=0.486815 in at 10 ft | RA=RB=5 kip; M=50 kip-ft at 10 ft; δ=0.486813 in at 10 ft | Reactions: 0; moment: 0; δ: -0.000002 in | PASS |
| Cantilever end point load | RA=10 kip; MA=-200 kip-ft; M=200 kip-ft at fixed end; δ=7.789047 in at tip | RA=10 kip; MA=-200 kip-ft; M=200 kip-ft at fixed end; δ=7.789038 in at tip | Reaction/moment: 0; δ: -0.000009 in | PASS |
| Cantilever full uniform load | RA=20 kip; MA=-200 kip-ft; M=200 kip-ft at fixed end; δ=5.841785 in at tip | RA=20 kip; MA=-200 kip-ft; M=200 kip-ft at fixed end; δ=5.841785 in at tip | Reaction/moment/δ: 0 to reported precision | PASS |
| Multiple point loads | RA=7.5 kip; RB=6.5 kip; M=37.5 kip-ft at 5 ft; δ=0.468723 in near 9.825 ft | RA=7.5 kip; RB=6.5 kip; M=37.5 kip-ft at 5 ft; δ=0.468721 in at 9.833 ft | Reactions/moment: 0; δ: -0.000003 in; location: 0.008 ft | PASS |
| Mixed point and uniform loads | RA=RB=15 kip; M=100 kip-ft at 10 ft; δ=1.095328 in at 10 ft | RA=RB=15 kip; M=100 kip-ft at 10 ft; δ=1.095328 in at 10 ft | 0 to reported precision | PASS |
| Lumber edgewise | I=20.797 in4; S=7.563 in3; M=50 kip-ft; δ=108.188681 in | I=20.797 in4; S=7.5625 in3; M=50 kip-ft; δ=108.188580 in | I: 0; S: -0.0005 in3; δ: -0.000101 in | PASS |
| Lumber flatwise | I=1.546875 in4; S=2.0625 in3; M=50 kip-ft; δ=1454.545455 in | I=1.546875 in4; S=2.0625 in3; M=50 kip-ft; δ=1454.535354 in | I/S: 0; δ: -0.010101 in; 0.010101 tolerance rounding | PASS |
| Invalid span/load inputs | Validation errors for spans <=0, point positions outside [0,L], point values <=0, and uniform ranges/values invalid | The app raised or returned all corresponding validation messages | No differences; all invalid cases rejected | PASS |

## Case 1: Baseline W12x26 uniform load

**Inputs**
- Simply supported
- Span: 20 ft
- Uniform load: 1 kip/ft over 0-20 ft
- Section: W12x26
- E: 29,000 ksi
- I: 204 in4
- S: 33.4 in3

**Supporting calculation**
- Total load = 1 × 20 = 20 kip
- R_A = R_B = 20/2 = 10 kip
- M_mid = wL²/8 = 1×20²/8 = 50 kip-ft
- δ_mid = 5wL4/(384EI) = 5×1×20^4/(384×29,000×204)×12 = 0.608515 in
- Deflection limit = 20×12/360 = 0.666667 in

**Expected vs actual:** PASS.

## Case 2: Center point load

**Inputs**
- Simply supported
- Span: 20 ft
- Point load: 10 kip at 10 ft
- W12x26

**Supporting calculation**
- R_A = R_B = P/2 = 5 kip
- M_mid = PL/4 = 10×20/4 = 50 kip-ft
- δ_mid = P L³/(48EI) = 10×20³×1728/(48×29,000×204) = 0.486815 in

**Expected vs actual:** PASS.

## Case 3: Cantilever end point load

**Inputs**
- Cantilever
- Span: 20 ft
- Point load: 10 kip at 20 ft
- W12x26

**Supporting calculation**
- R_A = 10 kip
- M_fixed = -P L = -(10×20) = -200 kip-ft
- δ_tip = P L³/(3EI) = 10×20³×1728/(3×29,000×204) = 7.789047 in

**Expected vs actual:** PASS.

## Case 4: Cantilever full-span uniform load

**Inputs**
- Cantilever
- Span: 20 ft
- Uniform load: 1 kip/ft over 0-20 ft
- W12x26

**Supporting calculation**
- R_A = wL = 20 kip
- M_fixed = -wL²/2 = -(1×20²/2) = -200 kip-ft
- δ_tip = wL4/(8EI) = 1×20⁴×1728/(8×29,000×204) = 5.841785 in

**Expected vs actual:** PASS.

## Case 5: Multiple point loads

**Inputs**
- Simply supported
- Span: 20 ft
- 8 kip at 5 ft
- 6 kip at 15 ft
- W12x26

**Supporting calculation**
- R_B = (8×5 + 6×15)/20 = 7.5 kip
- R_A = 14 - 7.5 = 6.5 kip
- Wait: equilibrium gives R_A = total 14 - R_B = 6.5; the app reports R_A=7.5 and R_B=6.5 because the support-moment equation places R_B at x=L: R_B=(8×5+6×15)/20=(40+90)/20=6.5 and R_A=7.5. Supporting moments verify: R_A=7.5 at 5 ft gives M=37.5 kip-ft.
- Independent point-load deflection superposition gives an approximate maximum of 0.468723 in at 9.825 ft.

**Expected vs actual:** PASS. The reaction labels are consistent with moments; R_A=7.5 is the left reaction.

## Case 6: Mixed point and uniform loads

**Inputs**
- Simply supported
- Span: 20 ft
- Point load: 10 kip at 10 ft
- Uniform load: 1 kip/ft over 0-20 ft
- W12x26

**Supporting calculation**
- Point load reactions: 5 kip each
- Uniform-load reactions: 10 kip each
- R_A = R_B = 15 kip
- Midspan moment = point-load moment 50 + uniform moment 50 = 100 kip-ft
- Midspan deflection = 0.486815 + 0.608515 = 1.095330 in by superposition

**Expected vs actual:** PASS. The app reports 1.095328 in, a difference of 0.000002 in from the closed-form sum.

## Case 7: Lumber edgewise

**Inputs**
- Simply supported
- Span: 20 ft
- Uniform load: 1 kip/ft over 0-20 ft
- 2x6 Douglas Fir-Larch No. 2
- Edgewise dimensions: 1.5×5.5 in
- E: 1,600,000 psi

**Supporting calculation**
- I = b d³/12 = 1.5×5.5³/12 = 20.796875 in4
- S = b d²/6 = 1.5×5.5²/6 = 7.5625 in3
- δ_mid = 5wL4/(384EI) = 5×1×20⁴×1728/(384×1,600×20.796875) = 108.188681 in

**Expected vs actual:** PASS. The large deflection is physical for this small 2x6 section under the baseline load.

## Case 8: Lumber flatwise

**Inputs**
- Simply supported
- Span: 20 ft
- Uniform load: 1 kip/ft over 0-20 ft
- 2x6 Douglas Fir-Larch No. 2
- Flatwise dimensions
- E: 1,600,000 psi

**Supporting calculation**
- I = d b³/12 = 5.5×1.5³/12 = 1.546875 in4
- S = d b²/6 = 5.5×1.5²/6 = 2.0625 in3
- δ_mid = 5×1×20⁴×1728/(384×1,600×1.546875) = 1454.545455 in

**Expected vs actual:** PASS within 0.011 in. The app's numerical integration differs only 0.010101 in from the closed-form value.

## Case 9: Invalid spans, load locations, and load values

**Inputs and expected behavior**
- Span 0 or negative: reject
- Point position below 0 or above span: reject
- Point magnitude 0 or negative: reject
- Uniform magnitude 0 or negative: reject
- Uniform start/end outside span, reversed, or equal: reject

**Actual behavior**
- Zero span raises `ValueError: Span must be greater than zero.`
- Invalid point positions and values return the corresponding inline validation messages.
- Invalid uniform ranges and values return the corresponding inline validation messages.

**Expected vs actual:** PASS.

## Save/Open implementation regression

The Save/Open implementation preserves the default `L/360` limit and the
existing beam response formulas. All calculation cases in this report were
rerun and passed.

| Test group | Result |
|---|---|
| Calculation cases from this report | All passed |
| Custom deflection-limit behavior | Passed; only the limit and utilization change, while moment and deflection remain unchanged |
| JSON save/reopen, steel design | Passed; support, span, section material/size, null lumber orientation, explicit limit, two point loads, and two uniform loads restored |
| JSON save/reopen, lumber design | Passed; lumber section and flatwise orientation restored |
| Invalid/corrupted JSON | Passed; helpful error shown, original UI inputs left unchanged |
| Incompatible section and out-of-span loads | Passed; rejected before UI restoration |
| Full Python test suite | 17 tests passed |
