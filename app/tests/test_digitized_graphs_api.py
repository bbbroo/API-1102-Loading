from __future__ import annotations

from fastapi.testclient import TestClient

from app.backend.main import app


def test_digitized_graphs_returns_all_figures_and_assets():
    with TestClient(app) as client:
        response = client.get("/api/digitized-graphs")
        assert response.status_code == 200
        payload = response.json()
        assert len(payload["figures"]) == 16

        first = payload["figures"][0]
        assert first["id"] == "03"
        assert first["factor"] == "KHe"
        assert first["underlay_url"].endswith("_underlay.png")
        assert first["overlay_url"].endswith("_overlay.png")
        assert first["calibrations"]["x"]["calibration_method"] == "piecewise_linear_labeled_ticks"
        assert first["curves"][0]["points"]

        for url in (first["underlay_url"], first["overlay_url"], first["csv_url"]):
            asset = client.get(url)
            assert asset.status_code == 200


def test_figure_7_preserves_depth_orientation():
    with TestClient(app) as client:
        figures = client.get("/api/digitized-graphs").json()["figures"]
        figure_7 = next(figure for figure in figures if figure["id"] == "07")

        assert figure_7["orientation"] == "depth_on_y"
        assert figure_7["x_units"] == "ft"
        assert figure_7["y_units"] == "dimensionless"
        assert figure_7["calibrations"]["x"]["page_coordinate"] == "page_y"
        assert figure_7["calibrations"]["y"]["page_coordinate"] == "page_x"
