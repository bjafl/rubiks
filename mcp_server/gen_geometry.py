# mcp_server/gen_geometry.py
from __future__ import annotations
import json
from pathlib import Path
from megaminx.moves import get_geometry_data

FACE_COLORS: dict[str, str] = {
    "U":   "#3498DB",
    "F":   "#FFFFFF",
    "R":   "#E74C3C",
    "L":   "#F39C12",
    "FL":  "#E91E8C",
    "FR":  "#9B59B6",
    "B":   "#D35400",
    "BR":  "#1ABC9C",
    "DR":  "#F1C40F",
    "D":   "#2C3E50",
    "DL":  "#95A5A6",
    "BL":  "#2ECC71",
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
