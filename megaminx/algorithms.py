# megaminx/algorithms.py
# Named algorithm sets for Megaminx.
# Each set is a list of move sequences (each sequence = list[str]).
#
# Face name mapping from standard WCA cube notation to Megaminx FACE_NAMES:
#   R  -> FR  (front-right upper face)
#   L  -> FL  (front-left upper face)
#   U  -> U   (top face)
#   F  -> F   (front face)
#   B  -> BR  or BL depending on context

ALGORITHM_SETS: dict[str, list[list[str]]] = {
    # Corner Orientation algorithms (CO — also permutes top edges as side effect)
    "CO_ALGS": [
        ["FR", "U", "FR-", "U", "FR", "U--", "FR-"],         # Sune
        ["FR-", "U-", "FR", "U-", "FR-", "U++", "FR"],        # Anti-Sune
        ["FR", "U++", "FR-", "U-", "FR", "U-", "FR-"],        # Double Sune variant
    ],
    # Corner Permutation algorithms
    "CP_ALGS": [
        ["FR", "U-", "FL-", "U", "FR-", "U-", "FL", "U"],    # Diagonal corner swap
        ["U", "FR", "U-", "FL-", "U", "FR-", "U-", "FL"],    # Adjacent corner swap
    ],
    # Last Layer combined
    "LL_ALGS": [
        ["FR", "U", "FR-", "U-"],                              # Sexy move
        ["FR-", "F", "FR", "F-"],                              # Sledgehammer
        ["F", "FR", "U-", "FR-", "U-", "FR", "U", "FR-", "F-"],  # T-perm
    ],
    # Edge orientation
    "EO_ALGS": [
        ["F", "FR", "U", "FR-", "U-", "F-"],                  # OLL edge flip
    ],
}

SINGLE_ALGS: dict[str, list[str]] = {
    "CO9":        ["FR", "U++", "FR-", "U-", "FR", "U", "FR-", "U-", "FR", "U-", "FR-"],
    "CO10":       ["FR", "U", "FR-", "U", "FR", "U-", "FR-", "U", "FR", "U--", "FR-"],
    "SUNE":       ["FR", "U", "FR-", "U", "FR", "U--", "FR-"],
    "ANTI_SUNE":  ["FR-", "U-", "FR", "U-", "FR-", "U++", "FR"],
    "NIKLAS":     ["FR", "U-", "FL-", "U", "FR-", "U-", "FL", "U"],
    "NIKLAS_INV": ["U-", "FL-", "U", "FR", "U-", "FL", "U", "FR-"],
    "EP1":        ["FR++", "U--", "FR--", "U-", "FR++", "U--", "FR--"],
    "EP2":        ["FR++", "U++", "FR--", "U", "FR++", "U++", "FR--"],
    "SEXY":       ["FR", "U", "FR-", "U-"],
    "SLEDGE":     ["FR-", "F", "FR", "F-"],
}

LIBRARY_ORDER = [
    "CO9", "CO10", "SUNE", "ANTI_SUNE", "NIKLAS", "NIKLAS_INV", "EP1", "EP2",
]


def get_library() -> list[dict]:
    """Return algorithms in display order for the viewer library."""
    return [{"name": n, "moves": SINGLE_ALGS[n]} for n in LIBRARY_ORDER]


def list_algorithms() -> dict[str, list[list[str]]]:
    return ALGORITHM_SETS


def get_algorithm_set(name: str) -> list[list[str]]:
    return ALGORITHM_SETS[name]  # KeyError if unknown


def get_single_alg(name: str) -> list[str]:
    return SINGLE_ALGS[name]  # KeyError if unknown
