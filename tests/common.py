from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

def fixture(name='clean'):
    return (ROOT/'tests/fixtures'/f'{name}.twee').read_bytes()
