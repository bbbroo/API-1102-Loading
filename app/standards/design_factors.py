DESIGN_FACTORS = {
    "Pipelines, mains, and service lines": {"1": 0.72, "2": 0.60, "3": 0.50, "4": 0.40},
    "Pipelines on bridges": {"1": 0.60, "2": 0.60, "3": 0.50, "4": 0.40},
}


def design_factor(location: str, class_location: str | int) -> float:
    return float(DESIGN_FACTORS[location][str(class_location)])


def temperature_derating(operating_temperature_f: float) -> float:
    return 1 - (1 / 30 / 50 * (operating_temperature_f - 250)) if operating_temperature_f > 250 else 1.0
