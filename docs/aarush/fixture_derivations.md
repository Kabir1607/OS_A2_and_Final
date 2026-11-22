# A6/A7 independent calculation workbook

Produced by the test-only unit-time oracle, without production imports.
Manual anchors and their arithmetic are in `fixture_checks.md`.
M = admission; S = start; C = completion; seat indices start at zero.

## comparison_FCFS_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R01 | 6 | 11 | 18 | 4 |
| R02 | 11 | 18 | 27 | 0 |
| R03 | 2 | 2 | 5 | 0 |
| R04 | 5 | 5 | 11 | 0 |
| R05 | 4 | 4 | 7 | 3 |
| R06 | 11 | 24 | 33 | 5 |
| R07 | 8 | 14 | 24 | 3 |
| R08 | 5 | 7 | 14 | 2 |
| R09 | 3 | 3 | 4 | 3 |
| R10 | 14 | 27 | 35 | 2 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 2 | R03 R03 R03 . . . | 3 | 0 | — |
| 3 | R03 R03 R03 R09 . . | 4 | 0 | — |
| 4 | R03 R03 R03 R05 . . | 4 | 0 | — |
| 5 | R04 R04 R08 R05 . . | 4 | 0 | — |
| 6 | R04 R04 R08 R05 R01 . | 5 | 0 | — |
| 7 | R04 R04 R08 . R01 . | 4 | 1 | — |
| 8 | R04 R04 R08 R07 R01 . | 5 | 0 | — |
| 9 | R04 R04 R08 R07 R01 . | 5 | 0 | R02, R06, R10 |
| 11 | R02 R02 R08 R07 R01 R06 | 6 | 0 | R10 |
| 14 | R02 R02 R10 R07 R01 R06 | 6 | 0 | — |
| 18 | R02 R02 R10 R07 . R06 | 5 | 0 | — |
| 24 | R02 R02 R10 . . R06 | 4 | 0 | — |
| 27 | . . R10 . . R06 | 2 | 2 | — |
| 33 | . . R10 . . . | 1 | 2 | — |
| 35 | . . . . . . | 0 | 0 | — |

Seat-time = **137**; window = [2, 35]; peak = 6; maximum fragmentation = 2.

## comparison_FCFS_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R01 | 6 | 11 | 18 | 1 |
| R02 | 11 | 18 | 27 | 3 |
| R03 | 2 | 2 | 5 | 0 |
| R04 | 5 | 5 | 11 | 4 |
| R05 | 4 | 4 | 7 | 3 |
| R06 | 11 | 24 | 33 | 5 |
| R07 | 8 | 14 | 24 | 2 |
| R08 | 5 | 7 | 14 | 0 |
| R09 | 3 | 3 | 4 | 3 |
| R10 | 14 | 27 | 35 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 2 | R03 R03 R03 . . . | 3 | 0 | — |
| 3 | R03 R03 R03 R09 . . | 4 | 0 | — |
| 4 | R03 R03 R03 R05 . . | 4 | 0 | — |
| 5 | R08 . . R05 R04 R04 | 4 | 0 | — |
| 6 | R08 R01 . R05 R04 R04 | 5 | 0 | — |
| 7 | R08 R01 . . R04 R04 | 4 | 0 | — |
| 8 | R08 R01 R07 . R04 R04 | 5 | 0 | — |
| 9 | R08 R01 R07 . R04 R04 | 5 | 0 | R02, R06, R10 |
| 11 | R08 R01 R07 R02 R02 R06 | 6 | 0 | R10 |
| 14 | R10 R01 R07 R02 R02 R06 | 6 | 0 | — |
| 18 | R10 . R07 R02 R02 R06 | 5 | 0 | — |
| 24 | R10 . . R02 R02 R06 | 4 | 0 | — |
| 27 | R10 . . . . R06 | 2 | 0 | — |
| 33 | R10 . . . . . | 1 | 0 | — |
| 35 | . . . . . . | 0 | 0 | — |

Seat-time = **137**; window = [2, 35]; peak = 6; maximum fragmentation = 0.

