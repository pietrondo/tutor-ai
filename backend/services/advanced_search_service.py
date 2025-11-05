#!/usr/bin/env python3
"""
Advanced Search Service for PDF documents with filters and categories
Supports full-text search, semantic search, and advanced filtering
"""

import os
import re
import json
import asyncio
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from enum import Enum
try:
    from services.rag_service import RAGService
except Exception as import_error:
    RAGService = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchType(Enum):
    TEXT = "text"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"

class SortOrder(Enum):
    RELEVANCE = "relevance"
    DATE = "date"
    ALPHABETICAL = "alphabetical"
    CONFIDENCE = "confidence"

@dataclass
class SearchFilter:
    """Advanced search filters"""
    course_ids: List[str] = None
    book_ids: List[str] = None
    user_ids: List[str] = None
    tags: List[str] = None
    annotation_types: List[str] = None
    date_range: Dict[str, datetime] = None
    confidence_range: Dict[str, float] = None
    page_range: Dict[str, int] = None
    is_public: Optional[bool] = None
    is_favorite: Optional[bool] = None
    min_text_length: Optional[int] = None
    language: Optional[str] = None

@dataclass
class SearchResult:
    """Individual search result"""
    id: str
    type: str  # "annotation", "pdf_content", "ocr_result"
    content: str
    title: str
    source: str  # pdf_filename, annotation_id, etc.
    course_id: str
    book_id: str
    page_number: Optional[int] = None
    user_id: Optional[str] = None
    score: float = 0.0
    confidence: Optional[float] = None
    tags: List[str] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

@dataclass
class SearchQuery:
    """Search query with all parameters"""
    query: str
    search_type: SearchType = SearchType.TEXT
    filters: Optional[SearchFilter] = None
    sort_order: SortOrder = SortOrder.RELEVANCE
    limit: int = 50
    offset: int = 0
    include_highlights: bool = True
    highlight_tags: bool = False

@dataclass
class SearchResponse:
    """Complete search response"""
    query: str
    results: List[SearchResult]
    total_count: int
    has_more: bool
    search_time: float
    facets: Dict[str, Dict[str, int]] = None
    suggestions: List[str] = None

