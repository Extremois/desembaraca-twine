"""Run the local checkout without installing a build backend."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from twine_edge_overlap.cli import main

if __name__=='__main__':
    raise SystemExit(main())
