import json
from pathlib import Path

GEOMETRY_PATH = Path(__file__).parent.parent / "viewer" / "geometry.json"


def test_geometry_file_exists():
    assert GEOMETRY_PATH.exists(), "Run: python -m mcp_server.gen_geometry"


def test_geometry_top_level_keys():
    g = json.loads(GEOMETRY_PATH.read_text())
    for key in ["faceNames", "faceColors", "faceVertices", "faceCenters",
                "faceCornerCycles", "faceEdgeCycles", "cornerFaces", "edgeFaces"]:
        assert key in g, f"Missing key: {key}"


def test_geometry_face_count():
    g = json.loads(GEOMETRY_PATH.read_text())
    assert len(g["faceNames"]) == 12
    assert len(g["faceVertices"]) == 12
    assert len(g["faceCenters"]) == 12


def test_geometry_face_vertices_shape():
    g = json.loads(GEOMETRY_PATH.read_text())
    for fv in g["faceVertices"]:
        assert len(fv) == 5
        for v in fv:
            assert len(v) == 3


def test_geometry_corner_counts():
    g = json.loads(GEOMETRY_PATH.read_text())
    assert len(g["cornerFaces"]) == 20
    assert all(len(cf) == 3 for cf in g["cornerFaces"])
    assert len(g["faceCornerCycles"]) == 12
    assert all(len(cc) == 5 for cc in g["faceCornerCycles"])


def test_geometry_edge_counts():
    g = json.loads(GEOMETRY_PATH.read_text())
    assert len(g["edgeFaces"]) == 30
    assert all(len(ef) == 2 for ef in g["edgeFaces"])
    assert len(g["faceEdgeCycles"]) == 12
    assert all(len(ec) == 5 for ec in g["faceEdgeCycles"])


def test_geometry_u_is_first():
    g = json.loads(GEOMETRY_PATH.read_text())
    assert g["faceNames"][0] == "U"
    assert g["faceNames"][-1] == "dL"


def test_geometry_colors_all_present():
    g = json.loads(GEOMETRY_PATH.read_text())
    for name in g["faceNames"]:
        assert name in g["faceColors"]
        color = g["faceColors"][name]
        assert color.startswith("#") and len(color) == 7
