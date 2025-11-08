#!/usr/bin/env python3
"""
Test completo del sistema RAG-based concept maps per libri
"""

import json
import time
import requests
import asyncio
from typing import Dict, Any, List

class RAGConceptMapTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.course_id = "90a903c0-4ef6-4415-ae3b-9dbc70ad69a9"
        self.test_books = [
            {"id": "e92ed79d-b92b-44d7-9627-172298a6ca0c", "title": "Manuale geografia storica"},
            {"id": "7a8b3b91-46c0-4b47-9e2b-083f79dc9f29", "title": "Sebastiano Caboto"},
            {"id": "7bd8fdca-80cf-44d6-8761-bd60dc5edada", "title": "La natura sottomessa"},
            {"id": "f92fed02-ecc3-48ea-b7af-7570464a2919", "title": "La terra Piatta"}
        ]

    def test_health_check(self):
        """Test che il backend sia raggiungibile"""
        print("🏥 Health Check")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Backend healthy: {response.json()['status']}")
                return True
            else:
                print(f"❌ Backend unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend non raggiungibile: {e}")
            return False

    def test_book_content_analysis(self, book_id: str, book_title: str):
        """Test analisi contenuti RAG per un libro"""
        print(f"\n📊 Analisi Contenuti RAG - {book_title}")

        try:
            # Test analysis summary
            analysis_request = {
                "course_id": self.course_id,
                "book_id": book_id,
                "include_full_analysis": False,
                "analysis_depth": "standard"
            }

            response = requests.post(
                f"{self.base_url}/api/book-concept-maps/{self.course_id}/{book_id}/analyze",
                json=analysis_request,
                timeout=30
            )

            if response.status_code == 200:
                analysis = response.json()
                summary = analysis.get("summary", {})

                print(f"   ✅ Analisi completata")
                print(f"   📄 Documenti usati: {summary.get('documents_used', 0)}")
                print(f"   🎯 Coverage score: {summary.get('rag_coverage_score', 0.0):.2f}")
                print(f"   📚 Qualità analisi: {summary.get('analysis_quality', 'N/A')}")
                print(f"   🔍 Temi trovati: {summary.get('main_themes_count', 0)}")
                print(f"   💡 Concetti chiave: {summary.get('key_concepts_count', 0)}")
                print(f"   📖 Struttura rilevata: {summary.get('structure_detected', False)}")

                return {
                    "success": True,
                    "quality_score": summary.get('rag_coverage_score', 0.0),
                    "documents_used": summary.get('documents_used', 0)
                }
            else:
                print(f"   ❌ Analisi fallita: {response.status_code}")
                print(f"   Error: {response.text}")
                return {"success": False, "error": response.text}

        except Exception as e:
            print(f"   ❌ Errore analisi: {e}")
            return {"success": False, "error": str(e)}

    def test_concept_map_generation(self, book_id: str, book_title: str, force_regenerate: bool = False):
        """Test generazione concept map RAG-based"""
        print(f"\n🧠 Generazione Concept Map - {book_title}")

        try:
            request_data = {
                "course_id": self.course_id,
                "book_id": book_id,
                "force_regeneration": force_regenerate,
                "quality_threshold": 0.6,
                "use_cache": not force_regenerate
            }

            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/book-concept-maps/{self.course_id}/{book_id}",
                json=request_data,
                timeout=120  # 2 minuti max
            )
            generation_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                concept_map = result.get("concept_map", {})
                metadata = result.get("generation_metadata", {})
                performance = result.get("performance_metrics", {})

                print(f"   ✅ Concept map generata in {generation_time:.2f}s")
                print(f"   📊 Metodo generazione: {metadata.get('generation_method', 'N/A')}")
                print(f"   🤖 RAG enhanced: {metadata.get('rag_enhanced', False)}")
                print(f"   🎯 Qualità RAG: {metadata.get('rag_quality_score', 0.0):.2f}")
                print(f"   📚 Concetti generati: {metadata.get('concepts_count', 0)}")
                print(f"   📄 Source count: {metadata.get('source_count', 0)}")
                print(f"   💾 Cache hit: {metadata.get('cache_hit', False)}")
                print(f"   ⚡ Performance: {performance.get('generation_time_seconds', 0):.3f}s")

                # Analizza qualità dei concetti
                concepts = concept_map.get("concepts", [])
                if concepts:
                    print(f"   📋 Esempi concetti:")
                    for i, concept in enumerate(concepts[:3]):  # Primi 3 concetti
                        name = concept.get("name", "N/A")
                        rag_supported = concept.get("rag_supported", False)
                        confidence = concept.get("confidence_score", 0.0)
                        print(f"      {i+1}. {name[:50]}... (RAG: {rag_supported}, Conf: {confidence:.2f})")

                return {
                    "success": True,
                    "generation_time": generation_time,
                    "concepts_count": len(concepts),
                    "rag_enhanced": metadata.get("rag_enhanced", False),
                    "quality_score": metadata.get("rag_quality_score", 0.0),
                    "cache_hit": metadata.get("cache_hit", False)
                }
            else:
                print(f"   ❌ Generazione fallita: {response.status_code}")
                print(f"   Error: {response.text}")
                return {"success": False, "error": response.text}

        except Exception as e:
            print(f"   ❌ Errore generazione: {e}")
            return {"success": False, "error": str(e)}

    def test_cache_performance(self, book_id: str, book_title: str):
        """Test performance cache"""
        print(f"\n💾 Test Cache Performance - {book_title}")

        try:
            # Prima generazione (cache miss)
            print("   🔄 Prima generazione (cache miss previsto)...")
            first_result = self.test_concept_map_generation(book_id, book_title, force_regenerate=True)

            if not first_result.get("success"):
                return {"success": False, "error": "First generation failed"}

            first_time = first_result.get("generation_time", 0)

            # Seconda generazione (cache hit previsto)
            print("   🔄 Seconda generazione (cache hit previsto)...")
            time.sleep(1)  # Breve pausa
            second_result = self.test_concept_map_generation(book_id, book_title, force_regenerate=False)

            if not second_result.get("success"):
                return {"success": False, "error": "Second generation failed"}

            second_time = second_result.get("generation_time", 0)
            cache_hit = second_result.get("cache_hit", False)

            # Calcola speedup
            speedup = first_time / second_time if second_time > 0 else 0

            print(f"   📊 Performance Cache:")
            print(f"      Prima generazione: {first_time:.3f}s")
            print(f"      Seconda generazione: {second_time:.3f}s")
            print(f"      Cache hit: {cache_hit}")
            print(f"      Speedup: {speedup:.1f}x")

            return {
                "success": True,
                "first_time": first_time,
                "second_time": second_time,
                "cache_hit": cache_hit,
                "speedup": speedup
            }

        except Exception as e:
            print(f"   ❌ Errore test cache: {e}")
            return {"success": False, "error": str(e)}

    def test_concept_map_summary(self, book_id: str, book_title: str):
        """Test endpoint summary concept map"""
        print(f"\n📋 Test Summary - {book_title}")

        try:
            response = requests.get(
                f"{self.base_url}/api/book-concept-maps/{self.course_id}/{book_id}",
                timeout=10
            )

            if response.status_code == 200:
                summary = response.json()
                print(f"   ✅ Summary recuperato")
                print(f"   📚 Libro: {summary.get('book_title', 'N/A')}")
                print(f"   🔢 Concetti: {summary.get('concepts_count', 0)}")
                print(f"   🤖 RAG enhanced: {summary.get('rag_enhanced', False)}")
                print(f"   🎯 Qualità: {summary.get('quality_score', 0.0):.2f}")
                print(f"   💾 Cache hit: {summary.get('cache_hit', False)}")
                print(f"   📅 Generato: {summary.get('generated_at', 'N/A')[:19]}")

                return {"success": True, "summary": summary}
            else:
                print(f"   ❌ Summary fallito: {response.status_code}")
                return {"success": False, "error": response.text}

        except Exception as e:
            print(f"   ❌ Errore summary: {e}")
            return {"success": False, "error": str(e)}

    def test_cache_stats(self):
        """Test statistiche cache"""
        print(f"\n📊 Test Cache Stats")

        try:
            response = requests.get(f"{self.base_url}/api/book-concept-maps/cache/stats", timeout=10)

            if response.status_code == 200:
                stats = response.json()
                cache_perf = stats.get("cache_performance", {})
                cache_content = stats.get("cache_content", {})

                print(f"   ✅ Statistiche cache:")
                print(f"      Hit rate: {cache_perf.get('hit_rate', 0.0):.2%}")
                print(f"      Total requests: {cache_perf.get('total_requests', 0)}")
                print(f"      Cache hits: {cache_perf.get('cache_hits', 0)}")
                print(f"      Avg response time: {cache_perf.get('avg_response_time', 0):.3f}s")
                print(f"      Total entries: {cache_content.get('total_entries', 0)}")
                print(f"      RAG enhanced entries: {cache_content.get('rag_enhanced_entries', 0)}")

                return {"success": True, "stats": stats}
            else:
                print(f"   ❌ Stats fallite: {response.status_code}")
                return {"success": False, "error": response.text}

        except Exception as e:
            print(f"   ❌ Errore stats: {e}")
            return {"success": False, "error": str(e)}

    def test_validation_endpoint(self, book_id: str, book_title: str):
        """Test endpoint validazione concept map"""
        print(f"\n✅ Test Validazione - {book_title}")

        try:
            # Prima genera una concept map da validare
            gen_result = self.test_concept_map_generation(book_id, book_title)
            if not gen_result.get("success"):
                return {"success": False, "error": "Cannot generate concept map for validation"}

            # Richiedi la concept map generata
            response = requests.get(
                f"{self.base_url}/api/book-concept-maps/{self.course_id}/{book_id}",
                timeout=10
            )

            if response.status_code != 200:
                return {"success": False, "error": "Cannot get concept map for validation"}

            concept_map = response.json()

            # Valida la concept map
            validation_request = {
                "course_id": self.course_id,
                "book_id": book_id,
                "concept_map": concept_map,
                "validation_level": "standard"
            }

            response = requests.post(
                f"{self.base_url}/api/book-concept-maps/validate",
                json=validation_request,
                timeout=30
            )

            if response.status_code == 200:
                validation = response.json()
                print(f"   ✅ Validazione completata")
                print(f"      Valid: {validation.get('is_valid', False)}")
                print(f"      Validation score: {validation.get('validation_score', 0.0):.2f}")
                print(f"      RAG alignment: {validation.get('rag_alignment_score', 0.0):.2f}")
                print(f"      Educational quality: {validation.get('educational_quality_score', 0.0):.2f}")
                print(f"      Issues found: {len(validation.get('issues_found', []))}")
                print(f"      Suggestions: {len(validation.get('suggestions', []))}")

                return {"success": True, "validation": validation}
            else:
                print(f"   ❌ Validazione fallita: {response.status_code}")
                return {"success": False, "error": response.text}

        except Exception as e:
            print(f"   ❌ Errore validazione: {e}")
            return {"success": False, "error": str(e)}

    def run_comprehensive_test(self):
        """Esegue test completo su tutti i libri"""
        print("🧪 TEST COMPLETIVO SISTEMA RAG-BASED CONCEPT MAPS")
        print("=" * 80)

        # Health check
        if not self.test_health_check():
            print("❌ Backend non disponibile, interrompo test")
            return

        results = {
            "books_tested": 0,
            "successful_analyses": 0,
            "successful_generations": 0,
            "cache_tests": 0,
            "validation_tests": 0,
            "performance_data": [],
            "errors": []
        }

        # Test per ogni libro
        for book in self.test_books:
            book_id = book["id"]
            book_title = book["title"]

            print(f"\n{'='*20} {book_title} {'='*20}")

            book_results = {
                "book_id": book_id,
                "book_title": book_title,
                "analysis": None,
                "generation": None,
                "cache": None,
                "validation": None
            }

            # 1. Test analisi contenuti
            analysis_result = self.test_book_content_analysis(book_id, book_title)
            book_results["analysis"] = analysis_result
            if analysis_result.get("success"):
                results["successful_analyses"] += 1

            # 2. Test generazione concept map
            generation_result = self.test_concept_map_generation(book_id, book_title)
            book_results["generation"] = generation_result
            if generation_result.get("success"):
                results["successful_generations"] += 1

            # 3. Test cache performance (solo se generazione ha successo)
            if generation_result.get("success"):
                cache_result = self.test_cache_performance(book_id, book_title)
                book_results["cache"] = cache_result
                if cache_result.get("success"):
                    results["cache_tests"] += 1

            # 4. Test summary
            self.test_concept_map_summary(book_id, book_title)

            # 5. Test validazione (solo se generazione ha successo)
            if generation_result.get("success"):
                validation_result = self.test_validation_endpoint(book_id, book_title)
                book_results["validation"] = validation_result
                if validation_result.get("success"):
                    results["validation_tests"] += 1

            results["books_tested"] += 1
            results["performance_data"].append(book_results)

        # Test statistiche cache finali
        print(f"\n{'='*20} CACHE STATS FINALI {'='*20}")
        self.test_cache_stats()

        # Riepilogo finale
        print(f"\n{'='*20} RIEPILOGO TEST {'='*20}")
        print(f"📚 Libri testati: {results['books_tested']}/{len(self.test_books)}")
        print(f"📊 Analisi RAG riuscite: {results['successful_analyses']}/{results['books_tested']}")
        print(f"🧠 Generazioni concept map riuscite: {results['successful_generations']}/{results['books_tested']}")
        print(f"💾 Test cache riusciti: {results['cache_tests']}/{results['successful_generations']}")
        print(f"✅ Test validazione riusciti: {results['validation_tests']}/{results['successful_generations']}")

        # Performance summary
        if results["performance_data"]:
            avg_quality = 0.0
            avg_time = 0.0
            cache_speedups = []
            rag_enhanced = 0

            for book_data in results["performance_data"]:
                if book_data["generation"] and book_data["generation"]["success"]:
                    avg_quality += book_data["generation"].get("quality_score", 0.0)
                    avg_time += book_data["generation"].get("generation_time", 0.0)
                    if book_data["generation"].get("rag_enhanced", False):
                        rag_enhanced += 1

                if book_data["cache"] and book_data["cache"]["success"]:
                    speedup = book_data["cache"].get("speedup", 0.0)
                    if speedup > 0:
                        cache_speedups.append(speedup)

            successful_gens = results["successful_generations"]
            if successful_gens > 0:
                avg_quality /= successful_gens
                avg_time /= successful_gens

            print(f"\n📊 PERFORMANCE SUMMARY:")
            print(f"   🎯 Qualità media RAG: {avg_quality:.2f}")
            print(f"   ⏱️ Tempo medio generazione: {avg_time:.2f}s")
            print(f"   🤖 Concept map RAG-enhanced: {rag_enhanced}/{successful_gens}")
            if cache_speedups:
                avg_speedup = sum(cache_speedups) / len(cache_speedups)
                print(f"   💾 Cache speedup medio: {avg_speedup:.1f}x")

        print(f"\n🎯 TEST COMPLETATO!")

def main():
    """Main test execution"""
    tester = RAGConceptMapTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()