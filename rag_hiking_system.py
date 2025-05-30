#!/usr/bin/env python3
"""
RAG System für Appenzeller Wanderungen
======================================

Ein intelligentes Retrieval Augmented Generation System für personalisierte
Wanderempfehlungen in der Region Appenzell.

Features:
- Semantische Suche mit Embeddings
- Query Expansion für bessere Retrieval-Ergebnisse
- Re-Ranking basierend auf Benutzerpräferenzen
- Intelligente Antwortgenerierung
"""

import json
import re
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class HikingQuery:
    """Strukturierte Hiking-Anfrage mit erkannten Präferenzen"""

    original_query: str
    expanded_query: str = ""
    difficulty_preference: Optional[str] = None  # T1-T6
    duration_preference: Optional[str] = None  # "kurz", "mittel", "lang"
    elevation_preference: Optional[str] = None  # "flach", "mittel", "anspruchsvoll"
    restaurant_required: bool = False
    keywords: List[str] = None
    region_keywords: List[str] = None


@dataclass
class RetrievalResult:
    """Retrieval-Ergebnis mit detailliertem Scoring"""

    route: Dict[str, Any]
    semantic_score: float
    keyword_score: float
    preference_score: float
    final_score: float
    explanation: str


class QueryExpander:
    """Erweitert Benutzeranfragen mit domain-spezifischen Synonymen"""

    def __init__(self):
        # Appenzell-spezifische Synonyme und Begriffe
        self.hiking_synonyms = {
            "einfach": ["leicht", "gemütlich", "familienfreundlich", "anfänger", "T1"],
            "schwer": [
                "schwierig",
                "anspruchsvoll",
                "fortgeschritten",
                "steil",
                "T3",
                "T4",
                "T5",
                "T6",
            ],
            "mittel": ["mäßig", "moderate", "T2"],
            "kurz": ["schnell", "kurze", "1 stunde", "2 stunden"],
            "lang": ["ausgedehnt", "ganztag", "4 stunden", "5 stunden", "6 stunden"],
            "aussicht": ["panorama", "blick", "sicht", "vista"],
            "restaurant": [
                "gasthaus",
                "gasthof",
                "berggasthaus",
                "einkehr",
                "verpflegung",
            ],
            "berg": ["gipfel", "höhe", "bergspitze"],
            "see": ["wasser", "gewässer", "seeli"],
            "wald": ["forst", "bäume"],
            "säntis": ["alpstein", "berge", "gipfel"],
            "wanderung": ["route", "weg", "pfad", "tour"],
            "familie": ["kinder", "familienfreundlich", "einfach"],
            "natur": ["landschaft", "umgebung", "flora", "fauna"],
        }

        # Schwierigkeitsgrad-Mapping
        self.difficulty_mapping = {
            "einfach": "T1",
            "leicht": "T1",
            "anfänger": "T1",
            "mittel": "T2",
            "moderate": "T2",
            "mäßig": "T2",
            "schwer": "T3",
            "schwierig": "T3",
            "anspruchsvoll": "T3",
            "sehr schwer": "T4",
            "experte": "T4",
            "extrem": "T5",
        }

        # Appenzeller Orte und Highlights
        self.appenzell_places = [
            "säntis",
            "alpstein",
            "ebenalp",
            "aescher",
            "seealpsee",
            "kronberg",
            "hoher kasten",
            "appenzell",
            "weissbad",
            "brülisau",
            "wasserauen",
            "schwägalp",
            "meglisalp",
            "schäfler",
            "hirschberg",
            "gäbris",
        ]

    def expand_query(self, query: str) -> HikingQuery:
        """Erweitert Anfrage und extrahiert Präferenzen"""
        query_lower = query.lower()
        expanded_terms = [query]

        hiking_query = HikingQuery(original_query=query)

        # Schwierigkeitsgrad erkennen
        for difficulty, sac_level in self.difficulty_mapping.items():
            if difficulty in query_lower:
                hiking_query.difficulty_preference = sac_level
                break

        # Dauer-Präferenz erkennen
        if any(
            term in query_lower for term in ["kurz", "schnell", "1 stunde", "2 stunde"]
        ):
            hiking_query.duration_preference = "kurz"
        elif any(
            term in query_lower for term in ["lang", "ganztag", "4 stunde", "5 stunde"]
        ):
            hiking_query.duration_preference = "lang"
        else:
            hiking_query.duration_preference = "mittel"

        # Höhenmeter-Präferenz erkennen
        if any(term in query_lower for term in ["flach", "eben", "wenig höhenmeter"]):
            hiking_query.elevation_preference = "flach"
        elif any(
            term in query_lower for term in ["steil", "viele höhenmeter", "aufstieg"]
        ):
            hiking_query.elevation_preference = "anspruchsvoll"
        else:
            hiking_query.elevation_preference = "mittel"

        # Restaurant-Anforderung prüfen
        hiking_query.restaurant_required = any(
            term in query_lower
            for term in ["restaurant", "gasthaus", "einkehr", "verpflegung", "essen"]
        )

        # Synonyme hinzufügen
        for word, synonyms in self.hiking_synonyms.items():
            if word in query_lower:
                expanded_terms.extend(synonyms)

        # Appenzeller Orte identifizieren
        region_keywords = []
        for place in self.appenzell_places:
            if place in query_lower:
                region_keywords.append(place)
                expanded_terms.append(place)

        hiking_query.expanded_query = " ".join(set(expanded_terms))
        hiking_query.keywords = list(set(expanded_terms))
        hiking_query.region_keywords = region_keywords

        return hiking_query