## comparison_FCFS_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R01 | 6 | 11 | 18 | 2 |
| R02 | 11 | 18 | 27 | 0 |
| R03 | 2 | 2 | 5 | 0 |
| R04 | 5 | 5 | 11 | 0 |
| R05 | 4 | 4 | 7 | 3 |
| R06 | 11 | 24 | 33 | 5 |
| R07 | 8 | 14 | 24 | 3 |
| R08 | 5 | 7 | 14 | 4 |
| R09 | 3 | 3 | 4 | 3 |
| R10 | 14 | 27 | 35 | 4 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 2 | R03 R03 R03 . . . | 3 | 0 | — |
| 3 | R03 R03 R03 R09 . . | 4 | 0 | — |
| 4 | R03 R03 R03 R05 . . | 4 | 0 | — |
| 5 | R04 R04 . R05 R08 . | 4 | 1 | — |
| 6 | R04 R04 R01 R05 R08 . | 5 | 0 | — |
| 7 | R04 R04 R01 . R08 . | 4 | 1 | — |
| 8 | R04 R04 R01 R07 R08 . | 5 | 0 | — |
| 9 | R04 R04 R01 R07 R08 . | 5 | 0 | R02, R06, R10 |
| 11 | R02 R02 R01 R07 R08 R06 | 6 | 0 | R10 |
| 14 | R02 R02 R01 R07 R10 R06 | 6 | 0 | — |
| 18 | R02 R02 . R07 R10 R06 | 5 | 0 | — |
| 24 | R02 R02 . . R10 R06 | 4 | 0 | — |
| 27 | . . . . R10 R06 | 2 | 0 | — |
| 33 | . . . . R10 . | 1 | 1 | — |
| 35 | . . . . . . | 0 | 0 | — |

Seat-time = **137**; window = [2, 35]; peak = 6; maximum fragmentation = 1.

## comparison_PRIORITY_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R01 | 6 | 22 | 29 | 4 |
| R02 | 13 | 13 | 22 | 0 |
| R03 | 2 | 2 | 5 | 0 |
| R04 | 5 | 7 | 13 | 0 |
| R05 | 4 | 4 | 7 | 3 |
| R06 | 13 | 22 | 31 | 2 |
| R07 | 8 | 12 | 22 | 3 |
| R08 | 5 | 5 | 12 | 2 |
| R09 | 3 | 3 | 4 | 3 |
| R10 | 13 | 29 | 37 | 5 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 2 | R03 R03 R03 . . . | 3 | 0 | — |
| 3 | R03 R03 R03 R09 . . | 4 | 0 | — |
| 4 | R03 R03 R03 R05 . . | 4 | 0 | — |
| 5 | R04 R04 R08 R05 . . | 4 | 0 | — |
| 6 | R04 R04 R08 R05 R01 . | 5 | 0 | — |
| 7 | R04 R04 R08 . R01 . | 4 | 1 | — |
| 8 | R04 R04 R08 R07 R01 . | 5 | 0 | — |
| 9 | R04 R04 R08 R07 R01 . | 5 | 0 | R02, R06, R10 |
| 12 | R04 R04 . R07 R01 . | 4 | 1 | R02, R06, R10 |
| 13 | R02 R02 R06 R07 R01 R10 | 6 | 0 | — |
| 22 | . . R06 . R01 R10 | 3 | 1 | — |
| 29 | . . R06 . . R10 | 2 | 2 | — |
| 31 | . . . . . R10 | 1 | 0 | — |
| 37 | . . . . . . | 0 | 0 | — |

Seat-time = **133**; window = [2, 37]; peak = 6; maximum fragmentation = 2.

## comparison_PRIORITY_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R01 | 6 | 22 | 29 | 1 |
| R02 | 13 | 13 | 22 | 3 |
| R03 | 2 | 2 | 5 | 0 |
| R04 | 5 | 7 | 13 | 4 |
| R05 | 4 | 4 | 7 | 3 |
| R06 | 13 | 22 | 31 | 0 |
| R07 | 8 | 12 | 22 | 2 |
| R08 | 5 | 5 | 12 | 0 |
| R09 | 3 | 3 | 4 | 3 |
| R10 | 13 | 29 | 37 | 5 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 2 | R03 R03 R03 . . . | 3 | 0 | — |
| 3 | R03 R03 R03 R09 . . | 4 | 0 | — |
| 4 | R03 R03 R03 R05 . . | 4 | 0 | — |
| 5 | R08 . . R05 R04 R04 | 4 | 0 | — |
| 6 | R08 R01 . R05 R04 R04 | 5 | 0 | — |
| 7 | R08 R01 . . R04 R04 | 4 | 0 | — |
| 8 | R08 R01 R07 . R04 R04 | 5 | 0 | — |
| 9 | R08 R01 R07 . R04 R04 | 5 | 0 | R02, R06, R10 |
| 12 | . R01 R07 . R04 R04 | 4 | 1 | R02, R06, R10 |
| 13 | R06 R01 R07 R02 R02 R10 | 6 | 0 | — |
| 22 | R06 R01 . . . R10 | 3 | 0 | — |
| 29 | R06 . . . . R10 | 2 | 0 | — |
| 31 | . . . . . R10 | 1 | 0 | — |
| 37 | . . . . . . | 0 | 0 | — |

