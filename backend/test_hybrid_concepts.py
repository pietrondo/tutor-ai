#!/usr/bin/env python3
"""
Test sistema ibrido di concept maps
"""

import json
import time
import requests
from typing import Dict, Any

def test_hybrid_api():
    """Test sistema ibrido con diversi livelli di profondità"""

    base_url = "http://localhost:8001"
    course_id = "90a903c0-4ef6-4415-ae3b-9dbc70ad69a9"
    book_id = "e92ed79d-b92b-44d7-9627-172298a6ca0c"  # Manuale geografia storica

    print("🧪 Testando Sistema Ibrido di Concept Maps")
    print("=" * 60)

    # Test 1: Basic mode (solo concept maps pre-generate)
    print("\n1️⃣ Test BASIC (solo concept maps veloci)")
    basic_request = {
        "course_id": course_id,
        "book_id": book_id,
        "depth_level": "basic",
        "include_rag_analysis": False
    }

    start_time = time.time()
    try:
        response = requests.post(f"{base_url}/hybrid-concepts", json=basic_request, timeout=10)
        basic_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Basic mode: {basic_time:.2f}s")
            print(f"   Concetti base: {len(data.get('base_concepts', {}).get('concepts', []))}")
            print(f"   RAG analysis: {'No' if not data.get('rag_analysis') else 'Sì'}")
        else:
            print(f"❌ Basic mode failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Basic mode error: {e}")

    # Test 2: Detailed mode (concept maps + RAG analysis)
    print("\n2️⃣ Test DETAILED (concept maps + RAG analysis)")
    detailed_request = {
        "course_id": course_id,
        "book_id": book_id,
        "depth_level": "detailed",
        "include_rag_analysis": True,
        "focus_topics": ["geografia storica", "metodi di analisi"]
    }

    start_time = time.time()
    try:
        response = requests.post(f"{base_url}/hybrid-concepts", json=detailed_request, timeout=60)
        detailed_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Detailed mode: {detailed_time:.2f}s")
            print(f"   Concetti base: {len(data.get('base_concepts', {}).get('concepts', []))}")
            print(f"   RAG results: {len(data.get('rag_analysis', {}).get('results', []))}")
            print(f"   Enhanced concepts: {len(data.get('enhanced_concepts', []))}")

            # Mostra insights RAG
            enhanced = data.get('enhanced_concepts', [])
            if enhanced:
                print(f"   🔍 Esempio enhanced concept:")
                first_enhanced = enhanced[0]
                if 'rag_insights' in first_enhanced:
                    print(f"      - {first_enhanced.get('name', 'N/A')}")
                    print(f"      - RAG insights: {len(first_enhanced['rag_insights'])}")
        else:
            print(f"❌ Detailed mode failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Detailed mode error: {e}")

    # Test 3: Confronto performance
    print("\n3️⃣ Confronto Performance")

    # Test fast API esistente
    fast_request = {
        "course_id": course_id,
        "book_id": book_id
    }

    start_time = time.time()
    try:
        response = requests.post(f"{base_url}/book-concepts", json=fast_request, timeout=10)
        fast_time = time.time() - start_time

        if response.status_code == 200:
            print(f"✅ Fast API: {fast_time:.2f}s (solo concept maps)")

        # Confronto tempi
        if 'basic_time' in locals() and 'fast_time' in locals():
            print(f"📊 Confronto tempi:")
            print(f"   Fast API: {fast_time:.2f}s")
            print(f"   Hybrid Basic: {basic_time:.2f}s")
            if 'detailed_time' in locals():
                print(f"   Hybrid Detailed: {detailed_time:.2f}s")

    except Exception as e:
        print(f"❌ Fast API error: {e}")

    # Test 4: Comprehensive mode (se c'è tempo)
    print("\n4️⃣ Test COMPREHENSIVE (full analysis)")
    comprehensive_request = {
        "course_id": course_id,
        "book_id": book_id,
        "depth_level": "comprehensive",
        "include_rag_analysis": True,
        "focus_topics": ["geografia storica", "sviluppo territoriale", "metodi di ricerca"]
    }

    start_time = time.time()
    try:
        response = requests.post(f"{base_url}/hybrid-concepts", json=comprehensive_request, timeout=90)
        comprehensive_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Comprehensive mode: {comprehensive_time:.2f}s")
            print(f"   Concetti base: {len(data.get('base_concepts', {}).get('concepts', []))}")
            print(f"   RAG results: {len(data.get('rag_analysis', {}).get('results', []))}")
            print(f"   Enhanced concepts: {len(data.get('enhanced_concepts', []))}")
        else:
            print(f"❌ Comprehensive mode failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Comprehensive mode error: {e}")

    print("\n" + "=" * 60)
    print("🎯 Test Sistema Ibrido Completato!")

if __name__ == "__main__":
    test_hybrid_api()