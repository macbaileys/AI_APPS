#!/usr/bin/env python3
"""
ZKB Wanderdokumente Processor
============================

Extrahiert Wanderrouten aus ZKB-PDFs und konvertiert sie
in das gleiche Format wie die Appenzeller Routen.
"""

import pdfplumber
import re
import json
from typing import List, Dict, Any
import os


class ZKBProcessor:
    """Processor für ZKB-Wanderdokumente"""

    def __init__(self):
        self.routes = []

    def extract_zkb_routes(self, pdf_path: str, max_pages: int = 20) -> List[Dict]:
        """Extrahiert Wanderrouten aus ZKB-PDF"""

        routes = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                pages_to_read = min(len(pdf.pages), max_pages)

                print(
                    f"   📄 Lese {pages_to_read} Seiten aus {os.path.basename(pdf_path)}"
                )

                for i in range(pages_to_read):
                    page = pdf.pages[i]
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"

                # Wanderungen im Text finden
                routes = self.parse_zkb_text(full_text, pdf_path)

        except Exception as e:
            print(f"⚠️ Fehler beim Verarbeiten von {pdf_path}: {e}")

        return routes

    def parse_zkb_text(self, text: str, source_pdf: str) -> List[Dict]:
        """Parst ZKB-Text und extrahiert Wanderungen"""

        routes = []

        # Pattern für Wanderungen (flexibel für verschiedene ZKB-Formate)
        patterns = [
            # Standard ZKB Format
            r"(\d+\.?\s+[\w\s\-äöüÄÖÜ]+(?:wanderung|tour|weg|pfad|rundweg)[\w\s\-äöüÄÖÜ]*)",
            # Ortsnamen mit Wanderbezug
            r"((?:Wanderung|Tour|Rundgang|Spaziergang)\s+[\w\s\-äöüÄÖÜ]+)",
            # Nach Nummern suchende Wanderungen
            r"(\d{1,3}[.\s]+[A-ZÄÖÜ][\w\s\-äöüÄÖÜ]{10,50})",
        ]

        # Suche nach Zeitangaben
        time_pattern = r"(\d+[.,]?\d*\s*(?:Std|Stunden?|h|Minuten?|min))"

        # Suche nach Distanzen
        distance_pattern = r"(\d+[.,]?\d*\s*km)"

        # Suche nach Höhenmetern
        elevation_pattern = r"(\d+\s*(?:m\s*ü\.?\s*M\.?|Höhenmeter|hm))"

        found_routes = set()  # Duplikate vermeiden

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)

            for match in matches:
                route_text = match.group(1).strip()

                # Mindestlänge und Qualitätsprüfung
                if len(route_text) < 10 or route_text in found_routes:
                    continue

                found_routes.add(route_text)

                # Kontext um den Match herum extrahieren
                start = max(0, match.start() - 300)
                end = min(len(text), match.end() + 300)
                context = text[start:end]

                # Metadaten extrahieren
                duration = self.extract_duration(context)
                distance = self.extract_distance(context)
                elevation = self.extract_elevation(context)

                # Route-Objekt erstellen
                route = {
                    "title": self.clean_title(route_text),
                    "description": self.extract_description(context, route_text),
                    "duration": duration,
                    "distance": distance,
                    "elevation_gain": elevation,
                    "sac_scale": self.estimate_difficulty(context, duration),
                    "restaurants": self.extract_restaurants(context),
                    "highlights": self.extract_highlights(context),
                    "source": f"ZKB - {os.path.basename(source_pdf)}",
                    "region": self.extract_region(context, route_text),
                }

                routes.append(route)

        # Duplikate entfernen und nach Qualität sortieren
        routes = self.deduplicate_routes(routes)

        print(
            f"   ✅ {len(routes)} Routen aus {os.path.basename(source_pdf)} extrahiert"
        )

        return routes

    def clean_title(self, title: str) -> str:
        """Bereinigt und formatiert Titel"""
        # Führende Nummern entfernen
        title = re.sub(r"^\d+[.\s]*", "", title)

        # Mehrfache Leerzeichen entfernen
        title = re.sub(r"\s+", " ", title)

        # Groß-/Kleinschreibung optimieren
        if title.isupper():
            title = title.title()

        return title.strip()

    def extract_duration(self, context: str) -> str:
        """Extrahiert Zeitangaben"""
        time_patterns = [
            r"(\d+[.,]?\d*\s*(?:Std|Stunden?))",
            r"(\d+[.,]?\d*\s*h\s*\d*)",
            r"(\d+\s*-\s*\d+\s*(?:Std|Stunden?))",
        ]

        for pattern in time_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1)

        return "Nicht angegeben"

    def extract_distance(self, context: str) -> str:
        """Extrahiert Distanzangaben"""
        distance_patterns = [
            r"(\d+[.,]?\d*\s*km)",
            r"(\d+[.,]?\d*\s*Kilometer)",
        ]

        for pattern in distance_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1)

        return "Nicht angegeben"

    def extract_elevation(self, context: str) -> str:
        """Extrahiert Höhenmeter"""
        elevation_patterns = [
            r"(\d+\s*m\s*ü\.?\s*M\.?)",
            r"(\d+\s*Höhenmeter)",
            r"(\d+\s*hm)",
            r"(\d+\s*m\s*Aufstieg)",
        ]

        for pattern in elevation_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(1)

        return "Nicht angegeben"

    def estimate_difficulty(self, context: str, duration: str) -> str:
        """Schätzt SAC-Schwierigkeit basierend auf Kontext"""

        # Direkte SAC-Angaben suchen
        sac_match = re.search(r"T\s*([1-6])", context, re.IGNORECASE)
        if sac_match:
            return f"T{sac_match.group(1)}"

        # Schlüsselwörter für Schwierigkeit
        if re.search(
            r"(schwierig|anspruchsvoll|steil|klettern)", context, re.IGNORECASE
        ):
            return "T3"
        elif re.search(r"(mittel|bergwanderung|bergweg)", context, re.IGNORECASE):
            return "T2"
        elif re.search(
            r"(einfach|leicht|spaziergang|familien)", context, re.IGNORECASE
        ):
            return "T1"

        # Fallback basierend auf Dauer
        if "Std" in duration or "h" in duration:
            try:
                hours = float(re.search(r"(\d+)", duration).group(1))
                if hours >= 5:
                    return "T3"
                elif hours >= 3:
                    return "T2"
                else:
                    return "T1"
            except:
                pass

        return "T1"  # Konservativer Fallback

    def extract_restaurants(self, context: str) -> List[str]:
        """Extrahiert Restaurant-/Einkehrmöglichkeiten"""
        restaurant_patterns = [
            r"(Restaurant\s+[\w\s\-äöüÄÖÜ]{3,25})",
            r"(Gasthaus\s+[\w\s\-äöüÄÖÜ]{3,25})",
            r"(Beizli\s+[\w\s\-äöüÄÖÜ]{3,25})",
            r"(Hotel\s+[\w\s\-äöüÄÖÜ]{3,25})",
        ]

        restaurants = []
        for pattern in restaurant_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                restaurant = match.group(1).strip()
                if restaurant not in restaurants:
                    restaurants.append(restaurant)

        return restaurants[:3]  # Max 3 Restaurants

    def extract_highlights(self, context: str) -> List[str]:
        """Extrahiert Highlights/Sehenswürdigkeiten"""
        highlight_patterns = [
            r"(Aussicht\s+[\w\s\-äöüÄÖÜ]{5,30})",
            r"(See\s+[\w\s\-äöüÄÖÜ]{3,20})",
            r"(Gipfel\s+[\w\s\-äöüÄÖÜ]{3,20})",
            r"(Wasserfall\s+[\w\s\-äöüÄÖÜ]{3,20})",
            r"(Kapelle\s+[\w\s\-äöüÄÖÜ]{3,20})",
        ]

        highlights = []
        for pattern in highlight_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                highlight = match.group(1).strip()
                if highlight not in highlights:
                    highlights.append(highlight)

        return highlights[:3]  # Max 3 Highlights

    def extract_description(self, context: str, title: str) -> str:
        """Extrahiert/generiert Beschreibung"""
        # Suche nach beschreibendem Text um den Titel herum
        sentences = re.split(r"[.!?]", context)

        description_parts = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and any(
                word in sentence.lower()
                for word in ["wanderung", "tour", "weg", "führt", "steigt", "aussicht"]
            ):
                description_parts.append(sentence)
                if len(description_parts) >= 2:  # Max 2 Sätze
                    break

        if description_parts:
            return ". ".join(description_parts) + "."
        else:
            return f"Wanderung {title} - Details siehe ZKB-Wanderführer."

    def extract_region(self, context: str, title: str) -> str:
        """Extrahiert Region/Kanton"""
        # Bekannte Schweizer Regionen/Kantone
        regions = [
            "Appenzell",
            "Graubünden",
            "Wallis",
            "Bern",
            "Zürich",
            "Luzern",
            "Uri",
            "Schwyz",
            "Glarus",
            "Freiburg",
        ]

        for region in regions:
            if region.lower() in context.lower() or region.lower() in title.lower():
                return region

        return "Schweiz"  # Fallback

    def deduplicate_routes(self, routes: List[Dict]) -> List[Dict]:
        """Entfernt Duplikate basierend auf Titel-Ähnlichkeit"""
        unique_routes = []
        seen_titles = set()

        for route in routes:
            title_key = route["title"].lower().replace(" ", "").replace("-", "")[:20]

            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_routes.append(route)

        return unique_routes

    def process_all_zkb_pdfs(self, pdf_folder: str = "PDFs") -> List[Dict]:
        """Verarbeitet alle ZKB-PDFs im Ordner"""

        all_routes = []

        if not os.path.exists(pdf_folder):
            print(f"⚠️ PDF-Ordner {pdf_folder} nicht gefunden")
            return all_routes

        zkb_files = [
            f
            for f in os.listdir(pdf_folder)
            if f.lower().startswith("zkb") and f.lower().endswith(".pdf")
        ]

        print(f"🏔️ Verarbeite {len(zkb_files)} ZKB-Dokumente...")

        for pdf_file in zkb_files:
            pdf_path = os.path.join(pdf_folder, pdf_file)
            routes = self.extract_zkb_routes(pdf_path)
            all_routes.extend(routes)

        print(f"✅ Insgesamt {len(all_routes)} ZKB-Routen extrahiert")
        return all_routes

    def save_zkb_routes(self, routes: List[Dict], output_file: str = "zkb_routes.json"):
        """Speichert ZKB-Routen als JSON"""

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(routes, f, ensure_ascii=False, indent=2)
            print(f"💾 ZKB-Routen gespeichert in {output_file}")
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")


def main():
    """Hauptfunktion für ZKB-Verarbeitung"""

    processor = ZKBProcessor()

    # Alle ZKB-PDFs verarbeiten
    routes = processor.process_all_zkb_pdfs()

    # Ergebnisse anzeigen
    print(f"\n📊 ZKB-Verarbeitungs-Ergebnisse:")
    print(f"• Gefundene Routen: {len(routes)}")

    if routes:
        # Erste 3 Routen als Beispiel anzeigen
        print(f"\n🏔️ Beispiel-Routen:")
        for i, route in enumerate(routes[:3], 1):
            print(f"{i}. {route['title']}")
            print(f"   • Dauer: {route['duration']}")
            print(f"   • Schwierigkeit: {route['sac_scale']}")
            print(f"   • Quelle: {route['source']}")

        # Speichern
        processor.save_zkb_routes(routes)
    else:
        print("❌ Keine Routen gefunden")


if __name__ == "__main__":
    main()
