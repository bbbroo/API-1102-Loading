from __future__ import annotations

from tools.sync_standards_tables import HIGHWAY_WORKBOOK, RAILROAD_WORKBOOK, read_workbook_tables

from app.standards import highway_tables, railroad_tables
from app.standards.metadata import SOURCE_WORKBOOKS


def test_generated_standards_tables_match_source_workbooks():
    workbook_tables = read_workbook_tables()

    assert highway_tables.EARTH_KHE_BY_E_PRIME == workbook_tables["Highway"]["EARTH_KHE_BY_E_PRIME"]
    assert highway_tables.BURIAL_A_BY_H_BD == workbook_tables["Highway"]["BURIAL_A_BY_H_BD"]
    assert highway_tables.BURIAL_B_BY_H_BD == workbook_tables["Highway"]["BURIAL_B_BY_H_BD"]
    assert highway_tables.EXCAVATION_BY_BD_D == workbook_tables["Highway"]["EXCAVATION_BY_BD_D"]
    assert highway_tables.IMPACT_BY_COVER == workbook_tables["Highway"]["IMPACT_BY_COVER"]
    assert highway_tables.KH_BY_ER == workbook_tables["Highway"]["KH_BY_ER"]
    assert highway_tables.KL_BY_ER == workbook_tables["Highway"]["KL_BY_ER"]
    assert highway_tables.GH_BY_DEPTH == workbook_tables["Highway"]["GH_BY_DEPTH"]
    assert highway_tables.GL_BY_DEPTH == workbook_tables["Highway"]["GL_BY_DEPTH"]

    assert railroad_tables.EARTH_KHE_BY_E_PRIME == workbook_tables["Railroad"]["EARTH_KHE_BY_E_PRIME"]
    assert railroad_tables.BURIAL_A_BY_H_BD == workbook_tables["Railroad"]["BURIAL_A_BY_H_BD"]
    assert railroad_tables.BURIAL_B_BY_H_BD == workbook_tables["Railroad"]["BURIAL_B_BY_H_BD"]
    assert railroad_tables.EXCAVATION_BY_BD_D == workbook_tables["Railroad"]["EXCAVATION_BY_BD_D"]
    assert railroad_tables.IMPACT_BY_COVER == workbook_tables["Railroad"]["IMPACT_BY_COVER"]
    assert railroad_tables.KH_BY_ER == workbook_tables["Railroad"]["KH_BY_ER"]
    assert railroad_tables.KL_BY_ER == workbook_tables["Railroad"]["KL_BY_ER"]
    assert railroad_tables.GH_BY_DEPTH == workbook_tables["Railroad"]["GH_BY_DEPTH"]
    assert railroad_tables.GL_BY_DEPTH == workbook_tables["Railroad"]["GL_BY_DEPTH"]
    assert railroad_tables.NH_BY_DEPTH == workbook_tables["Railroad"]["NH_BY_DEPTH"]
    assert railroad_tables.NL_BY_DEPTH == workbook_tables["Railroad"]["NL_BY_DEPTH"]


def test_standards_metadata_uses_corrected_workbooks():
    assert SOURCE_WORKBOOKS == {
        "highway": HIGHWAY_WORKBOOK.name,
        "railroad": RAILROAD_WORKBOOK.name,
    }
