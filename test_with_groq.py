#!/usr/bin/env python3
"""
Test mit Groq API Key
====================

Testet das komplette System inkl. PDF-Integration und Groq AI
"""

from advanced_groq_system import AdvancedGroqRAG


def test_complete_system():
    """Testet das komplette System mit Groq"""

    print("🧪 Test: Komplettes System mit Groq AI")
    print("=" * 60)

    try:
        # System mit API Key initialisieren
        api_key = "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"
        rag_system = AdvancedGroqRAG(groq_api_key=api_key)

        print(f"\n📊 System-Status:")
        print(f"• Routen geladen: {len(rag_system.routes)}")
        print(f"• Zusätzliche Dokumente: {len(rag_system.additional_context)}")
        print(
            f"• Groq Client: {'✅ Aktiv' if rag_system.groq_client else '❌ Inaktiv'}"
        )

        # PDF-Dokumente anzeigen
        pdf_docs = [
            key
            for key in rag_system.additional_context.keys()
            if key.startswith("pdf_")
        ]
        print(f"\n📄 PDF-Dokumente gefunden: {len(pdf_docs)}")

        for pdf_key in pdf_docs:
            pdf_data = rag_system.additional_context[pdf_key]
            pdf_name = pdf_key.replace("pdf_", "")
            content_length = len(pdf_data["content"])
            print(f"   📖 {pdf_name}: {content_length} Zeichen")

        # Test-Anfragen mit intelligenten Antworten
        test_queries = [
            "Einfache Wanderung mit Restaurant für die Familie",
            "Anspruchsvolle Bergtour mit spektakulärer Aussicht",
            "2-stündige Wanderung für Anfänger",
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: {query}")
            print("-" * 50)

            # RAG Retrieval
            results = rag_system.retrieve(query, k=3)
            print(f"• Gefundene Routen: {len(results)}")

            if results:
                print(f"• Top-Route: {results[0].route['title']}")
                print(f"• Score: {results[0].final_score:.2f}")

                # Intelligente Antwort generieren
                response = rag_system.generate_intelligent_response(query, results)
                print(f"\n🤖 AI-Antwort:")
                print(response[:300] + "..." if len(response) > 300 else response)
                print()

        print("\n✅ Alle Tests erfolgreich abgeschlossen!")

    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_complete_system()
