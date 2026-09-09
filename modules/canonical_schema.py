"""
Modelo canónico de EduAnalytics Hub.

Contrato interno mínimo que normaliza diferentes fuentes (CSV/Excel/API)
a un esquema común para Analytics, Dashboard Académico, Analista IA,
Laboratorio, Descubrimientos y futura Biblioteca/RAG.

No representa todas las columnas de las fuentes originales — solo los 8
campos necesarios para las funcionalidades actuales. Las fuentes externas
serán transformadas a este esquema vía una futura capa de mapping
(modules/mapper.py), sin que los módulos conozcan la estructura original.
"""

CANONICAL_FIELDS = {
    "id_estudiante": {
        "type": "str",
        "required": True,
        "origin": "id_estudiante",
        "description": "Identificador único del estudiante",
    },
    "grupo_id": {
        "type": "str",
        "required": True,
        "origin": "grupo_id",
        "description": "Grupo/curso al que pertenece el estudiante",
    },
    "materia": {
        "type": "str",
        "required": True,
        "origin": "materia",
        "description": "Materia/asignatura evaluada",
    },
    "nota": {
        "type": "float",
        "required": True,
        "origin": "nota",
        "range": (0, 5),
        "description": "Calificación numérica (0–5)",
    },
    "asistencia": {
        "type": "float",
        "required": True,
        "origin": "asistencia",
        "range": (0, 100),
        "description": "Porcentaje de asistencia (0–100)",
    },
    "tipo_apoyo": {
        "type": "str",
        "required": False,
        "origin": "tipo_apoyo",
        "description": "Tipo de apoyo solicitado (académico, psicológico, etc.)",
    },
    "tipo_usuario": {
        "type": "str",
        "required": False,
        "origin": "tipo_usuario",
        "description": "Rol del usuario (estudiante, docente, familiar)",
    },
    "timestamp": {
        "type": "datetime",
        "required": False,
        "origin": "timestamp / fecha_registro",
        "description": "Fecha/hora del registro (fallback fecha_registro si timestamp falta)",
    },
}

# Helpers mínimos para validación sin dependencias externas
REQUIRED_FIELDS = [k for k, v in CANONICAL_FIELDS.items() if v["required"]]
OPTIONAL_FIELDS = [k for k, v in CANONICAL_FIELDS.items() if not v["required"]]
