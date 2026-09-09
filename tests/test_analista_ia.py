import pandas as pd
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.chatbot_tools import filter_df, groupby_agg, describe_column, TOOL_SPECS
from modules.mapper import to_canonical, IDENTITY_MAPPING
from modules.canonical_schema import CANONICAL_FIELDS

def _sample_df():
    df_raw = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos_educativos.csv"), encoding="utf-8-sig")
    return to_canonical(df_raw, IDENTITY_MAPPING)

def test_filter():
    df = _sample_df()
    res = filter_df(df, "materia", "==", "Matemáticas")
    assert "rows_total" in res
    assert "preview" in res
    assert res["rows_total"] >= 0
    # whitelist
    err = filter_df(df, "habilidades", "==", "x")
    assert "error" in err

def test_groupby():
    df = _sample_df()
    res = groupby_agg(df, by="materia", agg="mean", target="nota")
    assert "table" in res
    assert len(res["table"]) > 0
    # check sorted
    assert res["table"][0]["materia"] is not None

def test_describe():
    df = _sample_df()
    res = describe_column(df, "materia")
    assert "unique" in res
    assert "top" in res

def test_whitelist():
    df = _sample_df()
    res = filter_df(df, "nota", "regex", ".*")
    assert "error" in res
    res2 = groupby_agg(df, by="nota", agg="mean", target="nota")
    assert "error" in res2

def test_no_exec():
    # tools no aceptan code param
    df = _sample_df()
    # intentar pasar code como value no debe ejecutar
    res = filter_df(df, "nota", "==", "__import__('os').system('echo hacked')")
    # debe filtrar como string, no ejecutar
    assert "rows_total" in res
    assert res["rows_total"] == 0  # no hay nota con ese string

def test_df_none():
    df = None
    # chatbot sin df debe manejarse: filter_df requiere DataFrame
    with pytest.raises(Exception):
        filter_df(df, "nota", "==", 4.0)

def test_context_no_full_df():
    # El LLM solo recibe head(3), no df completo — verificamos que TOOL_SPECS no expone df completo
    # y que chatbot_tools no tiene acceso a enviar df completo
    assert len(TOOL_SPECS) == 3
    for spec in TOOL_SPECS:
        assert "code" not in str(spec).lower()
        assert "exec" not in str(spec).lower()
    # verificar que filter no envía df completo, solo preview 15
    df = _sample_df()
    res = filter_df(df, "nota", ">", 0)
    assert len(res["preview"]) <= 15
    assert res["rows_total"] == len(df)  # total real, preview limitado

def test_tool_errors():
    df = _sample_df()
    res = filter_df(df, "nota", "in", "notalist")
    assert "error" in res
    res2 = groupby_agg(df, by="materia", agg="invalid", target="nota")
    assert "error" in res2
    res3 = describe_column(df, "invalid_col")
    assert "error" in res3
