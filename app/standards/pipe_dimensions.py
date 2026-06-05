"""Pipe dimensions ported from the API 1102 Highway workbook.

The Highway sheet exposes pipe sizes from the Tables sheet pipe-size grid.
Only rows with wall-thickness options are included because wall thickness is a
required worksheet input.
"""

PIPE_DIMENSIONS = {
    "1/4": {"nps": "1/4", "outside_diameter": 0.54, "wall_thickness_options": [0.065, 0.088, 0.119], "source": "Tables!C2:AD25"},
    "3/8": {"nps": "3/8", "outside_diameter": 0.675, "wall_thickness_options": [0.065, 0.091, 0.126], "source": "Tables!C2:AD25"},
    "1/2": {"nps": "1/2", "outside_diameter": 0.84, "wall_thickness_options": [0.083, 0.109, 0.147, 0.188, 0.294], "source": "Tables!C2:AD25"},
    "3/4": {"nps": "3/4", "outside_diameter": 1.05, "wall_thickness_options": [0.083, 0.113, 0.154, 0.219, 0.308], "source": "Tables!C2:AD25"},
    "1": {"nps": "1", "outside_diameter": 1.315, "wall_thickness_options": [0.109, 0.133, 0.179, 0.25, 0.358, 0.382], "source": "Tables!C2:AD25"},
    "1-1/4": {"nps": "1-1/4", "outside_diameter": 1.66, "wall_thickness_options": [0.109, 0.14, 0.191, 0.25, 0.358], "source": "Tables!C2:AD25"},
    "1-1/2": {"nps": "1-1/2", "outside_diameter": 1.9, "wall_thickness_options": [0.109, 0.145, 0.2, 0.281, 0.4], "source": "Tables!C2:AD25"},
    "2": {"nps": "2", "outside_diameter": 2.375, "wall_thickness_options": [0.109, 0.154, 0.218, 0.344, 0.436], "source": "Tables!C2:AD25"},
    "2-1/2": {"nps": "2-1/2", "outside_diameter": 2.875, "wall_thickness_options": [0.12, 0.203, 0.276, 0.375, 0.552], "source": "Tables!C2:AD25"},
    "3": {"nps": "3", "outside_diameter": 3.5, "wall_thickness_options": [0.12, 0.216, 0.3, 0.438, 0.6], "source": "Tables!C2:AD25"},
    "3-1/2": {"nps": "3-1/2", "outside_diameter": 4.0, "wall_thickness_options": [0.12, 0.226, 0.318, 0.636], "source": "Tables!C2:AD25"},
    "4": {"nps": "4", "outside_diameter": 4.5, "wall_thickness_options": [0.12, 0.125, 0.156, 0.188, 0.219, 0.237, 0.25, 0.281, 0.312, 0.337, 0.438, 0.531, 0.674], "source": "Tables!C2:AD25"},
    "4-1/2": {"nps": "4-1/2", "outside_diameter": 5.0, "wall_thickness_options": [0.247, 0.355], "source": "Tables!C2:AD25"},
    "5": {"nps": "5", "outside_diameter": 5.563, "wall_thickness_options": [0.134, 0.156, 0.188, 0.219, 0.258, 0.281, 0.312, 0.344, 0.375, 0.5, 0.625, 0.75], "source": "Tables!C2:AD25"},
    "6": {"nps": "6", "outside_diameter": 6.625, "wall_thickness_options": [0.134, 0.188, 0.219, 0.25, 0.28, 0.312, 0.344, 0.375, 0.432, 0.5, 0.562, 0.719, 0.864], "source": "Tables!C2:AD25"},
    "8": {"nps": "8", "outside_diameter": 8.625, "wall_thickness_options": [0.148, 0.188, 0.203, 0.219, 0.25, 0.277, 0.312, 0.322, 0.344, 0.375, 0.406, 0.438, 0.5, 0.594, 0.719, 0.812, 0.875, 0.906], "source": "Tables!C2:AD25"},
    "10": {"nps": "10", "outside_diameter": 10.75, "wall_thickness_options": [0.165, 0.188, 0.203, 0.219, 0.25, 0.279, 0.307, 0.344, 0.365, 0.438, 0.5, 0.594, 0.719, 0.844, 1.0, 1.125], "source": "Tables!C2:AD25"},
    "12": {"nps": "12", "outside_diameter": 12.75, "wall_thickness_options": [0.18, 0.203, 0.219, 0.25, 0.281, 0.312, 0.33, 0.344, 0.375, 0.406, 0.438, 0.5, 0.562, 0.688, 0.844, 1.0, 1.125, 1.312], "source": "Tables!C2:AD25"},
    "14": {"nps": "14", "outside_diameter": 14.0, "wall_thickness_options": [0.188, 0.21, 0.219, 0.25, 0.281, 0.312, 0.344, 0.375, 0.438, 0.469, 0.5, 0.594, 0.75, 0.938, 1.094, 1.25, 1.406, 2.0, 2.125, 2.2, 2.5], "source": "Tables!C2:AD25"},
    "16": {"nps": "16", "outside_diameter": 16.0, "wall_thickness_options": [0.188, 0.219, 0.25, 0.281, 0.312, 0.344, 0.375, 0.438, 0.5, 0.656, 0.812, 0.844, 1.031, 1.22, 1.281, 1.438, 1.5, 1.594, 1.75, 1.969], "source": "Tables!C2:AD25"},
    "18": {"nps": "18", "outside_diameter": 18.0, "wall_thickness_options": [0.188, 0.25, 0.281, 0.312, 0.344, 0.375, 0.438, 0.469, 0.5, 0.562, 0.656, 0.688, 0.75, 0.938, 1.156, 1.375, 1.531, 1.562, 1.781, 1.812, 2.062, 2.344], "source": "Tables!C2:AD25"},
    "20": {"nps": "20", "outside_diameter": 20.0, "wall_thickness_options": [0.218, 0.25, 0.281, 0.312, 0.344, 0.375, 0.406, 0.438, 0.469, 0.5, 0.594, 0.812, 1.031, 1.281, 1.5, 1.75, 1.969], "source": "Tables!C2:AD25"},
    "24": {"nps": "24", "outside_diameter": 24.0, "wall_thickness_options": [0.25, 0.281, 0.312, 0.344, 0.375, 0.406, 0.438, 0.469, 0.5, 0.562, 0.688, 0.938, 0.969, 1.219, 1.531, 1.812, 2.062, 2.344], "source": "Tables!C2:AD25"},
    "26": {"nps": "26", "outside_diameter": 26.0, "wall_thickness_options": [0.25, 0.281, 0.312, 0.344, 0.375, 0.406, 0.438, 0.5, 0.562], "source": "Tables!C2:AD25"},
    "30": {"nps": "30", "outside_diameter": 30.0, "wall_thickness_options": [0.312, 0.375, 0.438, 0.5, 0.625], "source": "Tables!C2:AD25"},
    "36": {"nps": "36", "outside_diameter": 36.0, "wall_thickness_options": [0.312, 0.375, 0.5, 0.625, 0.75], "source": "Tables!C2:AD25"},
    "42": {"nps": "42", "outside_diameter": 42.0, "wall_thickness_options": [0.375, 0.5], "source": "Tables!C2:AD25"},
    "48": {"nps": "48", "outside_diameter": 48.0, "wall_thickness_options": [0.375, 0.5], "source": "Tables!C2:AD25"},
}

NPS_ALIASES = {
    "0.25": "1/4",
    "0.375": "3/8",
    "0.5": "1/2",
    "0.75": "3/4",
    "1.25": "1-1/4",
    "1.5": "1-1/2",
    "2.5": "2-1/2",
    "3.5": "3-1/2",
    "4.5": "4-1/2",
}


def normalize_nps(nps: str | int | float | None) -> str:
    text = str(nps or "12").strip()
    return NPS_ALIASES.get(text, text)


def get_pipe(nps: str | int | float) -> dict:
    return PIPE_DIMENSIONS[normalize_nps(nps)]