Seat-time = **133**; window = [2, 37]; peak = 6; maximum fragmentation = 1.

## comparison_PRIORITY_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R01 | 6 | 22 | 29 | 2 |
| R02 | 12 | 13 | 22 | 4 |
| R03 | 2 | 2 | 5 | 0 |
| R04 | 5 | 7 | 13 | 0 |
| R05 | 4 | 4 | 7 | 3 |
| R06 | 13 | 22 | 31 | 0 |
| R07 | 8 | 12 | 22 | 3 |
| R08 | 5 | 5 | 12 | 4 |
| R09 | 3 | 3 | 4 | 3 |
| R10 | 13 | 29 | 37 | 1 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 2 | R03 R03 R03 . . . | 3 | 0 | — |
| 3 | R03 R03 R03 R09 . . | 4 | 0 | — |
| 4 | R03 R03 R03 R05 . . | 4 | 0 | — |
| 5 | R04 R04 . R05 R08 . | 4 | 1 | — |
| 6 | R04 R04 R01 R05 R08 . | 5 | 0 | — |
| 7 | R04 R04 R01 . R08 . | 4 | 1 | — |
| 8 | R04 R04 R01 R07 R08 . | 5 | 0 | — |
| 9 | R04 R04 R01 R07 R08 . | 5 | 0 | R02, R06, R10 |
| 12 | R04 R04 R01 R07 R02 R02 | 6 | 0 | R06, R10 |
| 13 | R06 R10 R01 R07 R02 R02 | 6 | 0 | — |
| 22 | R06 R10 R01 . . . | 3 | 0 | — |
| 29 | R06 R10 . . . . | 2 | 0 | — |
| 31 | . R10 . . . . | 1 | 1 | — |
| 37 | . . . . . . | 0 | 0 | — |

Seat-time = **135**; window = [2, 37]; peak = 6; maximum fragmentation = 1.

## completion_arrival_FCFS_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 3 | 0 |
| R2 | 0 | 0 | 3 | 3 |
| R3 | 3 | 3 | 5 | 0 |
| R4 | 5 | 5 | 6 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R2 R2 R2 | 6 | 0 | — |
| 3 | R3 R3 R3 R3 R3 R3 | 6 | 0 | R4 |
| 5 | R4 . . . . . | 1 | 0 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **31**; window = [0, 6]; peak = 6; maximum fragmentation = 0.

## completion_arrival_FCFS_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 3 | 0 |
| R2 | 0 | 0 | 3 | 3 |
| R3 | 3 | 3 | 5 | 0 |
| R4 | 5 | 5 | 6 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R2 R2 R2 | 6 | 0 | — |
| 3 | R3 R3 R3 R3 R3 R3 | 6 | 0 | R4 |
| 5 | R4 . . . . . | 1 | 0 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **31**; window = [0, 6]; peak = 6; maximum fragmentation = 0.

## completion_arrival_FCFS_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 3 | 0 |
| R2 | 0 | 0 | 3 | 3 |
| R3 | 3 | 3 | 5 | 0 |
| R4 | 5 | 5 | 6 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R2 R2 R2 | 6 | 0 | — |
| 3 | R3 R3 R3 R3 R3 R3 | 6 | 0 | R4 |
| 5 | R4 . . . . . | 1 | 0 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **31**; window = [0, 6]; peak = 6; maximum fragmentation = 0.

## completion_arrival_PRIORITY_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 3 | 0 |
| R2 | 0 | 0 | 3 | 3 |
| R3 | 3 | 3 | 5 | 0 |
| R4 | 5 | 5 | 6 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R2 R2 R2 | 6 | 0 | — |
| 3 | R3 R3 R3 R3 R3 R3 | 6 | 0 | R4 |
| 5 | R4 . . . . . | 1 | 0 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **31**; window = [0, 6]; peak = 6; maximum fragmentation = 0.

## completion_arrival_PRIORITY_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 3 | 0 |
| R2 | 0 | 0 | 3 | 3 |
| R3 | 3 | 3 | 5 | 0 |
| R4 | 5 | 5 | 6 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R2 R2 R2 | 6 | 0 | — |
| 3 | R3 R3 R3 R3 R3 R3 | 6 | 0 | R4 |
| 5 | R4 . . . . . | 1 | 0 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **31**; window = [0, 6]; peak = 6; maximum fragmentation = 0.

