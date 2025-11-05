"""
Hybrid Search Service - Combina Semantic Search con Keyword Search (BM25)
Implementazione ottimizzata per testo accademico italiano
"""

import math
import re
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict
import structlog
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from rank_bm25 import BM25Okapi
from services.rag_service import RAGService

logger = structlog.get_logger()

class HybridSearchService:
    """
    Servizio di Hybrid Search che combina:
    1. Semantic Search (ChromaDB + SentenceTransformer)
    2. Keyword Search (BM25)
    3. Fusion Ranking con pesi configurabili
    """

    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service
        self.bm25_index = None
        self.documents_corpus = []
        self.metadata_mapping = []

        # Configurazione pesi per hybrid search (ottimizzati per italiano)
        self.semantic_weight = 0.6  # Peso ricerca semantica
        self.keyword_weight = 0.4   # Peso ricerca keyword

        # Configurazioni per italiano
        self.min_query_length = 2
        self.max_results = 20
        self.fusion_method = "weighted_sum"  # weighted_sum, rrf, rank_fusion

        logger.info("HybridSearchService initialized",
                   semantic_weight=self.semantic_weight,
                   keyword_weight=self.keyword_weight,
                   fusion_method=self.fusion_method)

    def preprocess_italian_text(self, text: str) -> List[str]:
        """
        Preprocessing specifico per testo italiano ottimizzato per BM25
        """
        # Normalizzazione testo italiano
        text = text.lower()

        # Mantieni caratteri accentati ma normalizza varianti
        accent_mapping = {
            'á': 'à', 'â': 'à', 'ä': 'à',
            'é': 'è', 'ê': 'è', 'ë': 'è',
            'í': 'ì', 'î': 'ì', 'ï': 'ì',
            'ó': 'ò', 'ô': 'ò', 'ö': 'ò',
            'ú': 'ù', 'û': 'ù', 'ü': 'ù'
        }

        for old, new in accent_mapping.items():
            text = text.replace(old, new)

        # Rimuovi punteggiatura ma mantieni apostrofi (importante per italiano)
        text = re.sub(r'[^\w\sàèéìòùç]', ' ', text)

        # Tokenizzazione
        tokens = text.split()

        # Filtra stop words italiane personalizzate per ambito accademico
        italian_stopwords = {
            'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una', 'del', 'dello', 'della',
            'dei', 'degli', 'delle', 'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra',
            'e', 'ed', 'o', 'ma', 'se', 'anche', 'che', 'chi', 'cui', 'come', 'dove', 'quando',
            'quanto', 'quella', 'quello', 'quelli', 'quelle', 'questo', 'questa', 'questi',
            'queste', 'quale', 'quali', 'quindi', 'poi', 'ancora', 'altro', 'altri', 'altre',
            'tutti', 'tutte', 'tutto', 'ciascuno', 'ciascuna', 'ogni', 'alcuni', 'alcune',
            'nessuno', 'nessuna', 'più', 'meno', 'molto', 'molta', 'molti', 'molte',
            'poco', 'poca', 'pochi', 'poche', 'quasi', 'solo', 'proprio', 'cioè', 'ovvero',
            # Stop words accademiche comuni
            'secondo', 'seconda', 'secondi', 'seconde', 'secondo', 'ai', 'allo', 'alla',
            'agli', 'alle', 'dal', 'dallo', 'dalla', 'dai', 'dagli', 'dalle', 'nel', 'nello',
            'nella', 'nei', 'negli', 'nelle', 'sul', 'sullo', 'sulla', 'sui', 'sugli', 'sulle'
        }

        # Filtra tokens e mantieni solo quelli significativi
        filtered_tokens = []
        for token in tokens:
            if (len(token) >= self.min_query_length and
                token not in italian_stopwords and
                not token.isdigit() and
                not re.match(r'^[^\w\sàèéìòùç]+$', token)):
                filtered_tokens.append(token)

        return filtered_tokens

    def expand_query_italian(self, query: str) -> List[str]:
        """
        Espansione query con sinonimi e termini accademici italiani
        """
        # Sinonimi e termini correlati per ambito accademico italiano
        synonyms_map = {
            'studio': ['apprendimento', 'apprendistato', 'formazione', 'educazione'],
            'analisi': ['esame', 'valutazione', 'studio', 'indagine'],
            'metodo': ['tecnica', 'procedura', 'approccio', 'modalità'],
            'teoria': ['concetto', 'principio', 'dottrina', 'modello'],
            'pratica': ['applicazione', 'esercizio', 'esperienza', 'esecuzione'],
            'ricerca': ['indagine', 'studio', 'analisi', 'esplorazione'],
            'sistema': ['struttura', 'organizzazione', 'schema', 'meccanismo'],
            'processo': ['procedimento', 'ciclo', 'fase', 'sviluppo'],
            'problema': ['questione', 'difficoltà', 'sfida', 'ostacolo'],
            'soluzione': ['risposta', 'rimedio', 'strategia', 'intervento'],
            'definizione': ['significato', 'concetto', 'spiegazione', 'descrizione'],
            'esempio': ['caso', 'istanza', 'campione', 'modello'],
            'risultato': ['esito', 'conseguenza', 'effetto', 'product'],
            'dati': ['informazioni', 'elementi', 'valori', 'cifre'],
            'informazione': ['dato', 'notizia', 'messaggio', 'comunicazione']
        }

        # Preprocessing query
        query_tokens = self.preprocess_italian_text(query)
        expanded_tokens = list(query_tokens)

        # Aggiungi sinonimi
        for token in query_tokens:
            if token in synonyms_map:
                expanded_tokens.extend(synonyms_map[token])

        # Rimuovi duplicati ma mantieni ordine originale
        seen = set()
        final_tokens = []
        for token in expanded_tokens:
            if token not in seen:
                seen.add(token)
                final_tokens.append(token)

        return final_tokens

    def build_bm25_index(self, course_id: str, book_id: Optional[str] = None) -> bool:
        """
        Costruisce l'indice BM25 per i documenti di un corso
        """
        try:
            logger.info(f"Building BM25 index for course {course_id}")

            # Recupera tutti i documenti del corso
            results = self.rag_service.collection.get(
                where={"course_id": course_id, **({"book_id": book_id} if book_id else {})},
                limit=10000
            )

            if not results['documents']:
                logger.warning(f"No documents found for course {course_id}")
                return False

            # Preprocessa tutti i documenti per BM25
            self.documents_corpus = []
            self.metadata_mapping = []

            for doc, metadata in zip(results['documents'], results['metadatas']):
                # Preprocessing specifico per BM25
                tokens = self.preprocess_italian_text(doc)
                if tokens:  # Solo documenti con contenuti significativi
                    self.documents_corpus.append(tokens)
                    self.metadata_mapping.append(metadata)

            if not self.documents_corpus:
                logger.warning(f"No valid documents after preprocessing for course {course_id}")
                return False

            # Crea indice BM25 con parametri ottimizzati per italiano
            self.bm25_index = BM25Okapi(
                self.documents_corpus,
                k1=1.2,  # Parametri ottimizzati per testo italiano
                b=0.75,
                epsilon=0.25
            )

            logger.info(f"BM25 index built successfully with {len(self.documents_corpus)} documents")
            return True

        except Exception as e:
            logger.error(f"Error building BM25 index: {e}")
            return False

    def semantic_search(self, query: str, course_id: str, book_id: Optional[str] = None, k: int = 10) -> List[Tuple[Dict, float]]:
        """
        Esegue ricerca semantica usando ChromaDB
        """
        try:
            results = self.rag_service.collection.query(
                query_embeddings=self.rag_service.embedding_model.encode([query]).tolist(),
                n_results=k,
                where={"course_id": course_id, **({"book_id": book_id} if book_id else {})}
            )

            semantic_results = []
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                # Calcola score semantico normalizzato (inverso della distanza)
                semantic_score = 1.0 - (i * 0.1)  # Semplice normalizzazione
                semantic_results.append((metadata, semantic_score))

            return semantic_results

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    def keyword_search(self, query: str, k: int = 10) -> List[Tuple[Dict, float]]:
        """
        Esegue ricerca keyword usando BM25
        """
        try:
            if not self.bm25_index:
                logger.warning("BM25 index not built")
                return []

            # Espandi query per migliori risultati in italiano
            expanded_query = self.expand_query_italian(query)

            # Esegue ricerca BM25
            bm25_scores = self.bm25_index.get_scores(expanded_query)

            # Normalizza scores e crea risultati
            keyword_results = []
            max_score = max(bm25_scores) if max(bm25_scores) > 0 else 1

            for idx, score in enumerate(bm25_scores):
                if score > 0 and idx < len(self.metadata_mapping):
                    normalized_score = score / max_score
                    keyword_results.append((self.metadata_mapping[idx], normalized_score))

            # Ordina per score e prendi top k
            keyword_results.sort(key=lambda x: x[1], reverse=True)
            return keyword_results[:k]

        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []

    def reciprocal_rank_fusion(self, semantic_results: List[Tuple[Dict, float]],
                             keyword_results: List[Tuple[Dict, float]], k: int = 60) -> List[Tuple[Dict, float]]:
        """
        Reciprocal Rank Fusion (RRF) per combinare risultati
        """
        fused_results = defaultdict(float)

        # Aggiungi risultati semantici
        for rank, (metadata, score) in enumerate(semantic_results):
            doc_id = metadata.get('source', '') + str(metadata.get('chunk_index', ''))
            fused_results[doc_id] += 1.0 / (k + rank + 1)

        # Aggiungi risultati keyword
        for rank, (metadata, score) in enumerate(keyword_results):
            doc_id = metadata.get('source', '') + str(metadata.get('chunk_index', ''))
            fused_results[doc_id] += 1.0 / (k + rank + 1)

        # Converti in lista di risultati
        final_results = []
        for doc_id, rrf_score in fused_results.items():
            # Trova i metadati corrispondenti
            for metadata, _ in semantic_results + keyword_results:
                current_id = metadata.get('source', '') + str(metadata.get('chunk_index', ''))
                if current_id == doc_id:
                    final_results.append((metadata, rrf_score))
                    break

        # Ordina per RRF score
        final_results.sort(key=lambda x: x[1], reverse=True)
        return final_results

    def weighted_sum_fusion(self, semantic_results: List[Tuple[Dict, float]],
                           keyword_results: List[Tuple[Dict, float]]) -> List[Tuple[Dict, float]]:
        """
        Weighted Sum Fusion per combinare risultati
        """
        # Crea mappa per unione risultati
        results_map = {}

        # Aggiungi risultati semantici
        for metadata, semantic_score in semantic_results:
            doc_id = metadata.get('source', '') + str(metadata.get('chunk_index', ''))
            results_map[doc_id] = {
                'metadata': metadata,
                'semantic_score': semantic_score,
                'keyword_score': 0.0
            }

        # Aggiungi/aggiorna risultati keyword
        for metadata, keyword_score in keyword_results:
            doc_id = metadata.get('source', '') + str(metadata.get('chunk_index', ''))
            if doc_id in results_map:
                results_map[doc_id]['keyword_score'] = keyword_score
            else:
                results_map[doc_id] = {
                    'metadata': metadata,
                    'semantic_score': 0.0,
                    'keyword_score': keyword_score
                }

        # Calcola score finale e crea risultati
        final_results = []
        for doc_id, data in results_map.items():
            final_score = (
                self.semantic_weight * data['semantic_score'] +
                self.keyword_weight * data['keyword_score']
            )
            final_results.append((data['metadata'], final_score))

        # Ordina per score finale
        final_results.sort(key=lambda x: x[1], reverse=True)
        return final_results

    async def hybrid_search(self, query: str, course_id: str, book_id: Optional[str] = None,
                          k: int = 10) -> Dict[str, Any]:
        """
        Esegue ricerca hybrid combinando semantic e keyword search
        """
        try:
            # Verifica che l'indice BM25 sia costruito
            if not self.bm25_index:
                if not self.build_bm25_index(course_id, book_id):
                    # Fallback a solo semantic search
                    logger.warning("BM25 index failed, falling back to semantic search only")
                    return await self.rag_service.retrieve_context(query, course_id, book_id, k)

            logger.info(f"Executing hybrid search for query: '{query}'")

            # Esegue entrambe le ricerche in parallelo
            with ThreadPoolExecutor(max_workers=2) as executor:
                semantic_future = executor.submit(
                    self.semantic_search, query, course_id, book_id, k * 2
                )
                keyword_future = executor.submit(
                    self.keyword_search, query, k * 2
                )

                semantic_results = semantic_future.result()
                keyword_results = keyword_future.result()

            # Fusion dei risultati
            if self.fusion_method == "rrf":
                hybrid_results = self.reciprocal_rank_fusion(semantic_results, keyword_results)
            else:  # weighted_sum
                hybrid_results = self.weighted_sum_fusion(semantic_results, keyword_results)

            # Prendi top k risultati
            final_results = hybrid_results[:k]

            # Formatta risultati come retrieve_context
            context_texts = []
            sources = []

            # Recupera i documenti originali
            doc_ids = []
            for metadata, score in final_results:
                doc_id = metadata.get('source', '') + str(metadata.get('chunk_index', ''))
                doc_ids.append(doc_id)

            if doc_ids:
                try:
                    original_results = self.rag_service.collection.get(
                        where={"course_id": course_id, **({"book_id": book_id} if book_id else {})},
                        limit=1000
                    )

                    for metadata, score in final_results:
                        for i, (orig_doc, orig_metadata) in enumerate(zip(original_results['documents'], original_results['metadatas'])):
                            if (orig_metadata.get('source') == metadata.get('source') and
                                orig_metadata.get('chunk_index') == metadata.get('chunk_index')):
                                context_texts.append(orig_doc)
                                sources.append({
                                    "source": metadata.get('source', 'Unknown'),
                                    "chunk_index": metadata.get('chunk_index', 0),
                                    "relevance_score": score,
                                    "search_type": "hybrid"
                                })
                                break
                except Exception as e:
                    logger.error(f"Error retrieving original documents: {e}")

            if not context_texts:
                return {
                    "text": "",
                    "sources": [],
                    "message": "Nessun documento rilevante trovato per questa ricerca hybrid."
                }

            context_text = "\n\n".join(context_texts)

            return {
                "text": context_text,
                "sources": sources,
                "query": query,
                "course_id": course_id,
                "search_method": "hybrid",
                "semantic_count": len(semantic_results),
                "keyword_count": len(keyword_results),
                "fusion_method": self.fusion_method
            }

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fallback a semantic search tradizionale
            return await self.rag_service.retrieve_context(query, course_id, book_id, k)

    def update_weights(self, semantic_weight: float, keyword_weight: float):
        """
        Aggiorna i pesi per la fusione
        """
        total = semantic_weight + keyword_weight
        if total > 0:
            self.semantic_weight = semantic_weight / total
            self.keyword_weight = keyword_weight / total
            logger.info(f"Updated weights: semantic={self.semantic_weight:.2f}, keyword={self.keyword_weight:.2f}")

    def set_fusion_method(self, method: str):
        """
        Imposta il metodo di fusione
        """
        if method in ["weighted_sum", "rrf", "rank_fusion"]:
            self.fusion_method = method
            logger.info(f"Fusion method set to: {method}")
        else:
            logger.warning(f"Invalid fusion method: {method}")

    def get_search_stats(self) -> Dict[str, Any]:
        """
        Restituisce statistiche sul sistema di ricerca
        """
        return {
            "bm25_index_built": self.bm25_index is not None,
            "indexed_documents": len(self.documents_corpus),
            "semantic_weight": self.semantic_weight,
            "keyword_weight": self.keyword_weight,
            "fusion_method": self.fusion_method
        }