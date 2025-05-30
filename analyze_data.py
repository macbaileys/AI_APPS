#!/usr/bin/env python3
"""
Analyse der extrahierten Wanderdaten
"""

import json
from collections import Counter


def analyze_routes():
    with open("appenzell_routes_clean.json", "r", encoding="utf-8") as f:
        routes = json.load(f)

    print("=== DUPLIKATE ANALYSE ===")
    titles = {}
    duplicates = []
    for route in routes:
        title = route["title"]
        if title in titles:
            duplicates.append(title)
            print(f"DUPLIKAT: {title}")
            print(f"  ID 1: {titles[title]}")
            print(f"  ID 2: {route['id']}")
        else:
            titles[title] = route["id"]

    print(f"\nAnzahl Duplikate: {len(duplicates)}")

    print(f"\n=== SAC SKALEN ANALYSE ===")
    sac_counts = Counter([route.get("sac_scale", "Unknown") for route in routes])
    for sac, count in sorted(sac_counts.items()):
        print(f"{sac}: {count}")

    print(f"\n=== BESCHREIBUNGEN ANALYSE ===")
    short_descriptions = sum(1 for r in routes if len(r.get("description", "")) < 50)
    truncated = sum(
        1 for r in routes if r.get("description", "").endswith(("...", "-"))
    )

    print(f"Kurze Beschreibungen (<50 Zeichen): {short_descriptions}")
    print(f"Abgeschnittene Beschreibungen: {truncated}")

    print(f"\n=== BEISPIELE ABGESCHNITTENER BESCHREIBUNGEN ===")
    for route in routes[:5]:
        desc = route.get("description", "")
        if desc.endswith(("-", "...")):
            print(f"Route: {route['title']}")
            print(f"Beschreibung: {desc}")
            print(f"Raw Text Anfang: {route.get('raw_text', '')[:200]}...")
            print("-" * 50)


if __name__ == "__main__":
    analyze_routes()
