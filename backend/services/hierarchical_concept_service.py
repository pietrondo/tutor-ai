"""
Hierarchical Concept Service
Creates and manages hierarchical concept structures from course materials
"""

import json
import uuid
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import structlog

logger = structlog.get_logger()


class HierarchicalConceptService:
    """Service for creating and managing hierarchical concept maps"""

    def __init__(self) -> None:
        self.concept_store_path = "data/concept_maps.json"

    def _load_concept_maps(self) -> Dict[str, Any]:
        """Load existing concept maps from storage"""
        try:
            with open(self.concept_store_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"concept_maps": {}}
        except Exception as e:
            logger.error(f"Error loading concept maps: {e}")
            return {"concept_maps": {}}

    def _save_concept_maps(self, data: Dict[str, Any]) -> None:
        """Save concept maps to storage"""
        try:
            with open(self.concept_store_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving concept maps: {e}")

    def create_hierarchical_structure(
        self,
        course_id: str,
        course_name: str,
        flat_concepts: List[Dict[str, Any]],
        book_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create hierarchical concept structure from flat concepts
        Level 1: Macro concepts (chapters/major themes)
        Level 2+: Sub-concepts (detailed topics)
        """

        if not flat_concepts:
            return self._create_empty_structure(course_id, course_name, book_id)

        # Group concepts by chapters/sections for Level 1
        macro_concepts = self._group_by_chapters(flat_concepts)

        # Create hierarchical structure
        hierarchical_concepts = []

        for macro_group in macro_concepts:
            macro_concept = self._create_macro_concept(macro_group, course_id, book_id)

            # Create sub-concepts for this macro concept
            sub_concepts = self._create_sub_concepts(
                macro_group["concepts"],
                macro_concept["id"],
                course_id,
                book_id
            )

            macro_concept["children"] = sub_concepts
            hierarchical_concepts.append(macro_concept)

        # Create the complete structure
        structure = {
            "course_id": course_id,
            "course_name": course_name,
            "generated_at": datetime.now().isoformat(),
            "structure_type": "hierarchical",
            "source_count": len(flat_concepts),
            "macro_concepts_count": len(macro_concepts),
            "book_id": book_id,
            "concepts": hierarchical_concepts,
            "metadata": {
                "hierarchy_levels": self._calculate_hierarchy_depth(hierarchical_concepts),
                "expansion_state": "collapsed",  # Start with everything collapsed
                "generation_method": "hierarchical_ai_organization"
            }
        }

        return structure

    def _group_by_chapters(self, concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group concepts by chapters or create thematic groups"""
        groups = []
        chapter_groups = {}

        # Group by existing chapters
        for concept in concepts:
            chapter = concept.get("chapter")
            if chapter and chapter.get("title"):
                chapter_key = f"chapter_{chapter['index']}"
                if chapter_key not in chapter_groups:
                    chapter_groups[chapter_key] = {
                        "type": "chapter",
                        "title": chapter["title"],
                        "index": chapter["index"],
                        "concepts": []
                    }
                chapter_groups[chapter_key]["concepts"].append(concept)
            else:
                # Group by theme if no chapter
                theme = self._extract_theme(concept)
                if theme not in chapter_groups:
                    chapter_groups[theme] = {
                        "type": "theme",
                        "title": theme.replace("_", " ").title(),
                        "concepts": []
                    }
                chapter_groups[theme]["concepts"].append(concept)

        # Convert to sorted list
        sorted_groups = sorted(
            chapter_groups.values(),
            key=lambda x: x["index"] if x["type"] == "chapter" else 999
        )

        return sorted_groups

    def _extract_theme(self, concept: Dict[str, Any]) -> str:
        """Extract theme from concept name and topics"""
        name = concept.get("name", "").lower()
        related_topics = concept.get("related_topics", [])

        # Common themes mapping
        theme_keywords = {
            "fondamenti": ["fondamentale", "base", "introduzione", "concetti base"],
            "teoria": ["teoria", "principi", "modelli", "framework"],
            "pratica": ["pratica", "applicazione", "esercizi", "esempi"],
            "storia": ["storia", "evoluzione", "sviluppo", "cronologia"],
            "geografia": ["geografia", "territorio", "spazio", "luogo"],
            "economia": ["economia", "mercato", "finanza", "produzione"],
            "politica": ["politica", "governo", "istituzioni", "leggi"],
            "cultura": ["cultura", "arte", "letteratura", "tradizioni"],
            "tecnologia": ["tecnologia", "digitale", "informatica", "innovazione"],
            "ambiente": ["ambiente", "ecologia", "sostenibile", "natura"],
            "società": ["società", "sociale", "comunità", "gruppi"]
        }

        for theme, keywords in theme_keywords.items():
            if any(keyword in name for keyword in keywords):
                return theme

        for topic in related_topics:
            for theme, keywords in theme_keywords.items():
                if any(keyword in topic.lower() for keyword in keywords):
                    return theme

        return "concetti_vari"  # Default theme

    def _create_macro_concept(
        self,
        group: Dict[str, Any],
        course_id: str,
        book_id: Optional[str]
    ) -> Dict[str, Any]:
        """Create a macro concept from a group of concepts"""
        group_id = f"macro_{group['title'].lower().replace(' ', '-').replace(',', '')}"

        # Generate summary from group concepts
        concepts_in_group = group["concepts"]
        summary = self._generate_macro_summary(concepts_in_group, group["title"])

        # Combine learning objectives
        all_objectives = []
        for concept in concepts_in_group:
            all_objectives.extend(concept.get("learning_objectives", []))

        # Combine related topics
        all_topics = []
        for concept in concepts_in_group:
            all_topics.extend(concept.get("related_topics", []))
        unique_topics = list(set(all_topics))

        # Calculate importance based on sources
        total_sources = sum(concept.get("source_materials_count", 0) for concept in concepts_in_group)

        macro_concept = {
            "id": group_id,
            "name": group["title"],
            "summary": summary,
            "level": 1,  # Macro level
            "concept_type": "macro",
            "importance_score": min(total_sources / 10, 1.0),  # Normalized 0-1
            "related_topics": unique_topics[:10],  # Limit topics
            "learning_objectives": all_objectives[:8],  # Limit objectives
            "suggested_reading": self._combine_suggested_reading(concepts_in_group),
            "recommended_minutes": sum(concept.get("recommended_minutes", 30) for concept in concepts_in_group),
            "chapter_info": group if group["type"] == "chapter" else None,
            "sub_concepts_count": len(concepts_in_group),
            "source_materials_count": total_sources,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source_concepts": [c["id"] for c in concepts_in_group],
                "expansion_type": "manual_or_ai",
                "course_id": course_id,
                "book_id": book_id
            }
        }

        return macro_concept

    def _create_sub_concepts(
        self,
        concepts: List[Dict[str, Any]],
        parent_id: str,
        course_id: str,
        book_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Create sub-concepts from flat concepts"""
        sub_concepts = []

        for i, concept in enumerate(concepts):
            sub_concept_id = f"sub_{concept['id']}"

            sub_concept = {
                "id": sub_concept_id,
                "parent_id": parent_id,
                "name": concept["name"],
                "summary": concept.get("summary", ""),
                "level": 2,  # Sub-concept level
                "concept_type": "sub",
                "importance_score": min(concept.get("source_materials_count", 0) / 5, 1.0),
                "related_topics": concept.get("related_topics", []),
                "learning_objectives": concept.get("learning_objectives", []),
                "suggested_reading": concept.get("suggested_reading", []),
                "recommended_minutes": concept.get("recommended_minutes", 30),
                "quiz_outline": concept.get("quiz_outline", []),
                "chapter_info": concept.get("chapter"),
                "source_materials_count": concept.get("source_materials_count", 0),
                "material_sources": concept.get("material_sources", []),
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "original_concept_id": concept["id"],
                    "expansion_type": "ai_enhanced",
                    "course_id": course_id,
                    "book_id": book_id,
                    "depth_available": True  # Can be expanded further with AI
                }
            }

            sub_concepts.append(sub_concept)

        return sub_concepts

    def _generate_macro_summary(self, concepts: List[Dict[str, Any]], group_title: str) -> str:
        """Generate a summary for the macro concept"""
        if len(concepts) == 1:
            return concepts[0].get("summary", f"Studio approfondito di {group_title}")

        # Combine summaries from multiple concepts
        summaries = [c.get("summary", "") for c in concepts if c.get("summary")]
        if summaries:
            return f"Analisi completa di {group_title}: {' | '.join(summaries[:2])}"

        return f"Esplorazione tematica di {group_title} con approccio multidisciplinare"

    def _combine_suggested_reading(self, concepts: List[Dict[str, Any]]) -> List[str]:
        """Combine and deduplicate suggested readings"""
        all_readings = []
        seen = set()

        for concept in concepts:
            for reading in concept.get("suggested_reading", []):
                if reading not in seen:
                    all_readings.append(reading)
                    seen.add(reading)

        return all_readings[:10]  # Limit to 10 readings

    def _calculate_hierarchy_depth(self, concepts: List[Dict[str, Any]]) -> int:
        """Calculate the maximum depth of the hierarchy"""
        if not concepts:
            return 0

        max_depth = 1
        for concept in concepts:
            if "children" in concept and concept["children"]:
                child_depth = self._calculate_hierarchy_depth(concept["children"])
                max_depth = max(max_depth, child_depth + 1)

        return max_depth

    def _create_empty_structure(
        self,
        course_id: str,
        course_name: str,
        book_id: Optional[str]
    ) -> Dict[str, Any]:
        """Create an empty structure when no concepts are available"""
        return {
            "course_id": course_id,
            "course_name": course_name,
            "generated_at": datetime.now().isoformat(),
            "structure_type": "hierarchical",
            "source_count": 0,
            "macro_concepts_count": 0,
            "book_id": book_id,
            "concepts": [],
            "metadata": {
                "hierarchy_levels": 0,
                "expansion_state": "empty",
                "generation_method": "hierarchical_empty"
            }
        }

    def expand_concept_with_ai(
        self,
        course_id: str,
        book_id: Optional[str],
        concept_id: str,
        expansion_depth: int = 1
    ) -> Dict[str, Any]:
        """
        Expand a concept using AI to create deeper hierarchy levels
        """
        # This would integrate with the existing AI expansion service
        # For now, return a placeholder structure
        return {
            "success": False,
            "message": "AI expansion not yet implemented in hierarchical service",
            "expanded_concepts": []
        }

    def get_hierarchy_statistics(self, course_id: str, book_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about the hierarchical structure"""
        data = self._load_concept_maps()

        if book_id:
            # Get book-specific data
            course_data = data["concept_maps"].get(course_id, {})
            if "books" in course_data and book_id in course_data["books"]:
                concept_map = course_data["books"][book_id]
            else:
                return {"error": "Book concept map not found"}
        else:
            # Get course-wide data
            concept_map = data["concept_maps"].get(course_id)
            if not concept_map:
                return {"error": "Course concept map not found"}

        if concept_map.get("structure_type") != "hierarchical":
            return {"error": "Not a hierarchical structure"}

        stats = {
            "total_concepts": self._count_total_concepts(concept_map.get("concepts", [])),
            "macro_concepts": len(concept_map.get("concepts", [])),
            "max_depth": concept_map.get("metadata", {}).get("hierarchy_levels", 0),
            "structure_type": concept_map.get("structure_type"),
            "generation_method": concept_map.get("metadata", {}).get("generation_method", "unknown"),
            "expansion_potential": self._calculate_expansion_potential(concept_map.get("concepts", []))
        }

        return stats

    def _count_total_concepts(self, concepts: List[Dict[str, Any]]) -> int:
        """Count total concepts including nested ones"""
        total = len(concepts)
        for concept in concepts:
            if "children" in concept:
                total += self._count_total_concepts(concept["children"])
        return total

    def _calculate_expansion_potential(self, concepts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate how many concepts can be expanded"""
        expandable = 0
        fully_expanded = 0

        for concept in concepts:
            if concept.get("level", 1) < 3:  # Can expand up to level 3
                expandable += 1
                if concept.get("children"):
                    fully_expanded += 1

        return {
            "expandable_concepts": expandable,
            "fully_expanded_concepts": fully_expanded,
            "expansion_ratio": fully_expanded / max(expandable, 1)
        }


# Singleton instance
hierarchical_concept_service = HierarchicalConceptService()