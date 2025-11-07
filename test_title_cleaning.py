#!/usr/bin/env python3
"""
Test script per verificare la funzione di pulizia dei titoli dei nodi
"""

import sys
import os
sys.path.append('/mnt/c/Users/pietr/Documents/progetto/tutor-ai/backend')

# Import della funzione di pulizia
from app.api.mindmap_expand import _clean_node_title

def test_title_cleaning():
    """Test cases per la funzione _clean_node_title"""

    test_cases = [
        # Caso 1: URL completi
        {
            "input": "com it docs sebastiano-caboto-libro 12724853 Down...",
            "expected": "Viaggi di Esplorazione",
            "description": "URL con riferimento a Caboto"
        },
        {
            "input": "https://example.com/document.pdf page: 15, pos: 234",
            "expected": "Concetto Principale",
            "description": "URL completo con riferimenti"
        },

        # Caso 2: Riferimenti a pagine e posizioni
        {
            "input": "Concept analysis (page: 45, pos: 123)",
            "expected": "Concept analysis",
            "description": "Concetto con riferimenti pagina/posizione"
        },

        # Caso 3: ID esadecimali lunghi
        {
            "input": "Study material 85e4a794cc603636 with content",
            "expected": "Study material with content",
            "description": "Testo con ID esadecimale lungo"
        },

        # Caso 4: Riferimenti tra parentesi quadre
        {
            "input": "Historical analysis [source: document ABC]",
            "expected": "Historical analysis",
            "description": "Testo con riferimento in parentesi quadre"
        },

        # Caso 5: Testi puliti (non dovrebbero cambiare)
        {
            "input": "Viaggi e Scoperte",
            "expected": "Viaggi e Scoperte",
            "description": "Testo pulito non dovrebbe cambiare"
        },

        # Caso 6: Input vuoti o None
        {
            "input": "",
            "expected": "Concetto",
            "description": "Input vuoto"
        },
        {
            "input": None,
            "expected": "Concetto",
            "description": "Input None"
        }
    ]

    print("🧪 Test della funzione di pulizia titoli dei nodi")
    print("=" * 60)

    passed = 0
    total = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        input_val = test_case["input"]
        expected = test_case["expected"]
        description = test_case["description"]

        result = _clean_node_title(input_val)

        success = result == expected
        status = "✅ PASS" if success else "❌ FAIL"

        print(f"Test {i}: {description}")
        print(f"  Input:    '{input_val}'")
        print(f"  Atteso:   '{expected}'")
        print(f"  Risultato: '{result}'")
        print(f"  Status:   {status}")
        print()

        if success:
            passed += 1

    print("=" * 60)
    print(f"Risultati: {passed}/{total} test passati")

    if passed == total:
        print("🎉 Tutti i test sono passati!")
        return True
    else:
        print("⚠️ Alcuni test sono falliti")
        return False

if __name__ == "__main__":
    success = test_title_cleaning()
    sys.exit(0 if success else 1)