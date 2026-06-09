# megaminx/algorithms.py
# Named algorithm sets for Megaminx.
# Each set is a list of move sequences (each sequence = list[str]).
#
# WCA Megaminx face notation:
#   R  -> right face (solver's right, adjacent to F)
#   UL -> upper-left face (back-left, adjacent to U)
#   U  -> top face
#   F  -> front face

ALGORITHM_SETS: dict[str, list[list[str]]] = {
    # Corner Orientation algorithms (CO — also permutes top edges as side effect)
    "CO_ALGS": [
        ["R", "U", "R-", "U", "R", "U--", "R-"],          # Sune
        ["R-", "U-", "R", "U-", "R-", "U++", "R"],         # Anti-Sune
        ["R", "U++", "R-", "U-", "R", "U-", "R-"],         # Double Sune variant
    ],
    # Corner Permutation algorithms
    "CP_ALGS": [
        ["R", "U-", "UL-", "U", "R-", "U-", "UL", "U"],   # Diagonal corner swap
        ["U", "R", "U-", "UL-", "U", "R-", "U-", "UL"],   # Adjacent corner swap
    ],
    # Last Layer combined
    "LL_ALGS": [
        ["R", "U", "R-", "U-"],                             # Sexy move
        ["R-", "F", "R", "F-"],                             # Sledgehammer
        ["F", "R", "U-", "R-", "U-", "R", "U", "R-", "F-"],  # T-perm
    ],
    # Edge orientation
    "EO_ALGS": [
        ["F", "R", "U", "R-", "U-", "F-"],                 # OLL edge flip
    ],
}

SINGLE_ALGS: dict[str, list[str]] = {
    "CO9":        ["R", "U++", "R-", "U-", "R", "U", "R-", "U-", "R", "U-", "R-"],
    "CO10":       ["R", "U", "R-", "U", "R", "U-", "R-", "U", "R", "U--", "R-"],
    "SUNE":       ["R", "U", "R-", "U", "R", "U--", "R-"],
    "ANTI_SUNE":  ["R-", "U-", "R", "U-", "R-", "U++", "R"],
    "NIKLAS":     ["R", "U-", "UL-", "U", "R-", "U-", "UL", "U"],
    "NIKLAS_INV": ["U-", "UL-", "U", "R", "U-", "UL", "U", "R-"],
    "EP1":        ["R++", "U--", "R--", "U-", "R++", "U--", "R--"],
    "EP2":        ["R++", "U++", "R--", "U", "R++", "U++", "R--"],
    "SEXY":       ["R", "U", "R-", "U-"],
    "SLEDGE":     ["R-", "F", "R", "F-"],
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
