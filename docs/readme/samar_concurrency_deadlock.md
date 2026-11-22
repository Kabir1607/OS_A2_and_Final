# Concurrency, Synchronization, and Deadlock Prevention (Final Core)

**Author:** Samar (Tasks S1–S9)  
**Modules:** `resource_parser.py`, `trace.py`, `resources.py`, `workers.py`, `deadlock.py`

---

## 1. Coffman Conditions in the Smart Library

Deadlock can occur only if all four Coffman conditions hold simultaneously:

1. **Mutual Exclusion:** Each library resource (e.g., `REFERENCE_BOOK`, `JOURNAL`, `OS_BOOK_1`..`OS_BOOK_10`) has physical capacity 1. Only one reader can hold a given book at any moment.
2. **Hold and Wait:** A reader currently holding one book (e.g., `REFERENCE_BOOK`) can request and wait for another book (e.g., `JOURNAL`) without relinquishing its existing holdings.
3. **No Preemption:** Resources cannot be forcibly seized from a reader. In standard execution, a book is retained until the reader issues an explicit `RELEASE`.
4. **Circular Wait:** Two or more readers form a closed chain where each reader waits for a resource held by the next (e.g., R1 holds `REFERENCE_BOOK` and waits for `JOURNAL`; R2 holds `JOURNAL` and waits for `REFERENCE_BOOK`).

---

## 2. Threading Model and Free-Threaded Concurrency

