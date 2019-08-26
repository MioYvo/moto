# coding=utf-8
# __author__ = 'Mio'
from pathlib import Path


def real_path(p: Path) -> str:
    if not p.exists():
        p.mkdir(parents=True)
    return str(p.absolute())
