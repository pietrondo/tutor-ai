#!/usr/bin/env python3
"""
Test script to verify the mindmap expansion improvements
"""

import requests
import json
import time

def test_mindmap_expansion():
    """Test the mindmap expansion endpoint with the improvements"""

    # Test data from the console logs
    test_request = {
        "course_id": "e9195d61-9bd2-4e30-a183-cee2ab80f1b9",
        "book_id": "15327ff3-5143-4361-a215-3d8abffc2310",
        "node_text": "Evoluzione Storica",
        "node_context": "Manuale di geografia storica",
        "max_children": 4
    }

    print("🧪 Testing mindmap expansion with improvements...")
    print(f"📝 Request: {json.dumps(test_request, indent=2)}")

    try:
        response = requests.post(
            "http://localhost:8000/mindmap/expand",
            json=test_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"📊 Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Received response:")
            print(f"   - Success: {data.get('success')}")
            print(f"   - Nodes generated: {len(data.get('expanded_nodes', []))}")
            print(f"   - Generation method: {data.get('generation_method')}")
            print(f"   - Query time: {data.get('query_time', 0):.2f}s")
            print(f"   - Sources used: {len(data.get('sources_used', []))}")

            print("\n📋 Generated nodes:")
            for i, node in enumerate(data.get('expanded_nodes', []), 1):
                print(f"   {i}. {node.get('title', 'No title')}")
                print(f"      Summary: {node.get('summary', 'No summary')[:100]}...")
                print(f"      Priority: {node.get('priority')}")
                print(f"      AI Hint: {node.get('ai_hint', 'No hint')[:80]}...")
                print(f"      Study Actions: {len(node.get('study_actions', []))} actions")
                print()

            # Check if we still get generic "Approfondimento" nodes
            generic_nodes = [n for n in data.get('expanded_nodes', []) if 'Approfondimento' in n.get('title', '')]
            if generic_nodes:
                print(f"⚠️  Warning: Still found {len(generic_nodes)} generic nodes")
                for node in generic_nodes:
                    print(f"     - {node.get('title')}")
            else:
                print("🎉 Excellent! No generic 'Approfondimento' nodes found!")

        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        print("Make sure the backend is running on localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_mindmap_status():
    """Test the mindmap status endpoint"""

    print("\n🔍 Testing mindmap status endpoint...")

    try:
        response = requests.get("http://localhost:8000/mindmap/status", timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("✅ Status endpoint working:")
            print(f"   - Status: {data.get('status')}")
            print(f"   - Features: {data.get('features', {})}")
            print(f"   - Max expansions: {data.get('max_expansions_per_request')}")
            print(f"   - Supported types: {data.get('supported_node_types', [])}")
        else:
            print(f"❌ Status endpoint error: {response.status_code}")

    except Exception as e:
        print(f"❌ Status endpoint error: {e}")

if __name__ == "__main__":
    print("🚀 Testing mindmap expansion improvements")
    print("=" * 50)

    # Wait a moment for services to be fully ready
    time.sleep(2)

    test_mindmap_status()
    test_mindmap_expansion()

    print("\n" + "=" * 50)
    print("🎯 Test completed!")