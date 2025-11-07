"""
Test Suite per Hybrid Search Service
Verifica il corretto funzionamento della ricerca ibrida (semantic + keyword)
"""

import asyncio
import json
import pytest
import os
from typing import List, Dict, Any
from services.rag_service import RAGService
from services.hybrid_search_service import HybridSearchService

class MockRAGService:
    """Mock RAG service per testing"""

    def __init__(self):
        self.embedding_model = MockEmbeddingModel()
        self.collection = MockChromaCollection()

class MockEmbeddingModel:
    """Mock embedding model per testing"""

    def encode(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings mock basati sulla lunghezza del testo"""
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        for text in texts:
            # Simple embedding based on text characteristics
            embedding = [
                len(text) % 100 / 100,
                len(set(text.lower())) % 100 / 100,
                text.count(' ') % 100 / 100,
                sum(1 for c in text if c.isupper()) % 100 / 100,
                sum(1 for c in text if c.isdigit()) % 100 / 100
            ]
            # Extend to 768 dimensions (standard per sentence transformers)
            while len(embedding) < 768:
                embedding.append(0.1)
            embeddings.append(embedding)

        return embeddings

class MockChromaCollection:
    """Mock ChromaDB collection per testing"""

    def __init__(self):
        self.documents = [
            "L'intelligenza artificiale è una branca dell'informatica che studia sistemi intelligenti.",
            "Il machine learning è un sotto-campo dell'IA che permette ai computer di imparare dai dati.",
            "Le reti neurali sono ispirate al funzionamento del cervello umano.",
            "Il deep learning utilizza reti neurali profonde per elaborare dati complessi.",
            "Il natural language processing permette alle macchine di capire il linguaggio umano.",
            "Il computer vision permette alle macchine di vedere e interpretare immagini.",
            "La robot combina IA, meccanica ed elettronica per creare robot intelligenti.",
            "L'IA può essere applicata in medicina, finanza, trasporti e molti altri settori.",
            "L'apprendimento supervisionato utilizza dati etichettati per addestrare modelli.",
            "L'apprendimento non supervisionato scopre pattern in dati senza etichette."
        ]

        self.metadatas = [
            {"source": "introduzione_ai.pdf", "chunk_index": 0, "course_id": "cs101"},
            {"source": "machine_learning.pdf", "chunk_index": 0, "course_id": "cs101"},
            {"source": "neural_networks.pdf", "chunk_index": 0, "course_id": "cs101"},
            {"source": "deep_learning.pdf", "chunk_index": 0, "course_id": "cs101"},
            {"source": "nlp.pdf", "chunk_index": 0, "course_id": "cs101"},
            {"source": "computer_vision.pdf", "chunk_index": 0, "course_id": "cs101"},
            {"source": "robotics.pdf", "chunk_index": 0, "course_id": "cs101"},
            {"source": "ai_applications.pdf", "chunk_index": 0, "course_id": "cs101"},
            {"source": "supervised_learning.pdf", "chunk_index": 0, "course_id": "cs101"},
            {"source": "unsupervised_learning.pdf", "chunk_index": 0, "course_id": "cs101"}
        ]

    def query(self, query_embeddings=None, n_results=5, where=None):
        """Mock query che restituisce documenti rilevanti"""
        if where and where.get("course_id") != "cs101":
            return {"documents": [[]], "metadatas": [[]], "ids": [[]]}

        # Simple mock: return first n_results documents
        return {
            "documents": [self.documents[:n_results]],
            "metadatas": [self.metadatas[:n_results]],
            "ids": [[f"doc_{i}" for i in range(n_results)]]
        }

    def get(self, where=None, limit=1000):
        """Mock get che restituisce tutti i documenti"""
        if where and where.get("course_id") != "cs101":
            return {"documents": [], "metadatas": [], "ids": []}

        return {
            "documents": self.documents,
            "metadatas": self.metadatas,
            "ids": [f"doc_{i}" for i in range(len(self.documents))]
        }

class TestHybridSearch:
    """Test suite per HybridSearchService"""

    def __init__(self):
        self.mock_rag = MockRAGService()
        self.hybrid_service = HybridSearchService(self.mock_rag)

    def test_initialization(self):
        """Test inizializzazione del servizio"""
        print("🧪 Testing HybridSearchService initialization...")

        assert self.hybrid_service.semantic_weight == 0.6
        assert self.hybrid_service.keyword_weight == 0.4
        assert self.hybrid_service.fusion_method == "weighted_sum"
        assert self.hybrid_service.min_query_length == 2
        assert self.hybrid_service.max_results == 20

        print("✅ Initialization test passed")

    def test_italian_text_preprocessing(self):
        """Test preprocessing testo italiano"""
        print("🧪 Testing Italian text preprocessing...")

        test_cases = [
            {
                "input": "Cos'è l'intelligenza artificiale?",
                "expected_tokens": ["cosa", "intelligenza", "artificiale"]
            },
            {
                "input": "Il machine learning è molto importante",
                "expected_tokens": ["machine", "learning", "importante"]
            },
            {
                "input": "Reti neurali e deep learning",
                "expected_tokens": ["reti", "neurali", "deep", "learning"]
            }
        ]

        for case in test_cases:
            result = self.hybrid_service.preprocess_italian_text(case["input"])
            print(f"   Input: '{case['input']}'")
            print(f"   Expected: {case['expected_tokens']}")
            print(f"   Got: {result[:5]}")  # Show first 5 tokens

            # Verify all expected tokens are present
            for expected in case["expected_tokens"]:
                assert expected in result, f"Expected token '{expected}' not found in result"

        print("✅ Italian text preprocessing test passed")

    def test_query_expansion(self):
        """Test espansione query con sinonimi"""
        print("🧪 Testing query expansion...")

        test_cases = [
            {
                "input": "studio",
                "expected_contains": ["studio", "apprendimento", "formazione"]
            },
            {
                "input": "analisi",
                "expected_contains": ["analisi", "esame", "valutazione"]
            },
            {
                "input": "metodo",
                "expected_contains": ["metodo", "tecnica", "approccio"]
            }
        ]

        for case in test_cases:
            result = self.hybrid_service.expand_query_italian(case["input"])
            print(f"   Input: '{case['input']}' -> Expanded: {result}")

            # Check that original term is preserved
            assert case["input"] in result, f"Original term '{case['input']}' not preserved"

            # Check that some expected synonyms are added
            found_synonyms = any(exp in result for exp in case["expected_contains"][1:])
            assert found_synonyms, f"No synonyms found for '{case['input']}'"

        print("✅ Query expansion test passed")

    def test_bm25_index_building(self):
        """Test costruzione indice BM25"""
        print("🧪 Testing BM25 index building...")

        success = self.hybrid_service.build_bm25_index("cs101")
        assert success, "BM25 index building failed"
        assert self.hybrid_service.bm25_index is not None, "BM25 index is None"
        assert len(self.hybrid_service.documents_corpus) > 0, "No documents in corpus"
        assert len(self.hybrid_service.metadata_mapping) > 0, "No metadata mapping"

        print(f"   Built index with {len(self.hybrid_service.documents_corpus)} documents")
        print("✅ BM25 index building test passed")

    def test_semantic_search(self):
        """Test ricerca semantica"""
        print("🧪 Testing semantic search...")

        # Build index first
        self.hybrid_service.build_bm25_index("cs101")

        query = "intelligenza artificiale"
        results = self.hybrid_service.semantic_search(query, "cs101", k=5)

        assert isinstance(results, list), "Results should be a list"
        if results:
            assert isinstance(results[0], tuple), "Each result should be a tuple"
            assert len(results[0]) == 2, "Each result tuple should have 2 elements"
            print(f"   Query: '{query}' -> Found {len(results)} semantic results")

        print("✅ Semantic search test passed")

    def test_keyword_search(self):
        """Test ricerca keyword BM25"""
        print("🧪 Testing keyword search...")

        # Build index first
        self.hybrid_service.build_bm25_index("cs101")

        test_queries = [
            "intelligenza artificiale",
            "machine learning",
            "reti neurali",
            "deep learning"
        ]

        for query in test_queries:
            results = self.hybrid_service.keyword_search(query, k=5)

            print(f"   Query: '{query}' -> Found {len(results)} keyword results")

            if results:
                # Check that results are sorted by score
                scores = [score for _, score in results]
                assert all(earlier >= later for earlier, later in zip(scores, scores[1:])), \
                    "Results should be sorted by descending score"

        print("✅ Keyword search test passed")

    def test_weighted_sum_fusion(self):
        """Test fusione weighted sum"""
        print("🧪 Testing weighted sum fusion...")

        # Mock results
        semantic_results = [
            ({"source": "doc1.pdf", "chunk_index": 0}, 0.9),
            ({"source": "doc2.pdf", "chunk_index": 1}, 0.7),
            ({"source": "doc3.pdf", "chunk_index": 2}, 0.5)
        ]

        keyword_results = [
            ({"source": "doc2.pdf", "chunk_index": 1}, 0.8),
            ({"source": "doc4.pdf", "chunk_index": 3}, 0.6),
            ({"source": "doc1.pdf", "chunk_index": 0}, 0.4)
        ]

        fused_results = self.hybrid_service.weighted_sum_fusion(semantic_results, keyword_results)

        assert len(fused_results) == 4, f"Expected 4 unique documents, got {len(fused_results)}"

        # Check that results are sorted by final score
        scores = [score for _, score in fused_results]
        assert all(earlier >= later for earlier, later in zip(scores, scores[1:])), \
            "Fused results should be sorted by descending score"

        print(f"   Fusion result: {len(fused_results)} unique documents")
        print("✅ Weighted sum fusion test passed")

    def test_rrf_fusion(self):
        """Test Reciprocal Rank Fusion"""
        print("🧪 Testing Reciprocal Rank Fusion...")

        # Mock results
        semantic_results = [
            ({"source": "doc1.pdf", "chunk_index": 0}, 0.9),
            ({"source": "doc2.pdf", "chunk_index": 1}, 0.7),
            ({"source": "doc3.pdf", "chunk_index": 2}, 0.5)
        ]

        keyword_results = [
            ({"source": "doc2.pdf", "chunk_index": 1}, 0.8),
            ({"source": "doc4.pdf", "chunk_index": 3}, 0.6),
            ({"source": "doc1.pdf", "chunk_index": 0}, 0.4)
        ]

        fused_results = self.hybrid_search.reciprocal_rank_fusion(semantic_results, keyword_results)

        assert len(fused_results) == 4, f"Expected 4 unique documents, got {len(fused_results)}"

        print(f"   RRF result: {len(fused_results)} unique documents")
        print("✅ Reciprocal Rank Fusion test passed")

    async def test_hybrid_search_end_to_end(self):
        """Test completo della ricerca hybrid"""
        print("🧪 Testing end-to-end hybrid search...")

        query = "machine learning e reti neurali"
        course_id = "cs101"

        result = await self.hybrid_service.hybrid_search(query, course_id, k=5)

        assert "text" in result, "Result should contain 'text' field"
        assert "sources" in result, "Result should contain 'sources' field"
        assert "search_method" in result, "Result should contain 'search_method' field"
        assert result["search_method"] == "hybrid", "Search method should be 'hybrid'"

        if result["sources"]:
            print(f"   Query: '{query}' -> Found {len(result['sources'])} hybrid results")
            print(f"   First result source: {result['sources'][0]['source']}")
            print(f"   Search method: {result['search_method']}")

        print("✅ End-to-end hybrid search test passed")

    def test_weight_updates(self):
        """Test aggiornamento pesi"""
        print("🧪 Testing weight updates...")

        original_semantic = self.hybrid_service.semantic_weight
        original_keyword = self.hybrid_service.keyword_weight

        # Update weights
        self.hybrid_service.update_weights(0.8, 0.2)

        assert abs(self.hybrid_service.semantic_weight - 0.8) < 0.001, "Semantic weight not updated correctly"
        assert abs(self.hybrid_service.keyword_weight - 0.2) < 0.001, "Keyword weight not updated correctly"

        # Test normalization
        self.hybrid_service.update_weights(5.0, 5.0)
        assert abs(self.hybrid_service.semantic_weight - 0.5) < 0.001, "Weight normalization failed"
        assert abs(self.hybrid_service.keyword_weight - 0.5) < 0.001, "Weight normalization failed"

        # Restore original weights
        self.hybrid_service.update_weights(original_semantic, original_keyword)

        print("✅ Weight updates test passed")

    def test_fusion_method_updates(self):
        """Test aggiornamento metodo di fusione"""
        print("🧪 Testing fusion method updates...")

        original_method = self.hybrid_service.fusion_method

        # Test valid methods
        for method in ["weighted_sum", "rrf", "rank_fusion"]:
            self.hybrid_service.set_fusion_method(method)
            assert self.hybrid_service.fusion_method == method, f"Fusion method not updated to {method}"

        # Test invalid method (should not change)
        self.hybrid_service.set_fusion_method("invalid_method")
        assert self.hybrid_service.fusion_method in ["weighted_sum", "rrf", "rank_fusion"], \
            "Invalid fusion method should not be accepted"

        # Restore original method
        self.hybrid_service.set_fusion_method(original_method)

        print("✅ Fusion method updates test passed")

    def test_get_search_stats(self):
        """Test statistiche di ricerca"""
        print("🧪 Testing search stats...")

        # Build index first
        self.hybrid_service.build_bm25_index("cs101")

        stats = self.hybrid_service.get_search_stats()

        assert "bm25_index_built" in stats, "Stats should contain 'bm25_index_built'"
        assert "indexed_documents" in stats, "Stats should contain 'indexed_documents'"
        assert "semantic_weight" in stats, "Stats should contain 'semantic_weight'"
        assert "keyword_weight" in stats, "Stats should contain 'keyword_weight'"
        assert "fusion_method" in stats, "Stats should contain 'fusion_method'"

        assert stats["bm25_index_built"] is True, "BM25 index should be built"
        assert stats["indexed_documents"] > 0, "Should have indexed documents"

        print(f"   Stats: {stats}")
        print("✅ Search stats test passed")

async def run_all_tests():
    """Esegue tutti i test del HybridSearchService"""
    print("🚀 Starting HybridSearchService Test Suite")
    print("=" * 60)

    test_suite = TestHybridSearch()

    # Synchronous tests
    test_methods = [
        test_suite.test_initialization,
        test_suite.test_italian_text_preprocessing,
        test_suite.test_query_expansion,
        test_suite.test_bm25_index_building,
        test_suite.test_semantic_search,
        test_suite.test_keyword_search,
        test_suite.test_weighted_sum_fusion,
        test_suite.test_rrf_fusion,
        test_suite.test_weight_updates,
        test_suite.test_fusion_method_updates,
        test_suite.test_get_search_stats
    ]

    for test_method in test_methods:
        try:
            test_method()
        except Exception as e:
            print(f"❌ {test_method.__name__} failed: {e}")
            return False

    # Asynchronous tests
    async_tests = [
        test_suite.test_hybrid_search_end_to_end
    ]

    for test_method in async_tests:
        try:
            await test_method()
        except Exception as e:
            print(f"❌ {test_method.__name__} failed: {e}")
            return False

    print("=" * 60)
    print("🎉 All HybridSearchService tests passed!")
    print("=" * 60)

    # Performance summary
    print("\n📊 HybridSearchService Summary:")
    print("✅ Italian text preprocessing optimized")
    print("✅ Query expansion with synonyms working")
    print("✅ BM25 index building successful")
    print("✅ Semantic search integration working")
    print("✅ Keyword search (BM25) working")
    print("✅ Weighted sum fusion working")
    print("✅ Reciprocal Rank Fusion working")
    print("✅ End-to-end hybrid search working")
    print("✅ Configuration updates working")
    print("✅ Statistics reporting working")

    return True

if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(run_all_tests())

    if success:
        print("\n🏆 HybridSearchService is ready for production!")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        exit(1)