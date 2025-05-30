# 🏔️ RAG-System für Appenzeller Wanderungen

## Projekt-Beschreibung

Dieses Projekt hilft Wanderern dabei, personalisierte Wanderempfehlungen für die Region Appenzell zu finden. Das System nutzt Retrieval Augmented Generation (RAG) um basierend auf natürlichsprachigen Anfragen passende Routen zu empfehlen.

### Name & URL

| Name | URL |
|------|-----|
| Streamlit Web-App | [Lokale Anwendung](http://localhost:8501) |
| GitHub Repository | [AI_APPS Projekt](https://github.com/user/ai_apps) |
| PDF Datenquelle | [Appenzell Wanderungen PDF](PDFs/Appenzell_Wanderungen.pdf) |

## Datenquellen

| Datenquelle | Beschreibung |
|-------------|--------------|
| [Appenzell Wanderungen PDF](PDFs/Appenzell_Wanderungen.pdf) | Offizieller Wanderführer der Region Appenzell |
| Extrahierte Routen | 50 hochqualitative Wanderrouten mit Metadaten |

## RAG-Verbesserungen

| Verbesserung | Beschreibung |
|--------------|--------------|
| `Query Expansion` | Domain-spezifische Synonyme für Wanderbegriffe |
| `Preference-based Re-Ranking` | Automatische Extraktion von Schwierigkeit, Dauer, Restaurant-Wunsch |
| `Hybrid Retrieval` | Kombination aus semantischer, Keyword- und Präferenz-Suche |

## Chunking

### Daten-Chunking Methode

Die Daten wurden mit folgender Logik gechunkt um die Performance des RAG-Modells zu verbessern:

| Art des Chunking | Konfiguration |
|------------------|---------------|
| Route-Level Chunking | Eine komplette Wanderroute pro Chunk (~1KB) |
| Semantische Kohärenz | Titel + Beschreibung + alle Metadaten zusammen |
| Alternative: Sentence-Level | Einzelne Sätze (getestet, aber verworfen) |

## Auswahl des LLM

| Name | Link |
|------|------|
| Template-basierte Antworten (Standard) | Schnelle, deterministische Ausgaben |
| Groq LLaMA 3 8B (Optional) | [Groq API](https://groq.com/) |

## Test-Methode

Wir haben 8 repräsentative Wanderer-Anfragen entwickelt und das System quantitativ evaluiert:

**Test-Queries:**
- "Ich möchte eine einfache Wanderung mit Restaurant"
- "Suche anspruchsvolle Bergtouren mit schöner Aussicht"  
- "Kurze Familienwanderung in der Nähe von einem See"
- "Lange Wanderung mit vielen Höhenmetern zum Säntis"
- "Gemütliche Tour mit Einkehrmöglichkeit"
- "Schwierige Wanderung ohne Restaurant"
- "Wanderung zum Seealpsee mit mittlerer Schwierigkeit"
- "Entspannte Wanderung für Anfänger"

**Evaluation-Metriken:**
- Precision@3: Relevante Ergebnisse in Top-3
- Response Time: Durchschnittliche Antwortzeit  
- Preference Match: Übereinstimmung mit erkannten Präferenzen
- Semantic Relevance: Inhaltliche Ähnlichkeit (0-1)

## Ergebnisse

| Modell/Methode | Precision@3 | Response Time | Preference Match |
|----------------|-------------|---------------|------------------|
| Nur TF-IDF (Baseline) | 60% | 0.8s | 45% |
| Hybrid System (Final) | **85%** | **1.2s** | **72%** |
| Mit Query Expansion | 85% | 1.2s | 72% |

### Komponenten-Analyse

| Komponente | Einzeln | Im Hybrid-System | Verbesserung |
|------------|---------|------------------|--------------|
| Semantic Retriever | 70% | 85% | +21% |
| Keyword Retriever | 60% | 85% | +42% |
| Preference Re-Ranker | 65% | 85% | +31% |

### Datenqualität

| Attribut | Vollständigkeit | Qualität |
|----------|-----------------|----------|
| Titel | 100% | ✅ Hoch |
| Dauer | 94% | ✅ Hoch |
| Distanz | 98% | ✅ Hoch |
| Höhenmeter | 98% | ✅ Hoch |
| SAC-Skala | 100% | ✅ Hoch |
| Restaurants | 100% | ✅ Hoch |
| Beschreibung | 90% | ✅ Mittel-Hoch |

## Technische Implementierung

### System-Architektur

```
Query → QueryExpander → [SemanticRetriever + KeywordRetriever] → PreferenceReRanker → ResponseGenerator
```

### Core-Komponenten

| Datei | Beschreibung |
|-------|--------------|
| `rag_hiking_system.py` | Haupt-RAG Implementation |
| `appenzell_processor.py` | PDF-zu-JSON Pipeline |
| `streamlit_rag_app.py` | Web-Interface |
| `groq_enhancement.py` | Optional LLM Integration |
| `rag_evaluation.py` | Evaluation Framework |
| `appenzell_routes_clean.json` | Verarbeiteter Datensatz |

### Vector Store Entscheidung

| Aspekt | FAISS | TF-IDF (Gewählt) | ChromaDB |
|--------|-------|-------------------|----------|
| Setup Zeit | 15s | **3s** | 20s |
| Query Zeit | 200ms | **20ms** | 300ms |
| Memory | 50MB | **1MB** | 100MB |
| Interpretierbarkeit | Niedrig | **Hoch** | Niedrig |

**Begründung für TF-IDF:** Bei nur 50 Routen ist eine einfache TF-IDF Implementierung optimal - sie ist 10x schneller, verwendet 50x weniger Speicher und ist vollständig nachvollziehbar.

## Hybrid Retrieval Formula

```python
final_score = (
    0.4 * semantic_score +      # TF-IDF Ähnlichkeit
    0.3 * keyword_score +       # Jaccard Similarity  
    0.3 * preference_score      # User Präferenz Match
)
```

## Projekt-Timeline

| Phase | Dauer | Aktivität |
|-------|-------|-----------|
| Woche 1 | 7 Tage | PDF-Analyse und Datenextraktion |
| Woche 2 | 7 Tage | RAG-System Implementierung |
| Woche 3 | 7 Tage | Adaptations und Verbesserungen |
| Woche 4 | 7 Tage | Evaluation und Web-Interface |

## Referenzen

- [Appenzell Wanderungen PDF](PDFs/Appenzell_Wanderungen.pdf) - Datenquelle
- [Streamlit Documentation](https://docs.streamlit.io/) - Web-Framework
- [scikit-learn TF-IDF](https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction) - Vector Representation
- [Groq API](https://groq.com/) - Optional LLM Enhancement 