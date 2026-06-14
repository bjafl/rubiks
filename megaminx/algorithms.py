# megaminx/algorithms.py
# Named algorithm sets for Megaminx.
# Each set is a list of move sequences (each sequence = list[str]).
#
# WCA Megaminx face notation:
#   R  -> right face (solver's right, adjacent to U and F)
#   BR -> back-right face (adjacent to U and R)
#   U  -> top face
#   F  -> front face

ALGORITHM_SETS: dict[str, list[list[str]]] = {
    # Corner Orientation algorithms
    "CO_ALGS": [
        ["R-", "F-", "R", "F-", "R-", "F++", "R"],         # Sune
        ["R", "F", "R-", "F", "R", "F--", "R-"],           # Anti-Sune
        ["R-", "F--", "R", "F", "R-", "F", "R"],           # Double Sune variant
    ],
    # Corner Permutation algorithms (R and L are non-adjacent F-ring faces)
    "CP_ALGS": [
        ["R", "F-", "L-", "F", "R-", "F-", "L", "F"],     # Niklas: 3-cycle
        ["F-", "L-", "F", "R", "F-", "L", "F", "R-"],     # Niklas⁻¹: inverse 3-cycle
    ],
    # Last Layer combined
    "LL_ALGS": [
        ["R-", "F-", "R", "F"],                             # Sexy move
        ["R", "U-", "R-", "U"],                             # Sledgehammer
        ["U-", "R-", "F", "R", "F", "R-", "F-", "R", "U"],  # T-perm
    ],
    # Edge orientation
    "EO_ALGS": [
        ["U-", "R-", "F-", "R", "F", "U"],                 # OLL edge flip
    ],
}

SINGLE_ALGS: dict[str, list[str]] = {
    "CO9":        ["R-", "F--", "R", "F", "R-", "F-", "R", "F", "R-", "F", "R"],
    "CO10":       ["R-", "F-", "R", "F-", "R-", "F", "R", "F-", "R-", "F++", "R"],
    "SUNE":       ["R-", "F-", "R", "F-", "R-", "F++", "R"],
    "ANTI_SUNE":  ["R", "F", "R-", "F", "R", "F--", "R-"],
    "NIKLAS":     ["R", "F-", "L-", "F", "R-", "F-", "L", "F"],
    "NIKLAS_INV": ["F-", "L-", "F", "R", "F-", "L", "F", "R-"],
    "EP1":        ["R--", "F++", "R++", "F", "R--", "F++", "R++"],
    "EP2":        ["R--", "F--", "R++", "F-", "R--", "F--", "R++"],
    "SEXY":       ["R-", "F-", "R", "F"],
    "SLEDGE":     ["R", "U-", "R-", "U"],
}

LIBRARY_ORDER: list[str] = [
    "CO9", "CO10", "SUNE", "ANTI_SUNE", "NIKLAS", "NIKLAS_INV", "EP1", "EP2",
]


def get_library() -> list[dict]:
    """Return algorithms in display order for the viewer library."""
    return [{"name": n, "moves": list(SINGLE_ALGS[n])} for n in LIBRARY_ORDER]


def list_algorithms() -> dict[str, list[list[str]]]:
    return ALGORITHM_SETS


def get_algorithm_set(name: str) -> list[list[str]]:
    return ALGORITHM_SETS[name]  # KeyError if unknown


def get_single_alg(name: str) -> list[str]:
    return SINGLE_ALGS[name]  # KeyError if unknown
