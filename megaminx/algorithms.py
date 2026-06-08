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
    # Corner Orientation algorithms (affect only corner orientations)
    "CO_ALGS": [
        ["FR", "U", "FR-", "U", "FR", "U++", "FR-"],         # Sune
        ["FR-", "U-", "FR", "U-", "FR-", "U--", "FR"],        # Anti-Sune
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
    "SUNE":       ["FR", "U", "FR-", "U", "FR", "U++", "FR-"],
    "ANTI_SUNE":  ["FR-", "U-", "FR", "U-", "FR-", "U--", "FR"],
    "SEXY":       ["FR", "U", "FR-", "U-"],
    "SLEDGE":     ["FR-", "F", "FR", "F-"],
}


def list_algorithms() -> dict[str, list[list[str]]]:
    return ALGORITHM_SETS


def get_algorithm_set(name: str) -> list[list[str]]:
    return ALGORITHM_SETS[name]  # KeyError if unknown


def get_single_alg(name: str) -> list[str]:
    return SINGLE_ALGS[name]  # KeyError if unknown
