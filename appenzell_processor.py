#!/usr/bin/env python3
"""
Spezialisierter PDF-Prozessor für Appenzeller Wanderungen
Basiert auf detaillierter Seitenanalyse und User-Feedback
"""

import os
import re
import json
import pdfplumber
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib


@dataclass
class AppenzellRoute:
    """Datenklasse für eine Appenzeller Wanderroute"""

    id: str
    title: str
    description: str
    duration: str
    distance: str
    elevation_gain: str
    elevation_loss: str
    restaurants: List[str]
    sac_scale: str
    highlights: List[str]
    page_number: int
    raw_text: str


class AppenzellProcessor:
    """Spezialisierter Prozessor für Appenzeller Wanderungen"""

    def __init__(self):
        # Detaillierte Seitenkonfiguration basierend auf User-Angaben
        self.config = {
            "start_page": 8,
            "end_page": 81,  # Ab Seite 82 nur Werbung
            "skip_pages": {
                18,
                19,  # Seite 18&19 haben keine Wanderung
                31,
                32,
                33,
                34,
                35,
                36,
                37,
                38,
                39,  # Seite 31-39 auch keine wanderung
                48,  # Seite 48 keine wanderung
                50,
                56,
                66,
                68,
                69,  # seite 50,56,66,68,69 auch nicht
                74,
                75,  # seite 74&75 kein weg
                77,  # seite 77 kein weg
                80,  # s 80 kein weg
            },
            "double_pages": {
                40: [40, 41],  # Seite 40 streckt sich über 2 seiten
                72: [72, 73],  # seite 72 wieder 2 seiten
                78: [78, 79],  # s 78 zwei seiten
            },
        }

        print("🏔️ Appenzeller Wanderungen Prozessor initialisiert")
        print(
            f"   📄 Verarbeitung: Seite {self.config['start_page']} bis {self.config['end_page']}"
        )
        print(f"   ⏭️ Übersprungene Seiten: {sorted(self.config['skip_pages'])}")
        print(f"   📑 Doppelseiten: {list(self.config['double_pages'].keys())}")

    def process_appenzell_pdf(
        self, pdf_path: str = "PDFs/Appenzell_Wanderungen.pdf"
    ) -> List[Dict]:
        """Hauptfunktion zur Verarbeitung der Appenzeller PDF"""

        if not os.path.exists(pdf_path):
            print(f"❌ PDF nicht gefunden: {pdf_path}")
            return []

        print(f"\n📄 Verarbeite: {pdf_path}")
        routes = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"   📊 PDF hat {total_pages} Seiten")

                # Verarbeite alle relevanten Seiten
                current_page = self.config["start_page"]

                while current_page <= self.config["end_page"]:
                    # Überspringe bekannte Seiten ohne Wanderungen
                    if current_page in self.config["skip_pages"]:
                        print(f"  ⏭️ Überspringe Seite {current_page} (keine Wanderung)")
                        current_page += 1
                        continue

                    # Prüfe ob es eine Doppelseite ist
                    if current_page in self.config["double_pages"]:
                        pages_to_process = self.config["double_pages"][current_page]
                        print(f"  📑 Verarbeite Doppelseite: {pages_to_process}")
                        route = self.extract_route_from_pages(pdf, pages_to_process)
                        current_page = (
                            max(pages_to_process) + 1
                        )  # Springe nach der Doppelseite weiter
                    else:
                        print(f"  📄 Verarbeite Einzelseite: {current_page}")
                        route = self.extract_route_from_pages(pdf, [current_page])
                        current_page += 1

                    if route:
                        routes.append(route)
                        print(f"    ✅ Route extrahiert: {route['title'][:50]}...")
                    else:
                        print(f"    ⚠️ Keine gültige Route gefunden")

        except Exception as e:
            print(f"❌ Fehler beim Verarbeiten: {e}")

        print(f"\n🔧 Bereinige Duplikate und ungültige Einträge...")
        routes = self.remove_duplicates(routes)

        print(f"\n🎉 Fertig! {len(routes)} saubere Appenzeller Routen extrahiert")
        return routes

    def extract_route_from_pages(self, pdf, page_numbers: List[int]) -> Optional[Dict]:
        """Extrahiert eine Route von einer oder mehreren Seiten"""

        combined_text = ""

        # Sammle Text von allen Seiten
        for page_num in page_numbers:
            if page_num <= len(pdf.pages):
                page = pdf.pages[page_num - 1]  # pdfplumber ist 0-indiziert

                # Layout-Extraktion für beste Qualität
                text = page.extract_text(layout=True)
                if text:
                    combined_text += f"\n--- Seite {page_num} ---\n{text}\n"

        if not combined_text or len(combined_text) < 50:
            return None

        # Bereinige und parse den Text
        cleaned_text = self.clean_text(combined_text)
        route_data = self.parse_route_data(cleaned_text, page_numbers[0])

        return route_data

    def clean_text(self, text: str) -> str:
        """Bereinigt Text speziell für Appenzeller Format"""

        if not text:
            return ""

        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()
            # Behalte nur substantielle Zeilen
            if stripped and len(stripped) > 1:
                cleaned_lines.append(stripped)

        cleaned_text = "\n".join(cleaned_lines)

        # Normalisiere Leerzeichen
        cleaned_text = re.sub(r" +", " ", cleaned_text)
        cleaned_text = re.sub(r"\n\s*\n\s*\n", "\n\n", cleaned_text)

        return cleaned_text.strip()

    def parse_route_data(self, text: str, start_page: int) -> Dict:
        """Parst alle geforderten Routeninformationen"""

        route = {
            "id": hashlib.md5(
                f"appenzell_{start_page}_{text[:50]}".encode()
            ).hexdigest()[:8],
            "title": "",
            "description": "",
            "region": "Appenzell",
            "duration": "",
            "distance": "",
            "elevation_gain": "",
            "elevation_loss": "",
            "restaurants": [],
            "sac_scale": "",
            "highlights": [],
            "source_pdf": "Appenzell_Wanderungen.pdf",
            "page_number": start_page,
            "raw_text": text,
        }

        # 1. TITEL extrahieren
        route["title"] = self.extract_title(text)

        # 2. DAUER extrahieren
        route["duration"] = self.extract_duration(text)

        # 3. DISTANZ extrahieren
        route["distance"] = self.extract_distance(text)

        # 4. HÖHENMETER extrahieren
        elevation_gain, elevation_loss = self.extract_elevation(text)
        route["elevation_gain"] = elevation_gain
        route["elevation_loss"] = elevation_loss

        # 5. SAC WANDERSKALA extrahieren
        route["sac_scale"] = self.extract_sac_scale(text)

        # 6. RESTAURANTS extrahieren
        route["restaurants"] = self.extract_restaurants(text)

        # 7. BESCHREIBUNG extrahieren
        route["description"] = self.extract_description(text)

        # 8. HIGHLIGHTS extrahieren
        route["highlights"] = self.extract_highlights(text)

        return route

    def extract_title(self, text: str) -> str:
        """Extrahiert den Wanderungstitel"""

        lines = text.split("\n")

        # Suche in den ersten 20 Zeilen nach Großbuchstaben-Titel
        for line in lines[:20]:
            line = line.strip()

            # Appenzeller Titel: Großbuchstaben, 8-80 Zeichen, substantiell
            if (
                8 <= len(line) <= 80
                and line.isupper()
                and any(char.isalpha() for char in line)
                and
                # Filtere bekannte Nicht-Titel
                not any(
                    skip in line
                    for skip in [
                        "TAL- UND HÜGELWEGE",
                        "BERGWEGE",
                        "PFLANZEN IM ALPSTEIN",
                        "WANDERZEIT",
                        "SCHWIERIGKEIT",
                        "HÖHENMETER",
                    ]
                )
            ):

                # Entferne Seitenzahlen
                title = re.sub(r"\s+\d+\s*$", "", line).strip()
                if len(title) >= 8:
                    return title

        return f"Wanderung Seite {text.split()[0] if text.split() else 'Unknown'}"

    def extract_duration(self, text: str) -> str:
        """Extrahiert die Wanderdauer"""

        patterns = [
            r"(\d+)\s*Stunden?\s*(\d+)?\s*Minuten?",
            r"(\d+)\s*h\s*(\d+)?\s*min",
            r"(\d+)\s*Std\.?\s*(\d+)?\s*Min\.?",
            r"(\d+[,.]?\d*)\s*Stunden?",
            r"Wanderzeit[:\s]*(\d+[,.]?\d*)\s*(?:Stunden?|h)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return ""

    def extract_distance(self, text: str) -> str:
        """Extrahiert die Wanderdistanz"""

        patterns = [
            r"(\d+[,.]?\d*)\s*km",
            r"(\d+[,.]?\d*)\s*Kilometer",
            r"Distanz[:\s]*(\d+[,.]?\d*)\s*km",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if "Distanz" in match.group(0):
                    return match.group(1) + " km"
                return match.group(0).strip()

        return ""

    def extract_elevation(self, text: str) -> tuple:
        """Extrahiert Höhenmeter (Aufstieg/Abstieg)"""

        elevation_gain = ""
        elevation_loss = ""

        # Spezifisches Appenzeller Format: "8.73 km 510 m 510 m"
        lines = text.split("\n")
        for line in lines[:10]:  # Schaue in den ersten 10 Zeilen
            # Format: "XXX km YYY m ZZZ m" (Distanz, Aufstieg, Abstieg)
            km_pattern = r"(\d+[.,]?\d*)\s*km\s+(\d+)\s*m\s+(\d+)\s*m"
            match = re.search(km_pattern, line)
            if match:
                elevation_gain = match.group(2) + "m"
                elevation_loss = match.group(3) + "m"
                return elevation_gain, elevation_loss

        # Fallback: Traditionelle Muster
        gain_patterns = [
            r"(\d+)\s*m\s*(?:Aufstieg|↑|auf)",
            r"Aufstieg[:\s]*(\d+)\s*m",
            r"(\d+)\s*m\s*Höhenmeter\s*(?:auf|Aufstieg)",
            r"(\d+)\s*m\s+\d+\s*m",  # Erstes m in "XXX m YYY m"
        ]

        for pattern in gain_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                elevation_gain = match.group(1) + "m"
                break

        # Abstieg Muster
        loss_patterns = [
            r"(\d+)\s*m\s*(?:Abstieg|↓|ab)",
            r"Abstieg[:\s]*(\d+)\s*m",
            r"(\d+)\s*m\s*Höhenmeter\s*(?:ab|Abstieg)",
            r"\d+\s*m\s+(\d+)\s*m",  # Zweites m in "XXX m YYY m"
        ]

        for pattern in loss_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                elevation_loss = match.group(1) + "m"
                break

        return elevation_gain, elevation_loss

    def extract_sac_scale(self, text: str) -> str:
        """Extrahiert die SAC Wanderskala"""

        # Verbesserte Patterns für "T 1", "T 2", etc. (mit Leerzeichen)
        patterns = [
            r"SAC[:\s-]*T\s*([1-6])",  # "SAC-Wanderskala T 1"
            r"Wanderskala[:\s]*T\s*([1-6])",  # "Wanderskala T 1"
            r"\bT\s*([1-6])\b",  # Standalone "T 1" bis "T 6"
            r"SAC[:\s-]*([T1-6])",  # Fallback für "T1" format
            r"([T][1-6])",  # Direkte T1-T6 Matches
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Füge "T" hinzu falls nur Zahl gefunden
                result = match.group(1)
                if result.isdigit():
                    return f"T{result}"
                return result

        return ""

    def extract_restaurants(self, text: str) -> List[str]:
        """Extrahiert Restaurant/Einkehrmöglichkeiten"""

        restaurants = []

        # Restaurant-Keywords
        keywords = [
            "Restaurant",
            "Gasthaus",
            "Gasthof",
            "Beizli",
            "Café",
            "Hütte",
            "Berggasthaus",
            "Bergrestaurant",
            "Wirtschaft",
            "Alp",
        ]

        # Suche nach Restaurant-Erwähnungen
        for keyword in keywords:
            pattern = f"{keyword}[\\s]*([A-ZÄÖÜa-zäöü\\s-]+?)(?=[,\\.\\n]|$)"
            matches = re.findall(pattern, text, re.IGNORECASE)

            for match in matches:
                restaurant_name = f"{keyword} {match.strip()}"
                if (
                    len(restaurant_name) > 5
                    and len(restaurant_name) < 50
                    and restaurant_name not in restaurants
                ):
                    restaurants.append(restaurant_name)

        return restaurants[:3]  # Maximal 3 Restaurants

    def extract_description(self, text: str) -> str:
        """Extrahiert die Hauptbeschreibung - verbesserte Version"""

        lines = text.split("\n")
        description_lines = []

        # Finde substantielle Beschreibungszeilen
        collecting = False
        for line in lines:
            line = line.strip()

            # Überspringe leere und sehr kurze Zeilen
            if len(line) < 20:
                continue

            # Überspringe Großbuchstaben-Titel und Metadaten
            if line.isupper() or any(
                meta in line.lower()
                for meta in [
                    "stunden",
                    "minuten",
                    "km",
                    "sac-wanderskala",
                    "restaurant",
                    "höhenmeter",
                    "schwierigkeit",
                    "--- seite",
                    "tal- und hügelwege",
                    "bergwanderwege",
                    "rondom-wege",
                    "themenwege",
                ]
            ):
                continue

            # Sammle Text der wie eine Beschreibung aussieht
            if (
                len(line) > 30
                and not line.startswith("Hotel")
                and not line.startswith("Restaurant")
                and not line.startswith("Gasthaus")
                and not re.match(r"^\d+\.\d+\s*km", line)
            ):

                description_lines.append(line)
                collecting = True

                # Sammle bis zu 5 Sätze oder bis 600 Zeichen
                if (
                    len(description_lines) >= 5
                    or len(" ".join(description_lines)) > 600
                ):
                    break

        description = " ".join(description_lines)

        # Bereinige und normalisiere
        description = re.sub(
            r"\s+", " ", description
        )  # Mehrfache Leerzeichen entfernen
        description = description.strip()

        # Kürze auf vernünftige Länge aber vermeide Abschneiden mitten im Wort
        if len(description) > 500:
            # Finde letzten Satzpunkt vor 500 Zeichen
            truncate_pos = description.rfind(".", 0, 500)
            if truncate_pos > 200:  # Nur wenn genug Text bleibt
                description = description[: truncate_pos + 1]
            else:
                description = description[:500] + "..."

        return description

    def remove_duplicates(self, routes: List[Dict]) -> List[Dict]:
        """Entfernt Duplikate und ungültige Einträge"""

        seen_titles = set()
        clean_routes = []

        # Kategorien die übersprungen werden sollen
        skip_categories = {
            "RONDOM-WEGE",
            "BERGWANDERWEGE",
            "THEMENWEGE",
            "TAL- UND HÜGELWEGE",
            "BERGWANDERWEGE",
            "DREI-SEEN-WANDERUNG",
        }

        for route in routes:
            title = route.get("title", "").strip()

            # Überspringe leere Titel oder Kategorien
            if not title or title in skip_categories:
                continue

            # Überspringe Duplikate
            if title in seen_titles:
                continue

            # Überspringe Einträge ohne wesentlichen Inhalt
            if (
                not route.get("duration")
                and not route.get("distance")
                and len(route.get("description", "")) < 50
            ):
                continue

            seen_titles.add(title)
            clean_routes.append(route)

        return clean_routes

    def extract_highlights(self, text: str) -> List[str]:
        """Extrahiert besondere Highlights"""

        highlights = []

        # Typische Appenzeller Highlights
        highlight_keywords = [
            "Aussicht",
            "Panorama",
            "Gipfel",
            "See",
            "Seealpsee",
            "Wasserfall",
            "Alpstein",
            "Säntis",
            "Ebenalp",
            "Aescher",
            "Schöne Aussicht",
            "Bergsee",
            "Alp",
            "Hochebene",
            "Gratwanderung",
        ]

        text_lower = text.lower()
        for keyword in highlight_keywords:
            if keyword.lower() in text_lower:
                highlights.append(keyword)

        return highlights[:4]  # Maximal 4 Highlights

    def save_routes(
        self, routes: List[Dict], filename: str = "appenzell_routes_clean.json"
    ):
        """Speichert die extrahierten Routen"""

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(routes, f, ensure_ascii=False, indent=2)

        print(f"💾 {len(routes)} Appenzeller Routen gespeichert in {filename}")

    def print_summary(self, routes: List[Dict]):
        """Druckt eine detaillierte Zusammenfassung"""

        print(f"\n📊 APPENZELLER WANDERUNGEN - DETAILANALYSE")
        print("=" * 70)

        # Statistiken
        with_duration = sum(1 for r in routes if r["duration"])
        with_distance = sum(1 for r in routes if r["distance"])
        with_elevation = sum(1 for r in routes if r["elevation_gain"])
        with_sac = sum(1 for r in routes if r["sac_scale"])
        with_restaurants = sum(1 for r in routes if r["restaurants"])

        print(f"Total Routen: {len(routes)}")
        print(
            f"Mit Dauer: {with_duration}/{len(routes)} ({with_duration/len(routes)*100:.1f}%)"
        )
        print(
            f"Mit Distanz: {with_distance}/{len(routes)} ({with_distance/len(routes)*100:.1f}%)"
        )
        print(
            f"Mit Höhenmetern: {with_elevation}/{len(routes)} ({with_elevation/len(routes)*100:.1f}%)"
        )
        print(
            f"Mit SAC-Skala: {with_sac}/{len(routes)} ({with_sac/len(routes)*100:.1f}%)"
        )
        print(
            f"Mit Restaurants: {with_restaurants}/{len(routes)} ({with_restaurants/len(routes)*100:.1f}%)"
        )

        # Beispielrouten
        print(f"\n🔍 BEISPIELROUTEN:")
        print("-" * 50)

        for i, route in enumerate(routes[:5], 1):
            print(f"\n{i}. {route['title']}")
            print(f"   📍 Seite: {route['page_number']}")
            print(f"   ⏱️ Dauer: {route['duration'] or 'Nicht angegeben'}")
            print(f"   📏 Distanz: {route['distance'] or 'Nicht angegeben'}")
            print(f"   ⛰️ Aufstieg: {route['elevation_gain'] or 'Nicht angegeben'}")
            print(f"   🎯 SAC: {route['sac_scale'] or 'Nicht angegeben'}")
            if route["restaurants"]:
                print(f"   🍽️ Restaurants: {', '.join(route['restaurants'][:2])}")
            if route["description"]:
                print(f"   📝 Beschreibung: {route['description'][:100]}...")


def main():
    """Hauptfunktion"""

    processor = AppenzellProcessor()

    print("🏔️ STARTE APPENZELLER WANDERUNGEN EXTRAKTION")
    print("=" * 80)

    # Extrahiere Routen
    routes = processor.process_appenzell_pdf()

    if routes:
        # Speichere Ergebnisse
        processor.save_routes(routes)

        # Zeige detaillierte Zusammenfassung
        processor.print_summary(routes)

    else:
        print("❌ Keine Routen extrahiert!")


if __name__ == "__main__":
    main()
