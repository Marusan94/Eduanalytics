"""
CAJAL Article Generator - OpenRouter first, local fallback
IMRaD structure + real arXiv citations + tribunal scoring
OpenRouter first, local fallback
"""

import json
import re
from datetime import datetime
from modules.common import get_client

def _call_openrouter(prompt: str, model: str = "openai/gpt-4o-mini", max_tokens: int = 4000) -> str:
    """Llamada a OpenRouter"""
    from modules.common import get_client
    client = get_client()
    if not client:
        raise RuntimeError("No hay API key de OpenRouter configurada")
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Error OpenRouter: {e}")

def _fetch_arxiv_papers(query: str, max_results: int = 5) -> list:
    """Buscar papers reales en arXiv"""
    try:
        import requests
        import xml.etree.ElementTree as ET
        import urllib.parse
        
        query_encoded = urllib.parse.quote(query)
        url = f"http://export.arxiv.org/api/query?search_query=all:{query_encoded}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"
        
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.content)
        
        # Namespace
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        papers = []
        
        for entry in root.findall('atom:entry', {'atom': 'http://www.w3.org/2005/Atom'}):
            title = entry.find('atom:title', {'atom': 'http://www.w3.org/2005/Atom'})
            summary = entry.find('atom:summary', {'atom': 'http://www.w3.org/2005/Atom'})
            authors = entry.findall('atom:author/atom:name', {'atom': 'http://www.w3.org/2005/Atom'})
            published = entry.find('atom:published', {'atom': 'http://www.w3.org/2005/Atom'})
            arxiv_id = entry.find('atom:id', {'atom': 'http://www.w3.org/2005/Atom'})
            
            paper = {
                'title': title.text.strip() if title is not None else '',
                'abstract': summary.text.strip() if summary is not None else '',
                'authors': [a.text for a in authors],
                'published': published.text[:10] if published is not None else '',
                'arxiv_id': arxiv_id.text.split('/')[-1] if arxiv_id is not None else '',
                'url': f"https://arxiv.org/abs/{arxiv_id.text.split('/')[-1]}" if arxiv_id is not None else ''
            }
            papers.append(paper)
        
        return papers
    except Exception as e:
        return []

def generate_cajal_article(
    topic: str,
    level: str = "Maestría",
    format_style: str = "CAJAL (IMRaD + Puntuación Tribunal)",
    length: str = "800-1200 palabras",
    include_citations: bool = True,
    include_methodology: bool = True,
    include_stats: bool = False,
    peer_review: bool = True
) -> str:
    """
    Genera artículo CAJAL con estructura IMRaD, citas arXiv reales, puntuación tribunal
    """
    
    # Buscar papers reales si se piden citas
    papers = []
    if include_citations:
        papers = _fetch_arxiv_papers(topic, max_results=5)
    
    # Construir prompt detallado
    length_map = {
        "800-1200 palabras": "800-1200 palabras",
        "1500-2500 palabras": "1500-2500 palabras",
        "3000+ palabras": "3000+ palabras"
    }
    
    length_target = length_map.get(length, "800-1200 palabras")
    
    # Construir secciones IMRaD
    sections = ["Título", "Resumen (150 palabras)", "Palabras clave (5-7)"]
    
    sections.extend([
        "1. Introducción",
        "2. Justificación / Estado del arte",
        "3. Objetivos (General y Específicos)",
    ])
    
    if include_methodology:
        sections.append("3. Metodología")
    
    sections.extend([
        "4. Resultados",
        "5. Discusión",
        "6. Conclusiones",
        "Referencias"
    ])
    
    if peer_review:
        sections.append("Anexo: Puntuación Tribunal CAJAL")
    
    # Preparar contexto de papers reales
    papers_context = ""
    if include_citations and papers:
        papers_text = ""
        for i, p in enumerate(papers, 1):
            papers_text += f"\n[{i}] {p['title']} ({p['published'][:4]}). {p['abstract'][:200]}... URL: {p['url']}"
        citations_context = f"\nArtículos reales arXiv disponibles para citar:{papers_text}\n"
    else:
        citations_context = "\n[Generar referencias simuladas si no hay papers reales]\n"
    
    prompt = f"""Genera un artículo científico completo siguiendo el modelo CAJAL (IMRaD + Puntuación Tribunal).

**Tema:** {topic}
**Nivel:** {level}
**Formato:** {format_style}
**Extensión:** {length}
**Estructura IMRaD obligatoria:** {' > '.join(sections)}

**Requisitos obligatorios:**
1. Estructura IMRaD completa con todas las secciones numeradas
2. Resumen de máximo 150 palabras con: contexto, objetivo, metodología, resultados clave, conclusión
3. 5-7 palabras clave relevantes
4. Introducción con: contexto, problema, gap de conocimiento, objetivo
5. Justificación/Estado del arte con referencias a literatura real
6. Objetivo general y 3-4 objetivos específicos medibles
{'7. Metodología detallada: diseño, población, variables, instrumentos, análisis estadístico, ética' if include_methodology else ''}
8. Resultados con datos simulados realistas (tablas en markdown)
9. Discusión: interpretación, comparación con literatura, limitaciones, implicaciones
10. Conclusiones: respuesta a objetivos, implicaciones prácticas, líneas futuras
{'11. Puntuación Tribunal CAJAL: Originalidad (1-10), Rigor metodológico (1-10), Relevancia (1-10), Redacción (1-10), Impacto potencial (1-10) - Total/50' if True else ''}
{'12. Referencias en formato APA 7ma edición con DOIs reales de arXiv' if True else ''}

**Citas reales arXiv disponibles:**
{'[Usar papers reales de arXiv como referencias]' if True else '[Generar referencias simuladas]'}

**Contexto de papers reales arXiv:**
{_fetch_arxiv_papers('educational technology ' + ' '.join(filter(None, ['educational', 'technology']))) if True else 'Sin papers reales'}

---

**Instrucciones de generación:**
1. Genera el artículo COMPLETO en español académico formal
2. Usa formato markdown con encabezados #
2. Tablas en markdown cuando sea apropiado (resultados, comparaciones)
3. Citas en formato [1], [2] referenciando papers reales
3. Longitud objetivo: ~1200-1500 palabras
4. Tono: académico formal, objetivo, riguroso
5. NO inventes datos estadísticos - usa "datos simulados con fines ilustrativos" donde aplique
6. Citas reales de arXiv con formato APA 7ma: Autor, A. (Año). Título. Revista, Vol(Issue), pp-pp. DOI/URL
4. Puntuación tribunal CAJAL al final con justificación breve por criterio
5. Referencias en APA 7ma con DOIs reales

--- INICIO DEL ARTÍCULO ---
"""
    
    try:
        return _call_openrouter(prompt)
    except Exception as e:
        return _local_cajal_article(topic)


def _call_openrouter(prompt: str) -> str:
    """Llamada a OpenRouter"""
    from modules.common import get_client
    client = get_client()
    if not client:
        raise RuntimeError("No hay API key de OpenRouter configurada")
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un editor científico experto en redacción académica CAJAL/IMRaD. Generas artículos listos para publicación con citas reales y estructura rigurosa."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Error OpenRouter: {e}")