## completion_arrival_PRIORITY_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 3 | 0 |
| R2 | 0 | 0 | 3 | 3 |
| R3 | 3 | 3 | 5 | 0 |
| R4 | 5 | 5 | 6 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R2 R2 R2 | 6 | 0 | — |
| 3 | R3 R3 R3 R3 R3 R3 | 6 | 0 | R4 |
| 5 | R4 . . . . . | 1 | 0 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **31**; window = [0, 6]; peak = 6; maximum fragmentation = 0.

## equal_holes_coalescing_FCFS_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 0 | 0 | 6 | 2 |
| R3 | 0 | 2 | 4 | 4 |
| R4 | 4 | 4 | 5 | 0 |
| R5 | 4 | 5 | 6 | 1 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R2 R2 R3 R3 | 6 | 0 | — |
| 2 | . . R2 R2 R3 R3 | 4 | 0 | — |
| 4 | R4 R5 R2 R2 . . | 4 | 0 | — |
| 5 | . R5 R2 R2 . . | 3 | 1 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **27**; window = [0, 6]; peak = 6; maximum fragmentation = 1.

## equal_holes_coalescing_FCFS_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 0 | 0 | 6 | 2 |
| R3 | 0 | 2 | 4 | 4 |
| R4 | 4 | 4 | 5 | 0 |
| R5 | 4 | 5 | 6 | 1 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R2 R2 R3 R3 | 6 | 0 | — |
| 2 | . . R2 R2 R3 R3 | 4 | 0 | — |
| 4 | R4 R5 R2 R2 . . | 4 | 0 | — |
| 5 | . R5 R2 R2 . . | 3 | 1 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **27**; window = [0, 6]; peak = 6; maximum fragmentation = 1.

## equal_holes_coalescing_FCFS_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 0 | 0 | 6 | 2 |
| R3 | 0 | 2 | 4 | 4 |
| R4 | 4 | 4 | 5 | 0 |
| R5 | 4 | 5 | 6 | 4 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R2 R2 R3 R3 | 6 | 0 | — |
| 2 | . . R2 R2 R3 R3 | 4 | 0 | — |
| 4 | R4 . R2 R2 R5 . | 4 | 1 | — |
| 5 | . . R2 R2 R5 . | 3 | 1 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **27**; window = [0, 6]; peak = 6; maximum fragmentation = 1.

## equal_holes_coalescing_PRIORITY_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 0 | 0 | 6 | 2 |
| R3 | 0 | 2 | 4 | 4 |
| R4 | 4 | 4 | 5 | 0 |
| R5 | 4 | 5 | 6 | 1 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R2 R2 R3 R3 | 6 | 0 | — |
| 2 | . . R2 R2 R3 R3 | 4 | 0 | — |
| 4 | R4 R5 R2 R2 . . | 4 | 0 | — |
| 5 | . R5 R2 R2 . . | 3 | 1 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **27**; window = [0, 6]; peak = 6; maximum fragmentation = 1.

## equal_holes_coalescing_PRIORITY_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 0 | 0 | 6 | 2 |
| R3 | 0 | 2 | 4 | 4 |
| R4 | 4 | 4 | 5 | 0 |
| R5 | 4 | 5 | 6 | 1 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R2 R2 R3 R3 | 6 | 0 | — |
| 2 | . . R2 R2 R3 R3 | 4 | 0 | — |
| 4 | R4 R5 R2 R2 . . | 4 | 0 | — |
| 5 | . R5 R2 R2 . . | 3 | 1 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **27**; window = [0, 6]; peak = 6; maximum fragmentation = 1.

## equal_holes_coalescing_PRIORITY_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 0 | 0 | 6 | 2 |
| R3 | 0 | 2 | 4 | 4 |
| R4 | 4 | 4 | 5 | 0 |
| R5 | 4 | 5 | 6 | 4 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R2 R2 R3 R3 | 6 | 0 | — |
| 2 | . . R2 R2 R3 R3 | 4 | 0 | — |
| 4 | R4 . R2 R2 R5 . | 4 | 1 | — |
| 5 | . . R2 R2 R5 . | 3 | 1 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **27**; window = [0, 6]; peak = 6; maximum fragmentation = 1.

## fragmented_wait_FCFS_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 0 | 0 | 6 | 2 |
| R3 | 0 | 2 | 4 | 4 |
| R4 | 6 | 6 | 7 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R2 R2 R3 R3 | 6 | 0 | — |
| 2 | . . R2 R2 R3 R3 | 4 | 0 | R4 |
| 4 | . . R2 R2 . . | 2 | 2 | R4 |
| 6 | R4 R4 R4 . . . | 3 | 0 | — |
| 7 | . . . . . . | 0 | 0 | — |

