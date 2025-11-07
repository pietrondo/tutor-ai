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
from services.rag_service import RAGService

logger = structlog.get_logger()

class SimpleBM25:
    """
    Implementazione semplificata di BM25 senza dipendenze esterne
    """

    def __init__(self, corpus: List[List[str]], k1: float = 1.2, b: float = 0.75, epsilon: float = 0.25):
        """
        Inizializza BM25
        k1: parametro di saturation del termine frequency
        b: parametro di normalizzazione della lunghezza del documento
        epsilon: parametro per smoothing IDF
        """
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.corpus = corpus
        self.corpus_size = len(corpus)
        self.avgdl = sum(len(doc) for doc in corpus) / self.corpus_size if self.corpus_size > 0 else 0

        # Calcola IDF scores
        self.idf = {}
        self._build_idf()

    def _build_idf(self):
        """Calcola Inverse Document Frequency scores"""
        # Conta document frequency per ogni termine
        df = Counter()
        for doc in self.corpus:
            unique_terms = set(doc)
            df.update(unique_terms)

        # Calcola IDF scores
        for term in df:
            idf = math.log((self.corpus_size - df[term] + 0.5) / (df[term] + 0.5))
            self.idf[term] = idf

        # Applica epsilon smoothing per termini non visti
        max_idf = max(self.idf.values()) if self.idf else 0.0
        self.idf["<UNK>"] = math.log(self.corpus_size + 1) - max_idf - self.epsilon

    def get_scores(self, query: List[str]) -> List[float]:
        """
        Calcola BM25 scores per la query contro tutti i documenti
        """
        scores = []

        for i, doc in enumerate(self.corpus):
            score = 0.0
            doc_len = len(doc)

            for term in query:
                if term in doc:
                    # Term frequency in document
                    tf = doc.count(term)
                    # IDF del termine
                    idf = self.idf.get(term, self.idf["<UNK>"])
                    # BM25 formula
                    score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl))

            scores.append(score)

        return scores

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

        # Cache service (lazy loading)
        self.cache_service = None

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
            self.bm25_index = SimpleBM25(
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

    def _init_cache_service(self):
        """Inizializza il servizio di cache"""
        if self.cache_service is None:
            try:
                from services.cache_service import RedisCacheService
                self.cache_service = RedisCacheService()
                logger.info("HybridSearch cache service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize HybridSearch cache service: {e}")
                self.cache_service = None

    def _generate_hybrid_cache_key(self, query: str, course_id: str, book_id: Optional[str] = None,
                                 k: int = 10, semantic_weight: float = 0.6, keyword_weight: float = 0.4,
                                 fusion_method: str = "weighted_sum") -> str:
        """
        Genera cache key per risultati hybrid search
        """
        import hashlib
        key_components = [
            f"hybrid:{hashlib.md5(query.encode()).hexdigest()[:16]}",
            f"course:{course_id}",
            f"k:{k}",
            f"weights:{semantic_weight}:{keyword_weight}",
            f"fusion:{fusion_method}"
        ]

        if book_id:
            key_components.append(f"book:{book_id}")

        return ":".join(key_components)

    async def keyword_search_cached(self, query: str, k: int = 10) -> List[Tuple[Dict, float]]:
        """
        Esegue ricerca keyword BM25 con cache
        """
        try:
            self._init_cache_service()

            if self.cache_service:
                cache_key = f"bm25:{hashlib.md5(query.encode()).hexdigest()[:16]}:k:{k}"

                # Tenta cache
                from services.cache_service import CacheType
                cached_result = await self.cache_service.get(CacheType.HYBRAR_SEARCH, cache_key)

                if cached_result is not None:
                    logger.debug("BM25 cache hit", query=query[:30])
                    return cached_result

            # Cache miss - esegui ricerca
            result = self.keyword_search(query, k)

            # Salva in cache
            if self.cache_service and result:
                await self.cache_service.set(CacheType.HYBRAR_SEARCH, cache_key, result, ttl=1800)  # 30 min
                logger.debug("BM25 result cached", query=query[:30])

            return result

        except Exception as e:
            logger.error(f"Error in cached keyword search: {e}")
            # Fallback a ricerca diretta
            return self.keyword_search(query, k)

    async def semantic_search_cached(self, query: str, course_id: str, book_id: Optional[str] = None,
                                  k: int = 10) -> List[Tuple[Dict, float]]:
        """
        Esegue ricerca semantica con cache
        """
        try:
            self._init_cache_service()

            if self.cache_service:
                cache_key = self._generate_hybrid_cache_key(
                    query, course_id, book_id, k, self.semantic_weight, self.keyword_weight, self.fusion_method
                )

                # Tenta cache
                from services.cache_service import CacheType
                cached_result = await self.cache_service.get(CacheType.HYBRAR_SEARCH, cache_key)

                if cached_result is not None:
                    logger.debug("Semantic search cache hit", query=query[:30])
                    return cached_result

            # Cache miss - esegui ricerca
            result = self.semantic_search(query, course_id, book_id, k)

            # Salva in cache
            if self.cache_service and result:
                await self.cache_service.set(CacheType.HYBRAR_SEARCH, cache_key, result, ttl=1800)  # 30 min
                logger.debug("Semantic search result cached", query=query[:30])

            return result

        except Exception as e:
            logger.error(f"Error in cached semantic search: {e}")
            # Fallback a ricerca diretta
            return self.semantic_search(query, course_id, book_id, k)

    async def hybrid_search_cached(self, query: str, course_id: str, book_id: Optional[str] = None,
                                 k: int = 10, semantic_weight: Optional[float] = None,
                                 keyword_weight: Optional[float] = None,
                                 fusion_method: Optional[str] = None) -> Dict[str, Any]:
        """
        Esegue ricerca hybrid con cache layer completo
        """
        try:
            # Use provided weights or defaults
            sem_weight = semantic_weight or self.semantic_weight
            key_weight = keyword_weight or self.keyword_weight
            fusion_meth = fusion_method or self.fusion_method

            # Genera cache key completo
            if self.cache_service:
                cache_key = self._generate_hybrid_cache_key(
                    query, course_id, book_id, k, sem_weight, key_weight, fusion_meth
                )

                # Tenta cache completo
                from services.cache_service import CacheType
                cached_result = await self.cache_service.get(CacheType.HYBRAR_SEARCH, cache_key)

                if cached_result is not None:
                    logger.info("Hybrid search cache hit", query=query[:30], cache_key=cache_key[:32])
                    cached_result["cached"] = True
                    return cached_result

            # Cache miss - esegui ricerca completa con caching intermedio
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Esegue ricerche con caching
                semantic_future = executor.submit(
                    lambda: asyncio.run(self.semantic_search_cached(query, course_id, book_id, k * 2))
                )
                keyword_future = executor.submit(
                    lambda: asyncio.run(self.keyword_search_cached(query, k * 2))
                )

                semantic_results = semantic_future.result()
                keyword_results = keyword_future.result()

            # Fusion dei risultati
            if fusion_meth == "rrf":
                hybrid_results = self.reciprocal_rank_fusion(semantic_results, keyword_results)
            else:  # weighted_sum
                hybrid_results = self.weighted_sum_fusion(semantic_results, keyword_results)

            # Prepara risultato finale
            final_result = await self._prepare_hybrid_search_result(
                query, course_id, book_id, hybrid_results[:k], semantic_results, keyword_results
            )

            # Salva in cache
            if self.cache_service and final_result.get("text"):
                await self.cache_service.set(CacheType.HYBRAR_SEARCH, cache_key, final_result, ttl=1800)  # 30 min
                logger.info("Hybrid search result cached", query=query[:30], cache_key=cache_key[:32])

            final_result["cached"] = False
            return final_result

        except Exception as e:
            logger.error(f"Error in cached hybrid search: {e}")
            # Fallback a metodo tradizionale
            return await self.hybrid_search(query, course_id, book_id, k)

    async def _prepare_hybrid_search_result(self, query: str, course_id: str, book_id: Optional[str],
                                          hybrid_results: List[Tuple[Dict, float]],
                                          semantic_results: List[Tuple[Dict, float]],
                                          keyword_results: List[Tuple[Dict, float]]) -> Dict[str, Any]:
        """
        Prepara il risultato finale della ricerca hybrid
        """
        context_texts = []
        sources = []

        # Recupera i documenti originali
        if hybrid_results:
            doc_ids = []
            for metadata, score in hybrid_results:
                doc_id = metadata.get('source', '') + str(metadata.get('chunk_index', ''))
                doc_ids.append(doc_id)

            if doc_ids:
                try:
                    original_results = self.rag_service.collection.get(
                        where={"course_id": course_id, **({"book_id": book_id} if book_id else {})},
                        limit=1000
                    )

                    for metadata, score in hybrid_results:
                        for i, (orig_doc, orig_metadata) in enumerate(zip(original_results['documents'], original_results['metadatas'])):
                            if (orig_metadata.get('source') == metadata.get('source') and
                                orig_metadata.get('chunk_index') == metadata.get('chunk_index')):
                                context_texts.append(orig_doc)
                                sources.append({
                                    "source": metadata.get('source', 'Unknown'),
                                    "chunk_index": metadata.get('chunk_index', 0),
                                    "relevance_score": score,
                                    "search_type": "hybrid",
                                    "hybrid_components": {
                                        "semantic_available": any(orig_metadata.get('source') == metadata.get('source') and
                                                             orig_metadata.get('chunk_index') == metadata.get('chunk_index')
                                                             for metadata, _ in semantic_results),
                                        "keyword_available": any(orig_metadata.get('source') == metadata.get('source') and
                                                             orig_metadata.get('chunk_index') == metadata.get('chunk_index')
                                                             for metadata, _ in keyword_results)
                                    }
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
            "fusion_method": self.fusion_method,
            "cache_enabled": self.cache_service is not None
        }

    def get_search_stats(self) -> Dict[str, Any]:
        """
        Restituisce statistiche sul sistema di ricerca
        """
        base_stats = {
            "bm25_index_built": self.bm25_index is not None,
            "indexed_documents": len(self.documents_corpus),
            "semantic_weight": self.semantic_weight,
            "keyword_weight": self.keyword_weight,
            "fusion_method": self.fusion_method,
            "cache_enabled": self.cache_service is not None
        }

        # Add cache stats if available
        if self.cache_service:
            cache_stats = self.cache_service.get_metrics()
            base_stats["cache_metrics"] = cache_stats

        return base_stats

    async def invalidate_hybrid_cache(self, course_id: str, book_id: Optional[str] = None):
        """
        Invalida cache hybrid per corso specifico
        """
        try:
            self._init_cache_service()

            if self.cache_service:
                # Pattern per invalidazione cache hybrid
                pattern = f"tutor_ai:hybrid_search:*:course:{course_id}:*"
                if book_id:
                    pattern = f"tutor_ai:hybrid_search:*:course:{course_id}:*:book:{book_id}:*"

                # Includi anche BM25 cache
                bm25_pattern = "tutor_ai:hybrid_search:bm25:*"

                # Esegui invalidazione
                await self.cache_service.invalidate_by_pattern(pattern)
                await self.cache_service.invalidate_by_pattern(bm25_pattern)

                logger.info("Invalidated hybrid search cache", course_id=course_id, book_id=book_id)

        except Exception as e:
            logger.error(f"Error invalidating hybrid search cache: {e}")