# Shared fakes

Each owner publishes `fake_<module>.py` here, early: a minimal stand-in
with the same signatures and the same behaviour rules as in
`library_sim.pyi`. Test against these, never against private fakes.
A fake must pass its module's contract tests in `tests/contract/`.

| Module | Owner | Fake |
|---|---|---|
| errors, models, scheduler, parser, metrics, output, a1 | Kabir | none needed: the real modules are done (use them directly) |
| memory | Aarush | `fake_memory.py` (A7c), independent slot-list implementation |
| engine | Urvashi | `fake_engine.py` (U9g) |
| resource_parser, trace, resources, workers, deadlock | Samar | `fake_resources.py`, `fake_workers.py`, ... (S6c) |

Memory behavior checks run against both real and fake modules in the same suite.
The engine fake returns one fixed reader, the worker fake runs sequentially,
and the resource fake implements NONE-style ownership regardless of its policy
argument. Those fakes are development stand-ins, not evidence for real policy
or thread behavior. A2 archives omit the Final-only fakes and tests.
