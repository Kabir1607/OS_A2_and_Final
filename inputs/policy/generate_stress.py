"""Regenerate the fixed-seed P6 stress input; standard library only.

Each of 12 readers has balanced requests for two or three of four books.
The six-seat pool also forces later readers to wait for memory admission.
Run this file explicitly to update p6_randomized_stress.txt beside it.
"""
from pathlib import Path
import random


def main() -> None:
    rng = random.Random(3710)
    books = [f'OS_BOOK_{i}' for i in range(1,5)]
    readers = [f'R{i+1:02}' for i in range(12)]
    actions = []
    for reader in readers:
        selected = rng.sample(books,rng.choice((2,3)))
        for offset,book in enumerate(selected):
            actions.append(f'{reader},{offset},ACQUIRE,{book},1')
        for offset,book in enumerate(reversed(selected),start=4):
            actions.append(f'{reader},{offset},RELEASE,{book},1')
    lines = ['12','2']
    lines += [f'{reader},{i//3},{1+i%3},8,REGULAR,1,0' for i,reader in enumerate(readers)]
    lines += ['4'] + [f'{book},1' for book in books] + [str(len(actions))] + actions
    Path(__file__).with_name('p6_randomized_stress.txt').write_text('\n'.join(lines)+'\n')


if __name__ == '__main__':
    main()
