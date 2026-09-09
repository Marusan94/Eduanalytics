"""
Safe dataframe tools for Analista IA.
No exec/eval, no Python code from LLM — only whitelisted column/op/value.
"""

import pandas as pd
from modules.canonical_schema import CANONICAL_FIELDS

ALLOWED_COLUMNS = set(CANONICAL_FIELDS.keys())
ALLOWED_OPS = {"==", "!=", "<", "<=", ">", ">=", "in", "not in", "contains"}
ALLOWED_BY = {"grupo_id", "materia", "tipo_apoyo", "tipo_usuario"}
ALLOWED_AGG = {"count", "mean", "sum", "min", "max"}
ALLOWED_TARGET = {"nota", "asistencia", "id_estudiante"}
MAX_PREVIEW = 15


def _validate_column(col: str):
    if col not in ALLOWED_COLUMNS:
        raise ValueError(f"columna '{col}' no es canónica. Permitidas: {sorted(ALLOWED_COLUMNS)}")


def filter_df(df: pd.DataFrame, column: str, op: str, value) -> dict:
    """Filtra df por columna/op/value de forma segura."""
    _validate_column(column)
    if op not in ALLOWED_OPS:
        return {"error": f"op '{op}' no permitido. Permitidos: {sorted(ALLOWED_OPS)}"}
    if column not in df.columns:
        return {"error": f"columna '{column}' no existe en DataFrame"}
    # validar tipo value
    try:
        series = df[column]
        if op == "==":
            filtered = df[series == value]
        elif op == "!=":
            filtered = df[series != value]
        elif op == "<":
            filtered = df[pd.to_numeric(series, errors="coerce") < float(value)]
        elif op == "<=":
            filtered = df[pd.to_numeric(series, errors="coerce") <= float(value)]
        elif op == ">":
            filtered = df[pd.to_numeric(series, errors="coerce") > float(value)]
        elif op == ">=":
            filtered = df[pd.to_numeric(series, errors="coerce") >= float(value)]
        elif op == "in":
            if not isinstance(value, list):
                return {"error": "'in' espera lista de valores"}
            filtered = df[series.isin(value)]
        elif op == "not in":
            if not isinstance(value, list):
                return {"error": "'not in' espera lista de valores"}
            filtered = df[~series.isin(value)]
        elif op == "contains":
            filtered = df[series.astype("string").str.contains(str(value), case=False, na=False)]
        else:
            return {"error": f"op no manejado {op}"}
    except Exception as e:
        return {"error": f"Error al filtrar: {e}"}

    preview = filtered.head(MAX_PREVIEW).to_dict(orient="records")
    # convertir tipos no serializables (Timestamp, NA)
    for row in preview:
        for k, v in row.items():
            if pd.isna(v):
                row[k] = None
            elif hasattr(v, "isoformat"):
                try:
                    row[k] = v.isoformat()
                except Exception:
                    row[k] = str(v)
    return {"rows_total": len(filtered), "preview": preview, "rows_preview": len(preview)}


def groupby_agg(df: pd.DataFrame, by: str, agg: str, target: str) -> dict:
    """Agrupa por by y agrega target."""
    if by not in ALLOWED_BY:
        return {"error": f"'by' debe ser uno de {sorted(ALLOWED_BY)}"}
    if agg not in ALLOWED_AGG:
        return {"error": f"'agg' debe ser uno de {sorted(ALLOWED_AGG)}"}
    if target not in ALLOWED_TARGET and agg != "count":
        return {"error": f"'target' debe ser uno de {sorted(ALLOWED_TARGET)}"}
    if by not in df.columns:
        return {"error": f"columna by '{by}' no existe"}
    if agg != "count" and target not in df.columns:
        return {"error": f"columna target '{target}' no existe"}

    try:
        if agg == "count":
            table = df.groupby(by).size().reset_index(name="count")
        else:
            # asegurar numérico para mean/sum/min/max
            df2 = df.copy()
            df2[target] = pd.to_numeric(df2[target], errors="coerce")
            table = df2.groupby(by)[target].agg(agg).reset_index()
            table.rename(columns={target: f"{agg}_{target}"}, inplace=True)
        # ordenar por valor agregado descendente para utilidad
        sort_col = [c for c in table.columns if c != by][0]
        table = table.sort_values(sort_col, ascending=False)
        preview = table.head(MAX_PREVIEW).to_dict(orient="records")
        for row in preview:
            for k, v in row.items():
                if pd.isna(v):
                    row[k] = None
                elif hasattr(v, "isoformat"):
                    row[k] = str(v)
        return {"rows_total": len(table), "table": preview}
    except Exception as e:
        return {"error": f"Error en groupby_agg: {e}"}


def describe_column(df: pd.DataFrame, column: str) -> dict:
    """Describe columna canónica."""
    _validate_column(column)
    if column not in df.columns:
        return {"error": f"columna '{column}' no existe"}
    try:
        series = df[column]
        unique = int(series.nunique(dropna=True))
        top = series.value_counts(dropna=True).head(5).reset_index()
        top.columns = ["value", "count"]
        top_dict = top.to_dict(orient="records")
        stats = {}
        if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_float_dtype(series):
            s = pd.to_numeric(series, errors="coerce")
            stats = {"mean": round(float(s.mean()), 2) if not s.isna().all() else None,
                     "min": float(s.min()) if not s.isna().all() else None,
                     "max": float(s.max()) if not s.isna().all() else None,
                     "median": float(s.median()) if not s.isna().all() else None}
        return {"unique": unique, "top": top_dict, "stats": stats, "rows_total": len(df)}
    except Exception as e:
        return {"error": f"Error en describe: {e}"}


# OpenAI tool specs para function calling
TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "filter_df",
            "description": "Filtra filas del DataFrame canónico por condición segura",
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {"type": "string", "enum": sorted(list(ALLOWED_COLUMNS))},
                    "op": {"type": "string", "enum": sorted(list(ALLOWED_OPS))},
                    "value": {"description": "valor a comparar (string, number o array para in)", "oneOf": [{"type": "string"}, {"type": "number"}, {"type": "array", "items": {"type": "string"}}]}
                },
                "required": ["column", "op", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "groupby_agg",
            "description": "Agrupa por columna y agrega otra",
            "parameters": {
                "type": "object",
                "properties": {
                    "by": {"type": "string", "enum": sorted(list(ALLOWED_BY))},
                    "agg": {"type": "string", "enum": sorted(list(ALLOWED_AGG))},
                    "target": {"type": "string", "enum": sorted(list(ALLOWED_TARGET))}
                },
                "required": ["by", "agg", "target"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "describe_column",
            "description": "Describe valores de una columna canónica",
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {"type": "string", "enum": sorted(list(ALLOWED_COLUMNS))}
                },
                "required": ["column"]
            }
        }
    },
]
