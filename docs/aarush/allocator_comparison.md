# A7 allocator measurements

One deterministic A2 run per cell. See fixture_checks.md and fixture_derivations.md for independent calculations.

| Input | Scheduler | Allocator | average_waiting | average_turnaround | average_response | throughput | service_utilization_pct | average_memory_wait | completed_count | blocked_for_memory_count | peak_occupied | pool_utilization_pct | max_ext_frag | last_completion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| comparison.txt | FCFS | FIRST_FIT | 5.5000 | 11.8000 | 5.5000 | 0.3030 | 95.4545 | 0.9000 | 10 | 3 | 6 | 69.1919 | 2 | 35 |
| comparison.txt | FCFS | BEST_FIT | 5.5000 | 11.8000 | 5.5000 | 0.3030 | 95.4545 | 0.9000 | 10 | 3 | 6 | 69.1919 | 0 | 35 |
| comparison.txt | FCFS | WORST_FIT | 5.5000 | 11.8000 | 5.5000 | 0.3030 | 95.4545 | 0.9000 | 10 | 3 | 6 | 69.1919 | 1 | 35 |
| comparison.txt | PRIORITY | FIRST_FIT | 5.9000 | 12.2000 | 5.9000 | 0.2857 | 90.0000 | 1.2000 | 10 | 3 | 6 | 63.3333 | 2 | 37 |
| comparison.txt | PRIORITY | BEST_FIT | 5.9000 | 12.2000 | 5.9000 | 0.2857 | 90.0000 | 1.2000 | 10 | 3 | 6 | 63.3333 | 1 | 37 |
| comparison.txt | PRIORITY | WORST_FIT | 5.9000 | 12.2000 | 5.9000 | 0.2857 | 90.0000 | 1.1000 | 10 | 3 | 6 | 64.2857 | 1 | 37 |
