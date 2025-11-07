#!/usr/bin/env python3

import requests
import json

# Dati per test diretto
test_data = {
    "course_id": "e9195d61-9bd2-4e30-a183-cee2ab80f1b9",
    "book_id": "582d5f87-89bb-45da-8df5-28e33d7dc009",
    "topic": "Sebastiano Caboto",
    "focus_areas": ["introduzione", "viaggi", "scoperte"]
}

print("🧪 Test diretto endpoint /mindmap")
print(f"Dati: {json.dumps(test_data, indent=2)}")

try:
    response = requests.post(
        "http://localhost:8000/mindmap",
        json=test_data,
        headers={"Content-Type": "application/json"},
        timeout=60
    )

    print(f"\n📊 Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("✅ Risposta ricevuta")

        # Analizza i nodi
        mindmap = result.get('mindmap', {})
        nodes = mindmap.get('nodes', [])

        print(f"\n📋 Analisi nodi:")
        print(f"   Numero nodi principali: {len(nodes)}")

        for i, node in enumerate(nodes):
            print(f"\n   🔍 Nodo {i+1}:")
            print(f"      ID: {node.get('id', 'N/A')}")
            print(f"      Title: {node.get('title', 'N/A')}")
            print(f"      Title length: {len(node.get('title', ''))}")

            # Controlla se ci sono riferimenti sorgente nel titolo
            title = node.get('title', '')
            has_source_refs = any(ref in title.lower() for ref in [
                'docsity', 'http', 'www', 'com', 'libro', 'documento',
                'page:', 'pos:', 'downloaded by', 'gmail.com'
            ])
            print(f"      Contiene riferimenti sorgente: {'❌ SÌ' if has_source_refs else '✅ NO'}")

            # Controlla i figli
            children = node.get('children', [])
            print(f"      Figli: {len(children)}")

            for j, child in enumerate(children):
                child_title = child.get('title', '')
                child_has_refs = any(ref in child_title.lower() for ref in [
                    'docsity', 'http', 'www', 'com', 'libro', 'documento',
                    'page:', 'pos:', 'downloaded by', 'gmail.com'
                ])
                print(f"         Figlio {j+1}: {child_title[:50]}... {'❌ REFs' if child_has_refs else '✅ OK'}")
    else:
        print(f"❌ Errore: {response.text}")

except Exception as e:
    print(f"❌ Errore: {e}")

print("\n🔍 Controlla i log del backend per i messaggi di debug della pulizia")