Seat-time = **27**; window = [0, 7]; peak = 6; maximum fragmentation = 2.

## fragmented_wait_FCFS_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 0 | 0 | 6 | 2 |
| R3 | 0 | 2 | 4 | 4 |
| R4 | 6 | 6 | 7 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R2 R2 R3 R3 | 6 | 0 | — |
| 2 | . . R2 R2 R3 R3 | 4 | 0 | R4 |
| 4 | . . R2 R2 . . | 2 | 2 | R4 |
| 6 | R4 R4 R4 . . . | 3 | 0 | — |
| 7 | . . . . . . | 0 | 0 | — |

Seat-time = **27**; window = [0, 7]; peak = 6; maximum fragmentation = 2.

## fragmented_wait_FCFS_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 0 | 0 | 6 | 2 |
| R3 | 0 | 2 | 4 | 4 |
| R4 | 6 | 6 | 7 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R2 R2 R3 R3 | 6 | 0 | — |
| 2 | . . R2 R2 R3 R3 | 4 | 0 | R4 |
| 4 | . . R2 R2 . . | 2 | 2 | R4 |
| 6 | R4 R4 R4 . . . | 3 | 0 | — |
| 7 | . . . . . . | 0 | 0 | — |

Seat-time = **27**; window = [0, 7]; peak = 6; maximum fragmentation = 2.

## fragmented_wait_PRIORITY_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 0 | 0 | 6 | 2 |
| R3 | 0 | 2 | 4 | 4 |
| R4 | 6 | 6 | 7 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R2 R2 R3 R3 | 6 | 0 | — |
| 2 | . . R2 R2 R3 R3 | 4 | 0 | R4 |
| 4 | . . R2 R2 . . | 2 | 2 | R4 |
| 6 | R4 R4 R4 . . . | 3 | 0 | — |
| 7 | . . . . . . | 0 | 0 | — |

Seat-time = **27**; window = [0, 7]; peak = 6; maximum fragmentation = 2.

## fragmented_wait_PRIORITY_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 0 | 0 | 6 | 2 |
| R3 | 0 | 2 | 4 | 4 |
| R4 | 6 | 6 | 7 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R2 R2 R3 R3 | 6 | 0 | — |
| 2 | . . R2 R2 R3 R3 | 4 | 0 | R4 |
| 4 | . . R2 R2 . . | 2 | 2 | R4 |
| 6 | R4 R4 R4 . . . | 3 | 0 | — |
| 7 | . . . . . . | 0 | 0 | — |

Seat-time = **27**; window = [0, 7]; peak = 6; maximum fragmentation = 2.

## fragmented_wait_PRIORITY_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 0 | 0 | 6 | 2 |
| R3 | 0 | 2 | 4 | 4 |
| R4 | 6 | 6 | 7 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R2 R2 R3 R3 | 6 | 0 | — |
| 2 | . . R2 R2 R3 R3 | 4 | 0 | R4 |
| 4 | . . R2 R2 . . | 2 | 2 | R4 |
| 6 | R4 R4 R4 . . . | 3 | 0 | — |
| 7 | . . . . . . | 0 | 0 | — |

Seat-time = **27**; window = [0, 7]; peak = 6; maximum fragmentation = 2.

## head_of_line_FCFS_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 4 | 0 |
| R2 | 4 | 4 | 6 | 0 |
| R3 | 4 | 4 | 5 | 3 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R1 . . | 4 | 0 | R2, R3 |
| 4 | R2 R2 R2 R3 . . | 4 | 0 | — |
| 5 | R2 R2 R2 . . . | 3 | 0 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **23**; window = [0, 6]; peak = 4; maximum fragmentation = 0.

## head_of_line_FCFS_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 4 | 0 |
| R2 | 4 | 4 | 6 | 0 |
| R3 | 4 | 4 | 5 | 3 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R1 . . | 4 | 0 | R2, R3 |
| 4 | R2 R2 R2 R3 . . | 4 | 0 | — |
| 5 | R2 R2 R2 . . . | 3 | 0 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **23**; window = [0, 6]; peak = 4; maximum fragmentation = 0.

