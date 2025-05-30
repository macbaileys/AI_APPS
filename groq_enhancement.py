#!/usr/bin/env python3
"""
Groq Enhancement für das Appenzeller Wanderungen RAG System
===========================================================

Integration von Groq LLM für natürlichere Antwortgenerierung
"""

import os
from groq import Groq
from rag_hiking_system import AppenzellHikingRAG
from typing import List


class GroqEnhancedRAG(AppenzellHikingRAG):
    """Erweitert das RAG-System mit Groq LLM für bessere Antworten"""

    def __init__(self, groq_api_key: str = None):
        super().__init__()

        # Groq Client initialisieren
        self.groq_client = Groq(api_key=groq_api_key or os.getenv("GROQ_API_KEY"))

    def generate_groq_response(self, query: str, results: List) -> str:
        """Generiert natürlichsprachige Antwort mit Groq"""

        if not results:
            return "Entschuldigung, ich konnte keine passenden Wanderrouten für Ihre Anfrage finden."

        # Kontext aus Top-Ergebnissen erstellen
        context = ""
        for i, result in enumerate(results[:3], 1):
            route = result.route
            context += f"""
Route {i}: {route['title']}
- Dauer: {route.get('duration', 'Nicht angegeben')}
- Distanz: {route.get('distance', 'Nicht angegeben')}  
- Höhenmeter: {route.get('elevation_gain', 'Nicht angegeben')}
- Schwierigkeit: {route.get('sac_scale', 'Nicht angegeben')}
- Restaurants: {', '.join(route.get('restaurants', [])[:2]) if route.get('restaurants') else 'Keine'}
- Beschreibung: {route.get('description', '')[:200]}...
- Empfehlungsgrund: {result.explanation}
"""

        # Groq Prompt
        system_prompt = """Du bist ein freundlicher und sachkundiger Wanderführer für die Region Appenzell. 
Deine Aufgabe ist es, basierend auf den gefundenen Wanderrouten eine hilfreiche, natürliche und persönliche Empfehlung zu geben.

Stil-Richtlinien:
- Verwende einen warmen, einladenden Ton
- Gib praktische Tipps und Hinweise
- Erkläre warum die Routen zur Anfrage passen
- Erwähne besondere Highlights
- Verwende "Sie" als Anrede
- Halte die Antwort strukturiert aber natürlich"""

        user_prompt = f"""
Benutzeranfrage: "{query}"

Gefundene Wanderrouten:
{context}

Bitte erstellen Sie eine natürliche, hilfreiche Antwort die:
1. Die passendsten Routen empfiehlt
2. Erklärt warum sie zur Anfrage passen  
3. Praktische Hinweise gibt (Dauer, Schwierigkeit, Einkehr)
4. Besondere Highlights erwähnt
5. Mit einer freundlichen Empfehlung abschließt
"""

        try:
            # Groq API Aufruf
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model="llama3-8b-8192",  # Oder "mixtral-8x7b-32768"
                temperature=0.7,
                max_tokens=800,
            )

            return chat_completion.choices[0].message.content

        except Exception as e:
            print(f"Groq Fehler: {e}")
            # Fallback auf Template-Response
            return super().generate_response(query, results)

    def search_with_groq(self, query: str, k: int = 3) -> str:
        """Hauptsuchfunktion mit Groq-Enhancement"""

        print(f"🔍 Verarbeite Anfrage mit Groq: {query}")

        # Normale RAG-Suche
        results = self.retrieve(query, k=k)

        # Groq-Enhanced Response
        response = self.generate_groq_response(query, results)

        return response


def demo_groq_enhancement():
    """Demonstriert Groq-Enhanced RAG"""

    print("🏔️ Groq-Enhanced Appenzeller Wanderungen RAG")
    print("=" * 60)

    # Benötigt GROQ_API_KEY in Environment
    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY nicht gesetzt!")
        print("   export GROQ_API_KEY='your-api-key-here'")
        return

    try:
        # RAG mit Groq initialisieren
        groq_rag = GroqEnhancedRAG()
        print("✅ Groq-Enhanced RAG System initialisiert")

        # Demo-Anfragen
        demo_queries = [
            "Ich möchte eine einfache Wanderung mit Restaurant",
            "Suche eine anspruchsvolle Tour mit schöner Aussicht",
            "Welche Wanderung ist gut für Anfänger?",
        ]

        for query in demo_queries:
            print(f"\n📝 Anfrage: {query}")
            print("-" * 40)

            response = groq_rag.search_with_groq(query, k=2)
            print(response)

            print("\n" + "=" * 60)

    except Exception as e:
        print(f"❌ Fehler: {e}")


if __name__ == "__main__":
    demo_groq_enhancement()
