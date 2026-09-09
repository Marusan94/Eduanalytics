"""
Humanizer Module - OpenRouter first, local fallback
Paráfrasis, corrección, humanización, resumen
"""

import json
from modules.common import get_client

def _call_openrouter(prompt: str, model: str = "openai/gpt-4o-mini", temperature: float = 0.3, max_tokens: int = 2000) -> str:
    """Llamada a OpenRouter"""
    client = get_client()
    if not client:
        raise RuntimeError("No hay API key de OpenRouter configurada")
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Error OpenRouter: {e}")

def _local_fallback(text: str, operation: str) -> str:
    """Fallback local simple sin API"""
    import re
    
    # Operaciones básicas sin API
    text = text.strip()
    
    # Limpieza básica
    import re
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return f"[Modo local - sin API] {text[:200]}..."

def humanize_text(text: str, tone: str = "Académico", intensity: int = 3, language: str = "Español") -> str:
    """
    Humaniza texto generado por IA
    tone: Académico, Cercano, Formal, Divulgativo, Técnico
    intensity: 1-5 (1=sutil, 5=profundo)
    language: Español, Inglés, Portugués
    """
    intensity_desc = {
        1: "cambios mínimos, solo suavizar",
        2: "cambios ligeros, mejorar fluidez",
        3: "reestructurar párrafos, mejorar flujo",
        4: "reestructurar profundo, cambiar vocabulario",
        5: "reescritura completa manteniendo significado"
    }
    
    tone_prompts = {
        "Académico": "formal, objetivo, terminología precisa, estructura lógica",
        "Cercano": "natural, conversacional, empático, accesible",
        "Formal": "muy formal, impersonal, preciso, riguroso",
        "Divulgativo": "claro, atractivo, ejemplos, analogías",
        "Técnico": "preciso, especializado, terminología de dominio"
    }
    
    prompt = f"""Reescribe el siguiente texto humanizándolo según estas especificaciones:

**Tono:** {tone} ({tone_prompts.get(tone, '')})
**Intensidad:** {intensity}/5 - {intensity_desc.get(intensity, '')}
**Idioma:** {language}

**Texto original:**
{text}

**Instrucciones:**
- Mantén el significado exacto y la información factual
- Cambia la estructura de oraciones y vocabulario según el tono
- Intensidad {intensity}/5: {intensity_desc.get(intensity, '')}
- Elimina patrones típicos de IA (listas excesivas, transiciones forzadas, "en conclusión", "en resumen")
- Varía la longitud de oraciones
- Usa conectores naturales
- Mantén la información factual y datos numéricos exactos
- NO añadas información nueva ni inventes datos
- Resultado SOLO el texto reescrito, sin explicaciones

Texto a humanizar:
---"""
    
    try:
        return _call_openrouter(prompt)
    except Exception as e:
        # Fallback local
        return _local_humanize(text)

def _call_openrouter(prompt: str) -> str:
    from modules.common import get_client
    client = get_client()
    if not client:
        raise RuntimeError("No hay API key")
    
    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=3000
    )
    return response.choices[0].message.content.strip()

def _local_humanize(text: str) -> str:
    """Fallback local básico"""
    import re
    # Limpieza básica sin API
    text = re.sub(r'\s+', ' ', text.strip())
    # Cambios simples de patrones típicos de IA
    replacements = {
        r'\ben conclusión\b': 'en síntesis',
        r'\ben resumen\b': 'en síntesis',
        r'\ben definitiva\b': 'finalmente',
        r'\bpor lo tanto\b': 'por tanto',
        r'\bademás\b': 'además',
        r'\bpor otro lado\b': 'por otra parte',
        r'\ben conclusión\b': 'en síntesis',
    }
    import re
    result = text
    for pattern, replacement in replacements.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result.strip()


def summarize_text(text: str, length: str) -> str:
    """Resume texto a la longitud especificada"""
    length_map = {
        "Muy breve (50 palabras)": "50 palabras máximo",
        "Breve (100 palabras)": "100 palabras aprox",
        "Medio (200 palabras)": "200 palabras aprox",
        "Detallado (400+)": "400 palabras aprox"
    }
    
    target = length_map.get(length, "100 palabras")
    
    prompt = f"""Resume el siguiente texto en {target} manteniendo la información clave:

{text}

Reglas:
- Solo el resumen, sin intro/outro
- Mantén datos numéricos exactos
- Prioriza hallazgos/conclusiones principales
- Un párrafo cohesivo"""
    
    try:
        return _call_openrouter(f"""Resume en {length} manteniendo datos clave:
{text}""")
    except Exception:
        return _local_summarize(text, length)


def _local_summarize(text: str, length: str) -> str:
    """Fallback local simple"""
    words = text.split()
    target_words = {"Muy breve (50 palabras)": 50, "Breve (100 palabras)": 100, "Medio (200 palabras)": 200, "Detallado (400+)": 400}
    target = target_words.get(length, 100)
    
    if len(words) <= target:
        return text
    
    # Tomar primeras y últimas oraciones
    import re
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= 2:
        return text[:target*5] + "..."
    
    # Tomar primera, última y una del medio
    selected = [sentences[0]]
    if len(sentences) > 2:
        selected.append(sentences[len(sentences)//2])
    selected.append(sentences[-1])
    
    result = ". ".join(selected) + "."
    return result[:target*5] + "..." if len(result) > target*5 else result


def paraphrase_text(text: str, style: str) -> str:
    """Parafrasea texto en el estilo indicado"""
    style_prompts = {
        "Académico": "formal, vocabulario académico, estructura formal",
        "Simple": "lenguaje sencillo, oraciones cortas, vocabulario común",
        "Formal": "muy formal, impersonal, estructura rígida",
        "Creativo": "original, metáforas, vocabulario rico, narrativo"
    }
    
    prompt = f"""Parafrasea el siguiente texto en estilo {style_prompts.get(style, 'natural')}:

{text}

Reglas:
- Mantén el significado exacto
- Cambia estructura y vocabulario
- No añadas ni omitas información
- Solo el texto parafraseado"""
    
    try:
        return _call_openrouter(f"""Parafrasea en estilo {style}:
{text}""")
    except Exception:
        return f"[Modo local] {text[:200]}..."


def paraphrase_text(text: str, style: str) -> str:
    """Wrapper para compatibilidad"""
    return paraphrase_text(text, style)


def correct_style(text: str, target: str) -> str:
    """Corrige/mejora estilo del texto"""
    targets = {
        "Corregir gramática": "corrige errores gramaticales, ortografía, puntuación",
        "Mejorar fluidez": "mejora conectores, transiciones, flujo de lectura",
        "Formalizar": "eleva registro, vocabulario formal, elimina coloquialismos",
        "Simplificar": "simplifica vocabulario, acorta oraciones, claridad máxima"
    }
    
    prompt = f"""{targets.get(target, 'mejora el texto')}.
Mantén el significado exacto.

Texto:
{text}

Resultado:"""
    
    try:
        return _call_openrouter(f"""Corrige/mejora: {targets.get(target, 'mejora')}\n\n{text}""")
    except Exception:
        return f"[Local] {text[:200]}..."


def summarize_text(text: str, length: str) -> str:
    """Wrapper"""
    return summarize_text(text, length)


def correct_style(text: str, target: str) -> str:
    """Wrapper"""
    return correct_style(text, target)