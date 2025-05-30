#!/usr/bin/env python3
"""
Demo App - Appenzeller Wanderberater
====================================

Einfache Demo ohne Streamlit für das erweiterte RAG-System
mit PDF-Integration und Groq AI.
"""

from advanced_groq_system import AdvancedGroqRAG
import time


def print_header():
    """Zeigt den Header der Demo"""
    print("\n" + "=" * 70)
    print("🏔️  APPENZELLER WANDERBERATER - DEMO MIT GROQ AI  🏔️")
    print("=" * 70)
    print("📄 Automatische PDF-Integration + 🤖 Intelligente AI-Antworten")
    print("=" * 70)


def show_system_stats(rag_system):
    """Zeigt System-Statistiken"""
    print("\n📊 SYSTEM-STATUS:")
    print("-" * 40)
    print(f"• Geladene Wanderrouten: {len(rag_system.routes)}")
    print(f"• Zusätzliche Dokumente: {len(rag_system.additional_context)}")
    print(f"• Groq AI Status: {'✅ Aktiv' if rag_system.groq_client else '❌ Inaktiv'}")

    # PDF-Details anzeigen
    pdf_docs = [
        key for key in rag_system.additional_context.keys() if key.startswith("pdf_")
    ]
    print(f"\n📄 VERARBEITETE PDFs ({len(pdf_docs)}):")
    print("-" * 40)

    for pdf_key in pdf_docs:
        pdf_data = rag_system.additional_context[pdf_key]
        pdf_name = pdf_key.replace("pdf_", "")
        content_length = len(pdf_data["content"])
        print(f"   📖 {pdf_name:<30} {content_length:>5} Zeichen")


def demo_queries(rag_system):
    """Führt Demo-Anfragen durch"""

    demo_questions = [
        "Einfache Wanderung mit Restaurant für die Familie",
        "Anspruchsvolle Bergtour mit spektakulärer Aussicht",
        "2-stündige Wanderung für Anfänger",
        "Wanderung ohne Restaurant aber mit schöner Aussicht",
    ]

    print(f"\n🔍 DEMO-ANFRAGEN ({len(demo_questions)}):")
    print("=" * 70)

    for i, query in enumerate(demo_questions, 1):
        print(f"\n📝 Anfrage {i}: {query}")
        print("-" * 50)

        # Zeit messen
        start_time = time.time()

        try:
            # RAG Retrieval
            results = rag_system.retrieve(query, k=3)
            retrieval_time = time.time() - start_time

            print(
                f"⚡ RAG-Retrieval: {retrieval_time:.2f}s | Gefunden: {len(results)} Routen"
            )

            if results:
                # Top-Route anzeigen
                top_route = results[0].route
                print(f"🏔️ Top-Empfehlung: {top_route['title']}")
                print(f"   • Score: {results[0].final_score:.2f}")
                print(f"   • Dauer: {top_route.get('duration', 'N/A')}")
                print(f"   • Schwierigkeit: {top_route.get('sac_scale', 'N/A')}")

                # AI-Antwort generieren
                if rag_system.groq_client:
                    ai_start = time.time()
                    response = rag_system.generate_intelligent_response(query, results)
                    ai_time = time.time() - ai_start

                    print(f"\n🤖 GROQ AI-ANTWORT ({ai_time:.2f}s):")
                    print("▼" * 50)
                    print(response)
                    print("▲" * 50)
                else:
                    fallback = rag_system.generate_fallback_response(query, results)
                    print(f"\n📝 FALLBACK-ANTWORT:")
                    print(fallback[:200] + "...")

                total_time = time.time() - start_time
                print(f"\n⏱️ Gesamt-Zeit: {total_time:.2f}s")

        except Exception as e:
            print(f"❌ Fehler: {e}")

        print("\n" + "=" * 70)


def interactive_mode(rag_system):
    """Interaktiver Modus"""
    print("\n🔄 INTERAKTIVER MODUS")
    print("=" * 50)
    print("Stellen Sie Ihre eigenen Wanderfragen!")
    print("(Eingabe von 'exit' beendet das Programm)")

    while True:
        print("\n" + "-" * 50)
        user_query = input("🔍 Ihre Wanderfrage: ").strip()

        if user_query.lower() in ["exit", "quit", "beenden", "exit()"]:
            print("👋 Viel Spaß beim Wandern in Appenzell!")
            break

        if not user_query:
            continue

        try:
            print(f"\n🤖 Analysiere: '{user_query}'...")

            start_time = time.time()
            results = rag_system.retrieve(user_query, k=3)

            if results:
                response = rag_system.generate_intelligent_response(user_query, results)
                total_time = time.time() - start_time

                print(f"\n🏔️ EMPFEHLUNG ({total_time:.2f}s):")
                print("=" * 50)
                print(response)
                print("=" * 50)
            else:
                print(
                    "❌ Keine passenden Routen gefunden. Versuchen Sie andere Begriffe."
                )

        except Exception as e:
            print(f"❌ Fehler: {e}")


def main():
    """Hauptfunktion der Demo"""

    print_header()

    try:
        # System mit API Key initialisieren
        api_key = "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"
        print("🚀 Initialisiere Advanced Groq RAG System...")

        rag_system = AdvancedGroqRAG(groq_api_key=api_key)

        # System-Statistiken
        show_system_stats(rag_system)

        # Demo-Anfragen
        demo_queries(rag_system)

        # Interaktiver Modus anbieten
        print("\n🎯 DEMO ABGESCHLOSSEN!")
        choice = (
            input("\nMöchten Sie den interaktiven Modus starten? (j/n): ")
            .strip()
            .lower()
        )

        if choice in ["j", "ja", "yes", "y"]:
            interactive_mode(rag_system)
        else:
            print("\n👋 Demo beendet. Vielen Dank!")

    except Exception as e:
        print(f"❌ System-Fehler: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
