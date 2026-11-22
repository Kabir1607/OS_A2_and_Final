# A6 manual checks and A7 placement reasoning

These calculations were derived from reader demand, FIFO admission, and two
librarians. `tests/reference_a2.py` independently walks every time unit and
produces the full [workbook](fixture_derivations.md) and 54 golden files. It
imports no production parser, allocator, scheduler, metrics, or formatter.
Normal regression tests read golden files; they do not rewrite them.

## Eight small hand-checked fixtures

M = seat admission, S = first dispatch, C = completion. Unless stated otherwise,
all priorities tie, and the values hold for all six scheduler/allocator choices.
The unit-test anchors independently check the following timestamps and totals.

| Fixture | Hand check | Occupied seat-time | Peak | Maximum fragmentation |
|---|---|---:|---:|---:|
| initial_idle | R1 M=S=5, C=8, holds 2 seats for 3 units | 2×3=6 | 2 | 0 |
| head_of_line | R1 M=S=0,C=4; R2 M=S=4,C=6; R3 M=S=4,C=5. R3 cannot bypass R2. | 4×4 + 3×2 + 1×1=23 | 4 | 0 |
| completion_arrival | R1/R2 finish at 3; R3 receives all six seats at 3, finishes 5; R4 then runs 5–6. | 6×3 + 6×2 + 1=31 | 6 | 0 |
| request_bounds | R1 takes all seats 0–2; R2/R3 arrive 1, enter at 2, finish at 3/4. | 6×2 + 1×1 + 1×2=15 | 6 | 1 |
| fragmented_wait | R1 C=2; R2 C=6; R3 M=0,S=2,C=4; R4 arrives 2 but needs 3 adjacent seats and waits until 6, C=7. | 2×2 + 2×6 + 2×4 + 3×1=27 | 6 | 2 |
| equal_holes_coalescing | R1/R2/R3 as above; R4/R5 enter at 4, run 4–5 and 5–6; adjacent groups reunite on release. | 4+12+8+1+2=27 | 6 | 1 |
| long_idle_gap | R1 0–2; R2 20–21; R3 25–27. Empty intervals count in the elapsed denominator. | 1×2 + 6×1 + 2×2=12 | 6 | 0 |
| simultaneous_arrivals | Admission order R1,R10,R2. FCFS: R1 0–3,R10 0–2,R2 2–4. Priority: R10/R2 0–2,R1 2–5. | Both: 9 | 3 | FCFS 2; Priority 0 |

For the last fixture, FCFS fragmentation peaks at t=3, not t=2: only seat 2
is reserved, giving free runs of lengths 2 and 3, so F=5−3=2. This late-state
check matters even though service order was already determined.

All statistics use the window from first arrival through last completion.
Pool percentage = seat-time / (6×window length) × 100. For example the HOL
case gives 23/36×100=63.8889%. Full pool and empty pool both have F=0.

## Comparison workload: where placement diverges

At t=5, R03 has completed; R05 still owns seat 3. The free groups are 0–2
(length 3) and 4–5 (length 2). The new two-seat R04 request therefore goes to
0 under First/Worst Fit and to 4 under Best Fit. R08's one-seat request then
uses seat 2, 0, or 4 respectively. At t=6 R01 uses seat 4, 1, or 2.

| Timestamp | FIRST_FIT seats 0–5 | BEST_FIT | WORST_FIT |
|---:|---|---|---|
| 5, after admission | R04 R04 R08 R05 . . | R08 . . R05 R04 R04 | R04 R04 . R05 R08 . |
| 6, after admission | R04 R04 R08 R05 R01 . | R08 R01 . R05 R04 R04 | R04 R04 R01 R05 R08 . |

Those layouts explain the distinct FCFS maximum fragmentation values 2,0,1.
FCFS timing and average waiting tie because the different placements still
admit each reader at the same time. Under Priority, R08 runs before R04.
R08 completes at 12; under Worst Fit the released high-index group lets R02
enter at 12 instead of 13. R02 still waits until librarian dispatch at 13,
so its memory waiting decreases by one while ready waiting increases by one.
Total waiting/completion therefore tie, but memory utilization changes.

The full workbook lists M,S,C, seat starts, post-event states, and occupied
integrals for all six choices, including the comparison workload. Its results
are compared to the production engine and formatter in the regression suite.

## Reproduction

From the repository root:

```bash
python3 -m unittest tests.integration.test_a2_fixtures -v
python3 -m tests.reference_a2 --write
```

The second command explicitly rewrites golden files from the independent
reference. Review the manual anchors and workbook before accepting updated
expected files; never generate them from the production simulator.