## head_of_line_FCFS_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 4 | 0 |
| R2 | 4 | 4 | 6 | 0 |
| R3 | 4 | 4 | 5 | 3 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R1 . . | 4 | 0 | R2, R3 |
| 4 | R2 R2 R2 R3 . . | 4 | 0 | — |
| 5 | R2 R2 R2 . . . | 3 | 0 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **23**; window = [0, 6]; peak = 4; maximum fragmentation = 0.

## head_of_line_PRIORITY_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 4 | 0 |
| R2 | 4 | 4 | 6 | 0 |
| R3 | 4 | 4 | 5 | 3 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R1 . . | 4 | 0 | R2, R3 |
| 4 | R2 R2 R2 R3 . . | 4 | 0 | — |
| 5 | R2 R2 R2 . . . | 3 | 0 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **23**; window = [0, 6]; peak = 4; maximum fragmentation = 0.

## head_of_line_PRIORITY_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 4 | 0 |
| R2 | 4 | 4 | 6 | 0 |
| R3 | 4 | 4 | 5 | 3 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R1 . . | 4 | 0 | R2, R3 |
| 4 | R2 R2 R2 R3 . . | 4 | 0 | — |
| 5 | R2 R2 R2 . . . | 3 | 0 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **23**; window = [0, 6]; peak = 4; maximum fragmentation = 0.

## head_of_line_PRIORITY_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 4 | 0 |
| R2 | 4 | 4 | 6 | 0 |
| R3 | 4 | 4 | 5 | 3 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R1 . . | 4 | 0 | R2, R3 |
| 4 | R2 R2 R2 R3 . . | 4 | 0 | — |
| 5 | R2 R2 R2 . . . | 3 | 0 | — |
| 6 | . . . . . . | 0 | 0 | — |

Seat-time = **23**; window = [0, 6]; peak = 4; maximum fragmentation = 0.

## initial_idle_FCFS_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 5 | 5 | 8 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 5 | R1 R1 . . . . | 2 | 0 | — |
| 8 | . . . . . . | 0 | 0 | — |

Seat-time = **6**; window = [5, 8]; peak = 2; maximum fragmentation = 0.

## initial_idle_FCFS_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 5 | 5 | 8 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 5 | R1 R1 . . . . | 2 | 0 | — |
| 8 | . . . . . . | 0 | 0 | — |

Seat-time = **6**; window = [5, 8]; peak = 2; maximum fragmentation = 0.

## initial_idle_FCFS_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 5 | 5 | 8 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 5 | R1 R1 . . . . | 2 | 0 | — |
| 8 | . . . . . . | 0 | 0 | — |

Seat-time = **6**; window = [5, 8]; peak = 2; maximum fragmentation = 0.

## initial_idle_PRIORITY_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 5 | 5 | 8 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 5 | R1 R1 . . . . | 2 | 0 | — |
| 8 | . . . . . . | 0 | 0 | — |

Seat-time = **6**; window = [5, 8]; peak = 2; maximum fragmentation = 0.

## initial_idle_PRIORITY_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 5 | 5 | 8 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 5 | R1 R1 . . . . | 2 | 0 | — |
| 8 | . . . . . . | 0 | 0 | — |

Seat-time = **6**; window = [5, 8]; peak = 2; maximum fragmentation = 0.

## initial_idle_PRIORITY_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 5 | 5 | 8 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 5 | R1 R1 . . . . | 2 | 0 | — |
| 8 | . . . . . . | 0 | 0 | — |

Seat-time = **6**; window = [5, 8]; peak = 2; maximum fragmentation = 0.

## long_idle_gap_FCFS_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 20 | 20 | 21 | 0 |
| R3 | 25 | 25 | 27 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 . . . . . | 1 | 0 | — |
| 2 | . . . . . . | 0 | 0 | — |
| 20 | R2 R2 R2 R2 R2 R2 | 6 | 0 | — |
| 21 | . . . . . . | 0 | 0 | — |
| 25 | R3 R3 . . . . | 2 | 0 | — |
| 27 | . . . . . . | 0 | 0 | — |

Seat-time = **12**; window = [0, 27]; peak = 6; maximum fragmentation = 0.

## long_idle_gap_FCFS_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 20 | 20 | 21 | 0 |
| R3 | 25 | 25 | 27 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 . . . . . | 1 | 0 | — |
| 2 | . . . . . . | 0 | 0 | — |
| 20 | R2 R2 R2 R2 R2 R2 | 6 | 0 | — |
| 21 | . . . . . . | 0 | 0 | — |
| 25 | R3 R3 . . . . | 2 | 0 | — |
| 27 | . . . . . . | 0 | 0 | — |

Seat-time = **12**; window = [0, 27]; peak = 6; maximum fragmentation = 0.

