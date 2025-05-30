#!/usr/bin/env python3
"""
Test Script für PDF-Integration
===============================

Testet die PDF-Verarbeitung ohne Groq API Key
"""

from advanced_groq_system import AdvancedGroqRAG
import os


def test_pdf_integration():
    """Testet die PDF-Integration"""

    print("🧪 Test: PDF-Integration")
    print("=" * 50)

    try:
        # System ohne API Key initialisieren
        rag_system = AdvancedGroqRAG()

        print(f"\n📊 System-Status:")
        print(f"• Routen geladen: {len(rag_system.routes)}")
        print(f"• Zusätzliche Dokumente: {len(rag_system.additional_context)}")

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
            print(f"      Verarbeitet: {pdf_data['processed_at']}")
            print(f"      Inhalt-Preview: {pdf_data['content'][:100]}...")
            print()

        # Test-Anfrage ohne Groq
        print("🔍 Test-Suche:")
        results = rag_system.retrieve("einfache Wanderung mit Restaurant", k=3)
        print(f"• Gefundene Routen: {len(results)}")

        if results:
            print(f"• Top-Route: {results[0].route['title']}")
            print(f"• Score: {results[0].final_score:.2f}")

        # Fallback-Response testen
        fallback_response = rag_system.generate_fallback_response("test query", results)
        print(f"\n📝 Fallback-Response (ersten 200 Zeichen):")
        print(fallback_response[:200] + "...")

        print("\n✅ PDF-Integration Test erfolgreich!")

    except Exception as e:
        print(f"❌ Test-Fehler: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_pdf_integration()
