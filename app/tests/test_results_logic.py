from app.calculations.result_models import StressCheck, summarize_checks


def test_controlling_check_uses_highest_utilization():
    checks = [StressCheck("A", 5, 10), StressCheck("B", 9, 10)]
    overall, controlling = summarize_checks(checks, [])
    assert overall == "Pass"
    assert controlling == "B"


def test_fail_controls_over_warnings():
    checks = [StressCheck("A", 11, 10)]
    overall, controlling = summarize_checks(checks, [])
    assert overall == "Fail"
    assert controlling == "A"