- **Real Concurrency:** The simulation uses actual operating-system threads via `WorkerPool` (wrapping Python's `ThreadPoolExecutor`). Action batches for distinct readers execute concurrently across distinct worker threads.
- **The GIL Note:** CPython threads run under the Global Interpreter Lock (GIL), which prevents multiple native CPU cores from executing Python bytecode in parallel. However, thread preemption can occur between any two bytecodes or system calls. Thus, data races and lost wake-ups are real hazards if shared mutable state is unprotected.
- **Independence from GIL:** Atomicity is never assumed from the GIL. Every check-and-update on resource state, holder tracking, queue manipulation, and counter increments is strictly guarded inside `ResourceManager._lock`. This ensures complete safety and correctness on free-threaded Python (PEP 703) and alternative runtimes (PyPy).
- **Single-Coordinator Architecture:** Reader process lifecycle transitions (`Reader.transition`), virtual time progression, `ReadyQueue`, and memory pools (`SeatPool`, `AdmissionQueue`) are owned exclusively by the coordinator thread. Worker threads only touch `ResourceManager` and `Tracer`. This completely eliminates data races on reader lifecycle structures without fine-grained distributed locking.

---

## 3. Synchronization Primitives and Design

| Primitive | Location | Purpose |
|---|---|---|
| `threading.Lock` | `ResourceManager` | Guards all resource ownership, waiter queues, exclusivity checking, and statistics. Checked and updated in a single atomic critical section. |
| `threading.Lock` | `Tracer` | Ensures global sequential ordering (`seq`) and thread-safe appending and formatting of trace events. |
| `ThreadPoolExecutor` | `WorkerPool` | Manages real OS worker threads named `worker-1`, `worker-2`, etc. Submits batches, joins futures, and re-raises worker exceptions. |
| `threading.Barrier` | `run_blocking_demo`, stress tests | Synchronizes thread start phases to guarantee concurrent overlap when demonstrating race conditions and deadlocks. |
| `threading.Condition` | `run_blocking_demo` | Implements timed thread waiting (`wait(timeout=...)`) in the bounded blocking demonstration. |

---

## 4. Resource Allocation, Blocking, and Direct Handoff

### Virtual-Time Non-Blocking Workers
In a discrete-event simulation, worker threads must not park on real-time sleep waiting for virtual simulation time. When `manager.acquire()` finds a resource busy, it immediately records the reader as a waiter and returns `AcquireOutcome(status=BLOCKED)`. The coordinator thread then:
1. Marks the reader as `BLOCKED_RESOURCE` with `blocked_since = now`.
2. Frees the librarian execution unit (allowing other READY readers to be served).
3. Preserves the reader's contiguous memory seats in the `SeatPool`.

### Direct Handoff (Zero Lost Wake-ups)
When a resource is released (or rolled back), it is handed **directly** to the head of the FIFO waiter queue inside the critical section before releasing `ResourceManager._lock`:
- The resource is never left unowned in the open pool where an incoming reader could steal it.
- No lost wake-ups can occur because the waiter is marked as holding the resource immediately and returned in the `woken` list.
- When the coordinator re-dispatches a woken reader, the reader **already owns** the book; its action pointer advances (`next_action += 1`) without re-running the `ACQUIRE`, avoiding duplicate acquire errors [CONTRACT 1].

---

## 5. Deadlock Prevention Policies

Both policies accept **any valid input order** and never reject an input or leave unfinished readers (`COMPLETED_COUNT == N`).

### 1. ROLLBACK (Breaks Hold and Wait)
- **Rule:** If a reader requests a resource $X$ that is free, it is granted immediately. If $X$ is busy:
  - If the reader holds no other resources, it waits for $\{X\}$.
  - If the reader holds a set of resources $H$, it immediately releases **all** of $H$ (emitting `ROLLBACK` events and handing them off to waiting readers) and enters the queue waiting for the combined set $H \cup \{X\}$.
- **Atomic Grant:** A multi-resource request is granted atomically only when **every** requested resource is simultaneously free.
- **Invariant:** A reader never waits while holding any resource (`held_while_waiting == 0` strictly).

### 2. ORDERED (Breaks Circular Wait)
- **Rule:** Resources have a global total ordering given by lexicographical ID rank (`resource_rank`).
- **Free Grant Flexibility:** A free resource is granted in any order. Free acquisitions create no wait-for edges and cannot induce deadlocks.
- **Ordered Wait Invariant:** A reader may only **wait** for a resource ranked higher than all resources it currently holds.
- **Handling Out-of-Order Requests:**
  - If $X$ is busy and all held resources have $\text{rank} < \text{rank}(X)$, the reader waits in-order while retaining its holdings.
  - If $X$ is busy and some held resources have $\text{rank} > \text{rank}(X)$, the reader releases only those held resources ranked higher than $X$ (`ROLLBACK` events). It then waits to re-acquire $X$ and the rolled-back items in strictly ascending rank order.
- The reader is woken only once it has reacquired all required resources.

---

## 6. Policy Comparison and Default Selection

| Feature / Workload | ROLLBACK (Breaks Hold-and-Wait) | ORDERED (Breaks Circular Wait) | Winner / Analysis |
|---|---|---|---|
| **P1: In-order Low Contention** | Few rollbacks; low overhead | 0 rollbacks; direct grant | **ORDERED** (zero churn) |
| **P2: In-order High Contention** | Releases early, unblocking others | Readers hold while waiting (convoy) | **ROLLBACK** (lower overall wait) |
| **P3: Circular / Reversed** | Releases all holdings, retries set | Releases only higher-ranked items | **ORDERED** (fewer rollbacks) |
| **P4: Uncontended Out-of-Order** | 0 rollbacks, grants immediately | 0 rollbacks, grants immediately | **TIE** (zero overhead) |
| **P5: Multi-book vs Stream** | All-or-nothing wait risks starvation | Step-by-step progress | **ORDERED** (better fairness) |
| **P6: Randomized Stress** | High churn on multi-book sets | Predictable ascending acquisition | **ORDERED** (lower synchronization overhead) |

### Default Policy Choice: `ROLLBACK`
`DEFAULT_POLICY = PreventionPolicy.ROLLBACK` is committed as the default configuration because:
1. It guarantees `held_while_waiting == 0` under all conditions, completely eliminating hold-and-wait across all workloads.
2. In library workflows where readers hold books during extended study periods, holding resources while blocked creates severe convoys under FIFO admission. Releasing held books immediately frees them for other readers.
3. Both policies remain fully selectable at runtime via `--policy ROLLBACK|ORDERED`.

---

## 7. Assumptions, Edge Cases, and Limitations

1. **No Offset Rewind:** After a rollback, a reader's service offset does not rewind. The reader resumes execution from its current offset once re-granted its holdings.
2. **FIFO Fairness per Resource:** Waiters for any resource are resumed strictly in FIFO order. No OS lock fairness is assumed.
3. **Double Acquire / Double Release Protection:** `ResourceManager` raises `RuntimeError` if a holder or waiter attempts to re-acquire an already held/waiting resource [CONTRACT 1], or if an unheld resource is released.
4. **Exclusivity Audit:** `trace.audit_exclusivity` replays every trace event independently. `CHECK,EXCLUSIVITY_VIOLATIONS` reports $\max(\text{manager\_count}, \text{trace\_audit})$, guaranteeing that neither component can conceal an exclusivity failure [CONTRACT 4].
