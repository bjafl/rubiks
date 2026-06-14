# mcp_server/gen_geometry.py
from __future__ import annotations
import json
from pathlib import Path
from megaminx.moves import get_geometry_data

FACE_COLORS: dict[str, str] = {
    # cubing.js Megaminx color scheme (FaceRenamingMapper order → WCA name)
    "U":  "#ffffff",   # White
    "F":  "#008800",   # DarkGreen
    "L":  "#ff0000",   # Red   (internal "R" → WCA "L")
    "BL": "#e8d0a0",   # Cream (internal "C" → WCA "BL")
    "BR": "#3399ff",   # Aqua  (internal "A" → WCA "BR")
    "R":  "#8800dd",   # Purple (internal "L" → WCA "R")
    "FR": "#ff66cc",   # Pink  (internal "E" → WCA "FR")
    "FL": "#99ff00",   # Lime  (internal "BF" → WCA "FL")
    "DL": "#0000ff",   # BoldBlue (internal "BR" → WCA "DL")
    "B":  "#f4f400",   # Yellow (internal "BL" → WCA "B")
    "DR": "#ff8000",   # Orange (internal "I" → WCA "DR")
    "D":  "#888888",   # MediumGray
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
