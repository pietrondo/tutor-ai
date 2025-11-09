import chromadb
import os
import torch
import time
import copy
import math
import re
import socket
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple
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
import numpy as np

from services.course_service import CourseService
from services.annotation_service import AnnotationService

logger = structlog.get_logger()

class RAGService:
    def __init__(self):
        # Lazy loading - non caricare il modello all'avvio
        self.embedding_model = None
        # Use a lighter model for faster startup
        self.model_name = 'all-MiniLM-L6-v2'  # Much lighter than e5-large
        # Configurazioni ottimizzate per l'italiano
        self.chunk_size = 800  # Token 512-1024 ottimali per italiano
        self.chunk_overlap = 0.25  # 25% overlap per coerenza semantica
        self.max_chunk_length = 1024  # Massimo token per chunk

        # Disable ChromaDB for now to prevent hanging
        self.chroma_client = None
        self.collection = None
        # self.setup_collection()  # Commented out for faster startup

        # Inizializza HybridSearchService
        self.hybrid_search = None

        # Inizializza Cache Service (lazy loading)
        self.cache_service = None

        # Course/material helpers
        self.course_service = CourseService()
        self.book_chunk_cache: Dict[str, Dict[str, Any]] = {}
        self.max_cached_chunk_sets = 8
        self.max_cached_chunks = 1200
        self.annotation_service = AnnotationService()
        self.embedding_fallback_enabled = False
        self._tokenizer_pattern = re.compile(r"\w+", re.UNICODE)
        self._hf_available: Optional[bool] = None

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

    def _trim_chunk_cache(self):
        if len(self.book_chunk_cache) <= self.max_cached_chunk_sets:
            return

        oldest_key = None
        oldest_ts = time.time()
        for key, entry in self.book_chunk_cache.items():
            entry_ts = entry.get("updated_at", 0)
            if entry_ts <= oldest_ts:
                oldest_key = key
                oldest_ts = entry_ts

        if oldest_key is not None:
            self.book_chunk_cache.pop(oldest_key, None)

    def _resolve_scope_entities(self, course_id: str, book_id: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        try:
            course = self.course_service.get_course(course_id)
        except Exception as exc:
            logger.error("Failed to load course for scope", course_id=course_id, error=str(exc))
            return None, None

        if not course:
            return None, None

        book = None
        if book_id:
            for candidate in course.get("books", []) or []:
                if candidate.get("id") == book_id:
                    book = candidate
                    break

        return course, book

    def _get_scope_materials_and_meta(self, course_id: str, book_id: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        course, book = self._resolve_scope_entities(course_id, book_id)
        metadata: Dict[str, Any] = {
            "course_id": course_id,
            "book_id": book_id,
            "scope": "book" if book_id else "course"
        }

        if not course:
            return [], metadata

        metadata["course_name"] = course.get("name")
        metadata["materials_count"] = course.get("materials_count", 0)

        if book_id:
            if not book:
                return [], metadata

            materials = book.get("materials", []) or []
            metadata.update({
                "book_title": book.get("title"),
                "materials_count": len(materials)
            })
        else:
            materials = course.get("materials", []) or []
            metadata["materials_count"] = len(materials)

        return materials, metadata

    def _build_scope_metadata(self, course_id: str, book_id: Optional[str] = None) -> Dict[str, Any]:
        course, book = self._resolve_scope_entities(course_id, book_id)
        metadata: Dict[str, Any] = {
            "course_id": course_id,
            "book_id": book_id,
            "scope": "book" if book_id else "course"
        }

        if course:
            metadata["course_name"] = course.get("name")
            metadata["materials_count"] = course.get("materials_count", 0)

        if book:
            metadata["book_title"] = book.get("title")
            metadata["materials_count"] = book.get("materials_count", metadata.get("materials_count", 0))

        return metadata

    def _fetch_user_annotations(self, user_id: Optional[str], course_id: str,
                                book_id: Optional[str], limit: int = 8) -> List[Dict[str, Any]]:
        if not user_id:
            return []

        try:
            annotations = self.annotation_service.get_user_annotations(user_id, limit=500)
        except Exception as exc:
            logger.error("Failed to load user annotations", user_id=user_id, error=str(exc))
            return []

        filtered: List[Dict[str, Any]] = []
        for annotation in annotations:
            if not annotation.get("share_with_ai") and not annotation.get("is_public"):
                continue

            annotation_book_id = annotation.get("book_id") or None
            annotation_course_id = annotation.get("course_id") or None

            if book_id:
                if annotation_book_id == book_id:
                    filtered.append(annotation)
            else:
                if not annotation_book_id and (annotation_course_id == course_id or not annotation_course_id):
                    filtered.append(annotation)

            if len(filtered) >= limit:
                break

        return filtered

    def _format_annotation_snippet(self, annotation: Dict[str, Any]) -> str:
        selection = (annotation.get("selected_text") or annotation.get("text") or "").strip()
        note = (annotation.get("content") or "").strip()
        page = annotation.get("page_number")
        tags = annotation.get("tags") or []

        parts: List[str] = []
        if selection:
            parts.append(selection)
        if note:
            parts.append(f"Nota: {note}")
        if tags:
            parts.append(f"Tag: {', '.join(tags)}")

        snippet_body = "\n".join(parts).strip()
        header = f"Pagina {page}" if page else "Annotazione"
        return f"{header}: {snippet_body}" if snippet_body else header

    def _merge_user_annotations(self, context_result: Dict[str, Any], course_id: str,
                                book_id: Optional[str], user_id: Optional[str]) -> Dict[str, Any]:
        if not user_id:
            return context_result

        annotations = self._fetch_user_annotations(user_id, course_id, book_id)
        if not annotations:
            return context_result

        annotation_sections: List[str] = []
        annotation_sources: List[Dict[str, Any]] = []

        for idx, annotation in enumerate(annotations):
            snippet = self._format_annotation_snippet(annotation)
            if not snippet:
                continue

            annotation_sections.append(snippet)
            annotation_sources.append({
                "source": f"Nota personale pagina {annotation.get('page_number', '?')}",
                "chunk_index": idx,
                "relevance_score": 1.0,
                "type": "user_annotation",
                "annotation_id": annotation.get("id"),
                "page_number": annotation.get("page_number"),
                "course_id": annotation.get("course_id") or course_id,
                "book_id": annotation.get("book_id") or book_id
            })

        if not annotation_sections:
            return context_result

        merged_text = "NOTE PERSONALI DELLO STUDENTE\n" + "\n\n".join(annotation_sections)
        base_text = context_result.get("text", "")
        if base_text:
            merged_text = f"{merged_text}\n\n{base_text}"

        merged_result = dict(context_result)
        merged_result["text"] = merged_text
        existing_sources = context_result.get("sources", []) or []
        merged_result["sources"] = annotation_sources + list(existing_sources)

        scope = dict(context_result.get("scope") or {})
        scope["user_annotations_used"] = scope.get("user_annotations_used", 0) + len(annotation_sources)
        scope["annotations_strategy"] = "prepended"
        merged_result["scope"] = scope

        return merged_result

    def _build_material_signature(self, materials: List[Dict[str, Any]]) -> str:
        signatures: List[str] = []
        for material in materials:
            file_path = material.get("file_path")
            if not file_path or not os.path.exists(file_path):
                continue
            try:
                stat = os.stat(file_path)
                signatures.append(f"{file_path}:{int(stat.st_mtime)}:{stat.st_size}")
            except FileNotFoundError:
                continue

        return "|".join(sorted(signatures))

    def _build_chunks_from_materials(self, materials: List[Dict[str, Any]], course_id: str,
                                     book_id: Optional[str]) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        chunk_index = 0

        for material in materials:
            if chunk_index >= self.max_cached_chunks:
                break

            file_path = material.get("file_path")
            if not file_path or not os.path.exists(file_path):
                continue

            try:
                text = self.extract_text_from_pdf(file_path)
            except Exception as exc:
                logger.error("Failed to extract text for material", path=file_path, error=str(exc))
                continue

            text_chunks = self.split_text_into_chunks(text)

            for chunk in text_chunks:
                chunks.append({
                    "text": chunk,
                    "metadata": {
                        "course_id": course_id,
                        "book_id": book_id,
                        "source": material.get("filename") or os.path.basename(file_path),
                        "chunk_index": chunk_index,
                        "material_relative_path": material.get("relative_path"),
                        "material_path": file_path
                    }
                })
                chunk_index += 1

                if chunk_index >= self.max_cached_chunks:
                    break

        return chunks

    def _embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[List[float]]:
        if not chunks:
            return []

        texts = [chunk["text"] for chunk in chunks]
        self._load_embedding_model()
        if self.embedding_model is None:
            # Fallback: no embeddings to pre-compute
            return []

        embeddings = self.embedding_model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings

    def _get_or_build_chunk_entry(self, course_id: str, book_id: Optional[str],
                                  materials: List[Dict[str, Any]], scope_meta: Dict[str, Any]) -> Dict[str, Any]:
        cache_key = f"{course_id}:{book_id or 'all'}"
        signature = self._build_material_signature(materials)
        cache_entry = self.book_chunk_cache.get(cache_key)

        if cache_entry and cache_entry.get("signature") == signature:
            cache_entry["scope"] = scope_meta
            return cache_entry

        chunks = self._build_chunks_from_materials(materials, course_id, book_id)
        embeddings = self._embed_chunks(chunks)

        cache_entry = {
            "chunks": chunks,
            "embeddings": embeddings,
            "signature": signature,
            "scope": scope_meta,
            "updated_at": time.time()
        }

        self.book_chunk_cache[cache_key] = cache_entry
        self._trim_chunk_cache()
        return cache_entry

    def _rank_chunks_by_similarity(self, query: str, cache_entry: Dict[str, Any], k: int) -> List[Dict[str, Any]]:
        chunks = cache_entry.get("chunks") or []
        embeddings = cache_entry.get("embeddings") or []

        if not chunks or not embeddings:
            return [] if not self.embedding_fallback_enabled else self._rank_with_lexical_similarity(query, chunks, k)

        if self.embedding_model is None:
            return self._rank_with_lexical_similarity(query, chunks, k)

        query_embedding = self.embedding_model.encode([query], normalize_embeddings=True)[0]
        chunk_embeddings = np.array(embeddings)

        if chunk_embeddings.size == 0:
            return self._rank_with_lexical_similarity(query, chunks, k)

        scores = np.dot(chunk_embeddings, query_embedding)
        top_indices = np.argsort(scores)[::-1][:k]

        ranked: List[Dict[str, Any]] = []
        for idx in top_indices:
            if idx >= len(chunks):
                continue
            ranked.append({
                "chunk": chunks[idx],
                "score": float(scores[idx])
            })

        return ranked

    def _tokenize_for_similarity(self, text: str) -> List[str]:
        return self._tokenizer_pattern.findall(text.lower())

    def _lexical_vector(self, text: str) -> Counter:
        return Counter(self._tokenize_for_similarity(text))

    def _simple_similarity(self, text_a: str, text_b: str) -> float:
        vec_a = self._lexical_vector(text_a)
        vec_b = self._lexical_vector(text_b)

        if not vec_a or not vec_b:
            return 0.0

        dot = sum(vec_a[token] * vec_b.get(token, 0) for token in vec_a)
        norm_a = math.sqrt(sum(value * value for value in vec_a.values()))
        norm_b = math.sqrt(sum(value * value for value in vec_b.values()))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def _rank_with_lexical_similarity(self, query: str, chunks: List[Dict[str, Any]], k: int) -> List[Dict[str, Any]]:
        scored = []
        for chunk in chunks:
            score = self._simple_similarity(query, chunk.get("text", ""))
            scored.append({"chunk": chunk, "score": score})

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:k]

    def _attach_scope_usage(self, scope_meta: Dict[str, Any], sources: List[Dict[str, Any]],
                             strategy: str) -> Dict[str, Any]:
        scope = dict(scope_meta or {})
        used_materials = sorted({source.get("source") for source in sources if source.get("source")})
        scope["materials_used"] = used_materials
        scope["retrieval_strategy"] = strategy
        scope.setdefault("course_id", scope_meta.get("course_id") if scope_meta else None)
        return scope

    def _build_empty_context_response(self, course_id: str, book_id: Optional[str],
                                       scope_meta: Dict[str, Any], message: str) -> Dict[str, Any]:
        scope = dict(scope_meta or {})
        scope.setdefault("retrieval_strategy", "none")
        return {
            "text": "",
            "sources": [],
            "course_id": course_id,
            "book_id": book_id,
            "scope": scope,
            "message": message
        }

    async def _retrieve_context_local(self, query: str, course_id: str,
                                      book_id: Optional[str], k: int) -> Dict[str, Any]:
        materials, scope_meta = self._get_scope_materials_and_meta(course_id, book_id)

        if not materials:
            return self._build_empty_context_response(
                course_id,
                book_id,
                scope_meta,
                "Nessun materiale locale disponibile per il contesto selezionato"
            )

        chunk_entry = self._get_or_build_chunk_entry(course_id, book_id, materials, scope_meta)
        ranked_chunks = self._rank_chunks_by_similarity(query, chunk_entry, k)

        if not ranked_chunks:
            return self._build_empty_context_response(
                course_id,
                book_id,
                scope_meta,
                "Non sono stati trovati riferimenti pertinenti per questo libro"
            )

        combined_text = "\n\n".join(item["chunk"]["text"] for item in ranked_chunks)
        sources: List[Dict[str, Any]] = []
        for item in ranked_chunks:
            metadata = item["chunk"].get("metadata", {})
            sources.append({
                "source": metadata.get("source", "Local PDF"),
                "chunk_index": metadata.get("chunk_index"),
                "relevance_score": round(float(item.get("score", 0.0)), 4),
                "course_id": metadata.get("course_id"),
                "book_id": metadata.get("book_id"),
                "material_path": metadata.get("material_relative_path") or metadata.get("material_path")
            })

        scope = self._attach_scope_usage(chunk_entry.get("scope", scope_meta), sources, "local_fallback")

        return {
            "text": combined_text,
            "sources": sources,
            "course_id": course_id,
            "book_id": book_id,
            "scope": scope
        }

    async def _retrieve_context_vector(self, query: str, course_id: str,
                                        book_id: Optional[str], k: int) -> Dict[str, Any]:
        if self.collection is None:
            raise RuntimeError("Vector collection unavailable")

        self._load_embedding_model()
        if self.embedding_model is None:
            raise RuntimeError("Embedding model unavailable")

        query_embedding = self.embedding_model.encode([query]).tolist()
        where_filter = self._build_where_filter(course_id, book_id)

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=k,
            where=where_filter
        )

        documents = results.get('documents') or []
        metadatas = results.get('metadatas') or []

        if not documents or not documents[0]:
            scope_meta = self._build_scope_metadata(course_id, book_id)
            return self._build_empty_context_response(
                course_id,
                book_id,
                scope_meta,
                "Nessun documento indicizzato per il contesto selezionato"
            )

        context_text = "\n\n".join(documents[0])
        sources: List[Dict[str, Any]] = []

        for i, metadata in enumerate(metadatas[0]):
            sources.append({
                "source": metadata.get('source', 'Unknown'),
                "chunk_index": metadata.get('chunk_index', i),
                "relevance_score": round(1.0 - (i * 0.1), 4),
                "course_id": course_id,
                "book_id": metadata.get('book_id') or book_id
            })

        scope_meta = self._build_scope_metadata(course_id, book_id)
        scope = self._attach_scope_usage(scope_meta, sources, "vector_db")

        return {
            "text": context_text,
            "sources": sources,
            "course_id": course_id,
            "book_id": book_id,
            "scope": scope
        }

    def _load_embedding_model(self):
        """Carica il modello di embedding solo quando necessario"""
        if self.embedding_model is None:
            logger.info("Loading embedding model...")
            if self.embedding_fallback_enabled:
                logger.info("Embedding fallback already enabled – skipping model load")
                return

            if not self._is_hf_available():
                logger.warning("HuggingFace endpoint non raggiungibile: uso fallback testuale")
                self.embedding_fallback_enabled = True
                self.embedding_model = None
                return
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
                logger.error("Failed to load embedding model, falling back to lexical similarity", error=str(e))
                self.embedding_model = None
                self.embedding_fallback_enabled = True

    def _is_hf_available(self) -> bool:
        if self._hf_available is not None:
            return self._hf_available

        try:
            socket.gethostbyname('huggingface.co')
            self._hf_available = True
        except OSError:
            self._hf_available = False

        return self._hf_available

    def setup_collection(self):
        """Setup or get the ChromaDB collection"""
        if self.chroma_client is None:
            logger.warning("ChromaDB disabled - vector search will not work")
            return
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

    async def retrieve_context(self, query: str, course_id: str, book_id: Optional[str] = None,
                               k: int = 5, user_id: Optional[str] = None,
                               include_annotations: bool = True) -> Dict[str, Any]:
        """Retrieve relevant context for a query"""
        try:
            vector_result = None
            if self.collection is not None:
                try:
                    vector_result = await self._retrieve_context_vector(query, course_id, book_id, k)
                except Exception as exc:
                    logger.error("Vector retrieval failed, falling back to local chunks",
                                 course_id=course_id, book_id=book_id, error=str(exc))

            base_result: Dict[str, Any]
            if vector_result and vector_result.get("text"):
                base_result = vector_result
            else:
                local_result = await self._retrieve_context_local(query, course_id, book_id, k)
                if local_result.get("text"):
                    base_result = local_result
                else:
                    base_result = vector_result or local_result

            if include_annotations:
                return self._merge_user_annotations(base_result, course_id, book_id, user_id)

            return base_result

        except Exception as e:
            logger.error("Error retrieving context", error=str(e), course_id=course_id, book_id=book_id)
            scope = self._build_scope_metadata(course_id, book_id)
            empty_context = self._build_empty_context_response(course_id, book_id, scope, "Errore nel recupero del contesto")
            if include_annotations:
                return self._merge_user_annotations(empty_context, course_id, book_id, user_id)
            return empty_context

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
                                      use_hybrid: bool = False,
                                      user_id: Optional[str] = None,
                                      include_annotations: bool = True) -> Dict[str, Any]:
        """
        Retrieve context con cache layer per performance ottimizzate
        """
        try:
            # Inizializza cache service se necessario
            self._init_cache_service()

            result: Dict[str, Any]
            cache_key = None
            cache_type_cls = None

            if self.cache_service:
                try:
                    from services.cache_service import CacheType  # type: ignore
                    cache_type_cls = CacheType
                except Exception as import_error:
                    logger.error("Unable to import CacheType", error=str(import_error))
                    cache_type_cls = None

                cache_key = self._generate_cache_key(query, course_id, book_id, k, use_hybrid)
                cached_result = None
                if cache_type_cls is not None:
                    cached_result = await self.cache_service.get(cache_type_cls.QUERY_RESULT, cache_key)

                if cached_result is not None:
                    logger.info("Cache hit for RAG query", query=query[:50], cache_key=cache_key)
                    result = {
                        **cached_result,
                        "sources": list(cached_result.get("sources", []) or []),
                        "scope": dict(cached_result.get("scope") or {})
                    }
                else:
                    if use_hybrid:
                        result = await self.retrieve_context_hybrid(query, course_id, book_id, k)
                    else:
                        result = await self.retrieve_context(query, course_id, book_id, k,
                                                             user_id=user_id, include_annotations=False)

                    if cache_type_cls is not None and result.get("text"):
                        await self.cache_service.set(cache_type_cls.QUERY_RESULT, cache_key, copy.deepcopy(result))
                        logger.info("Cached RAG query result", query=query[:50], cache_key=cache_key)
            else:
                if use_hybrid:
                    result = await self.retrieve_context_hybrid(query, course_id, book_id, k)
                else:
                    result = await self.retrieve_context(query, course_id, book_id, k,
                                                         user_id=user_id, include_annotations=False)

            if include_annotations:
                return self._merge_user_annotations(result, course_id, book_id, user_id)

            return result

        except Exception as e:
            logger.error(f"Error in cached context retrieval: {e}")
            # Fallback a metodo tradizionale senza cache
            if use_hybrid:
                return await self.retrieve_context_hybrid(query, course_id, book_id, k)
            else:
                return await self.retrieve_context(query, course_id, book_id, k,
                                                   user_id=user_id, include_annotations=include_annotations)

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