class SimpleEmbedding:
    """Einfaches TF-IDF basiertes Embedding für semantische Suche"""

    def __init__(self):
        self.word_counts = defaultdict(int)
        self.doc_counts = defaultdict(int)
        self.total_docs = 0
        self.vocab = set()
        self.embeddings = {}

    def _tokenize(self, text: str) -> List[str]:
        """Einfache Tokenisierung"""
        # Bereinige Text und teile in Wörter auf
        text = re.sub(r"[^\w\s]", " ", text.lower())
        return [word for word in text.split() if len(word) > 2]

    def fit(self, documents: List[str]):
        """Trainiert das Embedding-Modell"""
        self.total_docs = len(documents)

        # Zähle Wort- und Dokumentfrequenzen
        for doc in documents:
            words = self._tokenize(doc)
            unique_words = set(words)

            for word in words:
                self.word_counts[word] += 1
                self.vocab.add(word)

            for word in unique_words:
                self.doc_counts[word] += 1

        # Erstelle Embeddings für jedes Dokument
        for i, doc in enumerate(documents):
            self.embeddings[i] = self._create_embedding(doc)

    def _create_embedding(self, text: str) -> np.ndarray:
        """Erstellt TF-IDF Embedding für Text"""
        words = self._tokenize(text)
        word_freq = defaultdict(int)

        # Term Frequency
        for word in words:
            word_freq[word] += 1

        # TF-IDF Vektor erstellen
        embedding = np.zeros(len(self.vocab))
        vocab_list = list(self.vocab)

        for i, word in enumerate(vocab_list):
            if word in word_freq:
                tf = word_freq[word] / len(words)
                idf = np.log(self.total_docs / (self.doc_counts[word] + 1))
                embedding[i] = tf * idf

        # Normalisierung
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def encode(self, text: str) -> np.ndarray:
        """Kodiert Text zu Embedding"""
        return self._create_embedding(text)

    def similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Berechnet Kosinus-Ähnlichkeit"""
        return np.dot(emb1, emb2)


class SemanticRetriever:
    """Semantische Suche mit einfachen Embeddings"""

    def __init__(self):
        self.embedding_model = SimpleEmbedding()
        self.routes = []
        self.route_embeddings = {}

    def build_index(self, routes: List[Dict[str, Any]]):
        """Erstellt Index für semantische Suche"""
        self.routes = routes

        # Erstelle umfassende Textrepräsentationen
        route_texts = []
        for route in routes:
            text_parts = [
                route.get("title", ""),
                route.get("description", ""),
                f"Dauer: {route.get('duration', '')}",
                f"Distanz: {route.get('distance', '')}",
                f"Höhenmeter: {route.get('elevation_gain', '')}",
                f"SAC: {route.get('sac_scale', '')}",
                f"Restaurants: {', '.join(route.get('restaurants', []))}",
                f"Highlights: {', '.join(route.get('highlights', []))}",
            ]
            combined_text = " ".join(filter(None, text_parts))
            route_texts.append(combined_text)

        # Trainiere Embedding-Modell
        self.embedding_model.fit(route_texts)

        logger.info(f"Semantischer Index für {len(routes)} Routen erstellt")

    def search(self, query: str, k: int = 10) -> List[Tuple[Dict, float]]:
        """Semantische Suche"""
        query_embedding = self.embedding_model.encode(query)

        results = []
        for i, route in enumerate(self.routes):
            route_embedding = self.embedding_model.embeddings[i]
            similarity = self.embedding_model.similarity(
                query_embedding, route_embedding
            )
            results.append((route, similarity))

        # Sortiere nach Ähnlichkeit
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]


class KeywordRetriever:
    """Keyword-basierte Suche für exakte Übereinstimmungen"""

    def __init__(self):
        self.routes = []
        self.route_texts = []

    def build_index(self, routes: List[Dict[str, Any]]):
        """Erstellt Keyword-Index"""
        self.routes = routes

        self.route_texts = []
        for route in routes:
            text_parts = [
                route.get("title", ""),
                route.get("description", ""),
                route.get("duration", ""),
                route.get("distance", ""),
                route.get("sac_scale", ""),
                " ".join(route.get("restaurants", [])),
                " ".join(route.get("highlights", [])),
            ]
            combined_text = " ".join(filter(None, text_parts)).lower()
            self.route_texts.append(combined_text)

        logger.info(f"Keyword-Index für {len(routes)} Routen erstellt")

    def search(self, query: str, k: int = 10) -> List[Tuple[Dict, float]]:
        """Keyword-Suche"""
        query_words = set(query.lower().split())

        results = []
        for i, (route, text) in enumerate(zip(self.routes, self.route_texts)):
            text_words = set(text.split())

            # Berechne Jaccard-Ähnlichkeit
            intersection = len(query_words & text_words)
            union = len(query_words | text_words)

            if union > 0:
                similarity = intersection / union
                if similarity > 0:
                    results.append((route, similarity))

        # Sortiere nach Ähnlichkeit
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]


class PreferenceReRanker:
    """Re-Ranking basierend auf Benutzerpräferenzen"""

    def __init__(self):
        self.duration_mapping = {
            "kurz": (0, 2.5),  # 0-2.5 Stunden
            "mittel": (2.5, 4.5),  # 2.5-4.5 Stunden
            "lang": (4.5, 10),  # 4.5+ Stunden
        }

        self.elevation_mapping = {
            "flach": (0, 300),  # 0-300m
            "mittel": (300, 600),  # 300-600m
            "anspruchsvoll": (600, 2000),  # 600m+
        }

    def calculate_preference_score(
        self, route: Dict[str, Any], query: HikingQuery
    ) -> float:
        """Berechnet Präferenz-Score"""
        score = 0.0

        # Schwierigkeitsgrad
        if query.difficulty_preference:
            route_sac = route.get("sac_scale", "").upper()
            if query.difficulty_preference.upper() in route_sac:
                score += 0.3

        # Dauer
        if query.duration_preference:
            duration_str = route.get("duration", "")
            duration_hours = self._extract_hours(duration_str)
            if duration_hours:
                target_range = self.duration_mapping.get(
                    query.duration_preference, (0, 10)
                )
                if target_range[0] <= duration_hours <= target_range[1]:
                    score += 0.3

        # Höhenmeter
        if query.elevation_preference:
            elevation_str = route.get("elevation_gain", "")
            elevation_meters = self._extract_elevation(elevation_str)
            if elevation_meters:
                target_range = self.elevation_mapping.get(
                    query.elevation_preference, (0, 2000)
                )
                if target_range[0] <= elevation_meters <= target_range[1]:
                    score += 0.2

        # Restaurant-Anforderung
        if query.restaurant_required:
            if route.get("restaurants") and len(route["restaurants"]) > 0:
                score += 0.2

        return score

    def _extract_hours(self, duration_str: str) -> Optional[float]:
        """Extrahiert Stunden aus Dauer-String"""
        if not duration_str:
            return None

        hours_match = re.search(r"(\d+)\s*(?:Stunden?|h)", duration_str, re.IGNORECASE)
        minutes_match = re.search(
            r"(\d+)\s*(?:Minuten?|min)", duration_str, re.IGNORECASE
        )

        hours = float(hours_match.group(1)) if hours_match else 0
        minutes = float(minutes_match.group(1)) if minutes_match else 0

        return hours + (minutes / 60) if hours > 0 or minutes > 0 else None

    def _extract_elevation(self, elevation_str: str) -> Optional[int]:
        """Extrahiert Höhenmeter"""
        if not elevation_str:
            return None

        match = re.search(r"(\d+)", elevation_str)
        return int(match.group(1)) if match else None


class AppenzellHikingRAG:
    """Haupt-RAG System für Appenzeller Wanderungen"""

    def __init__(self, routes_file: str = "appenzell_routes_clean.json"):
        self.routes_file = routes_file
        self.routes = []

        # Initialisiere Komponenten
        self.query_expander = QueryExpander()
        self.semantic_retriever = SemanticRetriever()
        self.keyword_retriever = KeywordRetriever()
        self.reranker = PreferenceReRanker()

        # Lade und indexiere Routen
        self._load_routes()
        self._build_indices()

    def _load_routes(self):
        """Lädt Wanderrouten aus JSON-Datei"""
        try:
            with open(self.routes_file, "r", encoding="utf-8") as f:
                self.routes = json.load(f)
            logger.info(f"✅ {len(self.routes)} Appenzeller Routen geladen")
        except FileNotFoundError:
            logger.error(f"❌ Routen-Datei nicht gefunden: {self.routes_file}")
            raise

    def _build_indices(self):
        """Erstellt alle Retrieval-Indizes"""
        logger.info("🔧 Erstelle Retrieval-Indizes...")
        self.semantic_retriever.build_index(self.routes)
        self.keyword_retriever.build_index(self.routes)
        logger.info("✅ Alle Indizes erfolgreich erstellt")

    def retrieve(self, query: str, k: int = 5) -> List[RetrievalResult]:
        """Haupt-Retrieval-Funktion mit Hybrid-Ansatz"""

        # 1. Query Expansion
        expanded_query = self.query_expander.expand_query(query)
        logger.info(f"🔍 Erweiterte Anfrage: {expanded_query.expanded_query[:100]}...")

        # 2. Semantische Suche
        semantic_results = self.semantic_retriever.search(
            expanded_query.expanded_query, k=k * 2
        )

        # 3. Keyword-Suche
        keyword_results = self.keyword_retriever.search(
            expanded_query.expanded_query, k=k * 2
        )

        # 4. Kombiniere und re-ranke Ergebnisse
        combined_results = self._combine_results(
            semantic_results, keyword_results, expanded_query, k
        )

        return combined_results

    def _combine_results(
        self,
        semantic_results: List[Tuple],
        keyword_results: List[Tuple],
        query: HikingQuery,
        k: int,
    ) -> List[RetrievalResult]:
        """Kombiniert und re-ranked Ergebnisse verschiedener Retriever"""

        # Sammle Scores für jede Route
        route_scores = {}

        # Semantische Ergebnisse hinzufügen
        for route, score in semantic_results:
            route_id = route["id"]
            if route_id not in route_scores:
                route_scores[route_id] = {
                    "route": route,
                    "semantic_score": score,
                    "keyword_score": 0.0,
                }
            else:
                route_scores[route_id]["semantic_score"] = max(
                    route_scores[route_id]["semantic_score"], score
                )

        # Keyword-Ergebnisse hinzufügen
        for route, score in keyword_results:
            route_id = route["id"]
            if route_id not in route_scores:
                route_scores[route_id] = {
                    "route": route,
                    "semantic_score": 0.0,
                    "keyword_score": score,
                }
            else:
                route_scores[route_id]["keyword_score"] = max(
                    route_scores[route_id]["keyword_score"], score
                )

        # Berechne finale Scores
        results = []
        for route_data in route_scores.values():
            route = route_data["route"]
            semantic_score = route_data["semantic_score"]
            keyword_score = route_data["keyword_score"]

            # Präferenz-Score
            preference_score = self.reranker.calculate_preference_score(route, query)

            # Gewichteter finaler Score
            final_score = (
                0.4 * semantic_score + 0.3 * keyword_score + 0.3 * preference_score
            )

            # Erstelle Erklärung
            explanation = self._create_explanation(
                route, query, semantic_score, keyword_score, preference_score
            )

            results.append(
                RetrievalResult(
                    route=route,
                    semantic_score=semantic_score,
                    keyword_score=keyword_score,
                    preference_score=preference_score,
                    final_score=final_score,
                    explanation=explanation,
                )
            )

        # Sortiere nach finalem Score
        results.sort(key=lambda x: x.final_score, reverse=True)
        return results[:k]

    def _create_explanation(
        self,
        route: Dict,
        query: HikingQuery,
        semantic_score: float,
        keyword_score: float,
        preference_score: float,
    ) -> str:
        """Erstellt Erklärung für Empfehlung"""
        explanations = []

        if semantic_score > 0.5:
            explanations.append("Hohe inhaltliche Übereinstimmung")
        elif semantic_score > 0.3:
            explanations.append("Gute thematische Relevanz")

        if keyword_score > 0.3:
            explanations.append("Enthält gesuchte Begriffe")

        if preference_score > 0.5:
            explanations.append("Passt sehr gut zu Ihren Präferenzen")
        elif preference_score > 0.3:
            explanations.append("Teilweise passend zu Ihren Wünschen")

        if not explanations:
            explanations.append("Allgemeine Relevanz für Appenzeller Wanderungen")

        return "; ".join(explanations)

    def generate_response(self, query: str, results: List[RetrievalResult]) -> str:
        """Generiert natürlichsprachige Antwort"""

        if not results:
            return "Ich konnte leider keine passenden Wanderrouten finden. Versuchen Sie es mit anderen Suchbegriffen."

        # Erstelle Kontext aus Top-Ergebnissen
        context_parts = []
        for i, result in enumerate(results[:3], 1):
            route = result.route
            context_parts.append(
                f"""
