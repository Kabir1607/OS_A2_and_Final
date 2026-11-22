"""Independent, unit-time A2 oracle for small course-project examples.

No production simulator, allocator, parser, metrics, or formatter is imported.
Run ``python3 -m tests.reference_a2 --write`` to explicitly rebuild the golden
files and their calculation workbook. Normal tests never rewrite expected data.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from tests import REPO_ROOT


def reference(text: str, scheduler: str, allocator: str) -> dict:
    """Walk one virtual unit at a time and independently produce an A2 report.

    Inputs are the valid seven-field fixtures. The deliberately simple clock
    makes completion-before-arrival ordering and occupied seat-time visible.
    """
    lines = text.strip().splitlines()
    rows = []
    for line in lines[2:]:
        pid, arrival, priority, service, category, seats, table = line.split(',')
        rows.append(dict(id=pid, a=int(arrival), p=int(priority), b=int(service),
                         seats=int(seats)))
    assert len(rows) == int(lines[0])
    slots = [None] * 6
    waiting, ready = [], []
    running = [None, None]
    admitted, started, completed, positions = {}, {}, {}, {}
    now = first = min(r['a'] for r in rows)
    peak = integral = fragmentation = 0
    timeline = []
    last_picture = None
    while True:
        # A finishing reader frees both its librarian and its exact seat block.
        for librarian in range(2):
            job = running[librarian]
            if job is not None and job[1] == now:
                completed[job[0]] = now
                slots = [None if owner == job[0] else owner for owner in slots]
                running[librarian] = None
        waiting.extend(sorted((r for r in rows if r['a'] == now), key=lambda r:r['id']))
        while waiting:
            groups = []
            i = 0
            while i < 6:
                if slots[i] is not None:
                    i += 1
                    continue
                start = i
                while i < 6 and slots[i] is None:
                    i += 1
                if i - start >= waiting[0]['seats']:
                    groups.append((start, i - start))
            if not groups:
                break  # Never try a smaller reader behind an unfitting head.
            if allocator == 'FIRST_FIT':
                start = groups[0][0]
            elif allocator == 'BEST_FIT':
                start = min(groups, key=lambda g:(g[1],g[0]))[0]
            else:
                start = max(groups, key=lambda g:(g[1],-g[0]))[0]
            r = waiting.pop(0)
            for i in range(start, start + r['seats']):
                slots[i] = r['id']
            admitted[r['id']] = now
            positions[r['id']] = start
            ready.append(r)
        for librarian in range(2):
            if running[librarian] is None and ready:
                if scheduler == 'FCFS':
                    key = lambda r:(r['a'],r['id'])
                else:
                    key = lambda r:(r['p'],r['a'],r['id'])
                r = min(ready, key=key)
                ready.remove(r)
                started[r['id']] = now
                running[librarian] = (r['id'], now + r['b'])
        occupied = sum(owner is not None for owner in slots)
        largest = length = 0
        for owner in slots:
            length = length + 1 if owner is None else 0
            largest = max(largest, length)
        frag = 6 - occupied - largest
        peak = max(peak, occupied)
        fragmentation = max(fragmentation, frag)
        picture = (tuple(slots), tuple(r['id'] for r in waiting), tuple(running))
        if picture != last_picture:
            timeline.append((now, slots.copy(), occupied, frag,
                             [r['id'] for r in waiting], running.copy()))
            last_picture = picture
        if len(completed) == len(rows):
            break
        # This state persists for the next unit, including periods of no service.
        integral += occupied
        now += 1
        assert now < 10000, 'reference fixture failed to make progress'

    records, output = [], []
    for r in sorted(rows, key=lambda r:r['id']):
        pid, a, b = r['id'], r['a'], r['b']
        m, s, c = admitted[pid], started[pid], completed[pid]
        values = [pid, a, r['p'], b, s, c, c-a-b, c-a, s-a, m, m-a, c-a-b-(m-a)]
        records.append(values)
        output.append('PROCESS,' + ','.join(map(str, values)))
    n = len(rows)
    elapsed = now - first
    summary = [
        ('AVERAGE_WAITING', sum(v[6] for v in records)/n),
        ('AVERAGE_TURNAROUND', sum(v[7] for v in records)/n),
        ('AVERAGE_RESPONSE', sum(v[8] for v in records)/n),
        ('THROUGHPUT', n/elapsed),
        ('SERVICE_UTILIZATION_PCT', sum(r['b'] for r in rows)/(2*elapsed)*100),
        ('AVERAGE_MEMORY_WAIT', sum(v[10] for v in records)/n),
    ]
    for name, value in summary:
        output.append(f'SUMMARY,{name},{value:.4f}')
    output += [f'SUMMARY,COMPLETED_COUNT,{n}',
               f'SUMMARY,BLOCKED_FOR_MEMORY_COUNT,{sum(v[10] > 0 for v in records)}',
               f'POOL,SPACE,6,{peak},{integral/(6*elapsed)*100:.4f},{fragmentation}']
    return dict(text='\n'.join(output)+'\n', records=records, positions=positions,
                timeline=timeline, integral=integral, peak=peak, frag=fragmentation,
                first=first, end=now)


def main() -> None:
    """Explicitly export independently calculated fixtures and their workbook."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', required=True)
    parser.parse_args()
    book = ['# A6/A7 independent calculation workbook', '',
            'Produced by the test-only unit-time oracle, without production imports.',
            'Manual anchors and their arithmetic are in `fixture_checks.md`.',
            'M = admission; S = start; C = completion; seat indices start at zero.', '']
    expected = REPO_ROOT / 'tests/expected/a2'
    expected.mkdir(parents=True, exist_ok=True)
    for path in sorted((REPO_ROOT/'inputs/a2').glob('*.txt')):
        for scheduler in ('FCFS','PRIORITY'):
            for allocator in ('FIRST_FIT','BEST_FIT','WORST_FIT'):
                result = reference(path.read_text(), scheduler, allocator)
                name = f'{path.stem}_{scheduler}_{allocator}'
                (expected/(name+'.out')).write_text(result['text'])
                book += [f'## {name}', '', '| Reader | M | S | C | Seat start |',
                         '|---|---:|---:|---:|---:|']
                for v in result['records']:
                    book.append(f'| {v[0]} | {v[9]} | {v[4]} | {v[5]} | {result["positions"][v[0]]} |')
                book += ['', '| t | Seats 0–5 | Occupied | Fragmentation | Waiting |',
                         '|---:|---|---:|---:|---|']
                for t, slots, occupied, frag, waiting, running in result['timeline']:
                    book.append(f'| {t} | {" ".join(s or "." for s in slots)} | {occupied} | {frag} | {", ".join(waiting) or "—"} |')
                book += ['', f'Seat-time = **{result["integral"]}**; window = '
                         f'[{result["first"]}, {result["end"]}]; peak = {result["peak"]}; '
                         f'maximum fragmentation = {result["frag"]}.', '']
    (REPO_ROOT/'docs/aarush/fixture_derivations.md').write_text('\n'.join(book)+'\n')


if __name__ == '__main__':
    main()