class AdvancedSearchService:
    """Advanced search service for PDF content and annotations"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.annotations_dir = self.data_dir / "annotations"
        self.courses_dir = self.data_dir / "courses"
        self.ocr_results_dir = self.data_dir / "ocr_results"
        self._rag_service: Optional["RAGService"] = None

        # Initialize indexes for fast searching
        self._build_indexes()

    def _build_indexes(self):
        """Build in-memory indexes for fast searching"""
        self.annotations_index = {}
        self.pdf_content_index = {}
        self.ocr_results_index = {}
        if self._rag_service is None and RAGService is None:
            logger.warning("RAGService not available. Semantic search will fall back to text search.")

        # Load annotations into index
        self._load_annotations_index()

        # Load OCR results into index
        self._load_ocr_results_index()

    def _load_annotations_index(self):
        """Load annotations into search index"""
        try:
            if not self.annotations_dir.exists():
                return

            for user_dir in self.annotations_dir.iterdir():
                if not user_dir.is_dir():
                    continue

                user_id = user_dir.name
                self._process_user_annotations(user_id, user_dir)

        except Exception as e:
            logger.error(f"Error loading annotations index: {e}")

    def _process_user_annotations(self, user_id: str, user_dir: Path):
        """Process annotations for a user"""
        try:
            for course_dir in user_dir.iterdir():
                if not course_dir.is_dir():
                    continue

                course_id = course_dir.name
                self._process_course_annotations(user_id, course_id, course_dir)

        except Exception as e:
            logger.error(f"Error processing user {user_id} annotations: {e}")

    def _process_course_annotations(self, user_id: str, course_id: str, course_dir: Path):
        """Process annotations for a course"""
        try:
            for book_dir in course_dir.iterdir():
                if not book_dir.is_dir():
                    continue

                book_id = book_dir.name

                # Process annotation files
                for annotation_file in book_dir.glob("*.json"):
                    self._index_annotation_file(user_id, course_id, book_id, annotation_file)

        except Exception as e:
            logger.error(f"Error processing course {course_id} annotations: {e}")

    def _index_annotation_file(self, user_id: str, course_id: str, book_id: str, annotation_file: Path):
        """Index a single annotation file"""
        try:
            with open(annotation_file, 'r', encoding='utf-8') as f:
                annotations = json.load(f)

            pdf_filename = annotation_file.stem.replace('.json', '')

            for annotation in annotations:
                index_key = f"{user_id}:{course_id}:{book_id}:{annotation['id']}"
                self.annotations_index[index_key] = {
                    **annotation,
                    'user_id': user_id,
                    'course_id': course_id,
                    'book_id': book_id,
                    'pdf_filename': pdf_filename,
                    'indexed_at': datetime.now()
                }

        except Exception as e:
            logger.error(f"Error indexing annotation file {annotation_file}: {e}")

    def _load_ocr_results_index(self):
        """Load OCR results into search index"""
        try:
            if not self.ocr_results_dir.exists():
                return

            for ocr_file in self.ocr_results_dir.glob("*_ocr.txt"):
                self._index_ocr_result_file(ocr_file)

        except Exception as e:
            logger.error(f"Error loading OCR results index: {e}")

    def _index_ocr_result_file(self, ocr_file: Path):
        """Index a single OCR result file"""
        try:
            with open(ocr_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract metadata from the OCR file
            metadata = self._parse_ocr_metadata(content)

            index_key = str(ocr_file)
            self.ocr_results_index[index_key] = {
                'filename': ocr_file.name,
                'content': content,
                'metadata': metadata,
                'indexed_at': datetime.now()
            }

        except Exception as e:
            logger.error(f"Error indexing OCR result file {ocr_file}: {e}")

    def _parse_ocr_metadata(self, ocr_content: str) -> Dict[str, Any]:
        """Parse metadata from OCR content"""
        metadata = {}

        # Extract basic metadata
        lines = ocr_content.split('\n')
        for line in lines:
            if line.startswith("OCR Result for:"):
                metadata['pdf_filename'] = line.split(':', 1)[1].strip()
            elif line.startswith("Total Pages:"):
                metadata['total_pages'] = int(line.split(':')[1].strip())
            elif line.startswith("Average Confidence:"):
                metadata['confidence'] = float(line.split(':')[1].replace('%', '').strip())

        return metadata

    def _get_rag_service(self) -> Optional["RAGService"]:
        """Lazily initialize and return the RAG service for semantic search."""
        if self._rag_service is not None:
            return self._rag_service

        if RAGService is None:
            logger.warning("RAGService import failed; semantic search disabled.")
            return None

        try:
            self._rag_service = RAGService()
            return self._rag_service
        except Exception as exc:
            logger.error(f"Failed to initialize RAGService for semantic search: {exc}")
            return None

    async def search(self, query: SearchQuery) -> SearchResponse:
        """Perform advanced search"""
        start_time = datetime.now()

        try:
            # Determine search strategy based on type
            if query.search_type == SearchType.TEXT:
                results = await self._text_search(query)
            elif query.search_type == SearchType.SEMANTIC:
                results = await self._semantic_search(query)
            else:  # HYBRID
                results = await self._hybrid_search(query)

            # Apply filters
            filtered_results = self._apply_filters(results, query.filters)

            # Sort results
            sorted_results = self._sort_results(filtered_results, query.sort_order)

            # Apply pagination
            total_count = len(sorted_results)
            paginated_results = sorted_results[query.offset:query.offset + query.limit]
            has_more = query.offset + query.limit < total_count

            # Generate highlights if requested
            if query.include_highlights:
                paginated_results = self._add_highlights(paginated_results, query.query)

            # Calculate search time
            search_time = (datetime.now() - start_time).total_seconds()

            # Generate facets and suggestions
            facets = self._generate_facets(paginated_results)
            suggestions = self._generate_suggestions(query.query, paginated_results)

            return SearchResponse(
                query=query.query,
                results=paginated_results,
                total_count=total_count,
                has_more=has_more,
                search_time=search_time,
                facets=facets,
                suggestions=suggestions
            )

        except Exception as e:
            logger.error(f"Error during search: {e}")
            return SearchResponse(
                query=query.query,
                results=[],
                total_count=0,
                has_more=False,
                search_time=(datetime.now() - start_time).total_seconds()
            )

    async def _text_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform text-based search"""
        results = []
        search_terms = self._prepare_search_terms(query.query)

        # Search in annotations
        annotation_results = self._search_annotations(search_terms)
        results.extend(annotation_results)

        # Search in OCR results
        ocr_results = self._search_ocr_results(search_terms)
        results.extend(ocr_results)

        # Calculate relevance scores
        results = self._calculate_text_relevance_scores(results, search_terms)

        return results

    def _prepare_search_terms(self, query: str) -> List[str]:
        """Prepare search terms for matching"""
        # Convert to lowercase and split
        terms = query.lower().strip().split()

        # Remove common stop words
        stop_words = {'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'una', 'dei', 'delle', 'del', 'della', 'in', 'con', 'su', 'per', 'tra', 'fra', 'a', 'da', 'di', 'che', 'e', 'è', 'non'}
        terms = [term for term in terms if term not in stop_words]

        return terms

    def _search_annotations(self, search_terms: List[str]) -> List[SearchResult]:
        """Search in annotations index"""
        results = []

        for index_key, annotation in self.annotations_index.items():
            score = 0.0
            content_matches = []

            # Search in selected_text
            if 'selected_text' in annotation:
                for term in search_terms:
                    if term in annotation['selected_text'].lower():
                        score += 1.0
                        content_matches.append(term)

            # Search in content/notes
            if 'content' in annotation and annotation['content']:
                for term in search_terms:
                    if term in annotation['content'].lower():
                        score += 0.8
                        content_matches.append(term)

            # Search in tags
            if 'tags' in annotation:
                for term in search_terms:
                    for tag in annotation['tags']:
                        if term in tag.lower():
                            score += 0.5
                            content_matches.append(term)

            if score > 0:
                result = SearchResult(
                    id=annotation['id'],
                    type="annotation",
                    content=annotation.get('selected_text', ''),
                    title=f"Annotation in {annotation.get('pdf_filename', 'Unknown')}",
                    source=annotation['id'],
                    course_id=annotation['course_id'],
                    book_id=annotation['book_id'],
                    page_number=annotation.get('page_number'),
                    user_id=annotation['user_id'],
                    score=score,
                    tags=annotation.get('tags', []),
                    created_at=datetime.fromisoformat(annotation['created_at']) if 'created_at' in annotation else None,
                    metadata={
                        'annotation_type': annotation.get('type'),
                        'is_public': annotation.get('is_public', False),
                        'is_favorite': annotation.get('is_favorite', False),
                        'matched_terms': list(set(content_matches))
                    }
                )
                results.append(result)

        return results

    def _search_ocr_results(self, search_terms: List[str]) -> List[SearchResult]:
        """Search in OCR results index"""
        results = []

        for index_key, ocr_result in self.ocr_results_index.items():
            score = 0.0
            content_matches = []

            content_lower = ocr_result['content'].lower()

            for term in search_terms:
                occurrences = content_lower.count(term)
                if occurrences > 0:
                    score += occurrences * 0.1
                    content_matches.append(term)

            if score > 0:
                metadata = ocr_result['metadata']
                result = SearchResult(
                    id=index_key,
                    type="ocr_result",
                    content=ocr_result['content'],
                    title=f"OCR Result: {metadata.get('pdf_filename', 'Unknown')}",
                    source=index_key,
                    course_id="",  # OCR results don't have course context
                    book_id="",   # OCR results don't have book context
                    score=score,
                    confidence=metadata.get('confidence'),
                    metadata={
                        'total_pages': metadata.get('total_pages'),
                        'matched_terms': list(set(content_matches))
                    }
                )
                results.append(result)

        return results

    def _calculate_text_relevance_scores(self, results: List[SearchResult], search_terms: List[str]) -> List[SearchResult]:
        """Calculate and normalize relevance scores"""
        if not results:
            return results

        # Find max score for normalization
        max_score = max(result.score for result in results)

        if max_score > 0:
            # Normalize scores
            for result in results:
                result.score = (result.score / max_score) * 100.0

        # Sort by score (descending)
        results.sort(key=lambda x: x.score, reverse=True)

        return results

    async def _semantic_search(self, query: SearchQuery, allow_text_fallback: bool = True) -> List[SearchResult]:
        """Perform semantic search leveraging the vector database when available."""
        rag_service = self._get_rag_service()
        if not rag_service or not getattr(rag_service, "collection", None):
            logger.warning("Semantic search unavailable: RAG service not ready.")
            if allow_text_fallback:
                return await self._text_search(query)
            return []

        try:
            rag_service._load_embedding_model()
            query_embedding = rag_service.embedding_model.encode([query.query]).tolist()
        except Exception as exc:
            logger.error(f"Failed to compute embeddings for semantic search: {exc}")
            if allow_text_fallback:
                return await self._text_search(query)
            return []

        where_filter = self._build_vector_where_filter(query.filters)
        search_k = max(query.limit + query.offset, 10)

        try:
            vector_results = rag_service.collection.query(
                query_embeddings=query_embedding,
                n_results=search_k,
                where=where_filter
            )
        except Exception as exc:
            logger.error(f"Vector search failed: {exc}")
            if allow_text_fallback:
                return await self._text_search(query)
            return []

        documents = vector_results.get("documents", [[]])
        metadatas = vector_results.get("metadatas", [[]])
        distances = vector_results.get("distances", [[]])
        ids = vector_results.get("ids", [[]])

        if not documents or not documents[0]:
            logger.info("Semantic search returned no vector matches.")
            return []

        semantic_results: List[SearchResult] = []

        for idx, content in enumerate(documents[0]):
            metadata = (metadatas[0][idx] if idx < len(metadatas[0]) else {}) or {}
            distance = distances[0][idx] if distances and distances[0] and idx < len(distances[0]) else None
            record_id = ids[0][idx] if ids and ids[0] and idx < len(ids[0]) else f"semantic-{idx}"

            # Convert distance (lower is better) to a percentage score.
            score = 0.0
            if distance is not None:
                score = max(0.0, (1.0 - distance) * 100.0)

            source_value = metadata.get("source") or record_id

            page_number = metadata.get("page") if "page" in metadata else metadata.get("page_number")
            if isinstance(page_number, str):
                page_number = int(page_number) if page_number.isdigit() else None
            elif not isinstance(page_number, int):
                page_number = None

            semantic_results.append(SearchResult(
                id=record_id,
                type="pdf_content",
                content=content or "",
                title=f"Contenuto PDF: {metadata.get('source') or 'Materiale'}",
                source=source_value,
                course_id=str(metadata.get("course_id") or ""),
                book_id=str(metadata.get("book_id") or ""),
                page_number=page_number,
                score=score,
                metadata={
                    "chunk_index": metadata.get("chunk_index"),
                    "total_chunks": metadata.get("total_chunks"),
                    "distance": distance,
                    "matched_terms": [],
                    "source": source_value
                }
            ))

        # Normalize scores to align with text search scale
        semantic_results = self._calculate_text_relevance_scores(semantic_results, [])
        return semantic_results

    async def _hybrid_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform hybrid search combining text and semantic results."""
        text_results = await self._text_search(query)
        semantic_results = await self._semantic_search(query, allow_text_fallback=False)

        combined: Dict[str, SearchResult] = {}

        def make_key(result: SearchResult) -> str:
            return f"{result.type}:{result.source}:{result.page_number or 0}:{result.id}"

        for result in text_results:
            combined[make_key(result)] = result

        for result in semantic_results:
            key = make_key(result)
            if key in combined:
                existing = combined[key]
                existing.score = max(existing.score, result.score)
                if result.metadata:
                    if existing.metadata:
                        merged_metadata = {**result.metadata, **existing.metadata}
                        existing.metadata = merged_metadata
                    else:
                        existing.metadata = result.metadata
            else:
                combined[key] = result

        return sorted(combined.values(), key=lambda x: x.score, reverse=True)

    def _apply_filters(self, results: List[SearchResult], filters: Optional[SearchFilter]) -> List[SearchResult]:
        """Apply advanced filters to search results"""
        if not filters:
            return results

        filtered_results = results

        # Course ID filter
        if filters.course_ids:
            filtered_results = [r for r in filtered_results if r.course_id in filters.course_ids]

        # Book ID filter
        if filters.book_ids:
            filtered_results = [r for r in filtered_results if r.book_id in filters.book_ids]

        # User ID filter
        if filters.user_ids:
            filtered_results = [r for r in filtered_results if r.user_id in filters.user_ids]

        # Tags filter
        if filters.tags:
            filtered_results = [
                r for r in filtered_results
                if r.tags and any(tag in r.tags for tag in filters.tags)
            ]

        # Annotation types filter
        if filters.annotation_types:
            filtered_results = [
                r for r in filtered_results
                if r.metadata and r.metadata.get('annotation_type') in filters.annotation_types
            ]

        # Date range filter
        if filters.date_range and 'start' in filters.date_range and 'end' in filters.date_range:
            filtered_results = [
                r for r in filtered_results
                if r.created_at and filters.date_range['start'] <= r.created_at <= filters.date_range['end']
            ]

        # Confidence range filter
        if filters.confidence_range and 'min' in filters.confidence_range and 'max' in filters.confidence_range:
            filtered_results = [
                r for r in filtered_results
                if r.confidence and filters.confidence_range['min'] <= r.confidence <= filters.confidence_range['max']
            ]

        # Page range filter
        if filters.page_range and 'min' in filters.page_range and 'max' in filters.page_range:
            filtered_results = [
                r for r in filtered_results
                if r.page_number and filters.page_range['min'] <= r.page_number <= filters.page_range['max']
            ]

        # Public filter
        if filters.is_public is not None:
            filtered_results = [
                r for r in filtered_results
                if r.metadata and r.metadata.get('is_public') == filters.is_public
            ]

        # Favorite filter
        if filters.is_favorite is not None:
            filtered_results = [
                r for r in filtered_results
                if r.metadata and r.metadata.get('is_favorite') == filters.is_favorite
            ]

        # Minimum text length filter
        if filters.min_text_length:
            filtered_results = [
                r for r in filtered_results
                if len(r.content) >= filters.min_text_length
            ]

        return filtered_results

    def _sort_results(self, results: List[SearchResult], sort_order: SortOrder) -> List[SearchResult]:
        """Sort search results"""
        if sort_order == SortOrder.RELEVANCE:
            return sorted(results, key=lambda x: x.score, reverse=True)
        elif sort_order == SortOrder.DATE:
            return sorted(results, key=lambda x: x.created_at or datetime.min, reverse=True)
        elif sort_order == SortOrder.ALPHABETICAL:
            return sorted(results, key=lambda x: x.title.lower())
        elif sort_order == SortOrder.CONFIDENCE:
            return sorted(results, key=lambda x: x.confidence or 0, reverse=True)
        else:
            return results

    def _add_highlights(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Add search highlights to results"""
        search_terms = self._prepare_search_terms(query)

        for result in results:
            if result.metadata:
                result.metadata['highlights'] = self._generate_highlights(result.content, search_terms)

        return results

    def _generate_highlights(self, content: str, search_terms: List[str]) -> List[str]:
        """Generate highlighted snippets"""
        highlights = []
        content_lower = content.lower()

        for term in search_terms:
            # Find first occurrence of term
            pos = content_lower.find(term)
            if pos != -1:
                # Extract snippet around the term
                start = max(0, pos - 50)
                end = min(len(content), pos + len(term) + 50)
                snippet = content[start:end]

                # Highlight the term
                highlighted_term = f"**{content[pos:pos+len(term)]}**"
                snippet = snippet.lower().replace(term, highlighted_term)

                highlights.append(snippet)
                break  # Only one highlight per term for now

        return highlights

    def _build_vector_where_filter(self, filters: Optional[SearchFilter]) -> Optional[Dict[str, Any]]:
        """Translate search filters into ChromaDB where clauses."""
        if not filters:
            return None

        where_filter: Dict[str, Any] = {}

        if filters.course_ids:
            if len(filters.course_ids) == 1:
                where_filter["course_id"] = filters.course_ids[0]
            else:
                where_filter["course_id"] = {"$in": filters.course_ids}

        if filters.book_ids:
            if len(filters.book_ids) == 1:
                where_filter["book_id"] = filters.book_ids[0]
            else:
                where_filter["book_id"] = {"$in": filters.book_ids}

        return where_filter or None

    def _generate_facets(self, results: List[SearchResult]) -> Dict[str, Dict[str, int]]:
        """Generate search facets for filtering"""
        facets = {}

        # Course facets
        course_counts = {}
        for result in results:
            if result.course_id:
                course_counts[result.course_id] = course_counts.get(result.course_id, 0) + 1

        if course_counts:
            facets['courses'] = course_counts

        # User facets
        user_counts = {}
        for result in results:
            if result.user_id:
                user_counts[result.user_id] = user_counts.get(result.user_id, 0) + 1

        if user_counts:
            facets['users'] = user_counts

        # Tag facets
        tag_counts = {}
        for result in results:
            if result.tags:
                for tag in result.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        if tag_counts:
            facets['tags'] = tag_counts

        # Type facets
        type_counts = {}
        for result in results:
            type_counts[result.type] = type_counts.get(result.type, 0) + 1

        if type_counts:
            facets['types'] = type_counts

        return facets

    def _generate_suggestions(self, query: str, results: List[SearchResult]) -> List[str]:
        """Generate search suggestions"""
        suggestions = []

        # Extract common terms from results
        all_terms = set()
        for result in results[:10]:  # Top 10 results
            words = re.findall(r'\b\w+\b', result.content.lower())
            all_terms.update(words)

        # Filter out query terms and common words
        query_terms = set(query.lower().split())
        stop_words = {'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'una', 'dei', 'delle', 'del', 'della', 'in', 'con', 'su', 'per', 'tra', 'fra'}

        suggestions = [
            term for term in all_terms
            if term not in query_terms and term not in stop_words and len(term) > 3
        ][:5]  # Top 5 suggestions

        return suggestions

    def get_search_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """Get autocomplete suggestions"""
        suggestions = []

        # This is a simple implementation - in production, you'd use a proper autocomplete service
        for index_key, annotation in self.annotations_index.items():
            content = annotation.get('selected_text', '') + ' ' + annotation.get('content', '')
            words = re.findall(r'\b\w+\b', content.lower())

            for word in words:
                if word.startswith(partial_query.lower()) and len(word) > len(partial_query):
                    suggestions.append(word)

        # Remove duplicates and limit
        suggestions = list(set(suggestions))[:limit]

        return suggestions

    def rebuild_indexes(self):
        """Rebuild search indexes"""
        logger.info("Rebuilding search indexes...")
        self.annotations_index.clear()
        self.pdf_content_index.clear()
        self.ocr_results_index.clear()
        self._build_indexes()
        logger.info("Search indexes rebuilt successfully")

# Global instance
advanced_search_service = AdvancedSearchService()
