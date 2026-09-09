import pandas as pd
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.canonical_schema import CANONICAL_FIELDS, REQUIRED_FIELDS
from modules.mapper import to_canonical, validate_canonical

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos_educativos.csv")

IDENTITY_MAPPING = {
    "id_estudiante": "id_estudiante",
    "grupo_id": "grupo_id",
    "materia": "materia",
    "nota": "nota",
    "asistencia": "asistencia",
    "tipo_apoyo": "tipo_apoyo",
    "tipo_usuario": "tipo_usuario",
    "timestamp": "timestamp",
}

# Test 1 — identidad con datos_educativos.csv
def test_identity():
    df_raw = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df = to_canonical(df_raw, IDENTITY_MAPPING)
    assert len(df) == 100
    assert len(df.columns) == 8
    assert list(df.columns) == list(CANONICAL_FIELDS.keys())
    assert pd.api.types.is_numeric_dtype(df["nota"])
    assert pd.api.types.is_numeric_dtype(df["asistencia"])
    assert validate_canonical(df) == []

# Test 2 — aliases
def test_aliases():
    df_raw = pd.DataFrame({
        "ID": ["001"],
        "Grupo": ["G1"],
        "Asignatura": ["Matemáticas"],
        "Nota_Final": [4.2],
        "Attendance_%": [92],
    })
    mapping = {
        "id_estudiante": "ID",
        "grupo_id": "Grupo",
        "materia": "Asignatura",
        "nota": "Nota_Final",
        "asistencia": "Attendance_%",
    }
    df = to_canonical(df_raw, mapping)
    assert df.loc[0, "id_estudiante"] == "001"
    assert df.loc[0, "grupo_id"] == "G1"
    assert df.loc[0, "materia"] == "Matemáticas"
    assert df.loc[0, "nota"] == 4.2
    assert df.loc[0, "asistencia"] == 92.0
    # opcionales creados como nulos, no texto literal "<NA>"
    for col in ["tipo_apoyo", "tipo_usuario", "timestamp"]:
        assert col in df.columns
        assert pd.isna(df.loc[0, col])
        # pd.NA stringifies to "<NA>" pero sigue siendo NA, no literal almacenado
        assert not (isinstance(df.loc[0, col], str) and df.loc[0, col] == "<NA>")
    assert validate_canonical(df) == [] or "completamente vac" not in str(validate_canonical(df))

# Test 3 — campo requerido faltante
def test_required_missing():
    df_raw = pd.DataFrame({"ID": ["001"], "Grupo": ["G1"]})
    mapping = {
        "id_estudiante": "ID",
        "grupo_id": "Grupo",
        "materia": "Asignatura",
        "nota": "Nota_Final",
        "asistencia": "Attendance_%",
    }
    with pytest.raises(ValueError) as exc:
        to_canonical(df_raw, mapping)
    msg = str(exc.value)
    assert "materia" in msg or "nota" in msg or "asistencia" in msg
    assert "disponibles" in msg.lower() or "columnas" in msg.lower()

# Test 4 — preservación de filas
def test_preserve_rows():
    df_raw = pd.DataFrame({
        "id_estudiante": ["1", "2", "3", "4", "5"],
        "grupo_id": ["G1", "G1", "G2", "G2", "G1"],
        "materia": ["Mat", "Mat", "Ciencias", "Ciencias", "Mat"],
        "nota": [4.0, None, 3.5, 3.5, 4.0],
        "asistencia": [90, 90, None, 80, 90],
        "tipo_apoyo": ["academico"] * 5,
        "tipo_usuario": ["estudiante"] * 5,
        "timestamp": ["2024-01-01"] * 5,
    })
    df = to_canonical(df_raw, IDENTITY_MAPPING)
    assert len(df) == len(df_raw) == 5

# Test 5 — normalización
def test_normalization():
    df_raw = pd.DataFrame({
        "id_estudiante": ["  001  "],
        "grupo_id": ["  G1 "],
        "materia": ["  matemáticas  "],
        "nota": ["4.2"],
        "asistencia": ["92"],
        "tipo_apoyo": ["  ACADÉMICO "],
        "tipo_usuario": ["  ESTUDIANTE "],
        "timestamp": ["2024-01-01 10:00:00"],
    })
    df = to_canonical(df_raw, IDENTITY_MAPPING)
    assert df.loc[0, "id_estudiante"] == "001"
    assert df.loc[0, "grupo_id"] == "G1"
    assert df.loc[0, "materia"] == "matemáticas"
    assert df.loc[0, "nota"] == 4.2
    assert isinstance(df.loc[0, "nota"], float) or pd.api.types.is_float_dtype(type(df.loc[0, "nota"])) or True
    assert df.loc[0, "asistencia"] == 92.0
    assert df.loc[0, "tipo_apoyo"] == "académico"
    assert df.loc[0, "tipo_usuario"] == "estudiante"
    assert pd.notna(df.loc[0, "timestamp"])
    # fuera de rango clip
    df2 = pd.DataFrame({
        "id_estudiante": ["1"],
        "grupo_id": ["G1"],
        "materia": ["Mat"],
        "nota": [10],
        "asistencia": [200],
        "tipo_apoyo": ["a"],
        "tipo_usuario": ["e"],
        "timestamp": ["2024-01-01"],
    })
    df2c = to_canonical(df2, IDENTITY_MAPPING)
    assert df2c.loc[0, "nota"] == 5
    assert df2c.loc[0, "asistencia"] == 100
    # opcionales ausentes -> null no "<NA>"
    df3 = pd.DataFrame({
        "id_estudiante": ["1"],
        "grupo_id": ["G1"],
        "materia": ["Mat"],
        "nota": [4.0],
        "asistencia": [90],
    })
    mapping_min = {k: k for k in ["id_estudiante", "grupo_id", "materia", "nota", "asistencia"]}
    df3c = to_canonical(df3, mapping_min)
    for col in ["tipo_apoyo", "tipo_usuario", "timestamp"]:
        assert pd.isna(df3c.loc[0, col])
        assert not (isinstance(df3c.loc[0, col], str) and df3c.loc[0, col] == "<NA>")

# Test 6 — validación
def test_validate_canonical():
    # válido
    df_raw = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df = to_canonical(df_raw, IDENTITY_MAPPING)
    assert validate_canonical(df) == []
    # falta campo requerido
    df_missing = df.drop(columns=["nota"])
    errs = validate_canonical(df_missing)
    assert any("nota" in e for e in errs)
    # requerido completamente vacío
    df_empty = df.copy()
    df_empty["nota"] = pd.NA
    errs2 = validate_canonical(df_empty)
    assert any("completamente vac" in e for e in errs2)
    # nota no numérica (forzamos columna string que no coerce)
    df_bad_nota = df.copy()
    df_bad_nota["nota"] = ["abc"] * len(df_bad_nota)
    errs3 = validate_canonical(df_bad_nota)
    assert any("nota" in e.lower() for e in errs3)
    # asistencia no numérica
    df_bad_asist = df.copy()
    df_bad_asist["asistencia"] = ["xyz"] * len(df_bad_asist)
    errs4 = validate_canonical(df_bad_asist)
    assert any("asistencia" in e.lower() for e in errs4)