**Route {i}: {route['title']}**
- Dauer: {route.get('duration', 'Nicht angegeben')}
- Distanz: {route.get('distance', 'Nicht angegeben')}
- Höhenmeter: {route.get('elevation_gain', 'Nicht angegeben')}
- Schwierigkeit: {route.get('sac_scale', 'Nicht angegeben')}
- Restaurants: {', '.join(route.get('restaurants', [])[:2]) if route.get('restaurants') else 'Keine angegeben'}
- Beschreibung: {route.get('description', '')[:150]}...
- Warum empfohlen: {result.explanation}
"""
            )

        context = "\n".join(context_parts)

        # Generiere Antwort
        response = f"""Basierend auf Ihrer Anfrage "{query}" habe ich {len(results)} passende Wanderrouten in Appenzell gefunden:

{context}

Diese Routen wurden basierend auf inhaltlicher Ähnlichkeit, Keyword-Übereinstimmung und Ihren erkannten Präferenzen ausgewählt. Jede Route enthält detaillierte Informationen über Dauer, Schwierigkeit und verfügbare Restaurants entlang des Weges.

Möchten Sie mehr Details zu einer bestimmten Route oder haben Sie andere Präferenzen?"""

        return response

    def search(self, query: str, k: int = 3) -> str:
        """Haupt-Suchschnittstelle"""
        logger.info(f"🎯 Verarbeite Anfrage: {query}")

        # Finde relevante Routen
        results = self.retrieve(query, k=k)

        # Generiere Antwort
        response = self.generate_response(query, results)

        return response


def main():
    """Demo des RAG-Systems"""
    print("🏔️ Appenzeller Wanderungen RAG System")
    print("=" * 60)

    # Initialisiere RAG-System
    try:
        rag = AppenzellHikingRAG()
        print("✅ RAG-System erfolgreich initialisiert")
    except Exception as e:
        print(f"❌ Fehler beim Initialisieren des RAG-Systems: {e}")
        return

    # Demo-Anfragen
    demo_queries = [
        "Ich möchte eine einfache Wanderung mit Restaurant",
        "Suche anspruchsvolle Bergtouren mit schöner Aussicht",
        "Kurze Familienwanderung in der Nähe von einem See",
        "Lange Wanderung mit vielen Höhenmetern zum Säntis",
        "Gemütliche Tour mit Einkehrmöglichkeit",
    ]

    print("\n🔍 Demo-Anfragen:")
    print("-" * 40)

    for query in demo_queries:
        print(f"\n📝 Anfrage: {query}")
        print("-" * 25)

        try:
            response = rag.search(query, k=2)  # Zeige 2 Top-Ergebnisse
            print(response)
        except Exception as e:
            print(f"❌ Fehler bei Anfrage: {e}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
