from app.calculations.interpolation import linear


def test_linear_interpolation_exact_and_between():
    value, trace = linear("test", {0.0: 0.0, 10.0: 20.0}, 5.0)
    assert value == 10.0
    assert trace.lower_bound == 0.0
    assert trace.upper_bound == 10.0
    assert not trace.extrapolated


def test_linear_interpolation_reports_extrapolation():
    value, trace = linear("test", {10.0: 20.0, 20.0: 30.0}, 5.0)
    assert value == 15.0
    assert trace.extrapolated
    assert trace.warning
