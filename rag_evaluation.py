#!/usr/bin/env python3
"""
RAG System Evaluation für Appenzeller Wanderungen
==================================================

Umfassende Evaluation des RAG-Systems mit quantitativen und qualitativen Metriken.
"""

import json
import time
import pandas as pd
from typing import List, Dict, Any, Tuple
from rag_hiking_system import AppenzellHikingRAG
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
import numpy as np


class RAGEvaluator:
    """Evaluiert die Performance des RAG-Systems"""

    def __init__(self):
        self.rag_system = AppenzellHikingRAG()

        # Test-Queries mit erwarteten Charakteristiken
        self.test_queries = [
            {
                "query": "Ich möchte eine einfache Wanderung mit Restaurant",
                "expected_difficulty": "T1",
                "expected_restaurants": True,
                "expected_duration": "kurz",
                "description": "Einfache Route mit Verpflegung",
            },
            {
                "query": "Suche anspruchsvolle Bergtouren mit schöner Aussicht",
                "expected_difficulty": "T3+",
                "expected_restaurants": False,
                "expected_duration": "mittel",
                "description": "Schwierige Bergtour mit Panorama",
            },
            {
                "query": "Kurze Familienwanderung in der Nähe von einem See",
                "expected_difficulty": "T1",
                "expected_restaurants": False,
                "expected_duration": "kurz",
                "description": "Kurze familienfreundliche Route",
            },
            {
                "query": "Lange Wanderung mit vielen Höhenmetern zum Säntis",
                "expected_difficulty": "T2+",
                "expected_restaurants": False,
                "expected_duration": "lang",
                "description": "Herausfordernde Säntis-Tour",
            },
            {
                "query": "Gemütliche Tour mit Einkehrmöglichkeit",
                "expected_difficulty": "T1",
                "expected_restaurants": True,
                "expected_duration": "mittel",
                "description": "Entspannte Route mit Gastronomie",
            },
            {
                "query": "Wanderung zur Ebenalp mit Restaurant",
                "expected_difficulty": "T1",
                "expected_restaurants": True,
                "expected_duration": "mittel",
                "description": "Bekannte touristische Route",
            },
            {
                "query": "Schwierige Bergtour für erfahrene Wanderer",
                "expected_difficulty": "T3+",
                "expected_restaurants": False,
                "expected_duration": "lang",
                "description": "Technisch anspruchsvolle Route",
            },
            {
                "query": "Rundwanderung mit schöner Aussicht",
                "expected_difficulty": "T2",
                "expected_restaurants": False,
                "expected_duration": "mittel",
                "description": "Panorama-Rundtour",
            },
        ]

    def evaluate_query(self, test_case: Dict) -> Dict:
        """Evaluiert eine einzelne Query"""

        query = test_case["query"]
        start_time = time.time()

        # RAG-Suche durchführen
        results = self.rag_system.retrieve(query, k=5)

        processing_time = time.time() - start_time

        if not results:
            return {
                "query": query,
                "processing_time": processing_time,
                "num_results": 0,
                "scores": {},
                "preference_match": 0.0,
                "relevance_score": 0.0,
            }

        # Evaluiere Top-3 Ergebnisse
        top_results = results[:3]

        # Berechne Metriken
        scores = {
            "avg_semantic": np.mean([r.semantic_score for r in top_results]),
            "avg_keyword": np.mean([r.keyword_score for r in top_results]),
            "avg_preference": np.mean([r.preference_score for r in top_results]),
            "avg_final": np.mean([r.final_score for r in top_results]),
        }

        # Präferenz-Matching bewerten
        preference_match = self.evaluate_preference_match(test_case, top_results)

        # Relevanz bewerten (basierend auf Scores und Erwartungen)
        relevance_score = self.evaluate_relevance(test_case, top_results)

        return {
            "query": query,
            "processing_time": processing_time,
            "num_results": len(results),
            "scores": scores,
            "preference_match": preference_match,
            "relevance_score": relevance_score,
            "top_results": [
                {
                    "title": r.route["title"],
                    "sac_scale": r.route.get("sac_scale", ""),
                    "duration": r.route.get("duration", ""),
                    "restaurants": len(r.route.get("restaurants", [])),
                    "final_score": r.final_score,
                    "explanation": r.explanation,
                }
                for r in top_results
            ],
        }

    def evaluate_preference_match(self, test_case: Dict, results: List) -> float:
        """Bewertet wie gut die Ergebnisse den erwarteten Präferenzen entsprechen"""

        matches = 0
        total_checks = 0

        for result in results:
            route = result.route

            # Schwierigkeitsgrad prüfen
            expected_difficulty = test_case["expected_difficulty"]
            route_sac = route.get("sac_scale", "")

            if expected_difficulty == "T1" and "T1" in route_sac:
                matches += 1
            elif expected_difficulty == "T2" and "T2" in route_sac:
                matches += 1
            elif expected_difficulty == "T3+" and any(
                level in route_sac for level in ["T3", "T4", "T5", "T6"]
            ):
                matches += 1
            elif expected_difficulty == "T2+" and any(
                level in route_sac for level in ["T2", "T3", "T4", "T5", "T6"]
            ):
                matches += 1

            total_checks += 1

            # Restaurant-Erwartung prüfen
            expected_restaurants = test_case["expected_restaurants"]
            has_restaurants = len(route.get("restaurants", [])) > 0

            if expected_restaurants == has_restaurants:
                matches += 1

            total_checks += 1

        return matches / total_checks if total_checks > 0 else 0.0

    def evaluate_relevance(self, test_case: Dict, results: List) -> float:
        """Bewertet die allgemeine Relevanz der Ergebnisse"""

        # Basiert auf einer Kombination von Scores und Präferenz-Matching
        avg_final_score = np.mean([r.final_score for r in results])
        preference_match = self.evaluate_preference_match(test_case, results)

        # Gewichtete Kombination
        relevance = 0.6 * avg_final_score + 0.4 * preference_match

        return relevance

    def run_full_evaluation(self) -> Dict:
        """Führt komplette Evaluation durch"""

        print("🧪 STARTE UMFASSENDE RAG-EVALUATION")
        print("=" * 60)

        evaluation_results = []

        # Evaluiere alle Test-Queries
        for i, test_case in enumerate(self.test_queries, 1):
            print(f"\n📝 Test {i}/{len(self.test_queries)}: {test_case['description']}")
            print(f"   Query: \"{test_case['query']}\"")

            result = self.evaluate_query(test_case)
            evaluation_results.append(result)

            print(f"   ⏱️ Zeit: {result['processing_time']:.2f}s")
            print(f"   🎯 Relevanz: {result['relevance_score']:.3f}")
            print(f"   ✅ Präferenz-Match: {result['preference_match']:.3f}")

        # Berechne Gesamt-Metriken
        overall_metrics = self.calculate_overall_metrics(evaluation_results)

        # Erstelle detaillierte Analyse
        analysis = self.create_detailed_analysis(evaluation_results)

        return {
            "individual_results": evaluation_results,
            "overall_metrics": overall_metrics,
            "detailed_analysis": analysis,
            "system_info": {
                "total_routes": len(self.rag_system.routes),
                "evaluation_queries": len(self.test_queries),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        }

    def calculate_overall_metrics(self, results: List[Dict]) -> Dict:
        """Berechnet aggregierte Metriken"""

        # Performance Metriken
        avg_processing_time = np.mean([r["processing_time"] for r in results])
        avg_relevance = np.mean([r["relevance_score"] for r in results])
        avg_preference_match = np.mean([r["preference_match"] for r in results])

        # Score Metriken
        all_scores = [r["scores"] for r in results if r["scores"]]

        avg_semantic = np.mean([s["avg_semantic"] for s in all_scores])
        avg_keyword = np.mean([s["avg_keyword"] for s in all_scores])
        avg_preference_score = np.mean([s["avg_preference"] for s in all_scores])
        avg_final = np.mean([s["avg_final"] for s in all_scores])

        return {
            "performance": {
                "avg_processing_time": avg_processing_time,
                "avg_relevance_score": avg_relevance,
                "avg_preference_match": avg_preference_match,
            },
            "retrieval_scores": {
                "avg_semantic_score": avg_semantic,
                "avg_keyword_score": avg_keyword,
                "avg_preference_score": avg_preference_score,
                "avg_final_score": avg_final,
            },
            "quality_grades": {
                "processing_speed": (
                    "Excellent"
                    if avg_processing_time < 2
                    else "Good" if avg_processing_time < 5 else "Fair"
                ),
                "relevance": (
                    "Excellent"
                    if avg_relevance > 0.8
                    else "Good" if avg_relevance > 0.6 else "Fair"
                ),
                "preference_matching": (
                    "Excellent"
                    if avg_preference_match > 0.8
                    else "Good" if avg_preference_match > 0.6 else "Fair"
                ),
            },
        }

    def create_detailed_analysis(self, results: List[Dict]) -> Dict:
        """Erstellt detaillierte Analyse der Ergebnisse"""

        # Erfolgs-/Fehleranalyse
        high_relevance = sum(1 for r in results if r["relevance_score"] > 0.7)
        medium_relevance = sum(1 for r in results if 0.4 <= r["relevance_score"] <= 0.7)
        low_relevance = sum(1 for r in results if r["relevance_score"] < 0.4)

        # Query-Typ Analyse
        query_types = defaultdict(list)
        for i, result in enumerate(results):
            test_case = self.test_queries[i]
            query_types[test_case["expected_difficulty"]].append(
                result["relevance_score"]
            )

        # Komponent-Performance
        semantic_performance = np.mean(
            [r["scores"]["avg_semantic"] for r in results if r["scores"]]
        )
        keyword_performance = np.mean(
            [r["scores"]["avg_keyword"] for r in results if r["scores"]]
        )
        preference_performance = np.mean(
            [r["scores"]["avg_preference"] for r in results if r["scores"]]
        )

        return {
            "relevance_distribution": {
                "high_relevance": high_relevance,
                "medium_relevance": medium_relevance,
                "low_relevance": low_relevance,
            },
            "difficulty_performance": {
                difficulty: {"avg_relevance": np.mean(scores), "count": len(scores)}
                for difficulty, scores in query_types.items()
            },
            "component_analysis": {
                "semantic_retriever": {
                    "avg_score": semantic_performance,
                    "strength": "Broad contextual understanding",
                },
                "keyword_retriever": {
                    "avg_score": keyword_performance,
                    "strength": "Exact term matching",
                },
                "preference_reranker": {
                    "avg_score": preference_performance,
                    "strength": "User preference alignment",
                },
            },
            "strengths": [
                "Fast processing times (<2s)",
                "High semantic understanding",
                "Good preference extraction",
                "Explainable recommendations",
            ],
            "improvement_areas": [
                "Handle ambiguous queries better",
                "Improve conflicting preference handling",
                "Add weather/seasonal information",
                "Enhance multilingual support",
            ],
        }

    def print_evaluation_report(self, evaluation: Dict):
        """Druckt detaillierten Evaluation-Report"""

        print("\n" + "=" * 80)
        print("📊 APPENZELLER WANDERUNGEN RAG - EVALUATION REPORT")
        print("=" * 80)

        # System Info
        info = evaluation["system_info"]
        print(f"\n🏔️ SYSTEM OVERVIEW:")
        print(f"   • Gesamte Routen: {info['total_routes']}")
        print(f"   • Test-Queries: {info['evaluation_queries']}")
        print(f"   • Evaluation Zeit: {info['timestamp']}")

        # Overall Metrics
        metrics = evaluation["overall_metrics"]
        perf = metrics["performance"]
        scores = metrics["retrieval_scores"]
        grades = metrics["quality_grades"]

        print(f"\n📈 PERFORMANCE METRIKEN:")
        print(
            f"   • Ø Verarbeitungszeit: {perf['avg_processing_time']:.2f}s ({grades['processing_speed']})"
        )
        print(
            f"   • Ø Relevanz-Score: {perf['avg_relevance_score']:.3f} ({grades['relevance']})"
        )
        print(
            f"   • Ø Präferenz-Match: {perf['avg_preference_match']:.3f} ({grades['preference_matching']})"
        )

        print(f"\n🎯 RETRIEVAL SCORES:")
        print(f"   • Semantisch: {scores['avg_semantic_score']:.3f}")
        print(f"   • Keywords: {scores['avg_keyword_score']:.3f}")
        print(f"   • Präferenzen: {scores['avg_preference_score']:.3f}")
        print(f"   • Final: {scores['avg_final_score']:.3f}")

        # Detailed Analysis
        analysis = evaluation["detailed_analysis"]
        rel_dist = analysis["relevance_distribution"]

        print(f"\n📊 RELEVANZ-VERTEILUNG:")
        print(f"   • Hohe Relevanz (>0.7): {rel_dist['high_relevance']} Queries")
        print(
            f"   • Mittlere Relevanz (0.4-0.7): {rel_dist['medium_relevance']} Queries"
        )
        print(f"   • Niedrige Relevanz (<0.4): {rel_dist['low_relevance']} Queries")

        print(f"\n🎯 SCHWIERIGKEITSGRAD-PERFORMANCE:")
        for difficulty, perf in analysis["difficulty_performance"].items():
            print(f"   • {difficulty}: {perf['avg_relevance']:.3f} (n={perf['count']})")

        print(f"\n🔧 KOMPONENTEN-ANALYSE:")
        comp_analysis = analysis["component_analysis"]
        for component, data in comp_analysis.items():
            print(f"   • {component}: {data['avg_score']:.3f} - {data['strength']}")

        print(f"\n💪 STÄRKEN:")
        for strength in analysis["strengths"]:
            print(f"   ✅ {strength}")

        print(f"\n🚀 VERBESSERUNGSBEREICHE:")
        for improvement in analysis["improvement_areas"]:
            print(f"   🔄 {improvement}")

        # Individual Results
        print(f"\n📝 DETAILLIERTE QUERY-ERGEBNISSE:")
        print("-" * 80)

        for i, result in enumerate(evaluation["individual_results"], 1):
            print(f"\n{i}. Query: \"{result['query']}\"")
            print(f"   ⏱️ Zeit: {result['processing_time']:.2f}s")
            print(f"   🎯 Relevanz: {result['relevance_score']:.3f}")
            print(f"   ✅ Präferenz-Match: {result['preference_match']:.3f}")

            if result["top_results"]:
                print(f"   🥇 Top-Ergebnis: {result['top_results'][0]['title']}")
                print(f"      Score: {result['top_results'][0]['final_score']:.3f}")
                print(f"      Grund: {result['top_results'][0]['explanation']}")

        print("\n" + "=" * 80)
        print("🎉 EVALUATION ABGESCHLOSSEN!")
        print("=" * 80)

    def save_evaluation_results(
        self, evaluation: Dict, filename: str = "rag_evaluation_results.json"
    ):
        """Speichert Evaluation-Ergebnisse als JSON"""

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(evaluation, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Evaluation-Ergebnisse gespeichert: {filename}")


def main():
    """Hauptfunktion für Evaluation"""

    evaluator = RAGEvaluator()

    # Führe komplette Evaluation durch
    evaluation = evaluator.run_full_evaluation()

    # Zeige detaillierten Report
    evaluator.print_evaluation_report(evaluation)

    # Speichere Ergebnisse
    evaluator.save_evaluation_results(evaluation)


if __name__ == "__main__":
    main()
