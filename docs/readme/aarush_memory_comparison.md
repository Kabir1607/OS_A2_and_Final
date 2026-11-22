# A2 allocation, FIFO admission, and observed trade-offs

Readers reserve a contiguous block of six indexed seat slots before waiting
for a librarian. First Fit scans upward, Best Fit picks the smallest fitting
hole, and Worst Fit picks the largest. Equal-size holes use the lowest start;
allocation starts at that index. Completion frees exactly the reservation,
so adjacent empty slots coalesce naturally. There is no compaction.

The admission line is strict FIFO, ordered by arrival then string ID. If the
head cannot fit, smaller later requests also wait. This protects arrival-order
admission but can lower seat and librarian utilization. Ready scheduling is a
separate FCFS/Priority decision among readers who already have seats.

First Fit is easy to explain and often finds a position early. Best Fit keeps
larger runs available by filling smaller holes, but may leave small remnants.
Worst Fit leaves a larger remainder in its selected hole but can consume the
largest available group. No policy is universally best; the six-seat model,
request sizes, and FIFO queue determine the observed result.

## Measured comparison

The fixed ten-reader `inputs/a2/comparison.txt` workload distinguishes placement
and fragmentation under all three algorithms. [Full measurements](../aarush/allocator_comparison.md)
include every scheduling/memory statistic; [independent checks](../aarush/fixture_checks.md)
and the [calculation workbook](../aarush/fixture_derivations.md) explain them.

| Scheduler | Allocator | Avg total wait | Avg memory wait | Seat utilization % | Max F_ext | Last completion |
|---|---|---:|---:|---:|---:|---:|
| FCFS | FIRST_FIT | 5.5000 | 0.9000 | 69.1919 | 2 | 35 |
| FCFS | BEST_FIT | 5.5000 | 0.9000 | 69.1919 | 0 | 35 |
| FCFS | WORST_FIT | 5.5000 | 0.9000 | 69.1919 | 1 | 35 |
| PRIORITY | FIRST_FIT | 5.9000 | 1.2000 | 63.3333 | 2 | 37 |
| PRIORITY | BEST_FIT | 5.9000 | 1.2000 | 63.3333 | 1 | 37 |
| PRIORITY | WORST_FIT | 5.9000 | 1.1000 | 64.2857 | 1 | 37 |

At t=5 the two-seat R04 request sees holes 0–2 and 4–5, separated by R05.
Best Fit takes 4–5; First/Worst Fit take 0–1. Subsequent one-seat placements
differ. Under FCFS those placements change fragmentation without changing
admission/dispatch times. Under Priority, Worst Fit admits R02 at t=12 rather
than 13, but its librarian start remains 13. Memory waiting falls while ready
waiting rises by the same amount. No completion-time improvement is claimed.

## Python A1 baseline

On these same readers, Python A1 FCFS has average waiting 5.5000, throughput
0.3030, librarian utilization 95.4545%, and last completion 35. Priority has
5.9000, 0.2857, 90.0000%, and 37. Memory waiting is zero in A1. A2 happens to
preserve these service timings while moving some waiting into the admission
queue. This is a property of this workload, not a universal equivalence.
The HOL fixture separately shows an idle librarian while a smaller request
waits behind the unfitting admission head.

## Assumptions and limits

Standard capacity is six and there are two librarians. Seats remain reserved
while a reader waits for service or a shared resource. Fragmentation/peak are
sampled after all events at a timestamp, and utilization is time-weighted.
The observation window starts at the first arrival. Q is read but unused;
TABLE_REQ is zero. Priority has no aging. No runtime memory map or compaction
is implemented; documentation diagrams are worked examples.
