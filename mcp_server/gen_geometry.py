"""Generate viewer/geometry.json from moves.py dodecahedron geometry data.

Run: python -m mcp_server.gen_geometry
"""
from __future__ import annotations
import json
from pathlib import Path
from megaminx.moves import get_geometry_data

FACE_COLORS: dict[str, str] = {
    "U":   "#FFFFFF",
    "F":   "#3498DB",
    "FR":  "#E74C3C",
    "BR":  "#F39C12",
    "BL":  "#E91E8C",
    "FL":  "#2ECC71",
    "DFR": "#9B59B6",
    "DR":  "#F1C40F",
    "DBR": "#1ABC9C",
    "DBL": "#95A5A6",
    "DFL": "#D35400",
    "D":   "#2C3E50",
}

OUTPUT = Path(__file__).parent.parent / "viewer" / "geometry.json"


def main() -> None:
    raw = get_geometry_data()
    out = {
        "faceNames":        raw["face_names"],
        "faceColors":       {name: FACE_COLORS[name] for name in raw["face_names"]},
        "faceVertices":     raw["face_vertices"],
        "faceCenters":      raw["face_centers"],
        "faceCornerCycles": raw["face_corner_cycles"],
        "faceEdgeCycles":   raw["face_edge_cycles"],
        "cornerFaces":      raw["corner_faces"],
        "edgeFaces":        raw["edge_faces"],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out, indent=2))
    print(f"Written: {OUTPUT}  ({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
