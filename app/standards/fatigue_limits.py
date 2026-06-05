def fatigue_limits(smys: float, weld_seam: str, outside_diameter: float) -> dict:
    """Workbook Tables rows 354-442 condensed for V1 validated cases."""
    if weld_seam == "Electric Resistance Welded":
        if smys <= 42000:
            return {"girth": 12000.0, "longitudinal": 21000.0}
        if smys <= 65000:
            return {"girth": 12000.0, "longitudinal": 23000.0}
    if smys >= 70000:
        return {"girth": 12000.0, "longitudinal": 13000.0 if smys == 70000 else 14000.0}
    return {"girth": 12000.0, "longitudinal": 12000.0}
