PIPE_GRADES = {
    "API 5L": {"X42": 42000, "X46": 46000, "X52": 52000, "X56": 56000, "X60": 60000, "X65": 65000, "X70": 70000, "X80": 80000},
    "ASTM A53": {"A": 30000, "B": 35000},
    "ASTM A106": {"A": 30000, "B": 35000},
    "Unknown": {"Unknown": 24000},
}

WELD_SEAM_FACTORS = {
    "Seamless": 1.0,
    "Electric Resistance Welded": 1.0,
    "Submerged Arc Welded": 1.0,
    "Combination Welded": 1.0,
    "Furnace Butt Welded": 0.6,
    "Electric Fusion Welded, Even Class": 1.0,
    "Electric Fusion Welded, Odd Class": 0.8,
    "Unknown Pipe Over 4 Inches": 0.8,
    "Unknown Pipe 4 Inches or Less": 0.6,
}


def smys(specification: str, grade: str) -> float:
    return float(PIPE_GRADES[specification][grade])


def joint_factor(weld_seam: str) -> float:
    return float(WELD_SEAM_FACTORS[weld_seam])
