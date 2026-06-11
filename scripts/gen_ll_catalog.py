#!/usr/bin/env python3
"""Generate LL catalog JSON files for a given stage."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from megaminx.ll_catalog import (
    CatalogBuilder,
    CO_STAGE, EP_STAGE, CP_STAGE_CO_FIRST, CP_STAGE_CO_LAST,
)

STAGES = {
    "co":         CO_STAGE,
    "ep":         EP_STAGE,
    "cp":         CP_STAGE_CO_FIRST,
    "cp-co-last": CP_STAGE_CO_LAST,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LL catalog JSON")
    parser.add_argument("--stage", choices=list(STAGES), required=True,
                        help="Which stage to generate (co | ep | cp | cp-co-last)")
    parser.add_argument("--moves", required=True,
                        help="Comma-separated move list, e.g. R,R-,R++,R--,U,U-")
    parser.add_argument("--max-depth", type=int, required=True,
                        help="Maximum solution depth to search")
    parser.add_argument("--output-dir", default="ll_catalog",
                        help="Directory for output JSON (default: ll_catalog/)")
    args = parser.parse_args()

    stage = STAGES[args.stage]
    move_set = [m.strip() for m in args.moves.split(",") if m.strip()]
    output_dir = Path(args.output_dir)

    print(f"Building {args.stage} catalog "
          f"(max_depth={args.max_depth}, {len(move_set)} moves)...")
    builder = CatalogBuilder(stage, move_set, args.max_depth)
    catalog = builder.build()

    out_path = output_dir / f"{args.stage}.json"
    catalog.save(out_path)
    print(f"Done: {len(catalog.cases)} cases -> {out_path}")


if __name__ == "__main__":
    main()
