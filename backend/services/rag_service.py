import chromadb
import os
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

logger = structlog.get_logger()

class RAGService:
    def __init__(self):
        # Lazy loading - non caricare il modello all'avvio
        self.embedding_model = None
        self.model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
        self.chroma_client = chromadb.PersistentClient(path="data/vector_db")
        self.collection = None
        self.setup_collection()
        logger.info("RAG Service initialized (model will be loaded on demand)", model=self.model_name)

    def _load_embedding_model(self):
        """Carica il modello di embedding solo quando necessario"""
        if self.embedding_model is None:
            logger.info("Loading embedding model...")
            try:
                self.embedding_model = SentenceTransformer(self.model_name)
                logger.info("Embedding model loaded successfully")
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

    def split_text_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            if end >= len(text):
                chunks.append(text[start:])
                break

            # Try to find a good breaking point (period, newline, or space)
            chunk = text[start:end]
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            last_space = chunk.rfind(' ')

            best_break = max(last_period, last_newline, last_space)

            if best_break > start + chunk_size // 2:  # Don't go back too far
                end = start + best_break + 1

            chunks.append(text[start:end])
            start = end - overlap

        return [chunk.strip() for chunk in chunks if chunk.strip()]

    async def retrieve_context(self, query: str, course_id: str, book_id: Optional[str] = None, k: int = 5) -> Dict[str, Any]:
        """Retrieve relevant context for a query"""
        try:
            # Generate query embedding
            self._load_embedding_model()
            query_embedding = self.embedding_model.encode([query]).tolist()

            # Build filter based on course_id and optional book_id
            where_filter = {"course_id": course_id}
            if book_id:
                where_filter["book_id"] = book_id

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
                    limit=1000
                )

            # Group by source document
            documents_by_source = {}

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
                documents_by_source[source]["total_chunks"] = metadata.get('total_chunks', len(documents_by_source[source]["chunks"]))

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
                where={"course_id": course_id, "book_id": book_id}
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