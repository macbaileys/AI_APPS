#!/usr/bin/env python3
"""
Advanced Groq Integration für Appenzeller Wanderungen
====================================================

Erweiterte Groq-Integration mit:
- Multi-Document Context (inkl. PDF-Verarbeitung)
- Intelligente Empfehlungslogik
- Erweiterte Kontextanalyse
- Personalisierte Beratung
"""

import os
import json
from groq import Groq
from rag_hiking_system import AppenzellHikingRAG
from typing import List, Dict, Any
import glob
import pdfplumber
from datetime import datetime


class AdvancedGroqRAG(AppenzellHikingRAG):
    """Erweiterte Groq-Integration mit Multi-Document Support inkl. PDF-Verarbeitung"""

    def __init__(self, groq_api_key: str = None):
        super().__init__()

        # Groq Client optional initialisieren
        self.groq_client = None
        api_key = (
            groq_api_key
            or os.getenv("GROQ_API_KEY")
            or "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"
        )

        if api_key:
            try:
                self.groq_client = Groq(api_key=api_key)
                print("🤖 Groq Client erfolgreich initialisiert")
            except Exception as e:
                print(f"⚠️ Groq Client Fehler: {e}")
                self.groq_client = None
        else:
            print("ℹ️ Groq API Key nicht gesetzt - Fallback-Modus aktiv")

        # Zusätzliche Kontextinformationen laden (inkl. PDFs)
        self.additional_context = self.load_additional_documents()

        print("🤖 Advanced Groq RAG System initialisiert")
        if self.additional_context:
            print(f"📄 {len(self.additional_context)} zusätzliche Dokumente geladen")

    def set_groq_api_key(self, api_key: str):
        """Setzt den Groq API Key nachträglich"""
        try:
            self.groq_client = Groq(api_key=api_key)
            print("✅ Groq API Key erfolgreich gesetzt!")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Setzen des API Keys: {e}")
            self.groq_client = None
            return False

    def extract_pdf_content(self, pdf_path: str, max_pages: int = 5) -> str:
        """Extrahiert Text aus PDF-Datei (begrenzt auf erste Seiten für Kontext)"""

        try:
            content = ""
            with pdfplumber.open(pdf_path) as pdf:
                # Begrenzte Anzahl Seiten für Performance
                pages_to_read = min(len(pdf.pages), max_pages)

                for i in range(pages_to_read):
                    page = pdf.pages[i]
                    page_text = page.extract_text()
                    if page_text:
                        content += page_text + "\n"

                # Falls PDF viele Seiten hat, Hinweis hinzufügen
                if len(pdf.pages) > max_pages:
                    content += f"\n[... PDF hat {len(pdf.pages)} Seiten, nur erste {max_pages} gelesen für Kontext ...]"

            return content[:3000]  # Begrenzte Textlänge für Kontext

        except Exception as e:
            print(f"⚠️ Fehler beim Lesen von {pdf_path}: {e}")
            return f"PDF verfügbar aber nicht lesbar: {os.path.basename(pdf_path)}"

    def load_additional_documents(self) -> Dict[str, Any]:
        """Lädt zusätzliche Dokumente für erweiterten Kontext (inkl. PDFs)"""

        context = {}

        try:
            # README.md für Projektkontext
            if os.path.exists("README.md"):
                with open("README.md", "r", encoding="utf-8") as f:
                    context["project_info"] = f.read()

            # RAG Dokumentation für technische Details
            if os.path.exists("RAG_DOCUMENTATION.md"):
                with open("RAG_DOCUMENTATION.md", "r", encoding="utf-8") as f:
                    context["technical_docs"] = f.read()

            # Evaluation Results für Performance-Daten
            if os.path.exists("rag_evaluation_results.json"):
                with open("rag_evaluation_results.json", "r", encoding="utf-8") as f:
                    context["evaluation_data"] = json.load(f)

            # PDFs aus dem PDFs Ordner verarbeiten
            pdf_folder = "PDFs"
            if os.path.exists(pdf_folder):
                pdf_files = glob.glob(os.path.join(pdf_folder, "*.pdf"))
                print(f"📄 Gefundene PDFs: {len(pdf_files)}")

                for pdf_path in pdf_files:
                    pdf_name = os.path.basename(pdf_path)
                    print(f"   📖 Verarbeite: {pdf_name}")

                    # PDF-Inhalt extrahieren
                    pdf_content = self.extract_pdf_content(pdf_path)
                    context[f"pdf_{pdf_name}"] = {
                        "content": pdf_content,
                        "file_path": pdf_path,
                        "processed_at": datetime.now().isoformat(),
                    }

            # Weitere JSON/Markdown Dateien im Verzeichnis
            for file_path in glob.glob("*.md") + glob.glob("*.json"):
                if file_path not in [
                    "README.md",
                    "RAG_DOCUMENTATION.md",
                    "rag_evaluation_results.json",
                ]:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            if file_path.endswith(".json"):
                                context[f"data_{file_path}"] = json.load(f)
                            else:
                                context[f"doc_{file_path}"] = f.read()
                    except Exception as e:
                        print(f"⚠️ Konnte {file_path} nicht laden: {e}")

        except Exception as e:
            print(f"⚠️ Fehler beim Laden zusätzlicher Dokumente: {e}")

        return context

    def create_enhanced_context(self, query: str, results: List) -> str:
        """Erstellt erweiterten Kontext für Groq (inkl. PDF-Inhalte)"""

        # Basis-Routen Kontext
        routes_context = ""
        for i, result in enumerate(results[:3], 1):
            route = result.route
            routes_context += f"""
🏔️ Route {i}: {route['title']}
• Dauer: {route.get('duration', 'Nicht angegeben')}
• Distanz: {route.get('distance', 'Nicht angegeben')}
• Höhenmeter: {route.get('elevation_gain', 'Nicht angegeben')}
• Schwierigkeit: {route.get('sac_scale', 'Nicht angegeben')}
• Restaurants: {', '.join(route.get('restaurants', [])[:2]) if route.get('restaurants') else 'Keine Angabe'}
• Highlights: {', '.join(route.get('highlights', [])[:3]) if route.get('highlights') else 'Siehe Beschreibung'}
• Beschreibung: {route.get('description', '')[:300]}...
• Warum empfohlen: {result.explanation}
• RAG-Score: {result.final_score:.2f}
"""

        # System-Performance Context
        performance_context = ""
        if "evaluation_data" in self.additional_context:
            eval_data = self.additional_context["evaluation_data"]
            if "system_stats" in eval_data:
                stats = eval_data["system_stats"]
                performance_context = f"""
📊 System-Performance:
• Precision@3: {stats.get('avg_precision_at_3', 0)*100:.0f}%
• Durchschnittliche Antwortzeit: {stats.get('avg_response_time', 0):.1f}s
• Präferenz-Match Rate: {stats.get('avg_preference_match', 0)*100:.0f}%
"""

        # PDF-Kontext hinzufügen
        pdf_context = ""
        pdf_docs = [
            key for key in self.additional_context.keys() if key.startswith("pdf_")
        ]
        if pdf_docs:
            pdf_context += "\n📚 Verfügbare PDF-Dokumente:\n"
            for pdf_key in pdf_docs[:3]:  # Nur erste 3 PDFs für Kontext
                pdf_data = self.additional_context[pdf_key]
                pdf_name = pdf_key.replace("pdf_", "")
                pdf_context += f"• {pdf_name}: {pdf_data['content'][:200]}...\n"

        # Regionale Besonderheiten
        regional_context = """
🌍 Appenzeller Wanderkontext:
• SAC-Skala: T1 (einfach) bis T6 (sehr schwierig)
• Typische Dauer: 1-6 Stunden
• Höhenlagen: 400m-2500m (Säntis)
• Beste Zeit: Mai-Oktober
• Besondere Highlights: Seealpsee, Äscher-Wildkirchli, Kronberg
"""

        return f"""
{routes_context}

{performance_context}

{pdf_context}

{regional_context}
"""

    def generate_intelligent_response(self, query: str, results: List) -> str:
        """Generiert intelligente Antwort mit erweitertem Kontext"""

        if not results:
            return self.generate_no_results_response(query)

        # Prüfen ob Groq Client verfügbar ist
        if not self.groq_client:
            print("ℹ️ Groq Client nicht verfügbar - verwende Fallback")
            return self.generate_fallback_response(query, results)

        # Erweiterten Kontext erstellen
        enhanced_context = self.create_enhanced_context(query, results)

        # Intelligenter System-Prompt
        system_prompt = """Du bist ein erfahrener Wanderführer und KI-Experte für die Region Appenzell. 

Deine Expertise umfasst:
• 50+ Wanderrouten in der Region
• SAC-Wanderskala und Sicherheitsaspekte  
• Lokale Gastronomie und Einkehrmöglichkeiten
• Wetter- und Saisonempfehlungen
• Personalisierte Routenplanung

Antwortstil:
• Freundlich und professionell
• Praktisch und umsetzbar
• Mit konkreten Handlungsempfehlungen
• Sicherheitshinweise bei schwierigen Routen
• "Sie" als höfliche Anrede

Struktur deine Antwort:
1. Kurze Einleitung zur Anfrage
2. Top-Empfehlung mit Begründung
3. Alternative(n) falls passend
4. Praktische Tipps (Ausrüstung, beste Zeit, etc.)
5. Freundlicher Abschluss"""

        user_prompt = f"""
BENUTZERANFRAGE: "{query}"

GEFUNDENE WANDERROUTEN & SYSTEM-KONTEXT:
{enhanced_context}

Bitte erstelle eine maßgeschneiderte, hilfreiche Wanderempfehlung die:
• Die beste Route für diese Anfrage hervorhebt
• Erklärt warum sie optimal passt
• Praktische Umsetzungstipps gibt
• Bei Bedarf Alternativen vorschlägt
• Sicherheits-/Ausrüstungshinweise enthält
• Mit einer motivierenden Schlussempfehlung endet

Halte die Antwort informativ aber nicht zu lang (max. 350 Wörter).
"""

        try:
            # Groq API Aufruf mit erweiterten Parametern
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                model="llama3-8b-8192",
                temperature=0.7,
                max_tokens=500,
                top_p=0.9,
                stream=False,
            )

            response = chat_completion.choices[0].message.content

            # Response-Qualität bewerten und ggf. verbessern
            return self.enhance_response_quality(response, query, results)

        except Exception as e:
            print(f"❌ Groq API Fehler: {e}")
            return self.generate_fallback_response(query, results)

    def generate_no_results_response(self, query: str) -> str:
        """Generiert hilfreiche Antwort auch ohne Ergebnisse"""

        if not self.groq_client:
            return f"""
Entschuldigung, ich konnte keine passenden Wanderrouten für "{query}" finden.

Versuchen Sie es mit:
• Spezifischeren Begriffen (z.B. "T2 Wanderung" statt "mittelschwer")
• Anderen Suchbegriffen (z.B. "Gasthaus" statt "Restaurant")
• Klareren Präferenzen (z.B. "2 Stunden" statt "kurz")

Die Appenzeller Region bietet wunderbare Wandermöglichkeiten für jeden Geschmack!
"""

        try:
            fallback_prompt = f"""
Der Benutzer fragt: "{query}"

Es wurden keine passenden Wanderrouten gefunden. Erstelle eine hilfreiche Antwort die:
• Erklärt warum keine Routen gefunden wurden
• Alternative Suchbegriffe vorschlägt  
• Allgemeine Appenzeller Wandertipps gibt
• Zur Präzisierung der Anfrage ermutigt

Ton: Freundlich und hilfreich, max. 200 Wörter.
"""

            completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": fallback_prompt}],
                model="llama3-8b-8192",
                temperature=0.8,
                max_tokens=300,
            )

            return completion.choices[0].message.content

        except Exception as e:
            return f"""
Entschuldigung, ich konnte keine passenden Wanderrouten für "{query}" finden.

Versuchen Sie es mit:
• Spezifischeren Begriffen (z.B. "T2 Wanderung" statt "mittelschwer")
• Anderen Suchbegriffen (z.B. "Gasthaus" statt "Restaurant")
• Klareren Präferenzen (z.B. "2 Stunden" statt "kurz")

Die Appenzeller Region bietet wunderbare Wandermöglichkeiten für jeden Geschmack!
"""

    def enhance_response_quality(self, response: str, query: str, results: List) -> str:
        """Verbessert Response-Qualität durch Post-Processing"""

        # Füge Metadaten hinzu falls nicht vorhanden
        if not any(
            word in response.lower() for word in ["dauer", "distanz", "höhenmeter"]
        ):
            top_route = results[0].route if results else None
            if top_route:
                response += f"\n\n📍 Kurz-Info zur Top-Empfehlung:\n"
                response += f"• {top_route.get('duration', 'Dauer unbekannt')}"
                response += f" • {top_route.get('distance', 'Distanz unbekannt')}"
                response += (
                    f" • {top_route.get('elevation_gain', 'Höhenmeter unbekannt')}"
                )

        return response

    def generate_fallback_response(self, query: str, results: List) -> str:
        """Fallback ohne Groq API"""

        if not results:
            return "Leider konnte ich keine passenden Routen finden. Versuchen Sie andere Suchbegriffe."

        route = results[0].route
        return f"""
Basierend auf Ihrer Anfrage "{query}" empfehle ich:

🏔️ {route['title']}
• Dauer: {route.get('duration', 'Nicht angegeben')}
• Distanz: {route.get('distance', 'Nicht angegeben')}
• Schwierigkeit: {route.get('sac_scale', 'Nicht angegeben')}

{route.get('description', '')[:200]}...

Diese Route passt gut zu Ihren Anforderungen. Weitere Details finden Sie in der vollständigen Routenbeschreibung.
"""

    def interactive_search(self):
        """Interaktive Suche mit Groq-Enhancement"""

        print("\n🏔️ Willkommen beim Advanced Groq Wanderberater!")
        print("=" * 60)

        if not os.getenv("GROQ_API_KEY"):
            print("❌ GROQ_API_KEY nicht gesetzt!")
            print("   Setzen Sie: export GROQ_API_KEY='your-api-key'")
            return

        while True:
            print("\n🔍 Stellen Sie Ihre Wanderfrage (oder 'exit' zum Beenden):")
            query = input("➤ ").strip()

            if query.lower() in ["exit", "quit", "beenden"]:
                print("🏔️ Viel Spaß beim Wandern in Appenzell! 🥾")
                break

            if not query:
                continue

            print(f"\n🤖 Analysiere: '{query}'...")

            try:
                # RAG Retrieval
                results = self.retrieve(query, k=3)

                # Groq-Enhanced Response
                response = self.generate_intelligent_response(query, results)

                print("\n" + "=" * 60)
                print("🏔️ WANDEREMPFEHLUNG:")
                print("=" * 60)
                print(response)
                print("=" * 60)

            except Exception as e:
                print(f"❌ Fehler: {e}")
                print("Versuchen Sie eine andere Anfrage.")


def demo_advanced_groq():
    """Demonstriert das erweiterte Groq-System"""

    print("🚀 Advanced Groq RAG System Demo")
    print("=" * 50)

    try:
        # System initialisieren (API Key ist jetzt eingebaut)
        groq_rag = AdvancedGroqRAG()

        # Demo-Queries
        demo_queries = [
            "Ich möchte eine einfache Wanderung mit Restaurant für die Familie",
            "Suche eine anspruchsvolle Bergtour mit spektakulärer Aussicht",
            "Welche Wanderung ist gut für Anfänger und dauert etwa 2 Stunden?",
        ]

        for query in demo_queries:
            print(f"\n📝 Demo-Anfrage: {query}")
            print("-" * 50)

            results = groq_rag.retrieve(query, k=2)
            response = groq_rag.generate_intelligent_response(query, results)

            print(response)
            print("\n" + "=" * 50)

        print("\n🎯 Demo abgeschlossen! Das System ist einsatzbereit.")

    except Exception as e:
        print(f"❌ Demo-Fehler: {e}")


if __name__ == "__main__":
    # Für Demo
    demo_advanced_groq()

    # Für interaktive Nutzung (auskommentiert)
    # groq_system = AdvancedGroqRAG()
    # groq_system.interactive_search()
