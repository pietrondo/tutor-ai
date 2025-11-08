#!/usr/bin/env python3
"""
Sistema ibrido di concept maps che combina pre-generate + RAG on-demand
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from fastapi import HTTPException
from services.llm_service import LLMService
from services.rag_service import RAGService

class HybridConceptRequest(BaseModel):
    course_id: str
    book_id: Optional[str] = None
    depth_level: str = "basic"  # "basic", "detailed", "comprehensive"
    include_rag_analysis: bool = False
    focus_topics: Optional[List[str]] = None

class HybridConceptService:
    def __init__(self):
        self.llm_service = LLMService()
        self.rag_service = RAGService()

    async def get_hybrid_concepts(self, request: HybridConceptRequest) -> Dict[str, Any]:
        """
        Sistema ibrido: concept maps pre-generate + RAG analysis on-demand
        """
        try:
            # 1. Carica concept maps base pre-generate (veloce)
            base_concepts = await self._load_base_concepts(request.course_id, request.book_id)

            if not base_concepts:
                raise HTTPException(status_code=404, detail="Concept maps not found")

            result = {
                "success": True,
                "course_id": request.course_id,
                "book_id": request.book_id,
                "depth_level": request.depth_level,
                "base_concepts": base_concepts,
                "rag_analysis": None,
                "enhanced_concepts": None
            }

            # 2. Aggiungi RAG analysis solo se richiesto
            if request.include_rag_analysis and request.depth_level in ["detailed", "comprehensive"]:
                rag_analysis = await self._get_rag_analysis(request)
                result["rag_analysis"] = rag_analysis

                # 3. Combina base concepts con RAG insights
                enhanced_concepts = await self._enhance_concepts_with_rag(
                    base_concepts, rag_analysis, request.focus_topics
                )
                result["enhanced_concepts"] = enhanced_concepts

            return result

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def _load_base_concepts(self, course_id: str, book_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Carica concept maps pre-generate dal file JSON"""
        try:
            concept_maps_path = Path("data/concept_maps.json")

            if not concept_maps_path.exists():
                return None

            with open(concept_maps_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if course_id not in data.get("concept_maps", {}):
                return None

            course_data = data["concept_maps"][course_id]

            if book_id and "books" in course_data and book_id in course_data["books"]:
                return course_data["books"][book_id]

            return course_data

        except Exception as e:
            print(f"Error loading base concepts: {e}")
            return None

    async def _get_rag_analysis(self, request: HybridConceptRequest) -> Dict[str, Any]:
        """
        RAG analysis ottimizzato per approfondimenti on-demand
        """
        try:
            # Costruisci query RAG specifica per il libro
            rag_query = self._build_rag_query(request)

            # Esegui RAG con limitazione per performance
            rag_results = await self._execute_optimized_rag(
                course_id=request.course_id,
                book_id=request.book_id,
                query=rag_query,
                max_results=5 if request.depth_level == "detailed" else 8
            )

            return {
                "query": rag_query,
                "results": rag_results["results"][:5],  # Limita per performance
                "key_insights": rag_results.get("key_insights", []),
                "sources_count": len(rag_results.get("sources", [])),
                "processing_time": rag_results.get("processing_time", 0)
            }

        except Exception as e:
            print(f"RAG analysis error: {e}")
            return {"error": str(e), "results": []}

    def _build_rag_query(self, request: HybridConceptRequest) -> str:
        """
        Costruisce query RAG specifica basata sul libro e livello di dettaglio
        """
        base_query = f"Analisi approfondita dei concetti chiave"

        if request.book_id:
            # Recupera titolo del libro per query più specifica
            book_title = self._get_book_title(request.course_id, request.book_id)
            base_query = f"Concetti fondamentali e temi principali del libro '{book_title}'"

        if request.focus_topics:
            topics_str = ", ".join(request.focus_topics)
            base_query += f" con focus su: {topics_str}"

        if request.depth_level == "comprehensive":
            base_query += ". Includi analisi dettagliata, contesto storico, collegamenti con altri concetti, e implicazioni pratiche."
        elif request.depth_level == "detailed":
            base_query += ". Includi spiegazioni dettagliate dei concetti principali."

        return base_query

    def _get_book_title(self, course_id: str, book_id: str) -> str:
        """Recupera titolo del libro per query RAG"""
        try:
            concept_maps_path = Path("data/concept_maps.json")
            with open(concept_maps_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if course_id in data.get("concept_maps", {}):
                books = data["concept_maps"][course_id].get("books", {})
                if book_id in books:
                    return books[book_id].get("book_title", "Libro sconosciuto")

        except Exception:
            pass
        return "Libro"

    async def _execute_optimized_rag(self, course_id: str, book_id: Optional[str],
                                   query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Esegui RAG ottimizzato con filtri specifici per libro e limitazione risultati
        """
        try:
            # Filtra source documents per libro specifico se book_id è fornito
            book_filter = f"books/{book_id}" if book_id else None

            # RAG con parametri ottimizzati
            rag_request = {
                "course_id": course_id,
                "query": query,
                "max_results": max_results,
                "include_sources": True,
                "similarity_threshold": 0.7,  # Soglia più alta per qualità
                "source_filter": book_filter
            }

            # Esegui RAG con timeout
            result = await asyncio.wait_for(
                self.rag_service.search(rag_request),
                timeout=30.0  # 30 secondi max per RAG
            )

            return result

        except asyncio.TimeoutError:
            return {"results": [], "error": "RAG timeout", "sources": []}
        except Exception as e:
            return {"results": [], "error": str(e), "sources": []}

    async def _enhance_concepts_with_rag(self, base_concepts: Dict[str, Any],
                                       rag_analysis: Dict[str, Any],
                                       focus_topics: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Combina concept maps base con insights dal RAG
        """
        enhanced = []

        # Arricchisci ogni concetto base con insights RAG
        if "concepts" in base_concepts:
            for concept in base_concepts["concepts"]:
                enhanced_concept = concept.copy()

                # Aggiungi insights RAG rilevanti
                rag_insights = self._extract_relevant_insights(
                    concept, rag_analysis.get("results", [])
                )

                if rag_insights:
                    enhanced_concept["rag_insights"] = rag_insights
                    enhanced_concept["enhanced_summary"] = self._combine_summaries(
                        concept.get("summary", ""), rag_insights
                    )

                enhanced.append(enhanced_concept)

        # Aggiungi nuovi concetti scoperti dal RAG
        new_concepts = self._extract_new_concepts_from_rag(
            base_concepts, rag_analysis, focus_topics
        )
        enhanced.extend(new_concepts)

        return enhanced

    def _extract_relevant_insights(self, concept: Dict[str, Any],
                                 rag_results: List[Dict[str, Any]]) -> List[str]:
        """Estrai insights RAG rilevanti per un concetto specifico"""
        insights = []
        concept_name = concept.get("name", "").lower()
        concept_topics = [topic.lower() for topic in concept.get("related_topics", [])]

        for result in rag_results:
            content = result.get("content", "").lower()

            # Controlla se il contenuto RAG è rilevante per questo concetto
            if (concept_name in content or
                any(topic in content for topic in concept_topics)):

                insight = result.get("content", "")[:300]  # Limita lunghezza
                if insight not in insights:
                    insights.append(insight)

        return insights[:3]  # Max 3 insights per concetto

    def _combine_summaries(self, base_summary: str, rag_insights: List[str]) -> str:
        """Combina summary base con insights RAG"""
        if not rag_insights:
            return base_summary

        combined = base_summary + "\n\nApprofondimenti:\n"
        for i, insight in enumerate(rag_insights, 1):
            combined += f"{i}. {insight}\n"

        return combined

    def _extract_new_concepts_from_rag(self, base_concepts: Dict[str, Any],
                                     rag_analysis: Dict[str, Any],
                                     focus_topics: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Estrai nuovi concetti scoperti dal RAG non presenti nelle concept maps base"""
        new_concepts = []
        base_concept_names = {c.get("name", "").lower() for c in base_concepts.get("concepts", [])}

        for result in rag_analysis.get("results", []):
            content = result.get("content", "")

            # Identifica potenziali nuovi concetti nel contenuto RAG
            potential_concepts = self._identify_concepts_in_text(content)

            for concept_name in potential_concepts:
                if concept_name.lower() not in base_concept_names:
                    new_concept = {
                        "id": f"rag-discovered-{len(new_concepts)}",
                        "name": concept_name,
                        "summary": f"Concepto scoperto tramite analisi RAG: {concept_name}",
                        "source": "rag_analysis",
                        "related_topics": focus_topics or [],
                        "learning_objectives": [
                            f"Comprendere {concept_name.lower()}",
                            "Analizzare il contesto e le implicazioni"
                        ],
                        "recommended_minutes": 30,
                        "quiz_outline": [
                            f"Spiegare {concept_name.lower()}",
                            "Analizzare il contesto"
                        ]
                    }
                    new_concepts.append(new_concept)

        return new_concepts[:2]  # Max 2 nuovi concetti per evitare overload

    def _identify_concepts_in_text(self, text: str) -> List[str]:
        """Identifica concetti principali nel testo RAG"""
        # Estrai frasi che potrebbero contenere concetti
        import re

        # Pattern per identificare concetti (parole in maiuscolo, termini specifici, etc.)
        concept_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Parole in maiuscolo
            r'\bconcetto\s+di\s+([^\s]+(?:\s+[^\s]+)*)',  # "concetto di X"
            r'\bprincipio\s+di\s+([^\s]+(?:\s+[^\s]+)*)',  # "principio di X"
            r'\bteoria\s+([^\s]+(?:\s+[^\s]+)*)',  # "teoria X"
        ]

        concepts = set()
        for pattern in concept_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            concepts.update(matches)

        return list(concepts)[:5]  # Max 5 concetti identificati

# Istanza globale del servizio
hybrid_service = HybridConceptService()

async def get_hybrid_concepts(request: HybridConceptRequest) -> Dict[str, Any]:
    """
    API endpoint per sistema ibrido di concept maps
    """
    return await hybrid_service.get_hybrid_concepts(request)