class BookContentAnalyzer:
    """
    Servizio specializzato per analizzare i contenuti dei libri usando RAG
    e generare contesto per concept maps book-specific
    """

    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service
        self.llm_service = None  # Lazy loading

    def _get_llm_service(self):
        """Lazy loading del LLM service"""
        if self.llm_service is None:
            from services.llm_service import LLMService
            self.llm_service = LLMService()
        return self.llm_service

    async def analyze_book_content(self, course_id: str, book_id: str) -> Dict[str, Any]:
        """
        Analisi completa dei contenuti di un libro usando RAG
        """
        try:
            logger.info(f"Starting RAG analysis for book {book_id} in course {course_id}")

            # 1. Estrai contenuti RAG specifici del libro
            book_content = await self._extract_book_rag_content(course_id, book_id)

            if not book_content.get("documents", []):
                logger.warning(f"No RAG content found for book {book_id}")
                return self._create_fallback_analysis(course_id, book_id)

            # 2. Analizza temi principali con AI
            themes_analysis = await self._analyze_main_themes(book_content, book_id)

            # 3. Estrai concetti chiave
            key_concepts = await self._extract_key_concepts(book_content, themes_analysis)

            # 4. Identifica struttura del libro
            book_structure = await self._identify_book_structure(book_content)

            # 5. Genera contesto per concept map generation
            concept_context = await self._generate_concept_map_context(
                book_content, themes_analysis, key_concepts, book_structure, book_id
            )

            result = {
                "success": True,
                "book_id": book_id,
                "course_id": course_id,
                "analysis": {
                    "content_summary": book_content["summary"],
                    "main_themes": themes_analysis["themes"],
                    "key_concepts": key_concepts,
                    "structure": book_structure,
                    "concept_context": concept_context,
                    "source_count": len(book_content["documents"]),
                    "analysis_quality": self._assess_analysis_quality(book_content, themes_analysis, key_concepts)
                },
                "rag_data": {
                    "documents_used": len(book_content["documents"]),
                    "total_chunks": sum(len(doc.get("chunks", [])) for doc in book_content["documents"]),
                    "coverage_score": book_content.get("coverage_score", 0.0)
                }
            }

            logger.info(f"Book analysis completed for {book_id}: {len(key_concepts)} concepts found")
            return result

        except Exception as e:
            logger.error(f"Error analyzing book {book_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "book_id": book_id,
                "course_id": course_id
            }

    async def _extract_book_rag_content(self, course_id: str, book_id: str) -> Dict[str, Any]:
        """
        Estrai contenuti RAG specifici del libro con query mirate
        """
        try:
            # Query strategiche per estrarre contenuti completi del libro
            analysis_queries = [
                "concetti principali e temi fondamentali",
                "struttura e organizzazione dei contenuti",
                "argomenti chiave e argomentazioni principali",
                "definizioni e terminologia specifica",
                "esempi pratici e applicazioni"
            ]

            all_documents = []
            total_sources = set()

            for query in analysis_queries:
                # RAG search con filtro libro-specifico
                search_result = await self.rag_service.search_documents(
                    course_id=course_id,
                    search_query=query,
                    max_results=8,
                    book_filter=book_id  # Filtra solo per questo libro
                )

                if search_result.get("success"):
                    for doc in search_result.get("documents", []):
                        # Evita duplicati
                        doc_id = doc.get("id", "")
                        if doc_id not in total_sources:
                            all_documents.append(doc)
                            total_sources.add(doc_id)

            # Organizza i contenuti per analisi
            organized_content = self._organize_book_content(all_documents, book_id)

            return {
                "success": True,
                "documents": organized_content["documents"],
                "summary": organized_content["summary"],
                "coverage_score": self._calculate_coverage_score(all_documents, book_id),
                "total_sources": len(all_documents)
            }

        except Exception as e:
            logger.error(f"Error extracting RAG content for book {book_id}: {e}")
            return {"success": False, "documents": [], "summary": "", "coverage_score": 0.0}

    def _organize_book_content(self, documents: List[Dict], book_id: str) -> Dict[str, Any]:
        """
        Organizza i contenuti RAG del libro per struttura e rilevanza
        """
        try:
            # Raggruppa per tipo di contenuto
            organized = {
                "definitions": [],
                "concepts": [],
                "examples": [],
                "structure": [],
                "other": []
            }

            all_text = []
            for doc in documents:
                content = doc.get("content", "")
                all_text.append(content)

                # Classifica il contenuto
                if any(keyword in content.lower() for keyword in ["definizione", "significato", "è", "consiste in"]):
                    organized["definitions"].append(doc)
                elif any(keyword in content.lower() for keyword in ["concetto", "principio", "teoria", "idea"]):
                    organized["concepts"].append(doc)
                elif any(keyword in content.lower() for keyword in ["esempio", "caso", "applicazione"]):
                    organized["examples"].append(doc)
                elif any(keyword in content.lower() for keyword in ["capitolo", "sezione", "parte", "struttura"]):
                    organized["structure"].append(doc)
                else:
                    organized["other"].append(doc)

            # Crea summary dei contenuti
            summary = self._create_content_summary(organized, all_text)

            return {
                "documents": documents,
                "organized": organized,
                "summary": summary
            }

        except Exception as e:
            logger.error(f"Error organizing content: {e}")
            return {
                "documents": documents,
                "organized": {},
                "summary": "Errore nell'organizzazione dei contenuti"
            }

    def _create_content_summary(self, organized: Dict[str, List], all_text: List[str]) -> str:
        """
        Crea un riassunto dei contenuti organizzati
        """
        summary_parts = []

        if organized.get("definitions"):
            summary_parts.append(f"{len(organized['definitions'])} definizioni")

        if organized.get("concepts"):
            summary_parts.append(f"{len(organized['concepts'])} concetti principali")

        if organized.get("examples"):
            summary_parts.append(f"{len(organized['examples'])} esempi pratici")

        if organized.get("structure"):
            summary_parts.append("informazioni sulla struttura")

        total_content = len(all_text)
        if total_content > 0:
            summary_parts.append(f"{total_content} segmenti di contenuto")

        return "Contenuti rilevanti: " + ", ".join(summary_parts)

    async def _analyze_main_themes(self, book_content: Dict[str, Any], book_id: str) -> Dict[str, Any]:
        """
        Analizza i temi principali usando AI reasoning sui contenuti RAG
        """
        try:
            if not book_content.get("documents"):
                return {"themes": [], "analysis": "No content available"}

            # Prepara il testo per l'analisi AI
            content_text = self._prepare_content_for_ai(book_content["documents"][:15])  # Limita per performance

            # Prompt specializzato per analisi temi
            analysis_prompt = f"""
            Analizza i seguenti contenuti di un libro e identifica i temi principali:

            CONTENUTI DEL LIBRO:
            {content_text}

            Compito:
            1. Identifica 3-5 temi principali del libro
            2. Per ogni tema, descrivine l'importanza e come si collega agli altri
            3. Evidenzia concetti trasversali che collegano i temi
            4. Valuta la complessità e profondità di ogni tema

            Rispondi in formato JSON con questa struttura:
            {{
                "themes": [
                    {{
                        "name": "Nome del tema",
                        "description": "Descrizione dettagliata",
                        "importance": "alta/media/bassa",
                        "connections": ["tema1", "tema2"],
                        "concepts": ["concetto1", "concetto2"]
                    }}
                ],
                "cross_cutting_concepts": ["concetto1", "concetto2"],
                "complexity_assessment": "bassa/media/alta"
            }}
            """

            llm_service = self._get_llm_service()
            response = await llm_service.generate_response(analysis_prompt)

            # Parsing della risposta
            try:
                themes_data = json.loads(response.get("content", "{}"))
                return themes_data
            except json.JSONDecodeError:
                # Fallback se JSON parsing fallisce
                return {
                    "themes": [
                        {
                            "name": "Temi Principali",
                            "description": response.get("content", "Analisi non disponibile")[:200],
                            "importance": "media",
                            "connections": [],
                            "concepts": []
                        }
                    ],
                    "cross_cutting_concepts": [],
                    "complexity_assessment": "media"
                }

        except Exception as e:
            logger.error(f"Error analyzing themes: {e}")
            return {"themes": [], "analysis": f"Error: {str(e)}"}

    async def _extract_key_concepts(self, book_content: Dict[str, Any], themes_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Estrai concetti chiave dai contenuti RAG e dall'analisi dei temi
        """
        try:
            key_concepts = []

            # 1. Concetti dai temi identificati
            for theme in themes_analysis.get("themes", []):
                for concept_name in theme.get("concepts", []):
                    if concept_name and concept_name not in [c.get("name") for c in key_concepts]:
                        key_concepts.append({
                            "name": concept_name,
                            "source": "theme_analysis",
                            "theme": theme.get("name"),
                            "importance": theme.get("importance", "media")
                        })

            # 2. Concetti cross-cutting
            for concept in themes_analysis.get("cross_cutting_concepts", []):
                if concept and concept not in [c.get("name") for c in key_concepts]:
                    key_concepts.append({
                        "name": concept,
                        "source": "cross_cutting",
                        "importance": "alta"
                    })

            # 3. Concetti estratti direttamente dai documenti RAG
            document_concepts = self._extract_concepts_from_documents(book_content.get("documents", []))
            for concept in document_concepts:
                if concept["name"] not in [c.get("name") for c in key_concepts]:
                    key_concepts.append(concept)

            # 4. Limita e ordina per importanza
            key_concepts = sorted(key_concepts, key=lambda x: self._concept_importance_score(x), reverse=True)
            return key_concepts[:15]  # Max 15 concetti chiave

        except Exception as e:
            logger.error(f"Error extracting key concepts: {e}")
            return []

    def _extract_concepts_from_documents(self, documents: List[Dict]) -> List[Dict[str, Any]]:
        """
        Estrai concetti dai documenti RAG usando pattern matching
        """
        concepts = []
        import re

        # Pattern per identificare concetti
        concept_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # Termini in maiuscolo
            r'\bconcetto\s+di\s+([^\s,\.]+(?:\s+[^\s,\.]+)*)',  # "concetto di X"
            r'\bprincipio\s+([^\s,\.]+(?:\s+[^\s,\.]+)*)',  # "principio X"
            r'\bteoria\s+([^\s,\.]+(?:\s+[^\s,\.]+)*)',  # "teoria X"
            r'\bdefinizione\s+di\s+([^\s,\.]+(?:\s+[^\s,\.]+)*)',  # "definizione di X"
        ]

        concept_frequency = {}

        for doc in documents:
            content = doc.get("content", "")
            for pattern in concept_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    concept_name = match.strip()
                    if len(concept_name) > 2:  # Ignora termini troppo corti
                        concept_frequency[concept_name] = concept_frequency.get(concept_name, 0) + 1

        # Converti in lista e filtra per frequenza
        for concept_name, frequency in concept_frequency.items():
            if frequency >= 2:  # Appare almeno 2 volte
                concepts.append({
                    "name": concept_name,
                    "source": "document_extraction",
                    "frequency": frequency,
                    "importance": "alta" if frequency >= 4 else "media"
                })

        return concepts

    def _concept_importance_score(self, concept: Dict[str, Any]) -> float:
        """
        Calcola punteggio di importanza per un concetto
        """
        score = 0.0

        # Fonte del concetto
        if concept.get("source") == "cross_cutting":
            score += 10.0
        elif concept.get("source") == "theme_analysis":
            score += 8.0
        elif concept.get("source") == "document_extraction":
            score += 5.0

        # Importanza esplicita
        importance = concept.get("importance", "media")
        if importance == "alta":
            score += 5.0
        elif importance == "media":
            score += 3.0

        # Frequenza (se disponibile)
        frequency = concept.get("frequency", 1)
        score += min(frequency, 5)  # Max 5 punti per frequenza

        return score

    async def _identify_book_structure(self, book_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identifica la struttura del libro dai contenuti RAG
        """
        try:
            documents = book_content.get("documents", [])

            # Cerca pattern strutturali nei documenti
            structure_info = {
                "has_chapters": False,
                "estimated_chapters": 0,
                "sections": [],
                "complexity": "media"
            }

            chapter_keywords = ["capitolo", "chapter", "parte", "section", "sezione"]
            chapter_count = 0
            sections_found = set()

            for doc in documents:
                content = doc.get("content", "").lower()

                # Conta capitoli
                for keyword in chapter_keywords:
                    if keyword in content:
                        structure_info["has_chapters"] = True
                        chapter_count += content.count(keyword)

                # Estrai sezioni
                section_pattern = r'\b(capitolo\s+\d+|parte\s+\d+|sezione\s+[a-z0-9]+)\b'
                import re
                sections = re.findall(section_pattern, content, re.IGNORECASE)
                sections_found.update(sections)

            structure_info["estimated_chapters"] = min(chapter_count, 20)  # Max 20 per realismo
            structure_info["sections"] = list(sections_found)[:10]  # Max 10 sezioni

            # Valuta complessità
            if structure_info["estimated_chapters"] > 10:
                structure_info["complexity"] = "alta"
            elif structure_info["estimated_chapters"] < 5:
                structure_info["complexity"] = "bassa"

            return structure_info

        except Exception as e:
            logger.error(f"Error identifying book structure: {e}")
            return {"has_chapters": False, "estimated_chapters": 0, "sections": [], "complexity": "media"}

    async def _generate_concept_map_context(self, book_content: Dict[str, Any],
                                          themes_analysis: Dict[str, Any],
                                          key_concepts: List[Dict[str, Any]],
                                          book_structure: Dict[str, Any],
                                          book_id: str) -> str:
        """
        Genera il contesto completo per la generazione di concept maps
        """
        try:
            # Informazioni sul libro
            book_title = self._get_book_title(book_id)

            # Contesto tematico
            themes_context = ""
            if themes_analysis.get("themes"):
                themes_context = "\n".join([
                    f"- {theme.get('name', 'Tema')}: {theme.get('description', '')[:100]}..."
                    for theme in themes_analysis["themes"][:5]
                ])

            # Contesto concettuale
            concepts_context = ""
            if key_concepts:
                concepts_context = "\n".join([
                    f"- {concept.get('name', 'Concetto')} (importanza: {concept.get('importance', 'media')})"
                    for concept in key_concepts[:10]
                ])

            # Contesto strutturale
            structure_context = f"Struttura: {book_structure.get('estimated_chapters', 0)} capitoli stimati"

            # Assembla il contesto completo
            full_context = f"""
            CONTESTO PER CONCEPT MAP - Libro: {book_title}

            TEMI PRINCIPALI:
            {themes_context}

            CONCETTI CHIAVE IDENTIFICATI:
            {concepts_context}

            {structure_context}

            Questo contesto deve essere usato per generare concept maps che:
            1. Riflettano i temi e concetti effettivamente presenti nel libro
            2. Rispettino la struttura e l'organizzazione dei contenuti
            3. Siano gerarchicamente organizzate per importanza
            4. Includano obiettivi di apprendimento realistici
            """

            return full_context

        except Exception as e:
            logger.error(f"Error generating concept map context: {e}")
            return f"Contesto base per generazione concept map del libro {book_id}"

    def _get_book_title(self, book_id: str) -> str:
        """
        Recupera il titolo del libro dall'ID
        """
        try:
            courses_path = Path("data/courses/courses.json")
            if courses_path.exists():
                with open(courses_path, 'r', encoding='utf-8') as f:
                    courses_data = json.load(f)

                for course in courses_data.get("courses", []):
                    for book in course.get("books", []):
                        if book.get("id") == book_id:
                            return book.get("title", f"Libro {book_id}")
        except Exception:
            pass
        return f"Libro {book_id}"

    def _calculate_coverage_score(self, documents: List[Dict], book_id: str) -> float:
        """
        Calcola uno score di copertura dei contenuti RAG
        """
        if not documents:
            return 0.0

        # Score basato su numero e qualità dei documenti
        doc_count_score = min(len(documents) / 10.0, 1.0)  # Normalizza a max 10 doc
        content_score = sum(len(doc.get("content", "")) for doc in documents) / 10000.0  # Normalizza per 10k caratteri

        return min((doc_count_score + content_score) / 2.0, 1.0)

    def _assess_analysis_quality(self, book_content: Dict[str, Any],
                               themes_analysis: Dict[str, Any],
                               key_concepts: List[Dict[str, Any]]) -> str:
        """
        Valuta la qualità dell'analisi
        """
        try:
            quality_score = 0.0

            # Copertura contenuti
            coverage = book_content.get("coverage_score", 0.0)
            quality_score += coverage * 0.4

            # Qualità temi
            themes_count = len(themes_analysis.get("themes", []))
            if themes_count >= 3:
                quality_score += 0.3
            elif themes_count >= 1:
                quality_score += 0.15

            # Qualità concetti
            concepts_count = len(key_concepts)
            if concepts_count >= 8:
                quality_score += 0.3
            elif concepts_count >= 4:
                quality_score += 0.15

            # Valutazione finale
            if quality_score >= 0.8:
                return "eccellente"
            elif quality_score >= 0.6:
                return "buona"
            elif quality_score >= 0.4:
                return "sufficiente"
            else:
                return "migliorabile"

        except Exception:
            return "sconosciuta"

    def _create_fallback_analysis(self, course_id: str, book_id: str) -> Dict[str, Any]:
        """
        Crea un'analisi di fallback quando non ci sono contenuti RAG
        """
        book_title = self._get_book_title(book_id)

        return {
            "success": True,
            "book_id": book_id,
            "course_id": course_id,
            "analysis": {
                "content_summary": f"Nessun contenuto RAG disponibile per {book_title}",
                "main_themes": {"themes": [], "cross_cutting_concepts": [], "complexity_assessment": "bassa"},
                "key_concepts": [],
                "structure": {"has_chapters": False, "estimated_chapters": 0, "sections": [], "complexity": "bassa"},
                "concept_context": f"Contesto minimale per il libro {book_title}. È necessaria analisi manuale.",
                "analysis_quality": "migliorabile"
            },
            "rag_data": {
                "documents_used": 0,
                "total_chunks": 0,
                "coverage_score": 0.0
            }
        }

    def _prepare_content_for_ai(self, documents: List[Dict], max_chars: int = 8000) -> str:
        """
        Prepara i contenuti per l'analisi AI, limitando la lunghezza
        """
        content_parts = []
        total_chars = 0

        for doc in documents:
            content = doc.get("content", "")
            if total_chars + len(content) > max_chars:
                # Tronca l'ultimo contenuto se necessario
                remaining = max_chars - total_chars
                if remaining > 100:  # Include solo se è abbastanza lungo
                    content_parts.append(content[:remaining] + "...")
                break

            content_parts.append(content)
            total_chars += len(content)

        return "\n\n---\n\n".join(content_parts)