## long_idle_gap_FCFS_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 20 | 20 | 21 | 0 |
| R3 | 25 | 25 | 27 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 . . . . . | 1 | 0 | — |
| 2 | . . . . . . | 0 | 0 | — |
| 20 | R2 R2 R2 R2 R2 R2 | 6 | 0 | — |
| 21 | . . . . . . | 0 | 0 | — |
| 25 | R3 R3 . . . . | 2 | 0 | — |
| 27 | . . . . . . | 0 | 0 | — |

Seat-time = **12**; window = [0, 27]; peak = 6; maximum fragmentation = 0.

## long_idle_gap_PRIORITY_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 20 | 20 | 21 | 0 |
| R3 | 25 | 25 | 27 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 . . . . . | 1 | 0 | — |
| 2 | . . . . . . | 0 | 0 | — |
| 20 | R2 R2 R2 R2 R2 R2 | 6 | 0 | — |
| 21 | . . . . . . | 0 | 0 | — |
| 25 | R3 R3 . . . . | 2 | 0 | — |
| 27 | . . . . . . | 0 | 0 | — |

Seat-time = **12**; window = [0, 27]; peak = 6; maximum fragmentation = 0.

## long_idle_gap_PRIORITY_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 20 | 20 | 21 | 0 |
| R3 | 25 | 25 | 27 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 . . . . . | 1 | 0 | — |
| 2 | . . . . . . | 0 | 0 | — |
| 20 | R2 R2 R2 R2 R2 R2 | 6 | 0 | — |
| 21 | . . . . . . | 0 | 0 | — |
| 25 | R3 R3 . . . . | 2 | 0 | — |
| 27 | . . . . . . | 0 | 0 | — |

Seat-time = **12**; window = [0, 27]; peak = 6; maximum fragmentation = 0.

## long_idle_gap_PRIORITY_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 20 | 20 | 21 | 0 |
| R3 | 25 | 25 | 27 | 0 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 . . . . . | 1 | 0 | — |
| 2 | . . . . . . | 0 | 0 | — |
| 20 | R2 R2 R2 R2 R2 R2 | 6 | 0 | — |
| 21 | . . . . . . | 0 | 0 | — |
| 25 | R3 R3 . . . . | 2 | 0 | — |
| 27 | . . . . . . | 0 | 0 | — |

Seat-time = **12**; window = [0, 27]; peak = 6; maximum fragmentation = 0.

## request_bounds_FCFS_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 2 | 2 | 3 | 0 |
| R3 | 2 | 2 | 4 | 1 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R1 R1 R1 | 6 | 0 | — |
| 1 | R1 R1 R1 R1 R1 R1 | 6 | 0 | R2, R3 |
| 2 | R2 R3 . . . . | 2 | 0 | — |
| 3 | . R3 . . . . | 1 | 1 | — |
| 4 | . . . . . . | 0 | 0 | — |

Seat-time = **15**; window = [0, 4]; peak = 6; maximum fragmentation = 1.

## request_bounds_FCFS_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 2 | 2 | 3 | 0 |
| R3 | 2 | 2 | 4 | 1 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R1 R1 R1 | 6 | 0 | — |
| 1 | R1 R1 R1 R1 R1 R1 | 6 | 0 | R2, R3 |
| 2 | R2 R3 . . . . | 2 | 0 | — |
| 3 | . R3 . . . . | 1 | 1 | — |
| 4 | . . . . . . | 0 | 0 | — |

Seat-time = **15**; window = [0, 4]; peak = 6; maximum fragmentation = 1.

## request_bounds_FCFS_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 2 | 2 | 3 | 0 |
| R3 | 2 | 2 | 4 | 1 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R1 R1 R1 | 6 | 0 | — |
| 1 | R1 R1 R1 R1 R1 R1 | 6 | 0 | R2, R3 |
| 2 | R2 R3 . . . . | 2 | 0 | — |
| 3 | . R3 . . . . | 1 | 1 | — |
| 4 | . . . . . . | 0 | 0 | — |

Seat-time = **15**; window = [0, 4]; peak = 6; maximum fragmentation = 1.

## request_bounds_PRIORITY_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 2 | 2 | 3 | 0 |
| R3 | 2 | 2 | 4 | 1 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R1 R1 R1 | 6 | 0 | — |
| 1 | R1 R1 R1 R1 R1 R1 | 6 | 0 | R2, R3 |
| 2 | R2 R3 . . . . | 2 | 0 | — |
| 3 | . R3 . . . . | 1 | 1 | — |
| 4 | . . . . . . | 0 | 0 | — |

