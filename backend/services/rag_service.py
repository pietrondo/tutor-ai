import chromadb
import os
import torch
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import PyPDF2
import fitz  # PyMuPDF
import pdfplumber
from io import BytesIO
import uuid
import json
import structlog
from pathlib import Path
import hashlib

logger = structlog.get_logger()

class RAGService:
    def __init__(self):
        # Lazy loading - non caricare il modello all'avvio
        self.embedding_model = None
        # Miglior modello multilingua 2025 per italiano
        self.model_name = 'intfloat/multilingual-e5-large'
        # Configurazioni ottimizzate per l'italiano
        self.chunk_size = 800  # Token 512-1024 ottimali per italiano
        self.chunk_overlap = 0.25  # 25% overlap per coerenza semantica
        self.max_chunk_length = 1024  # Massimo token per chunk

        self.chroma_client = chromadb.PersistentClient(path="data/vector_db")
        self.collection = None
        self.setup_collection()

        # Inizializza HybridSearchService
        self.hybrid_search = None

        # Inizializza Cache Service (lazy loading)
        self.cache_service = None

        logger.info("RAG Service initialized with Italian-optimized settings",
                   model=self.model_name,
                   chunk_size=self.chunk_size,
                   overlap=self.chunk_overlap)

    def _build_where_filter(self, course_id: str, book_id: Optional[str] = None) -> Dict[str, Any]:
        """Build a ChromaDB where filter that is compatible with newer query semantics."""
        conditions: List[Dict[str, Any]] = [{"course_id": course_id}]
        if book_id:
            conditions.append({"book_id": book_id})

        if len(conditions) == 1:
            return conditions[0]

        return {"$and": conditions}

    def _load_embedding_model(self):
        """Carica il modello di embedding solo quando necessario"""
        if self.embedding_model is None:
            logger.info("Loading embedding model...")
            try:
                # Detecta automaticamente GPU/CUDA
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                logger.info(f"Using device: {device}")

                if torch.cuda.is_available():
                    logger.info(f"CUDA device: {torch.cuda.get_device_name()}")
                    logger.info(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")

                self.embedding_model = SentenceTransformer(self.model_name, device=device)
                logger.info("Embedding model loaded successfully", device=device)
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise

    def setup_collection(self):
        """Setup or get the ChromaDB collection"""
        try:
            self.collection = self.chroma_client.get_collection("course_materials")
        except Exception:
            self.collection = self.chroma_client.create_collection(
                name="course_materials",
                metadata={"hnsw:space": "cosine"}
            )

    async def index_pdf(self, file_path: str, course_id: str, book_id: Optional[str] = None):
        """Extract text from PDF and index it in the vector database"""
        try:
            # Extract text from PDF
            text_content = self.extract_text_from_pdf(file_path)

            if not text_content.strip():
                raise ValueError("No text content found in PDF")

            # Split text into chunks
            chunks = self.split_text_into_chunks(text_content)

            # Generate embeddings and store in ChromaDB
            documents = []
            metadatas = []
            ids = []

            for i, chunk in enumerate(chunks):
                doc_id = f"{course_id}_{book_id if book_id else 'general'}_{uuid.uuid4().hex[:8]}_{i}"
                documents.append(chunk)
                metadata = {
                    "course_id": course_id,
                    "source": os.path.basename(file_path),
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
                if book_id:
                    metadata["book_id"] = book_id
                metadatas.append(metadata)
                ids.append(doc_id)

            # Generate embeddings
            self._load_embedding_model()
            embeddings = self.embedding_model.encode(documents).tolist()

            # Add to ChromaDB
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )

            print(f"Successfully indexed {len(chunks)} chunks from {file_path}")

        except Exception as e:
            print(f"Error indexing PDF: {e}")
            raise e

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyMuPDF (more reliable than PyPDF2)"""
        try:
            doc = fitz.open(file_path)
            text = ""

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()

            doc.close()
            return text

        except Exception as e:
            print(f"Error extracting text with PyMuPDF: {e}")
            # Fallback to PyPDF2
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                return text
            except Exception as e2:
                print(f"Error extracting text with PyPDF2: {e2}")
                raise Exception("Could not extract text from PDF")

    def analyze_pdf_structure(self, file_path: str) -> Dict[str, Any]:
        """Analyze PDF structure to extract chapters, sections and hierarchical content"""
        try:
            doc = fitz.open(file_path)

            # Extract table of contents if available
            toc = doc.get_toc()
            chapters = []

            if toc:
                # Process table of contents
                for level, title, page_num in toc:
                    if level <= 2:  # Chapters and main sections
                        chapters.append({
                            'level': level,
                            'title': title.strip(),
                            'page': page_num,
                            'type': 'chapter' if level == 1 else 'section'
                        })
            else:
                # No TOC available - try to detect chapters from text patterns
                full_text = ""
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    full_text += page.get_text() + f"\n--- PAGE {page_num + 1} ---\n"

                # Common chapter patterns in Italian textbooks
                chapter_patterns = [
                    r'Capitolo\s+(\d+)\s*[:\-\.]\s*(.+)',
                    r'CAP\.?\s*(\d+)\s*[:\-\.]\s*(.+)',
                    r'(\d+)\.\s*([A-Z][^.]+)',
                    r'Lezione\s+(\d+)\s*[:\-\.]\s*(.+)',
                    r'Modulo\s+(\d+)\s*[:\-\.]\s*(.+)',
                    r'Unità\s+(\d+)\s*[:\-\.]\s*(.+)'
                ]

                import re
                for pattern in chapter_patterns:
                    matches = re.finditer(pattern, full_text, re.IGNORECASE)
                    for match in matches:
                        if len(match.groups()) == 2:
                            chapter_num, chapter_title = match.groups()
                            # Find page number for this chapter
                            chapter_start = match.start()
                            page_match = re.search(r'--- PAGE (\d+) ---', full_text[chapter_start:chapter_start + 200])
                            page_num = int(page_match.group(1)) if page_match else 1

                            chapters.append({
                                'level': 1,
                                'title': f"Capitolo {chapter_num.strip()}: {chapter_title.strip()}",
                                'page': page_num,
                                'type': 'chapter'
                            })
                        elif len(match.groups()) == 1:
                            chapter_title = match.group(1)
                            chapter_start = match.start()
                            page_match = re.search(r'--- PAGE (\d+) ---', full_text[chapter_start:chapter_start + 200])
                            page_num = int(page_match.group(1)) if page_match else 1

                            chapters.append({
                                'level': 1,
                                'title': chapter_title.strip(),
                                'page': page_num,
                                'type': 'chapter'
                            })

                # Remove duplicates and sort by page
                chapters = list({(ch['page'], ch['title']): ch for ch in chapters}.values())
                chapters.sort(key=lambda x: x['page'])

            # Extract content for each chapter
            chapter_contents = []
            for i, chapter in enumerate(chapters):
                start_page = chapter['page'] - 1  # 0-based indexing
                end_page = chapters[i + 1]['page'] - 1 if i + 1 < len(chapters) else len(doc)

                chapter_text = ""
                for page_num in range(start_page, end_page):
                    try:
                        page = doc.load_page(page_num)
                        chapter_text += page.get_text() + "\n"
                    except:
                        continue

                # Extract key topics from chapter content
                topics = self._extract_topics_from_text(chapter_text)

                chapter_contents.append({
                    'chapter_number': i + 1,
                    'title': chapter['title'],
                    'page_start': start_page + 1,
                    'page_end': end_page,
                    'content': chapter_text[:2000],  # Limit for processing
                    'topics': topics,
                    'estimated_reading_time': len(chapter_text.split()) // 200  # ~200 words per minute
                })

            doc.close()

            return {
                'chapters': chapter_contents,
                'total_chapters': len(chapters),
                'has_toc': bool(toc),
                'structure_detected': len(chapters) > 0
            }

        except Exception as e:
            logger.error(f"Error analyzing PDF structure: {e}")
            # Return empty structure if analysis fails
            return {
                'chapters': [],
                'total_chapters': 0,
                'has_toc': False,
                'structure_detected': False
            }

    def _extract_topics_from_text(self, text: str) -> List[str]:
        """Extract key topics and concepts from text using pattern matching"""
        topics = []

        # Common academic patterns in Italian
        topic_patterns = [
            r'\b([A-Z][a-z]+(?:zione|mento|ità|ismo|tà|e)\b)',  # Words ending in common suffixes
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:zione|mento))\b',  # Two-word concepts
            r'\b\d+\.\s*([A-Z][^.]+)',  # Numbered items
            r'\b•\s*([A-Z][^.]+)',  # Bullet points (if present)
        ]

        import re
        for pattern in topic_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, str) and len(match) > 3 and len(match) < 50:
                    topics.append(match)

        # Remove duplicates and limit
        topics = list(set(topics))[:10]  # Max 10 topics per chapter
        return topics

    def split_text_into_chunks(self, text: str, chunk_size: int = None, overlap_ratio: float = None) -> List[str]:
        """Split text into overlapping chunks optimized for Italian text"""
        # Usa le configurazioni predefinite se non specificate
        if chunk_size is None:
            chunk_size = self.chunk_size
        if overlap_ratio is None:
            overlap_ratio = self.chunk_overlap

        overlap = int(chunk_size * overlap_ratio)

        # Preprocessing per testo italiano: mantieni accenti e caratteri speciali
        # Rimuovi solo artefatti tipici dei PDF
        cleaned_text = self.clean_italian_text(text)

        if len(cleaned_text) <= chunk_size:
            return [cleaned_text]

        chunks = []
        start = 0

        while start < len(cleaned_text):
            end = start + chunk_size

            if end >= len(cleaned_text):
                chunks.append(cleaned_text[start:])
                break

            # Punti di interruzione ottimali per italiano (prioritizzati)
            chunk = cleaned_text[start:end]

            # Cerca punti di interruzione in ordine di priorità per italiano
            last_period = chunk.rfind('.')  # Punteggiatura forte
            last_semicolon = chunk.rfind(';')  # Punteggiatura media
            last_colon = chunk.rfind(':')  # Punteggiatura media
            last_newline = chunk.rfind('\n')  # Nuova riga
            last_comma = chunk.rfind(',')  # Punteggiatura leggera (solo se necessario)
            last_space = chunk.rfind(' ')  # Ultima risorsa

            # Scegli il miglior punto di interruzione
            for break_point in [last_period, last_semicolon, last_colon, last_newline]:
                if break_point > start + chunk_size // 3:  # Non tornare indietro troppo
                    end = start + break_point + 1
                    break
            else:
                # Se nessun punto forte funziona, prova la virgola
                if last_comma > start + chunk_size // 4:
                    end = start + last_comma + 1
                else:
                    # Ultima risorsa: usa lo spazio
                    if last_space > start + chunk_size // 2:
                        end = start + last_space

            chunks.append(cleaned_text[start:end])
            start = end - overlap

        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def clean_italian_text(self, text: str) -> str:
        """Preprocessing specifico per testi italiani"""
        import re

        # Rimuovi artefatti PDF comuni ma mantieni caratteri italiani
        cleaned = text

        # Rimuovi caratteri di controllo e artefatti PDF
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned)

        # Rimuovi spazi multipli e newlines eccessivi
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Mantieni accenti e caratteri speciali italiani (à, è, é, ì, ò, ù, ecc.)
        # Non rimuovere questi caratteri sono importanti per l'italiano

        # Rimuovi solo artefatti grafici tipici dei PDF
        cleaned = re.sub(r'[^\w\s\.,;:!?\'"àèéìòùÀÈÉÌÒÙçÇäöüÄÖÜß\-\n\(\)]+', ' ', cleaned)

        # Assicurati che la punteggiatura sia formattata correttamente
        cleaned = re.sub(r'\s+([.,;:!?])', r'\1', cleaned)

        return cleaned.strip()

    async def retrieve_context(self, query: str, course_id: str, book_id: Optional[str] = None, k: int = 5) -> Dict[str, Any]:
        """Retrieve relevant context for a query"""
        try:
            # Generate query embedding
            self._load_embedding_model()
            query_embedding = self.embedding_model.encode([query]).tolist()

            # Build filter based on course_id and optional book_id
            where_filter = self._build_where_filter(course_id, book_id)

            # Search in ChromaDB with course and book filter
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=k,
                where=where_filter
            )

            if not results['documents'][0]:
                return {
                    "text": "",
                    "sources": [],
                    "message": "Nessun documento rilevante trovato per questo corso."
                }

            # Format results
            context_text = "\n\n".join(results['documents'][0])
            sources = []

            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                sources.append({
                    "source": metadata.get('source', 'Unknown'),
                    "chunk_index": metadata.get('chunk_index', i),
                    "relevance_score": 1.0 - (i * 0.1)  # Simple relevance scoring
                })

            return {
                "text": context_text,
                "sources": sources,
                "query": query,
                "course_id": course_id
            }

        except Exception as e:
            print(f"Error retrieving context: {e}")
            return {
                "text": "",
                "sources": [],
                "error": "Errore nel recupero del contesto"
            }

    async def search_documents(self, course_id: str, search_query: str = None) -> Dict[str, Any]:
        """Search all documents for a course"""
        try:
            if search_query:
                # Semantic search
                self._load_embedding_model()
                query_embedding = self.embedding_model.encode([search_query]).tolist()
                results = self.collection.query(
                    query_embeddings=query_embedding,
                    n_results=20,
                    where={"course_id": course_id}
                )
            else:
                # Get all documents for the course
                results = self.collection.get(
                    where={"course_id": course_id},
                    limit=5000  # Increased limit to handle more documents
                )

            # Group by source document
            documents_by_source = {}

            # Pre-calculate chunk counts for each source
            source_chunk_counts = {}
            for metadata in results.get('metadatas', []):
                source = metadata.get('source', 'Unknown')
                source_chunk_counts[source] = source_chunk_counts.get(source, 0) + 1

            for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                source = metadata.get('source', 'Unknown')
                if source not in documents_by_source:
                    documents_by_source[source] = {
                        "source": source,
                        "chunks": [],
                        "total_chunks": 0
                    }

                documents_by_source[source]["chunks"].append({
                    "index": metadata.get('chunk_index', i),
                    "content": doc[:200] + "..." if len(doc) > 200 else doc
                })
                # Use the pre-calculated count
                documents_by_source[source]["total_chunks"] = source_chunk_counts[source]

            return {
                "documents": list(documents_by_source.values()),
                "total_sources": len(documents_by_source),
                "course_id": course_id
            }

        except Exception as e:
            print(f"Error searching documents: {e}")
            return {"error": str(e), "documents": []}

    def delete_course_documents(self, course_id: str):
        """Delete all documents for a specific course"""
        try:
            self.collection.delete(
                where={"course_id": course_id}
            )
            print(f"Deleted all documents for course {course_id}")
        except Exception as e:
            print(f"Error deleting course documents: {e}")

    def delete_book_documents(self, course_id: str, book_id: str):
        """Delete all documents for a specific book"""
        try:
            self.collection.delete(
                where=self._build_where_filter(course_id, book_id)
            )
            print(f"Deleted all documents for book {book_id} in course {course_id}")
        except Exception as e:
            print(f"Error deleting book documents: {e}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed documents"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": "course_materials"
            }
        except Exception as e:
            return {"error": str(e)}

    def _init_hybrid_search(self):
        """Inizializza il servizio di hybrid search"""
        if self.hybrid_search is None:
            try:
                from services.hybrid_search_service import HybridSearchService
                self.hybrid_search = HybridSearchService(self)
                logger.info("HybridSearchService initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize HybridSearchService: {e}")
                self.hybrid_search = None

    async def retrieve_context_hybrid(self, query: str, course_id: str,
                                    book_id: Optional[str] = None, k: int = 5) -> Dict[str, Any]:
        """
        Retrieve context using hybrid search (semantic + keyword)
        """
        try:
            # Inizializza hybrid search se necessario
            self._init_hybrid_search()

            if self.hybrid_search:
                # Usa hybrid search con caching
                result = await self.hybrid_search.hybrid_search_cached(query, course_id, book_id, k)
                logger.info("Hybrid search executed successfully",
                          query=query, course_id=course_id, results=len(result.get('sources', [])),
                          cached=result.get('cached', False))
                return result
            else:
                # Fallback a semantic search tradizionale
                logger.warning("Hybrid search not available, falling back to semantic search")
                return await self.retrieve_context(query, course_id, book_id, k)

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fallback garantito
            return await self.retrieve_context(query, course_id, book_id, k)

    def get_hybrid_search_stats(self) -> Dict[str, Any]:
        """
        Get statistics about hybrid search performance
        """
        try:
            if self.hybrid_search:
                return self.hybrid_search.get_search_stats()
            else:
                return {
                    "hybrid_search_available": False,
                    "message": "HybridSearchService not initialized"
                }
        except Exception as e:
            return {
                "hybrid_search_available": False,
                "error": str(e)
            }

    def _init_cache_service(self):
        """Inizializza il servizio di cache Redis"""
        if self.cache_service is None:
            try:
                from services.cache_service import RedisCacheService, CacheType
                self.cache_service = RedisCacheService()
                logger.info("Redis cache service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache service: {e}")
                self.cache_service = None

    def _generate_cache_key(self, query: str, course_id: str, book_id: Optional[str] = None,
                           k: int = 5, use_hybrid: bool = False) -> str:
        """
        Genera cache key univoco per query RAG
        """
        key_components = [
            f"query:{hashlib.md5(query.encode()).hexdigest()[:16]}",
            f"course:{course_id}",
            f"k:{k}",
            f"hybrid:{use_hybrid}"
        ]

        if book_id:
            key_components.append(f"book:{book_id}")

        return ":".join(key_components)

    async def retrieve_context_cached(self, query: str, course_id: str,
                                    book_id: Optional[str] = None, k: int = 5,
                                    use_hybrid: bool = False) -> Dict[str, Any]:
        """
        Retrieve context con cache layer per performance ottimizzate
        """
        try:
            # Inizializza cache service se necessario
            self._init_cache_service()

            if self.cache_service:
                # Genera cache key
                cache_key = self._generate_cache_key(query, course_id, book_id, k, use_hybrid)

                # Tenta di recuperare dalla cache
                from services.cache_service import CacheType
                cached_result = await self.cache_service.get(CacheType.QUERY_RESULT, cache_key)

                if cached_result is not None:
                    logger.info("Cache hit for RAG query", query=query[:50], cache_key=cache_key)
                    return cached_result

            # Cache miss - esegui query normale
            if use_hybrid:
                result = await self.retrieve_context_hybrid(query, course_id, book_id, k)
            else:
                result = await self.retrieve_context(query, course_id, book_id, k)

            # Salva nella cache
            if self.cache_service and result.get("text"):  # Solo cache risultati validi
                await self.cache_service.set(CacheType.QUERY_RESULT, cache_key, result)
                logger.info("Cached RAG query result", query=query[:50], cache_key=cache_key)

            return result

        except Exception as e:
            logger.error(f"Error in cached context retrieval: {e}")
            # Fallback a metodo tradizionale senza cache
            if use_hybrid:
                return await self.retrieve_context_hybrid(query, course_id, book_id, k)
            else:
                return await self.retrieve_context(query, course_id, book_id, k)

    async def get_embedding_cached(self, text: str) -> List[float]:
        """
        Calcola embedding con cache per ottimizzare calcoli ripetuti
        """
        try:
            self._init_cache_service()

            if self.cache_service:
                # Genera cache key basato su hash del testo
                cache_key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"

                # Tenta cache
                from services.cache_service import CacheType
                cached_embedding = await self.cache_service.get(CacheType.EMBEDDING, cache_key)

                if cached_embedding is not None:
                    logger.debug("Cache hit for embedding", text_hash=cache_key[:16])
                    return cached_embedding

            # Cache miss - calcola embedding
            self._load_embedding_model()
            embedding = self.embedding_model.encode([text])[0].tolist()

            # Salva in cache
            if self.cache_service:
                await self.cache_service.set(CacheType.EMBEDDING, cache_key, embedding)
                logger.debug("Cached embedding", text_hash=cache_key[:16])

            return embedding

        except Exception as e:
            logger.error(f"Error in cached embedding: {e}")
            # Fallback a calcolo diretto
            self._load_embedding_model()
            return self.embedding_model.encode([text])[0].tolist()

    def invalidate_course_cache(self, course_id: str, book_id: Optional[str] = None):
        """
        Invalida tutte le cache entries per un corso specifico
        """
        try:
            self._init_cache_service()

            if self.cache_service:
                # Pattern per invalidazione
                pattern = f"tutor_ai:query_result:*:course:{course_id}:*"
                if book_id:
                    pattern = f"tutor_ai:query_result:*:course:{course_id}:*:book:{book_id}:*"

                # Esegui invalidazione asincrona
                import asyncio
                asyncio.create_task(self.cache_service.invalidate_by_pattern(pattern))

                logger.info("Invalidated cache for course", course_id=course_id, book_id=book_id)

        except Exception as e:
            logger.error(f"Error invalidating course cache: {e}")

    async def get_cache_metrics(self) -> Dict[str, Any]:
        """
        Restituisce metriche del sistema di cache
        """
        try:
            self._init_cache_service()

            if self.cache_service:
                cache_metrics = self.cache_service.get_metrics()
                redis_info = self.cache_service.get_redis_info()
                health_status = await self.cache_service.health_check()

                return {
                    "cache_enabled": True,
                    "metrics": cache_metrics,
                    "redis_info": redis_info,
                    "health": health_status
                }
            else:
                return {
                    "cache_enabled": False,
                    "message": "Redis cache service not available"
                }

        except Exception as e:
            logger.error(f"Error getting cache metrics: {e}")
            return {
                "cache_enabled": False,
                "error": str(e)
            }

    async def clear_cache(self, cache_type: Optional[str] = None):
        """
        Pulisce la cache (tutti i tipi o tipo specifico)
        """
        try:
            self._init_cache_service()

            if self.cache_service:
                if cache_type:
                    from services.cache_service import CacheType
                    try:
                        cache_enum = CacheType(cache_type)
                        deleted_count = await self.cache_service.clear_by_type(cache_enum)
                        logger.info(f"Cleared {deleted_count} entries for cache type: {cache_type}")
                        return {"success": True, "deleted_count": deleted_count, "type": cache_type}
                    except ValueError:
                        logger.error(f"Invalid cache type: {cache_type}")
                        return {"success": False, "error": f"Invalid cache type: {cache_type}"}
                else:
                    # Clear all cache
                    from services.cache_service import CacheType
                    total_deleted = 0
                    for cache_type_enum in CacheType:
                        deleted = await self.cache_service.clear_by_type(cache_type_enum)
                        total_deleted += deleted

                    logger.info(f"Cleared all cache: {total_deleted} entries deleted")
                    return {"success": True, "deleted_count": total_deleted, "type": "all"}
            else:
                return {"success": False, "message": "Cache service not available"}

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return {"success": False, "error": str(e)}
