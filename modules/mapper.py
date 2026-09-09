"""
Mapper canónico: RAW DataFrame -> DataFrame canónico.

Transforma un DataFrame con columnas origen arbitrarias a las 8 columnas
definidas en modules/canonical_schema.py usando un mapping dict
{canonico: origen}. Testeable como Python puro, sin Streamlit.
"""

import pandas as pd
from modules.canonical_schema import CANONICAL_FIELDS, REQUIRED_FIELDS

# Mapping identidad para el CSV actual (datos_educativos.csv)
IDENTITY_MAPPING = {k: k for k in CANONICAL_FIELDS}


def _normalize_series(series: pd.Series, canon: str) -> pd.Series:
    field = CANONICAL_FIELDS[canon]
    t = field["type"]
    if canon in ("id_estudiante", "grupo_id", "materia"):
        # string strip
        return series.astype("string").str.strip()
    if canon == "nota":
        # numeric coerce + clip 0-5
        s = pd.to_numeric(series, errors="coerce")
        return s.clip(lower=0, upper=5)
    if canon == "asistencia":
        s = pd.to_numeric(series, errors="coerce")
        return s.clip(lower=0, upper=100)
    if canon in ("tipo_apoyo", "tipo_usuario"):
        return series.astype("string").str.strip().str.lower()
    if canon == "timestamp":
        return pd.to_datetime(series, errors="coerce")
    # fallback por tipo
    if t == "str":
        return series.astype("string").str.strip()
    if t == "float":
        return pd.to_numeric(series, errors="coerce")
    if t == "datetime":
        return pd.to_datetime(series, errors="coerce")
    return series


def to_canonical(df_raw: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """
    Transforma df_raw a df_canónico según mapping {canonico: origen}.
    No elimina filas (len preserved), no dedup, no reset_index extra.
    Campos required faltantes -> ValueError. Opcionales faltantes -> columna con NA.
    Retorna DataFrame con exactamente las columnas de CANONICAL_FIELDS en orden.
    """
    if not isinstance(df_raw, pd.DataFrame):
        raise TypeError("df_raw debe ser pd.DataFrame")
    if not isinstance(mapping, dict):
        raise TypeError("mapping debe ser dict[str, str]")

    # Validar required
    missing_required = []
    missing_details = []
    available = list(df_raw.columns)
    for canon in REQUIRED_FIELDS:
        src = mapping.get(canon)
        if not src or src not in df_raw.columns:
            missing_required.append(canon)
            missing_details.append(f"{canon} -> '{src}' no existe (disponibles: {available})" if src else f"{canon} sin mapping")

    if missing_required:
        raise ValueError(
            f"Faltan campos canónicos requeridos: {missing_required}. "
            f"Detalles: {missing_details}. "
            f"Columnas disponibles en RAW: {available}. "
            f"Mapping recibido: {mapping}"
        )

    # Construir df_canónico preservando filas
    n = len(df_raw)
    data = {}
    for canon in CANONICAL_FIELDS:
        src = mapping.get(canon)
        if src and src in df_raw.columns:
            series = df_raw[src]
            # normalizar
            series = _normalize_series(series, canon)
            # preservar len (normalización no debe cambiar len)
            if len(series) != n:
                raise RuntimeError(f"Normalización cambió len para {canon}")
            data[canon] = series
        else:
            # opcional faltante -> columna con NA del tipo apropiado
            if canon in REQUIRED_FIELDS:
                # ya validado arriba, no debería llegar aquí
                raise ValueError(f"Campo requerido {canon} no mapeado")
            # crear NA según tipo
            t = CANONICAL_FIELDS[canon]["type"]
            if t == "float":
                data[canon] = pd.Series([pd.NA] * n, dtype="Float64")
            elif t == "datetime":
                data[canon] = pd.Series([pd.NaT] * n, dtype="datetime64[ns]")
            else:
                data[canon] = pd.Series([pd.NA] * n, dtype="string")

    df_canon = pd.DataFrame(data, columns=list(CANONICAL_FIELDS.keys()))

    # No eliminar filas
    assert len(df_canon) == n, "to_canonical no debe cambiar len"

    return df_canon


def validate_canonical(df: pd.DataFrame) -> list[str]:
    """
    Valida df canónico. Retorna lista de errores (vacía si OK).
    No usa Streamlit, solo Python puro.
    """
    errors: list[str] = []

    if not isinstance(df, pd.DataFrame):
        return ["validate_canonical espera pd.DataFrame"]

    # 1. existen todos los REQUIRED_FIELDS como columnas
    for canon in REQUIRED_FIELDS:
        if canon not in df.columns:
            errors.append(f"Falta columna requerida: {canon}")

    # 2. columnas requeridas no completamente vacías (al menos un valor no-NA)
    for canon in REQUIRED_FIELDS:
        if canon in df.columns:
            if df[canon].isna().all():
                errors.append(f"Columna requerida '{canon}' está completamente vacía (todos NA)")

    # 3. nota numérica
    if "nota" in df.columns:
        s = pd.to_numeric(df["nota"], errors="coerce")
        # si hay al menos un valor no-NA original pero todos coerce a NA, es error
        if df["nota"].notna().any() and s.notna().sum() == 0:
            errors.append("Columna 'nota' no puede interpretarse como numérica")
        # rango check informativo (no falla si clip ya aplicado, pero avisa si hay out-of-range sin clip)
        # no error duro, solo si hay valores fuera de 0-5 antes de clip — omitido porque to_canonical ya clipea

    # 4. asistencia numérica
    if "asistencia" in df.columns:
        s = pd.to_numeric(df["asistencia"], errors="coerce")
        if df["asistencia"].notna().any() and s.notna().sum() == 0:
            errors.append("Columna 'asistencia' no puede interpretarse como numérica")

    # 5. no validamos pérdida de filas aquí (es responsabilidad de to_canonical)

    return errors