Seat-time = **15**; window = [0, 4]; peak = 6; maximum fragmentation = 1.

## request_bounds_PRIORITY_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 2 | 2 | 3 | 0 |
| R3 | 2 | 2 | 4 | 1 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R1 R1 R1 | 6 | 0 | — |
| 1 | R1 R1 R1 R1 R1 R1 | 6 | 0 | R2, R3 |
| 2 | R2 R3 . . . . | 2 | 0 | — |
| 3 | . R3 . . . . | 1 | 1 | — |
| 4 | . . . . . . | 0 | 0 | — |

Seat-time = **15**; window = [0, 4]; peak = 6; maximum fragmentation = 1.

## request_bounds_PRIORITY_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 2 | 0 |
| R2 | 2 | 2 | 3 | 0 |
| R3 | 2 | 2 | 4 | 1 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R1 R1 R1 R1 R1 | 6 | 0 | — |
| 1 | R1 R1 R1 R1 R1 R1 | 6 | 0 | R2, R3 |
| 2 | R2 R3 . . . . | 2 | 0 | — |
| 3 | . R3 . . . . | 1 | 1 | — |
| 4 | . . . . . . | 0 | 0 | — |

Seat-time = **15**; window = [0, 4]; peak = 6; maximum fragmentation = 1.

## simultaneous_arrivals_FCFS_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 3 | 0 |
| R10 | 0 | 0 | 2 | 1 |
| R2 | 0 | 2 | 4 | 2 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R10 R2 . . . | 3 | 0 | — |
| 2 | R1 . R2 . . . | 2 | 1 | — |
| 3 | . . R2 . . . | 1 | 2 | — |
| 4 | . . . . . . | 0 | 0 | — |

Seat-time = **9**; window = [0, 4]; peak = 3; maximum fragmentation = 2.

## simultaneous_arrivals_FCFS_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 3 | 0 |
| R10 | 0 | 0 | 2 | 1 |
| R2 | 0 | 2 | 4 | 2 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R10 R2 . . . | 3 | 0 | — |
| 2 | R1 . R2 . . . | 2 | 1 | — |
| 3 | . . R2 . . . | 1 | 2 | — |
| 4 | . . . . . . | 0 | 0 | — |

Seat-time = **9**; window = [0, 4]; peak = 3; maximum fragmentation = 2.

## simultaneous_arrivals_FCFS_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 0 | 3 | 0 |
| R10 | 0 | 0 | 2 | 1 |
| R2 | 0 | 2 | 4 | 2 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R10 R2 . . . | 3 | 0 | — |
| 2 | R1 . R2 . . . | 2 | 1 | — |
| 3 | . . R2 . . . | 1 | 2 | — |
| 4 | . . . . . . | 0 | 0 | — |

Seat-time = **9**; window = [0, 4]; peak = 3; maximum fragmentation = 2.

## simultaneous_arrivals_PRIORITY_FIRST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 2 | 5 | 0 |
| R10 | 0 | 0 | 2 | 1 |
| R2 | 0 | 0 | 2 | 2 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R10 R2 . . . | 3 | 0 | — |
| 2 | R1 . . . . . | 1 | 0 | — |
| 5 | . . . . . . | 0 | 0 | — |

Seat-time = **9**; window = [0, 5]; peak = 3; maximum fragmentation = 0.

## simultaneous_arrivals_PRIORITY_BEST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 2 | 5 | 0 |
| R10 | 0 | 0 | 2 | 1 |
| R2 | 0 | 0 | 2 | 2 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R10 R2 . . . | 3 | 0 | — |
| 2 | R1 . . . . . | 1 | 0 | — |
| 5 | . . . . . . | 0 | 0 | — |

Seat-time = **9**; window = [0, 5]; peak = 3; maximum fragmentation = 0.

## simultaneous_arrivals_PRIORITY_WORST_FIT

| Reader | M | S | C | Seat start |
|---|---:|---:|---:|---:|
| R1 | 0 | 2 | 5 | 0 |
| R10 | 0 | 0 | 2 | 1 |
| R2 | 0 | 0 | 2 | 2 |

| t | Seats 0–5 | Occupied | Fragmentation | Waiting |
|---:|---|---:|---:|---|
| 0 | R1 R10 R2 . . . | 3 | 0 | — |
| 2 | R1 . . . . . | 1 | 0 | — |
| 5 | . . . . . . | 0 | 0 | — |

Seat-time = **9**; window = [0, 5]; peak = 3; maximum fragmentation = 0.

