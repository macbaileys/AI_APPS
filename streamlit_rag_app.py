#!/usr/bin/env python3
"""
Streamlit Web Interface für das Appenzeller Wanderungen RAG System
==================================================================

Eine interaktive Webanwendung für intelligente Wanderempfehlungen
mit schöner Benutzeroberfläche und detaillierten Visualisierungen.
"""

import streamlit as st
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from rag_hiking_system import AppenzellHikingRAG
import re
from typing import List, Dict
import time

# Page configuration
st.set_page_config(
    page_title="🏔️ Appenzeller Wanderungen RAG",
    page_icon="🥾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS für besseres Design
st.markdown(
    """
<style>
.main-header {
    font-size: 3rem;
    font-weight: bold;
    text-align: center;
    color: #2E7D32;
    margin-bottom: 0.5rem;
}

.sub-header {
    font-size: 1.2rem;
    text-align: center;
    color: #4CAF50;
    margin-bottom: 2rem;
}

.route-card {
    background: linear-gradient(135deg, #E8F5E8 0%, #F1F8E9 100%);
    padding: 1.5rem;
    border-radius: 10px;
    border: 1px solid #C8E6C9;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.metric-card {
    background: #FFFFFF;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #E0E0E0;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.search-tips {
    background: #FFF3E0;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #FF9800;
    margin: 1rem 0;
}

.stButton > button {
    background: linear-gradient(90deg, #4CAF50 0%, #45A049 100%);
    color: white;
    border: none;
    padding: 0.5rem 2rem;
    border-radius: 25px;
    font-weight: bold;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def load_rag_system():
    """Lädt das RAG-System (cached für Performance)"""
    try:
        return AppenzellHikingRAG()
    except Exception as e:
        st.error(f"❌ Fehler beim Laden des RAG-Systems: {e}")
        return None


def extract_duration_hours(duration_str: str) -> float:
    """Extrahiert Stunden aus Dauer-String"""
    if not duration_str:
        return 0

    hours_match = re.search(r"(\d+)\s*(?:Stunden?|h)", duration_str, re.IGNORECASE)
    minutes_match = re.search(r"(\d+)\s*(?:Minuten?|min)", duration_str, re.IGNORECASE)

    hours = float(hours_match.group(1)) if hours_match else 0
    minutes = float(minutes_match.group(1)) if minutes_match else 0

    return hours + (minutes / 60)


def extract_elevation(elevation_str: str) -> int:
    """Extrahiert Höhenmeter als Integer"""
    if not elevation_str:
        return 0

    match = re.search(r"(\d+)", elevation_str)
    return int(match.group(1)) if match else 0


def create_route_visualization(routes: List[Dict]):
    """Erstellt interaktive Visualisierungen der Routen"""

    # Vorbereitung der Daten
    data = []
    for route in routes:
        duration_hours = extract_duration_hours(route.get("duration", ""))
        elevation = extract_elevation(route.get("elevation_gain", ""))

        data.append(
            {
                "title": (
                    route["title"][:30] + "..."
                    if len(route["title"]) > 30
                    else route["title"]
                ),
                "full_title": route["title"],
                "duration_hours": duration_hours,
                "elevation_gain": elevation,
                "sac_scale": route.get("sac_scale", "Unknown"),
                "distance": route.get("distance", ""),
                "restaurants": len(route.get("restaurants", [])),
            }
        )

    df = pd.DataFrame(data)

    # Scatterplot: Dauer vs. Höhenmeter
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Dauer vs. Höhenmeter")

        fig1 = px.scatter(
            df,
            x="duration_hours",
            y="elevation_gain",
            color="sac_scale",
            size="restaurants",
            hover_data=["full_title", "distance"],
            title="Wanderrouten nach Dauer und Höhenmetern",
            labels={
                "duration_hours": "Dauer (Stunden)",
                "elevation_gain": "Höhenmeter (m)",
                "sac_scale": "SAC-Skala",
            },
        )
        fig1.update_layout(height=400)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("🎯 SAC-Skalen Verteilung")

        sac_counts = df["sac_scale"].value_counts()

        fig2 = px.pie(
            values=sac_counts.values,
            names=sac_counts.index,
            title="Verteilung der Schwierigkeitsgrade",
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)


def display_route_card(route: Dict, score: float = None, explanation: str = ""):
    """Zeigt eine Route als schöne Karte an"""

    with st.container():
        st.markdown('<div class="route-card">', unsafe_allow_html=True)

        # Header mit Titel und Score
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### 🥾 {route['title']}")
        with col2:
            if score is not None:
                st.metric("Match Score", f"{score:.2f}")

        # Haupt-Informationen
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"**⏱️ Dauer**  \n{route.get('duration', 'N/A')}")
        with col2:
            st.markdown(f"**📏 Distanz**  \n{route.get('distance', 'N/A')}")
        with col3:
            st.markdown(f"**⛰️ Höhenmeter**  \n{route.get('elevation_gain', 'N/A')}")
        with col4:
            st.markdown(f"**🎯 SAC-Skala**  \n{route.get('sac_scale', 'N/A')}")

        # Restaurants
        if route.get("restaurants"):
            st.markdown(f"**🍽️ Restaurants:** {', '.join(route['restaurants'][:3])}")

        # Highlights
        if route.get("highlights"):
            st.markdown(f"**✨ Highlights:** {', '.join(route['highlights'][:5])}")

        # Beschreibung
        if route.get("description"):
            with st.expander("📝 Vollständige Beschreibung"):
                st.write(route["description"])

        # Erklärung (wenn verfügbar)
        if explanation:
            st.info(f"💡 **Warum empfohlen:** {explanation}")

        st.markdown("</div>", unsafe_allow_html=True)


def main():
    """Hauptfunktion der Streamlit-App"""

    # Header
    st.markdown(
        '<div class="main-header">🏔️ Appenzeller Wanderungen</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-header">Intelligente RAG-basierte Wanderempfehlungen</div>',
        unsafe_allow_html=True,
    )

    # RAG-System laden
    rag_system = load_rag_system()

    if not rag_system:
        st.error(
            "❌ RAG-System konnte nicht geladen werden. Bitte prüfen Sie die Konfiguration."
        )
        return

    # Sidebar für Einstellungen
    with st.sidebar:
        st.header("🔧 Einstellungen")

        # Anzahl Ergebnisse
        num_results = st.slider(
            "Anzahl Ergebnisse",
            min_value=1,
            max_value=10,
            value=3,
            help="Wie viele Wanderrouten sollen angezeigt werden?",
        )

        # Erweiterte Optionen
        st.subheader("🎛️ Erweiterte Optionen")

        show_scores = st.checkbox(
            "Scoring-Details anzeigen",
            value=False,
            help="Zeigt detaillierte Scores für jede Empfehlung",
        )

        show_visualizations = st.checkbox(
            "Datenvisualisierungen anzeigen",
            value=True,
            help="Zeigt interaktive Charts und Grafiken",
        )

        # Statistiken
        st.subheader("📊 Datenbank-Statistiken")
        total_routes = len(rag_system.routes)

        st.metric("Total Routen", total_routes)

        # SAC-Verteilung
        sac_counts = {}
        for route in rag_system.routes:
            sac = route.get("sac_scale", "Unknown")
            sac_counts[sac] = sac_counts.get(sac, 0) + 1

        for sac, count in sorted(sac_counts.items()):
            st.text(f"{sac}: {count} Routen")

    # Hauptbereich
    col1, col2 = st.columns([2, 1])

    with col2:
        st.markdown('<div class="search-tips">', unsafe_allow_html=True)
        st.markdown("**💡 Such-Tipps:**")
        st.markdown(
            """
        - "Einfache Wanderung mit Restaurant"
        - "Anspruchsvolle Bergtour mit Aussicht"  
        - "Kurze Familienwanderung"
        - "Lange Tour zum Säntis"
        - "Gemütlicher Weg mit Einkehr"
        """
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col1:
        # Suchbereich
        st.subheader("🔍 Wanderroute suchen")

        # Suchfeld
        query = st.text_input(
            "Beschreiben Sie Ihre gewünschte Wanderung:",
            placeholder="z.B. Ich möchte eine einfache Wanderung mit schöner Aussicht...",
            help="Verwenden Sie natürliche Sprache. Das System versteht Präferenzen für Schwierigkeit, Dauer und Ausstattung.",
        )

        # Such-Button
        search_clicked = st.button("🔍 Suchen", use_container_width=True)

    # Suche ausführen
    if search_clicked and query:
        with st.spinner("🔍 Suche nach passenden Wanderrouten..."):
            start_time = time.time()

            # RAG-Suche durchführen
            results = rag_system.retrieve(query, k=num_results)

            search_time = time.time() - start_time

        # Ergebnisse anzeigen
        if results:
            st.success(
                f"✅ {len(results)} passende Routen in {search_time:.2f}s gefunden!"
            )

            # Visualisierungen (wenn aktiviert)
            if show_visualizations and len(results) > 1:
                st.subheader("📊 Visualisierung der Suchergebnisse")
                route_data = [result.route for result in results]
                create_route_visualization(route_data)

            # Ergebnisse anzeigen
            st.subheader("🎯 Empfohlene Wanderrouten")

            for i, result in enumerate(results, 1):
                st.markdown(f"### {i}. Empfehlung")

                if show_scores:
                    # Detailliertes Scoring anzeigen
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Semantisch", f"{result.semantic_score:.3f}")
                    with col2:
                        st.metric("Keywords", f"{result.keyword_score:.3f}")
                    with col3:
                        st.metric("Präferenzen", f"{result.preference_score:.3f}")
                    with col4:
                        st.metric("Final", f"{result.final_score:.3f}")

                # Route anzeigen
                display_route_card(
                    result.route,
                    score=result.final_score,
                    explanation=result.explanation,
                )

                st.markdown("---")

        else:
            st.warning(
                "😕 Keine passenden Routen gefunden. Versuchen Sie andere Suchbegriffe."
            )

    elif search_clicked:
        st.warning("⚠️ Bitte geben Sie eine Suchanfrage ein.")

    # Demo-Bereich
    if not query:
        st.subheader("🌟 Demo-Anfragen")
        st.write("Probieren Sie eine der folgenden Beispiel-Anfragen aus:")

        demo_queries = [
            "Ich möchte eine einfache Wanderung mit Restaurant",
            "Suche anspruchsvolle Bergtouren mit schöner Aussicht",
            "Kurze Familienwanderung in der Nähe von einem See",
            "Lange Wanderung mit vielen Höhenmetern zum Säntis",
            "Gemütliche Tour mit Einkehrmöglichkeit",
        ]

        cols = st.columns(2)
        for i, demo_query in enumerate(demo_queries):
            col = cols[i % 2]
            with col:
                if st.button(f"'{demo_query}'", key=f"demo_{i}"):
                    st.rerun()

    # Alle Routen anzeigen (wenn gewünscht)
    if show_visualizations:
        with st.expander("📈 Alle Routen visualisieren"):
            st.subheader("🗺️ Übersicht aller verfügbaren Wanderrouten")
            create_route_visualization(rag_system.routes)

    # Footer
    st.markdown("---")
    st.markdown(
        """
    <div style='text-align: center; color: #666; padding: 20px;'>
        🏔️ <strong>Appenzeller Wanderungen RAG System</strong><br>
        Entwickelt mit ❤️ für Wanderbegeisterte | 
        Powered by Streamlit & Custom RAG Architecture
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
