# Policy comparison workloads

Use both schedulers and both safe policies with FIRST_FIT and 30 repetitions.
These files test hypotheses; measured outcomes are in
`docs/aarush/policy_comparison.md` and `policy_results.json` in the source repo.

- P1: consistent acquisition order and low contention; not necessarily ascending lexical rank.
- P2: longer in-order holding intervals and three readers; compare convoying/churn.
- P3: three-reader reversed/circular requests.
- P4: uncontended out-of-order requests; both should avoid rollback overhead.
- P5: one multi-book reader and three single-book readers. It is a finite example,
  not a proof of starvation or starvation freedom.
- P6: 12 readers, four resources, requests for two or three distinct books each;
  every acquisition has a later release. Arrival groups also contend for six seats.
  `generate_stress.py` uses Python's `random.Random(3710)`, samples book order,
  acquires at offsets 0 onward, and releases in reverse order from offset 4.

Run `python3 inputs/policy/generate_stress.py` to explicitly regenerate P6.
Runs may pick different worker winners; fixed inputs do not make Final races
or real wall-clock timings deterministic.
