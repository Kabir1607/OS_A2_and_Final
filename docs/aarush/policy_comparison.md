# A7b policy measurements

30 repeats per cell; FIRST_FIT; Python 3.12.3.
Each metric is mean [minimum, maximum]. Wall time includes in-memory ownership tracing and worker synchronization.
Virtual outcomes can vary with real worker interleavings; reruns need not reproduce wall times.

| Input | Scheduler | Allocator | Policy | Runs | All completed | All safe | average_waiting | average_turnaround | throughput | service_utilization_pct | total_resource_wait | max_resource_wait | acquisitions | wait_events | rollbacks | resources_rolled_back | held_while_waiting | wall_time_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| p1_in_order_low_contention.txt | FCFS | FIRST_FIT | ROLLBACK | 30 | True | True | 2.500000 [2.500000, 2.500000] | 8.500000 [8.500000, 8.500000] | 0.181818 [0.181818, 0.181818] | 54.545455 [54.545455, 54.545455] | 5.000000 [5.000000, 5.000000] | 5.000000 [5.000000, 5.000000] | 4.000000 [4.000000, 4.000000] | 1.000000 [1.000000, 1.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.001513 [0.000712, 0.014540] |
| p1_in_order_low_contention.txt | FCFS | FIRST_FIT | ORDERED | 30 | True | True | 2.500000 [2.500000, 2.500000] | 8.500000 [8.500000, 8.500000] | 0.181818 [0.181818, 0.181818] | 54.545455 [54.545455, 54.545455] | 5.000000 [5.000000, 5.000000] | 5.000000 [5.000000, 5.000000] | 4.000000 [4.000000, 4.000000] | 1.000000 [1.000000, 1.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.001097 [0.000755, 0.001905] |
| p1_in_order_low_contention.txt | PRIORITY | FIRST_FIT | ROLLBACK | 30 | True | True | 2.500000 [2.500000, 2.500000] | 8.500000 [8.500000, 8.500000] | 0.181818 [0.181818, 0.181818] | 54.545455 [54.545455, 54.545455] | 5.000000 [5.000000, 5.000000] | 5.000000 [5.000000, 5.000000] | 4.000000 [4.000000, 4.000000] | 1.000000 [1.000000, 1.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.001020 [0.000710, 0.001782] |
| p1_in_order_low_contention.txt | PRIORITY | FIRST_FIT | ORDERED | 30 | True | True | 2.500000 [2.500000, 2.500000] | 8.500000 [8.500000, 8.500000] | 0.181818 [0.181818, 0.181818] | 54.545455 [54.545455, 54.545455] | 5.000000 [5.000000, 5.000000] | 5.000000 [5.000000, 5.000000] | 4.000000 [4.000000, 4.000000] | 1.000000 [1.000000, 1.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.001072 [0.000726, 0.001568] |
| p2_in_order_high_contention.txt | FCFS | FIRST_FIT | ROLLBACK | 30 | True | True | 7.666667 [7.666667, 7.666667] | 17.666667 [17.666667, 17.666667] | 0.120000 [0.120000, 0.120000] | 60.000000 [60.000000, 60.000000] | 20.000000 [20.000000, 20.000000] | 13.000000 [13.000000, 13.000000] | 8.000000 [8.000000, 8.000000] | 3.000000 [3.000000, 3.000000] | 2.000000 [2.000000, 2.000000] | 2.000000 [2.000000, 2.000000] | 0.000000 [0.000000, 0.000000] | 0.001429 [0.000988, 0.002058] |
| p2_in_order_high_contention.txt | FCFS | FIRST_FIT | ORDERED | 30 | True | True | 7.666667 [7.666667, 7.666667] | 17.666667 [17.666667, 17.666667] | 0.120000 [0.120000, 0.120000] | 60.000000 [60.000000, 60.000000] | 20.000000 [20.000000, 20.000000] | 13.000000 [13.000000, 13.000000] | 7.000000 [7.000000, 7.000000] | 3.000000 [3.000000, 3.000000] | 1.000000 [1.000000, 1.000000] | 1.000000 [1.000000, 1.000000] | 1.000000 [1.000000, 1.000000] | 0.001290 [0.000992, 0.002072] |
| p2_in_order_high_contention.txt | PRIORITY | FIRST_FIT | ROLLBACK | 30 | True | True | 7.666667 [7.666667, 7.666667] | 17.666667 [17.666667, 17.666667] | 0.120000 [0.120000, 0.120000] | 60.000000 [60.000000, 60.000000] | 20.000000 [20.000000, 20.000000] | 13.000000 [13.000000, 13.000000] | 8.000000 [8.000000, 8.000000] | 3.000000 [3.000000, 3.000000] | 2.000000 [2.000000, 2.000000] | 2.000000 [2.000000, 2.000000] | 0.000000 [0.000000, 0.000000] | 0.001494 [0.001058, 0.002074] |
| p2_in_order_high_contention.txt | PRIORITY | FIRST_FIT | ORDERED | 30 | True | True | 7.666667 [7.666667, 7.666667] | 17.666667 [17.666667, 17.666667] | 0.120000 [0.120000, 0.120000] | 60.000000 [60.000000, 60.000000] | 20.000000 [20.000000, 20.000000] | 13.000000 [13.000000, 13.000000] | 7.000000 [7.000000, 7.000000] | 3.000000 [3.000000, 3.000000] | 1.000000 [1.000000, 1.000000] | 1.000000 [1.000000, 1.000000] | 1.000000 [1.000000, 1.000000] | 0.001398 [0.000993, 0.002152] |
| p3_reversed_circular.txt | FCFS | FIRST_FIT | ROLLBACK | 30 | True | True | 3.666667 [3.666667, 3.666667] | 9.666667 [9.666667, 9.666667] | 0.230769 [0.230769, 0.230769] | 69.230769 [69.230769, 69.230769] | 10.000000 [10.000000, 10.000000] | 7.000000 [7.000000, 7.000000] | 7.000000 [7.000000, 7.000000] | 2.000000 [2.000000, 2.000000] | 1.000000 [1.000000, 1.000000] | 1.000000 [1.000000, 1.000000] | 0.000000 [0.000000, 0.000000] | 0.001433 [0.000969, 0.002022] |
| p3_reversed_circular.txt | FCFS | FIRST_FIT | ORDERED | 30 | True | True | 4.000000 [4.000000, 4.000000] | 10.000000 [10.000000, 10.000000] | 0.214286 [0.214286, 0.214286] | 64.285714 [64.285714, 64.285714] | 11.000000 [11.000000, 11.000000] | 7.000000 [7.000000, 7.000000] | 7.000000 [7.000000, 7.000000] | 3.000000 [3.000000, 3.000000] | 1.000000 [1.000000, 1.000000] | 1.000000 [1.000000, 1.000000] | 1.000000 [1.000000, 1.000000] | 0.001438 [0.000932, 0.002410] |
| p3_reversed_circular.txt | PRIORITY | FIRST_FIT | ROLLBACK | 30 | True | True | 3.666667 [3.666667, 3.666667] | 9.666667 [9.666667, 9.666667] | 0.230769 [0.230769, 0.230769] | 69.230769 [69.230769, 69.230769] | 10.000000 [10.000000, 10.000000] | 7.000000 [7.000000, 7.000000] | 7.000000 [7.000000, 7.000000] | 2.000000 [2.000000, 2.000000] | 1.000000 [1.000000, 1.000000] | 1.000000 [1.000000, 1.000000] | 0.000000 [0.000000, 0.000000] | 0.001346 [0.000982, 0.001719] |
| p3_reversed_circular.txt | PRIORITY | FIRST_FIT | ORDERED | 30 | True | True | 4.000000 [4.000000, 4.000000] | 10.000000 [10.000000, 10.000000] | 0.214286 [0.214286, 0.214286] | 64.285714 [64.285714, 64.285714] | 11.000000 [11.000000, 11.000000] | 7.000000 [7.000000, 7.000000] | 7.000000 [7.000000, 7.000000] | 3.000000 [3.000000, 3.000000] | 1.000000 [1.000000, 1.000000] | 1.000000 [1.000000, 1.000000] | 1.000000 [1.000000, 1.000000] | 0.001499 [0.001010, 0.001895] |
| p4_out_of_order_uncontended.txt | FCFS | FIRST_FIT | ROLLBACK | 30 | True | True | 0.000000 [0.000000, 0.000000] | 6.000000 [6.000000, 6.000000] | 0.200000 [0.200000, 0.200000] | 60.000000 [60.000000, 60.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 4.000000 [4.000000, 4.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000599 [0.000563, 0.001012] |
| p4_out_of_order_uncontended.txt | FCFS | FIRST_FIT | ORDERED | 30 | True | True | 0.000000 [0.000000, 0.000000] | 6.000000 [6.000000, 6.000000] | 0.200000 [0.200000, 0.200000] | 60.000000 [60.000000, 60.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 4.000000 [4.000000, 4.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000714 [0.000579, 0.001297] |
| p4_out_of_order_uncontended.txt | PRIORITY | FIRST_FIT | ROLLBACK | 30 | True | True | 0.000000 [0.000000, 0.000000] | 6.000000 [6.000000, 6.000000] | 0.200000 [0.200000, 0.200000] | 60.000000 [60.000000, 60.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 4.000000 [4.000000, 4.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000651 [0.000564, 0.001107] |
| p4_out_of_order_uncontended.txt | PRIORITY | FIRST_FIT | ORDERED | 30 | True | True | 0.000000 [0.000000, 0.000000] | 6.000000 [6.000000, 6.000000] | 0.200000 [0.200000, 0.200000] | 60.000000 [60.000000, 60.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 4.000000 [4.000000, 4.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000686 [0.000569, 0.001513] |
| p5_multibook_vs_single.txt | FCFS | FIRST_FIT | ROLLBACK | 30 | True | True | 2.750000 [2.750000, 2.750000] | 8.250000 [8.250000, 8.250000] | 0.266667 [0.266667, 0.266667] | 73.333333 [73.333333, 73.333333] | 8.000000 [8.000000, 8.000000] | 5.000000 [5.000000, 5.000000] | 6.000000 [6.000000, 6.000000] | 2.000000 [2.000000, 2.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.001479 [0.001033, 0.002443] |
| p5_multibook_vs_single.txt | FCFS | FIRST_FIT | ORDERED | 30 | True | True | 2.750000 [2.750000, 2.750000] | 8.250000 [8.250000, 8.250000] | 0.266667 [0.266667, 0.266667] | 73.333333 [73.333333, 73.333333] | 8.000000 [8.000000, 8.000000] | 5.000000 [5.000000, 5.000000] | 6.000000 [6.000000, 6.000000] | 2.000000 [2.000000, 2.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.001447 [0.001049, 0.002049] |
| p5_multibook_vs_single.txt | PRIORITY | FIRST_FIT | ROLLBACK | 30 | True | True | 1.500000 [1.500000, 1.500000] | 7.000000 [7.000000, 7.000000] | 0.250000 [0.250000, 0.250000] | 68.750000 [68.750000, 68.750000] | 3.000000 [3.000000, 3.000000] | 3.000000 [3.000000, 3.000000] | 6.000000 [6.000000, 6.000000] | 1.000000 [1.000000, 1.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.001301 [0.000969, 0.002070] |
| p5_multibook_vs_single.txt | PRIORITY | FIRST_FIT | ORDERED | 30 | True | True | 1.500000 [1.500000, 1.500000] | 7.000000 [7.000000, 7.000000] | 0.250000 [0.250000, 0.250000] | 68.750000 [68.750000, 68.750000] | 3.000000 [3.000000, 3.000000] | 3.000000 [3.000000, 3.000000] | 6.000000 [6.000000, 6.000000] | 1.000000 [1.000000, 1.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.000000 [0.000000, 0.000000] | 0.001443 [0.001022, 0.002197] |
| p6_randomized_stress.txt | FCFS | FIRST_FIT | ROLLBACK | 30 | True | True | 19.750000 [19.750000, 19.750000] | 27.750000 [27.750000, 27.750000] | 0.226415 [0.226415, 0.226415] | 90.566038 [90.566038, 90.566038] | 86.000000 [86.000000, 86.000000] | 26.000000 [26.000000, 26.000000] | 42.000000 [42.000000, 42.000000] | 15.000000 [15.000000, 15.000000] | 10.000000 [10.000000, 10.000000] | 12.000000 [12.000000, 12.000000] | 0.000000 [0.000000, 0.000000] | 0.005614 [0.004520, 0.007305] |
| p6_randomized_stress.txt | FCFS | FIRST_FIT | ORDERED | 30 | True | True | 24.916667 [24.916667, 24.916667] | 32.916667 [32.916667, 32.916667] | 0.206897 [0.206897, 0.206897] | 82.758621 [82.758621, 82.758621] | 185.000000 [185.000000, 185.000000] | 49.000000 [49.000000, 49.000000] | 38.000000 [38.000000, 38.000000] | 20.000000 [20.000000, 20.000000] | 7.000000 [7.000000, 7.000000] | 8.000000 [8.000000, 8.000000] | 7.000000 [7.000000, 7.000000] | 0.005461 [0.004333, 0.007559] |
| p6_randomized_stress.txt | PRIORITY | FIRST_FIT | ROLLBACK | 30 | True | True | 20.166667 [20.166667, 20.166667] | 28.166667 [28.166667, 28.166667] | 0.222222 [0.222222, 0.222222] | 88.888889 [88.888889, 88.888889] | 105.000000 [105.000000, 105.000000] | 23.000000 [23.000000, 23.000000] | 37.000000 [37.000000, 37.000000] | 12.000000 [12.000000, 12.000000] | 7.000000 [7.000000, 7.000000] | 7.000000 [7.000000, 7.000000] | 0.000000 [0.000000, 0.000000] | 0.005275 [0.004037, 0.007704] |
| p6_randomized_stress.txt | PRIORITY | FIRST_FIT | ORDERED | 30 | True | True | 25.666667 [25.666667, 25.666667] | 33.666667 [33.666667, 33.666667] | 0.203390 [0.203390, 0.203390] | 81.355932 [81.355932, 81.355932] | 174.000000 [174.000000, 174.000000] | 40.000000 [40.000000, 40.000000] | 39.000000 [39.000000, 39.000000] | 20.000000 [20.000000, 20.000000] | 8.000000 [8.000000, 8.000000] | 9.000000 [9.000000, 9.000000] | 7.000000 [7.000000, 7.000000] | 0.005826 [0.004220, 0.010821] |

## Per-metric comparisons

Means differing by less than 1e-3 tie; lower is better except throughput/utilization. A counter winner is not an overall fairness winner.

| Input | Scheduler | Metric | Better mean |
|---|---|---|---|
| p1_in_order_low_contention.txt | FCFS | average_waiting | TIE |
| p1_in_order_low_contention.txt | FCFS | average_turnaround | TIE |
| p1_in_order_low_contention.txt | FCFS | throughput | TIE |
| p1_in_order_low_contention.txt | FCFS | service_utilization_pct | TIE |
| p1_in_order_low_contention.txt | FCFS | total_resource_wait | TIE |
| p1_in_order_low_contention.txt | FCFS | max_resource_wait | TIE |
| p1_in_order_low_contention.txt | FCFS | acquisitions | TIE |
| p1_in_order_low_contention.txt | FCFS | wait_events | TIE |
| p1_in_order_low_contention.txt | FCFS | rollbacks | TIE |
| p1_in_order_low_contention.txt | FCFS | resources_rolled_back | TIE |
| p1_in_order_low_contention.txt | FCFS | held_while_waiting | TIE |
| p1_in_order_low_contention.txt | FCFS | wall_time_s | TIE |
| p1_in_order_low_contention.txt | PRIORITY | average_waiting | TIE |
| p1_in_order_low_contention.txt | PRIORITY | average_turnaround | TIE |
| p1_in_order_low_contention.txt | PRIORITY | throughput | TIE |
| p1_in_order_low_contention.txt | PRIORITY | service_utilization_pct | TIE |
| p1_in_order_low_contention.txt | PRIORITY | total_resource_wait | TIE |
| p1_in_order_low_contention.txt | PRIORITY | max_resource_wait | TIE |
| p1_in_order_low_contention.txt | PRIORITY | acquisitions | TIE |
| p1_in_order_low_contention.txt | PRIORITY | wait_events | TIE |
| p1_in_order_low_contention.txt | PRIORITY | rollbacks | TIE |
| p1_in_order_low_contention.txt | PRIORITY | resources_rolled_back | TIE |
| p1_in_order_low_contention.txt | PRIORITY | held_while_waiting | TIE |
| p1_in_order_low_contention.txt | PRIORITY | wall_time_s | TIE |
| p2_in_order_high_contention.txt | FCFS | average_waiting | TIE |
| p2_in_order_high_contention.txt | FCFS | average_turnaround | TIE |
| p2_in_order_high_contention.txt | FCFS | throughput | TIE |
| p2_in_order_high_contention.txt | FCFS | service_utilization_pct | TIE |
| p2_in_order_high_contention.txt | FCFS | total_resource_wait | TIE |
| p2_in_order_high_contention.txt | FCFS | max_resource_wait | TIE |
| p2_in_order_high_contention.txt | FCFS | acquisitions | ORDERED |
| p2_in_order_high_contention.txt | FCFS | wait_events | TIE |
| p2_in_order_high_contention.txt | FCFS | rollbacks | ORDERED |
| p2_in_order_high_contention.txt | FCFS | resources_rolled_back | ORDERED |
| p2_in_order_high_contention.txt | FCFS | held_while_waiting | ROLLBACK |
| p2_in_order_high_contention.txt | FCFS | wall_time_s | TIE |
| p2_in_order_high_contention.txt | PRIORITY | average_waiting | TIE |
| p2_in_order_high_contention.txt | PRIORITY | average_turnaround | TIE |
| p2_in_order_high_contention.txt | PRIORITY | throughput | TIE |
| p2_in_order_high_contention.txt | PRIORITY | service_utilization_pct | TIE |
| p2_in_order_high_contention.txt | PRIORITY | total_resource_wait | TIE |
| p2_in_order_high_contention.txt | PRIORITY | max_resource_wait | TIE |
| p2_in_order_high_contention.txt | PRIORITY | acquisitions | ORDERED |
| p2_in_order_high_contention.txt | PRIORITY | wait_events | TIE |
| p2_in_order_high_contention.txt | PRIORITY | rollbacks | ORDERED |
| p2_in_order_high_contention.txt | PRIORITY | resources_rolled_back | ORDERED |
| p2_in_order_high_contention.txt | PRIORITY | held_while_waiting | ROLLBACK |
| p2_in_order_high_contention.txt | PRIORITY | wall_time_s | TIE |
| p3_reversed_circular.txt | FCFS | average_waiting | ROLLBACK |
| p3_reversed_circular.txt | FCFS | average_turnaround | ROLLBACK |
| p3_reversed_circular.txt | FCFS | throughput | ROLLBACK |
| p3_reversed_circular.txt | FCFS | service_utilization_pct | ROLLBACK |
| p3_reversed_circular.txt | FCFS | total_resource_wait | ROLLBACK |
| p3_reversed_circular.txt | FCFS | max_resource_wait | TIE |
| p3_reversed_circular.txt | FCFS | acquisitions | TIE |
| p3_reversed_circular.txt | FCFS | wait_events | ROLLBACK |
| p3_reversed_circular.txt | FCFS | rollbacks | TIE |
| p3_reversed_circular.txt | FCFS | resources_rolled_back | TIE |
| p3_reversed_circular.txt | FCFS | held_while_waiting | ROLLBACK |
| p3_reversed_circular.txt | FCFS | wall_time_s | TIE |
| p3_reversed_circular.txt | PRIORITY | average_waiting | ROLLBACK |
| p3_reversed_circular.txt | PRIORITY | average_turnaround | ROLLBACK |
| p3_reversed_circular.txt | PRIORITY | throughput | ROLLBACK |
| p3_reversed_circular.txt | PRIORITY | service_utilization_pct | ROLLBACK |
| p3_reversed_circular.txt | PRIORITY | total_resource_wait | ROLLBACK |
| p3_reversed_circular.txt | PRIORITY | max_resource_wait | TIE |
| p3_reversed_circular.txt | PRIORITY | acquisitions | TIE |
| p3_reversed_circular.txt | PRIORITY | wait_events | ROLLBACK |
| p3_reversed_circular.txt | PRIORITY | rollbacks | TIE |
| p3_reversed_circular.txt | PRIORITY | resources_rolled_back | TIE |
| p3_reversed_circular.txt | PRIORITY | held_while_waiting | ROLLBACK |
| p3_reversed_circular.txt | PRIORITY | wall_time_s | TIE |
| p4_out_of_order_uncontended.txt | FCFS | average_waiting | TIE |
| p4_out_of_order_uncontended.txt | FCFS | average_turnaround | TIE |
| p4_out_of_order_uncontended.txt | FCFS | throughput | TIE |
| p4_out_of_order_uncontended.txt | FCFS | service_utilization_pct | TIE |
| p4_out_of_order_uncontended.txt | FCFS | total_resource_wait | TIE |
| p4_out_of_order_uncontended.txt | FCFS | max_resource_wait | TIE |
| p4_out_of_order_uncontended.txt | FCFS | acquisitions | TIE |
| p4_out_of_order_uncontended.txt | FCFS | wait_events | TIE |
| p4_out_of_order_uncontended.txt | FCFS | rollbacks | TIE |
| p4_out_of_order_uncontended.txt | FCFS | resources_rolled_back | TIE |
| p4_out_of_order_uncontended.txt | FCFS | held_while_waiting | TIE |
| p4_out_of_order_uncontended.txt | FCFS | wall_time_s | TIE |
| p4_out_of_order_uncontended.txt | PRIORITY | average_waiting | TIE |
| p4_out_of_order_uncontended.txt | PRIORITY | average_turnaround | TIE |
| p4_out_of_order_uncontended.txt | PRIORITY | throughput | TIE |
| p4_out_of_order_uncontended.txt | PRIORITY | service_utilization_pct | TIE |
| p4_out_of_order_uncontended.txt | PRIORITY | total_resource_wait | TIE |
| p4_out_of_order_uncontended.txt | PRIORITY | max_resource_wait | TIE |
| p4_out_of_order_uncontended.txt | PRIORITY | acquisitions | TIE |
| p4_out_of_order_uncontended.txt | PRIORITY | wait_events | TIE |
| p4_out_of_order_uncontended.txt | PRIORITY | rollbacks | TIE |
| p4_out_of_order_uncontended.txt | PRIORITY | resources_rolled_back | TIE |
| p4_out_of_order_uncontended.txt | PRIORITY | held_while_waiting | TIE |
| p4_out_of_order_uncontended.txt | PRIORITY | wall_time_s | TIE |
| p5_multibook_vs_single.txt | FCFS | average_waiting | TIE |
| p5_multibook_vs_single.txt | FCFS | average_turnaround | TIE |
| p5_multibook_vs_single.txt | FCFS | throughput | TIE |
| p5_multibook_vs_single.txt | FCFS | service_utilization_pct | TIE |
| p5_multibook_vs_single.txt | FCFS | total_resource_wait | TIE |
| p5_multibook_vs_single.txt | FCFS | max_resource_wait | TIE |
| p5_multibook_vs_single.txt | FCFS | acquisitions | TIE |
| p5_multibook_vs_single.txt | FCFS | wait_events | TIE |
| p5_multibook_vs_single.txt | FCFS | rollbacks | TIE |
| p5_multibook_vs_single.txt | FCFS | resources_rolled_back | TIE |
| p5_multibook_vs_single.txt | FCFS | held_while_waiting | TIE |
| p5_multibook_vs_single.txt | FCFS | wall_time_s | TIE |
| p5_multibook_vs_single.txt | PRIORITY | average_waiting | TIE |
| p5_multibook_vs_single.txt | PRIORITY | average_turnaround | TIE |
| p5_multibook_vs_single.txt | PRIORITY | throughput | TIE |
| p5_multibook_vs_single.txt | PRIORITY | service_utilization_pct | TIE |
| p5_multibook_vs_single.txt | PRIORITY | total_resource_wait | TIE |
| p5_multibook_vs_single.txt | PRIORITY | max_resource_wait | TIE |
| p5_multibook_vs_single.txt | PRIORITY | acquisitions | TIE |
| p5_multibook_vs_single.txt | PRIORITY | wait_events | TIE |
| p5_multibook_vs_single.txt | PRIORITY | rollbacks | TIE |
| p5_multibook_vs_single.txt | PRIORITY | resources_rolled_back | TIE |
| p5_multibook_vs_single.txt | PRIORITY | held_while_waiting | TIE |
| p5_multibook_vs_single.txt | PRIORITY | wall_time_s | TIE |
| p6_randomized_stress.txt | FCFS | average_waiting | ROLLBACK |
| p6_randomized_stress.txt | FCFS | average_turnaround | ROLLBACK |
| p6_randomized_stress.txt | FCFS | throughput | ROLLBACK |
| p6_randomized_stress.txt | FCFS | service_utilization_pct | ROLLBACK |
| p6_randomized_stress.txt | FCFS | total_resource_wait | ROLLBACK |
| p6_randomized_stress.txt | FCFS | max_resource_wait | ROLLBACK |
| p6_randomized_stress.txt | FCFS | acquisitions | ORDERED |
| p6_randomized_stress.txt | FCFS | wait_events | ROLLBACK |
| p6_randomized_stress.txt | FCFS | rollbacks | ORDERED |
| p6_randomized_stress.txt | FCFS | resources_rolled_back | ORDERED |
| p6_randomized_stress.txt | FCFS | held_while_waiting | ROLLBACK |
| p6_randomized_stress.txt | FCFS | wall_time_s | TIE |
| p6_randomized_stress.txt | PRIORITY | average_waiting | ROLLBACK |
| p6_randomized_stress.txt | PRIORITY | average_turnaround | ROLLBACK |
| p6_randomized_stress.txt | PRIORITY | throughput | ROLLBACK |
| p6_randomized_stress.txt | PRIORITY | service_utilization_pct | ROLLBACK |
| p6_randomized_stress.txt | PRIORITY | total_resource_wait | ROLLBACK |
| p6_randomized_stress.txt | PRIORITY | max_resource_wait | ROLLBACK |
| p6_randomized_stress.txt | PRIORITY | acquisitions | ROLLBACK |
| p6_randomized_stress.txt | PRIORITY | wait_events | ROLLBACK |
| p6_randomized_stress.txt | PRIORITY | rollbacks | ROLLBACK |
| p6_randomized_stress.txt | PRIORITY | resources_rolled_back | ROLLBACK |
| p6_randomized_stress.txt | PRIORITY | held_while_waiting | ROLLBACK |
| p6_randomized_stress.txt | PRIORITY | wall_time_s | TIE |
