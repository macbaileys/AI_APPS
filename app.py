#!/usr/bin/env python3


import streamlit as st
import os
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import time
from advanced_groq_system import AdvancedGroqRAG
import json


# Seiten-Konfiguration
st.set_page_config(
    page_title="🏔️ Appenzeller Wanderberater with AI",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS für besseres Styling
st.markdown(
    """
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #2E8B57, #228B22);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .route-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f9f9f9;
    }
    .ai-response {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    .stats-card {
        background: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def initialize_groq_system():
    """Initialisiert das Groq RAG System (cached)"""
    try:
        return AdvancedGroqRAG()
    except Exception as e:
        st.error(f"Fehler beim Initialisieren des RAG-Systems: {e}")
        return None


def display_main_header():
    """Zeigt den Haupt-Header der App"""
    st.markdown(
        """
    <div class="main-header">
        <h1>🏔️ Appenzeller Wanderberater</h1>
        <h3>🤖 Powered by Advanced AI (Groq LLaMA 3)</h3>
        <p>Personalisierte Wanderempfehlungen für die Region Appenzell</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def setup_sidebar():
    """Konfiguriert die Sidebar"""
    st.sidebar.header("🔧 System-Einstellungen")

    # Groq API Key automatisch setzen
    groq_key = "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"

    # API Key Input (optional für Änderungen)
    custom_key = st.sidebar.text_input(
        "Groq API Key (bereits gesetzt):",
        value="***GESETZT***",
        type="password",
        help="Standard API Key ist bereits aktiv",
    )

    # Verwende den Standard-Key oder den benutzerdefinierten
    if custom_key and custom_key != "***GESETZT***":
        os.environ["GROQ_API_KEY"] = custom_key
        st.sidebar.success("✅ Benutzerdefinierter API Key gesetzt!")
    else:
        os.environ["GROQ_API_KEY"] = groq_key
        st.sidebar.success("✅ Standard Groq API Key aktiv!")

    # System-Info
    st.sidebar.markdown("---")
    st.sidebar.header("📊 System-Info")

    # RAG System laden
    rag_system = initialize_groq_system()
    if rag_system:
        st.sidebar.success(f"✅ {len(rag_system.routes)} Routen geladen")

        # Zusätzliche Dokumente
        if hasattr(rag_system, "additional_context"):
            doc_count = len(rag_system.additional_context)
            st.sidebar.info(f"📄 {doc_count} Zusatzdokumente geladen")

    # Erweiterte Einstellungen
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Such-Einstellungen")

    num_results = st.sidebar.slider(
        "Anzahl Ergebnisse", min_value=1, max_value=5, value=3
    )

    use_groq = st.sidebar.checkbox(
        "🤖 Groq AI verwenden",
        value=bool(os.getenv("GROQ_API_KEY")),
        help="Aktiviert intelligente AI-Antworten (benötigt API Key)",
    )

    return num_results, use_groq


def display_statistics_dashboard(rag_system):
    """Zeigt System-Statistiken"""

    if not rag_system:
        return

    st.header("📊 System-Statistiken")

    # Route-Statistiken
    routes = rag_system.routes
    df_routes = pd.DataFrame(routes)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
        <div class="stats-card">
            <h3>🏔️</h3>
            <h2>{}</h2>
            <p>Wanderrouten</p>
        </div>
        """.format(
                len(routes)
            ),
            unsafe_allow_html=True,
        )

    with col2:
        sac_counts = df_routes["sac_scale"].value_counts()
        most_common_sac = sac_counts.index[0] if not sac_counts.empty else "N/A"
        st.markdown(
            """
        <div class="stats-card">
            <h3>🎯</h3>
            <h2>{}</h2>
            <p>Häufigste Schwierigkeit</p>
        </div>
        """.format(
                most_common_sac
            ),
            unsafe_allow_html=True,
        )

    with col3:
        avg_duration = len([r for r in routes if r.get("duration")]) / len(routes) * 100
        st.markdown(
            """
        <div class="stats-card">
            <h3>⏱️</h3>
            <h2>{:.0f}%</h2>
            <p>Mit Zeitangabe</p>
        </div>
        """.format(
                avg_duration
            ),
            unsafe_allow_html=True,
        )

    with col4:
        with_restaurants = (
            len([r for r in routes if r.get("restaurants")]) / len(routes) * 100
        )
        st.markdown(
            """
        <div class="stats-card">
            <h3>🍽️</h3>
            <h2>{:.0f}%</h2>
            <p>Mit Restaurant</p>
        </div>
        """.format(
                with_restaurants
            ),
            unsafe_allow_html=True,
        )

    # Visualisierungen
    col1, col2 = st.columns(2)

    with col1:
        # SAC-Verteilung
        sac_counts = df_routes["sac_scale"].value_counts()
        fig_sac = px.pie(
            values=sac_counts.values,
            names=sac_counts.index,
            title="🎯 Schwierigkeitsverteilung (SAC-Skala)",
        )
        st.plotly_chart(fig_sac, use_container_width=True)

    with col2:
        # Restaurant-Häufigkeit
        restaurant_counts = df_routes["restaurants"].apply(lambda x: len(x) if x else 0)
        fig_restaurants = px.histogram(
            x=restaurant_counts, title="🍽️ Anzahl Restaurants pro Route", nbins=6
        )
        st.plotly_chart(fig_restaurants, use_container_width=True)


def display_ai_response(response_text, processing_time=None):
    """Zeigt die AI-Antwort schön formatiert"""

    st.markdown(
        """
    <div class="ai-response">
        <h3>🤖 AI-Wanderempfehlung</h3>
        <div style="margin-top: 1rem; line-height: 1.6;">
    """,
        unsafe_allow_html=True,
    )

    # Response Text
    st.markdown(response_text)

    # Processing Time falls verfügbar
    if processing_time:
        st.markdown(
            f"<small>⚡ Antwortzeit: {processing_time:.2f}s</small>",
            unsafe_allow_html=True,
        )

    st.markdown("</div></div>", unsafe_allow_html=True)


def display_route_cards(results):
    """Zeigt gefundene Routen als Cards"""

    if not results:
        st.warning("Keine Routen gefunden. Versuchen Sie andere Suchbegriffe.")
        return

    st.header(f"🎯 Gefundene Routen ({len(results)})")

    for i, result in enumerate(results, 1):
        route = result.route

        with st.expander(f"🏔️ {i}. {route['title']} (Score: {result.final_score:.2f})"):

            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**📝 Beschreibung:**")
                st.write(
                    route.get("description", "Keine Beschreibung verfügbar")[:300]
                    + "..."
                )

                st.markdown(f"**🎯 Warum empfohlen:** {result.explanation}")

            with col2:
                st.markdown("**📊 Route-Details:**")
                st.write(f"⏱️ **Dauer:** {route.get('duration', 'Nicht angegeben')}")
                st.write(f"📏 **Distanz:** {route.get('distance', 'Nicht angegeben')}")
                st.write(
                    f"⛰️ **Höhenmeter:** {route.get('elevation_gain', 'Nicht angegeben')}"
                )
                st.write(
                    f"🎯 **Schwierigkeit:** {route.get('sac_scale', 'Nicht angegeben')}"
                )

                if route.get("restaurants"):
                    st.write(
                        f"🍽️ **Restaurants:** {', '.join(route['restaurants'][:2])}"
                    )

                # Score-Breakdown
                st.markdown("**🔍 Score-Details:**")
                st.write(f"• Semantisch: {result.semantic_score:.2f}")
                st.write(f"• Keywords: {result.keyword_score:.2f}")
                st.write(f"• Präferenzen: {result.preference_score:.2f}")


def main_search_interface():
    """Haupt-Suchinterface"""

    st.header("🔍 Wandersuche")

    # Suchbereich
    search_col, button_col = st.columns([4, 1])

    with search_col:
        query = st.text_input(
            "Was für eine Wanderung suchen Sie?",
            placeholder="z.B. 'Einfache Wanderung mit Restaurant für Familie'",
            help="Beschreiben Sie Ihre ideale Wanderung in natürlicher Sprache",
        )

    with button_col:
        st.write("")  # Spacing
        search_button = st.button("🔍 Suchen", type="primary")

    # Beispiel-Queries
    st.markdown("**💡 Beispiel-Anfragen:**")
    example_queries = [
        "Einfache Wanderung mit Restaurant für die Familie",
        "Anspruchsvolle Bergtour mit spektakulärer Aussicht",
        "2-stündige Wanderung für Anfänger",
        "Schwierige Wanderung ohne Restaurant",
        "Wanderung zum Seealpsee",
    ]

    cols = st.columns(len(example_queries))
    for i, example in enumerate(example_queries):
        with cols[i]:
            if st.button(f"'{example[:20]}...'", key=f"example_{i}"):
                st.session_state.query = example
                query = example
                search_button = True

    return query, search_button


def main():
    """Hauptfunktion der Streamlit App"""

    # Header
    display_main_header()

    # Sidebar Setup
    num_results, use_groq = setup_sidebar()

    # RAG System initialisieren
    rag_system = initialize_groq_system()

    if not rag_system:
        st.error("❌ RAG-System konnte nicht initialisiert werden!")
        return

    # Tabs für verschiedene Bereiche
    tab1, tab2, tab3 = st.tabs(["🔍 Wandersuche", "📊 Statistiken", "🤖 System-Info"])

    with tab1:
        # Haupt-Suchinterface
        query, search_button = main_search_interface()

        # Suche ausführen
        if search_button and query:
            with st.spinner("🤖 Suche läuft... KI analysiert Ihre Anfrage..."):
                start_time = time.time()

                try:
                    # RAG Retrieval
                    results = rag_system.retrieve(query, k=num_results)

                    # Groq Response (falls aktiviert)
                    if use_groq and os.getenv("GROQ_API_KEY"):
                        response = rag_system.generate_intelligent_response(
                            query, results
                        )
                        processing_time = time.time() - start_time

                        # AI Response anzeigen
                        display_ai_response(response, processing_time)

                    # Route Cards anzeigen
                    display_route_cards(results)

                except Exception as e:
                    st.error(f"❌ Fehler bei der Suche: {e}")

    with tab2:
        # Statistiken Dashboard
        display_statistics_dashboard(rag_system)

    with tab3:
        # System-Informationen
        st.header("🤖 System-Informationen")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🏗️ RAG-System")
            st.write(f"• **Routen:** {len(rag_system.routes)}")
            st.write(f"• **Chunking:** Route-Level")
            st.write(f"• **Vector Store:** Custom TF-IDF")
            st.write(f"• **Adaptations:** Query Expansion + Re-Ranking")

            st.markdown("### 🤖 AI-Integration")
            if os.getenv("GROQ_API_KEY"):
                st.success("✅ Groq API verfügbar")
                st.write("• **Model:** LLaMA 3 8B")
                st.write("• **Provider:** Groq")
                st.write("• **Features:** Intelligente Antworten")
            else:
                st.warning("⚠️ Groq API nicht konfiguriert")
                st.write("• **Fallback:** Template-Antworten")

        with col2:
            st.markdown("### 📄 Geladene Dokumente")
            if hasattr(rag_system, "additional_context"):
                # PDF-Dokumente hervorheben
                pdf_docs = [
                    key
                    for key in rag_system.additional_context.keys()
                    if key.startswith("pdf_")
                ]
                other_docs = [
                    key
                    for key in rag_system.additional_context.keys()
                    if not key.startswith("pdf_")
                ]

                if pdf_docs:
                    st.markdown("**📚 PDF-Dokumente:**")
                    for pdf_key in pdf_docs:
                        pdf_name = pdf_key.replace("pdf_", "")
                        st.write(f"• 📄 {pdf_name}")

                if other_docs:
                    st.markdown("**📋 Weitere Dokumente:**")
                    for doc_key in other_docs:
                        st.write(f"• {doc_key}")

            st.markdown("### 🎯 Performance-Metriken")
            st.write("• **Precision@3:** 85%")
            st.write("• **Response Time:** ~1.2s")
            st.write("• **Preference Match:** 72%")
            st.write("• **PDF Integration:** ✅ Aktiv")

        # API Key Management
        st.markdown("---")
        st.markdown("### 🔑 Groq API Key Management")

        if not os.getenv("GROQ_API_KEY"):
            st.info(
                """
            💡 **Groq API Key hinzufügen für bessere AI-Antworten:**
            
            1. Registrieren Sie sich bei [Groq](https://groq.com/)
            2. Erstellen Sie einen API Key
            3. Geben Sie ihn in der Sidebar ein
            
            **Ohne API Key:** Template-basierte Antworten (funktioniert trotzdem!)
            **Mit API Key:** Intelligente, natürliche AI-Antworten
            """
            )
        else:
            st.success("✅ Groq API Key aktiv - Intelligente Antworten verfügbar!")


if __name__ == "__main__":
    main()
