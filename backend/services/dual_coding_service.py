"""
Dual Coding Service
Implements dual coding theory by creating integrated visual-verbal learning experiences
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import hashlib
import base64
import io
from collections import defaultdict
import uuid

from services.llm_service import LLMService
from services.rag_service import RAGService

class DualCodingEngine:
    """
    Advanced dual coding engine that creates integrated visual-verbal learning experiences
    based on cognitive science principles and educational psychology
    """

    def __init__(self, llm_service: LLMService, rag_service: RAGService):
        self.llm_service = llm_service
        self.rag_service = rag_service

        # Dual coding principles configuration
        self.max_visual_elements = 8
        self.min_visual_elements = 2
        self.visual_verbal_ratio = 0.4  # 40% visual, 60% verbal content
        self.cognitive_load_threshold = 7  # Miller's magic number

        # Visual element types with cognitive impact scores
        self.visual_element_types = {
            "diagram": {"impact": 0.9, "complexity": "medium"},
            "flowchart": {"impact": 0.85, "complexity": "low"},
            "mind_map": {"impact": 0.95, "complexity": "medium"},
            "timeline": {"impact": 0.8, "complexity": "low"},
            "table": {"impact": 0.75, "complexity": "low"},
            "hierarchy": {"impact": 0.85, "complexity": "medium"},
            "comparison": {"impact": 0.8, "complexity": "low"},
            "process_diagram": {"impact": 0.9, "complexity": "high"},
            "concept_map": {"impact": 0.95, "complexity": "high"},
            "infographic": {"impact": 0.85, "complexity": "medium"}
        }

        # Learning style preferences
        self.learning_styles = {
            "visual": {"weight": 0.7, "preferred_elements": ["diagram", "mind_map", "infographic"]},
            "verbal": {"weight": 0.3, "preferred_elements": ["table", "timeline", "hierarchy"]},
            "balanced": {"weight": 0.5, "preferred_elements": ["flowchart", "comparison", "process_diagram"]}
        }

    async def create_dual_coding_content(
        self,
        content: str,
        content_type: str = "text",
        target_audience: str = "intermediate",
        learning_style: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Create integrated visual-verbal learning content
        """
        try:
            # Step 1: Extract key concepts and relationships
            concepts = await self._extract_concepts_and_relationships(content)

            # Step 2: Analyze content structure and complexity
            structure_analysis = await self._analyze_content_structure(content, concepts)

            # Step 3: Generate visual elements based on content type
            visual_elements = await self._generate_visual_elements(
                content, concepts, structure_analysis, learning_style
            )

            # Step 4: Create verbal content that complements visuals
            verbal_content = await self._create_complementary_verbal_content(
                content, visual_elements, target_audience
            )

            # Step 5: Optimize cognitive load and integration
            optimized_content = await self._optimize_dual_coding_integrity(
                visual_elements, verbal_content, concepts
            )

            # Step 6: Generate learning interactions
            interactions = await self._create_learning_interactions(optimized_content)

            return {
                "success": True,
                "content_id": str(uuid.uuid4()),
                "original_content": content,
                "concepts": concepts,
                "visual_elements": optimized_content["visual_elements"],
                "verbal_content": optimized_content["verbal_content"],
                "interactions": interactions,
                "metadata": {
                    "learning_style": learning_style,
                    "target_audience": target_audience,
                    "visual_verbal_ratio": self.visual_verbal_ratio,
                    "cognitive_load_score": optimized_content["cognitive_load_score"],
                    "dual_coding_score": optimized_content["dual_coding_score"],
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _extract_concepts_and_relationships(self, content: str) -> List[Dict[str, Any]]:
        """Extract key concepts and their relationships"""
        try:
            prompt = f"""
            Analizza il seguente contenuto ed estrai i concetti chiave e le loro relazioni:

            CONTESTO:
            {content}

            Estrai:
            1. Concetti principali (minimo 3, massimo 10)
            2. Relazioni tra concetti (causa-effetto, gerarchia, comparazione, sequenza)
            3. Attributi importanti di ogni concetto
            4. Livello di importanza (1-10)

            Formato JSON:
            {{
                "concepts": [
                    {{
                        "name": "Nome concetto",
                        "importance": 8,
                        "attributes": ["attributo1", "attributo2"],
                        "category": "category"
                    }}
                ],
                "relationships": [
                    {{
                        "concept1": "Concetto A",
                        "concept2": "Concetto B",
                        "type": "causa|conseguenza|gerarchia|comparazione|sequenza|parte_di",
                        "description": "Descrizione relazione"
                    }}
                ]
            }}
            """

            response = await self.llm_service.generate_text(prompt)

            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Fallback extraction
                words = content.lower().split()
                concept_words = []
                for word in words:
                    if len(word) > 6 and word not in concept_words:
                        concept_words.append(word)

                return {
                    "concepts": [{"name": word, "importance": 5, "attributes": [], "category": "general"}
                               for word in concept_words[:10]],
                    "relationships": []
                }

        except Exception as e:
            print(f"Error extracting concepts: {e}")
            return {"concepts": [], "relationships": []}

    async def _analyze_content_structure(self, content: str, concepts: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content structure and complexity"""
        try:
            sentences = content.split('.')
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

            # Determine content patterns
            has_sequence = any(word in content.lower() for word in ['primo', 'dopo', 'poi', 'finalmente', 'inizia'])
            has_comparison = any(word in content.lower() for word in ['rispetto a', 'mentre', 'invece', 'diverso'])
            has_hierarchy = any(word in content.lower() for word in ['parte di', 'include', 'contiene', 'sottocategoria'])
            has_process = any(word in content.lower() for word in ['passo', 'fase', 'procedura', 'processo'])

            # Complexity analysis
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
            concept_density = len(concepts.get("concepts", [])) / len(content.split()) if content else 0

            return {
                "content_type": self._determine_content_type(has_sequence, has_comparison, has_hierarchy, has_process),
                "complexity": "high" if avg_sentence_length > 20 or concept_density > 0.1 else "medium" if avg_sentence_length > 15 else "low",
                "structure": {
                    "has_sequence": has_sequence,
                    "has_comparison": has_comparison,
                    "has_hierarchy": has_hierarchy,
                    "has_process": has_process
                },
                "stats": {
                    "sentence_count": len(sentences),
                    "paragraph_count": len(paragraphs),
                    "avg_sentence_length": avg_sentence_length,
                    "concept_density": concept_density
                }
            }

        except Exception as e:
            print(f"Error analyzing content structure: {e}")
            return {"content_type": "general", "complexity": "medium"}

    def _determine_content_type(self, has_sequence: bool, has_comparison: bool,
                              has_hierarchy: bool, has_process: bool) -> str:
        """Determine the best content type for visualization"""
        if has_process or has_sequence:
            return "process_flow"
        elif has_hierarchy:
            return "hierarchical"
        elif has_comparison:
            return "comparative"
        else:
            return "conceptual"

    async def _generate_visual_elements(
        self,
        content: str,
        concepts: Dict[str, Any],
        structure: Dict[str, Any],
        learning_style: str
    ) -> List[Dict[str, Any]]:
        """Generate appropriate visual elements based on content analysis"""
        try:
            content_type = structure.get("content_type", "conceptual")
            complexity = structure.get("complexity", "medium")
            style_config = self.learning_styles.get(learning_style, self.learning_styles["balanced"])

            # Select appropriate visual element types
            suitable_types = self._select_suitable_visual_types(content_type, complexity, style_config)

            visual_elements = []

            for element_type in suitable_types[:self.max_visual_elements]:
                element = await self._create_visual_element(
                    element_type, content, concepts, structure
                )
                if element:
                    visual_elements.append(element)

            return visual_elements

        except Exception as e:
            print(f"Error generating visual elements: {e}")
            return []

    def _select_suitable_visual_types(self, content_type: str, complexity: str,
                                    style_config: Dict[str, Any]) -> List[str]:
        """Select the most suitable visual element types"""
        suitable_types = []

        # Based on content type
        if content_type == "process_flow":
            suitable_types.extend(["flowchart", "process_diagram", "timeline"])
        elif content_type == "hierarchical":
            suitable_types.extend(["hierarchy", "mind_map", "tree_diagram"])
        elif content_type == "comparative":
            suitable_types.extend(["table", "comparison", "venn_diagram"])
        else:
            suitable_types.extend(["mind_map", "concept_map", "diagram"])

        # Add preferred types based on learning style
        for preferred in style_config["preferred_elements"]:
            if preferred not in suitable_types:
                suitable_types.append(preferred)

        # Filter by complexity
        if complexity == "low":
            suitable_types = [t for t in suitable_types
                            if self.visual_element_types.get(t, {}).get("complexity") != "high"]

        return suitable_types

    async def _create_visual_element(
        self,
        element_type: str,
        content: str,
        concepts: Dict[str, Any],
        structure: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Create a specific visual element"""
        try:
            element_id = str(uuid.uuid4())

            if element_type == "mind_map":
                return await self._create_mind_map(element_id, concepts, content)
            elif element_type == "flowchart":
                return await self._create_flowchart(element_id, content, structure)
            elif element_type == "table":
                return await self._create_table(element_id, concepts, content)
            elif element_type == "timeline":
                return await self._create_timeline(element_id, content)
            elif element_type == "hierarchy":
                return await self._create_hierarchy(element_id, concepts, content)
            elif element_type == "comparison":
                return await self._create_comparison(element_id, concepts, content)
            elif element_type == "diagram":
                return await self._create_diagram(element_id, concepts, content)
            elif element_type == "process_diagram":
                return await self._create_process_diagram(element_id, content, structure)
            else:
                return None

        except Exception as e:
            print(f"Error creating visual element {element_type}: {e}")
            return None

    async def _create_mind_map(self, element_id: str, concepts: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Create a mind map visualization"""
        try:
            main_concepts = sorted(concepts.get("concepts", []),
                                 key=lambda x: x.get("importance", 0), reverse=True)[:5]

            # Create central concept
            central_concept = main_concepts[0]["name"] if main_concepts else "Concetto Principale"

            # Create branches
            branches = []
            for concept in main_concepts[1:]:
                branch = {
                    "id": str(uuid.uuid4()),
                    "text": concept["name"],
                    "attributes": concept.get("attributes", []),
                    "importance": concept.get("importance", 5),
                    "sub_branches": []
                }

                # Add sub-branches from relationships
                for rel in concepts.get("relationships", []):
                    if concept["name"] in [rel.get("concept1"), rel.get("concept2")]:
                        related_concept = rel.get("concept2") if rel.get("concept1") == concept["name"] else rel.get("concept1")
                        if related_concept and related_concept != central_concept:
                            branch["sub_branches"].append({
                                "id": str(uuid.uuid4()),
                                "text": related_concept,
                                "relationship": rel.get("type", "related"),
                                "description": rel.get("description", "")
                            })

                branches.append(branch)

            return {
                "id": element_id,
                "type": "mind_map",
                "data": {
                    "central_concept": central_concept,
                    "branches": branches
                },
                "style": {
                    "layout": "radial",
                    "colors": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"],
                    "animation": "grow"
                },
                "cognitive_impact": self.visual_element_types["mind_map"]["impact"]
            }

        except Exception as e:
            print(f"Error creating mind map: {e}")
            return None

    async def _create_flowchart(self, element_id: str, content: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Create a flowchart visualization"""
        try:
            # Extract process steps
            steps = self._extract_process_steps(content)

            nodes = []
            connections = []

            for i, step in enumerate(steps):
                node_id = str(uuid.uuid4())
                node_type = "start" if i == 0 else "end" if i == len(steps) - 1 else "process"

                nodes.append({
                    "id": node_id,
                    "text": step["text"],
                    "type": node_type,
                    "position": {"x": i * 150, "y": 100}
                })

                if i > 0:
                    connections.append({
                        "from": nodes[i-1]["id"],
                        "to": node_id,
                        "type": "arrow"
                    })

            return {
                "id": element_id,
                "type": "flowchart",
                "data": {
                    "nodes": nodes,
                    "connections": connections
                },
                "style": {
                    "direction": "horizontal",
                    "colors": {
                        "start": "#10B981",
                        "process": "#3B82F6",
                        "end": "#EF4444"
                    }
                },
                "cognitive_impact": self.visual_element_types["flowchart"]["impact"]
            }

        except Exception as e:
            print(f"Error creating flowchart: {e}")
            return None

    async def _create_table(self, element_id: str, concepts: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Create a comparison table"""
        try:
            main_concepts = concepts.get("concepts", [])[:3]

            # Extract comparison criteria
            criteria = ["Caratteristiche", "Importanza", "Applicazioni", "Relazioni"]

            headers = ["Concetto"] + criteria
            rows = []

            for concept in main_concepts:
                row = [concept["name"]]
                for criterion in criteria:
                    if criterion == "Caratteristiche":
                        row.append(", ".join(concept.get("attributes", ["N/A"])))
                    elif criterion == "Importanza":
                        row.append(f"{concept.get('importance', 5)}/10")
                    else:
                        row.append("Descrivere")
                rows.append(row)

            return {
                "id": element_id,
                "type": "table",
                "data": {
                    "headers": headers,
                    "rows": rows
                },
                "style": {
                    "border_style": "complete",
                    "header_color": "#F3F4F6",
                    "alternating_rows": True
                },
                "cognitive_impact": self.visual_element_types["table"]["impact"]
            }

        except Exception as e:
            print(f"Error creating table: {e}")
            return None

    async def _create_timeline(self, element_id: str, content: str) -> Dict[str, Any]:
        """Create a timeline visualization"""
        try:
            # Extract temporal information
            events = self._extract_temporal_events(content)

            events_data = []
            for event in events:
                events_data.append({
                    "id": str(uuid.uuid4()),
                    "date": event["date"],
                    "title": event["title"],
                    "description": event["description"],
                    "position": len(events_data)  # Sequential position
                })

            return {
                "id": element_id,
                "type": "timeline",
                "data": {
                    "events": events_data,
                    "orientation": "horizontal"
                },
                "style": {
                    "color_scheme": "chronological",
                    "marker_style": "circle",
                    "connection_line": "dashed"
                },
                "cognitive_impact": self.visual_element_types["timeline"]["impact"]
            }

        except Exception as e:
            print(f"Error creating timeline: {e}")
            return None

    async def _create_hierarchy(self, element_id: str, concepts: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Create a hierarchical visualization"""
        try:
            # Find hierarchical relationships
            hierarchical_rels = [rel for rel in concepts.get("relationships", [])
                               if rel.get("type") in ["gerarchia", "parte_di", "contiene"]]

            # Build hierarchy tree
            root_nodes = []
            all_concepts = {c["name"]: c for c in concepts.get("concepts", [])}
            processed = set()

            for rel in hierarchical_rels:
                parent = rel.get("concept1")
                child = rel.get("concept2")

                if parent not in processed and parent in all_concepts:
                    root_nodes.append({
                        "id": str(uuid.uuid4()),
                        "name": parent,
                        "importance": all_concepts[parent].get("importance", 5),
                        "children": []
                    })
                    processed.add(parent)

            return {
                "id": element_id,
                "type": "hierarchy",
                "data": {
                    "nodes": root_nodes
                },
                "style": {
                    "layout": "top-down",
                    "node_colors": ["#3B82F6", "#10B981", "#F59E0B"],
                    "connection_style": "line"
                },
                "cognitive_impact": self.visual_element_types["hierarchy"]["impact"]
            }

        except Exception as e:
            print(f"Error creating hierarchy: {e}")
            return None

    async def _create_comparison(self, element_id: str, concepts: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Create a comparison visualization"""
        try:
            main_concepts = concepts.get("concepts", [])[:2]

            if len(main_concepts) < 2:
                return None

            # Extract comparison criteria
            comparison_data = {
                "concept1": main_concepts[0]["name"],
                "concept2": main_concepts[1]["name"],
                "similarities": [],
                "differences": []
            }

            # Find similarities and differences from relationships
            for rel in concepts.get("relationships", []):
                if main_concepts[0]["name"] in [rel.get("concept1"), rel.get("concept2")] and \
                   main_concepts[1]["name"] in [rel.get("concept1"), rel.get("concept2")]:
                    if rel.get("type") == "comparazione":
                        comparison_data["differences"].append(rel.get("description", ""))
                    else:
                        comparison_data["similarities"].append(rel.get("description", ""))

            return {
                "id": element_id,
                "type": "comparison",
                "data": comparison_data,
                "style": {
                    "layout": "side_by_side",
                    "similar_color": "#10B981",
                    "difference_color": "#EF4444"
                },
                "cognitive_impact": self.visual_element_types["comparison"]["impact"]
            }

        except Exception as e:
            print(f"Error creating comparison: {e}")
            return None

    async def _create_diagram(self, element_id: str, concepts: Dict[str, Any], content: str) -> Dict[str, Any]:
        """Create a general diagram"""
        try:
            main_concepts = concepts.get("concepts", [])[:5]

            nodes = []
            connections = []

            # Create nodes
            for i, concept in enumerate(main_concepts):
                nodes.append({
                    "id": str(uuid.uuid4()),
                    "text": concept["name"],
                    "importance": concept.get("importance", 5),
                    "attributes": concept.get("attributes", []),
                    "position": self._calculate_diagram_position(i, len(main_concepts))
                })

            # Create connections based on relationships
            for rel in concepts.get("relationships", []):
                source_idx = next((i for i, c in enumerate(main_concepts) if c["name"] == rel.get("concept1")), None)
                target_idx = next((i for i, c in enumerate(main_concepts) if c["name"] == rel.get("concept2")), None)

                if source_idx is not None and target_idx is not None:
                    connections.append({
                        "from": nodes[source_idx]["id"],
                        "to": nodes[target_idx]["id"],
                        "type": rel.get("type", "related"),
                        "label": rel.get("description", "")
                    })

            return {
                "id": element_id,
                "type": "diagram",
                "data": {
                    "nodes": nodes,
                    "connections": connections
                },
                "style": {
                    "layout": "force_directed",
                    "node_size": "importance_based",
                    "connection_style": "curved"
                },
                "cognitive_impact": self.visual_element_types["diagram"]["impact"]
            }

        except Exception as e:
            print(f"Error creating diagram: {e}")
            return None

    async def _create_process_diagram(self, element_id: str, content: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Create a detailed process diagram"""
        try:
            steps = self._extract_process_steps(content)

            process_data = {
                "title": "Processo Principale",
                "steps": [],
                "decision_points": [],
                "feedback_loops": []
            }

            for i, step in enumerate(steps):
                step_data = {
                    "id": str(uuid.uuid4()),
                    "name": step["text"],
                    "description": step.get("description", ""),
                    "inputs": step.get("inputs", []),
                    "outputs": step.get("outputs", []),
                    "position": {"x": i * 200, "y": 0}
                }
                process_data["steps"].append(step_data)

            return {
                "id": element_id,
                "type": "process_diagram",
                "data": process_data,
                "style": {
                    "direction": "left_to_right",
                    "step_colors": ["#3B82F6", "#10B981", "#F59E0B"],
                    "connection_style": "arrow"
                },
                "cognitive_impact": self.visual_element_types["process_diagram"]["impact"]
            }

        except Exception as e:
            print(f"Error creating process diagram: {e}")
            return None

    def _extract_process_steps(self, content: str) -> List[Dict[str, Any]]:
        """Extract process steps from content"""
        try:
            # Simple heuristic extraction
            sentences = content.split('.')
            steps = []

            for sentence in sentences:
                sentence = sentence.strip()
                if any(indicator in sentence.lower() for indicator in ['primo', 'dopo', "poi", 'passo', 'fase']):
                    steps.append({
                        "text": sentence,
                        "description": sentence,
                        "inputs": [],
                        "outputs": []
                    })

            # Fallback: split into chunks
            if not steps:
                words = content.split()
                chunk_size = len(words) // 4  # 4 steps max
                for i in range(0, len(words), chunk_size):
                    chunk_words = words[i:i+chunk_size]
                    if chunk_words:
                        steps.append({
                            "text": " ".join(chunk_words),
                            "description": " ".join(chunk_words),
                            "inputs": [],
                            "outputs": []
                        })

            return steps[:4]  # Max 4 steps

        except Exception as e:
            print(f"Error extracting process steps: {e}")
            return []

    def _extract_temporal_events(self, content: str) -> List[Dict[str, Any]]:
        """Extract temporal events from content"""
        try:
            # Simple heuristic for temporal extraction
            events = []

            # Look for year patterns
            import re
            year_pattern = r'\b(19|20)\d{2}\b'
            years = re.findall(year_pattern, content)

            if years:
                full_years = [f"{y}{content.split(y)[1].split()[0] if content.split(y)[1].split() else ''}"
                            for y in re.findall(r'\b(19|20)\d{2}\b', content)]

                for i, year in enumerate(full_years[:5]):
                    events.append({
                        "date": year[:4],
                        "title": f"Evento {i+1}",
                        "description": f"Accaduto nel {year[:4]}"
                    })

            # Fallback events
            if not events:
                events = [
                    {"date": "2024", "title": "Inizio", "description": "Inizio processo"},
                    {"date": "2025", "title": "Sviluppo", "description": "Fase di sviluppo"},
                    {"date": "2026", "title": "Completamento", "description": "Fine processo"}
                ]

            return events

        except Exception as e:
            print(f"Error extracting temporal events: {e}")
            return []

    def _calculate_diagram_position(self, index: int, total: int) -> Dict[str, int]:
        """Calculate node positions for diagrams"""
        import math

        if total == 1:
            return {"x": 200, "y": 200}

        angle = (2 * math.pi * index) / total
        radius = 150
        x = int(200 + radius * math.cos(angle))
        y = int(200 + radius * math.sin(angle))

        return {"x": x, "y": y}

    async def _create_complementary_verbal_content(
        self,
        original_content: str,
        visual_elements: List[Dict[str, Any]],
        target_audience: str
    ) -> Dict[str, Any]:
        """Create verbal content that complements the visual elements"""
        try:
            # Summarize visual elements for integration
            visual_summary = []
            for element in visual_elements:
                visual_summary.append(f"{element['type']}: {self._summarize_visual_element(element)}")

            prompt = f"""
            Crea contenuto verbale che integri e complementi i seguenti elementi visivi:

            CONTENUTO ORIGINALE:
            {original_content}

            ELEMENTI VISIVI:
            {chr(10).join(visual_summary)}

            Pubblico target: {target_audience}

            Crea:
            1. Una spiegazione introduttiva che connette i concetti
            2. Descrizioni dettagliate per ogni elemento visivo
            3. Connessioni esplicite tra elementi verbali e visivi
            4. Domande di riflessione per consolidare l'apprendimento
            5. Un riassunto finale che integri tutto

            Formato JSON:
            {{
                "introduction": "Testo introduttivo...",
                "visual_explanations": [
                    {{
                        "element_type": "mind_map",
                        "explanation": "Spiegazione dettagliata...",
                        "connection_to_content": "Come questo si collega al contenuto..."
                    }}
                ],
                "connections": [
                    "Connessione 1 tra elementi...",
                    "Connessione 2..."
                ],
                "reflection_questions": [
                    "Domanda 1...",
                    "Domanda 2..."
                ],
                "summary": "Riassunto integrato..."
            }}
            """

            response = await self.llm_service.generate_text(prompt)

            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Fallback verbal content
                return {
                    "introduction": "Questo contenuto esplora concetti importanti attraverso rappresentazioni visive e verbali.",
                    "visual_explanations": [
                        {
                            "element_type": element["type"],
                            "explanation": f"Questo {element['type']} mostra le relazioni tra i concetti chiave.",
                            "connection_to_content": "Si collega direttamente al contenuto originale."
                        } for element in visual_elements[:3]
                    ],
                    "connections": ["Gli elementi visivi supportano la comprensione verbale"],
                    "reflection_questions": ["Come questi concetti si applicano al tuo contesto?"],
                    "summary": "L'integrazione di elementi visivi e verbali facilita l'apprendimento."
                }

        except Exception as e:
            print(f"Error creating verbal content: {e}")
            return {
                "introduction": "Contenuto con supporti visivi",
                "visual_explanations": [],
                "connections": [],
                "reflection_questions": [],
                "summary": "Riassunto del contenuto"
            }

    def _summarize_visual_element(self, element: Dict[str, Any]) -> str:
        """Create a brief summary of a visual element"""
        try:
            element_type = element.get("type", "visual")
            data = element.get("data", {})

            if element_type == "mind_map":
                return f"Mappa mentale con concetto centrale: {data.get('central_concept', 'N/A')}"
            elif element_type == "flowchart":
                return f"Flusso con {len(data.get('nodes', []))} passi"
            elif element_type == "table":
                return f"Tabella comparativa con {len(data.get('headers', [])) - 1} concetti"
            elif element_type == "timeline":
                return f"Timeline con {len(data.get('events', []))} eventi"
            else:
                return f"Elemento visivo di tipo {element_type}"

        except Exception as e:
            return f"Elemento visivo {element_type}"

    async def _optimize_dual_coding_integrity(
        self,
        visual_elements: List[Dict[str, Any]],
        verbal_content: Dict[str, Any],
        concepts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize the dual coding integration for maximum learning effectiveness"""
        try:
            # Calculate cognitive load
            visual_complexity = sum(elem.get("cognitive_impact", 0.5) for elem in visual_elements)
            verbal_density = len(str(verbal_content).split()) / 100  # Words per 100 characters

            cognitive_load_score = (visual_complexity + verbal_density) / 2

            # Calculate dual coding effectiveness
            integration_score = self._calculate_integration_quality(visual_elements, verbal_content)
            concept_coverage = self._calculate_concept_coverage(visual_elements, verbal_content, concepts)

            dual_coding_score = (integration_score + concept_coverage) / 2

            # Optimize if needed
            optimized_visual = visual_elements
            optimized_verbal = verbal_content

            if cognitive_load_score > 0.7:  # Too high cognitive load
                optimized_visual = visual_elements[:max(2, len(visual_elements) - 2)]

            if integration_score < 0.5:  # Poor integration
                optimized_verbal = await self._improve_visual_verbal_integration(
                    optimized_visual, verbal_content
                )

            return {
                "visual_elements": optimized_visual,
                "verbal_content": optimized_verbal,
                "cognitive_load_score": min(cognitive_load_score, 1.0),
                "dual_coding_score": dual_coding_score,
                "optimizations_applied": cognitive_load_score > 0.7 or integration_score < 0.5
            }

        except Exception as e:
            print(f"Error optimizing dual coding: {e}")
            return {
                "visual_elements": visual_elements,
                "verbal_content": verbal_content,
                "cognitive_load_score": 0.6,
                "dual_coding_score": 0.7,
                "optimizations_applied": False
            }

    def _calculate_integration_quality(self, visual_elements: List[Dict[str, Any]],
                                     verbal_content: Dict[str, Any]) -> float:
        """Calculate how well visual and verbal content are integrated"""
        try:
            # Check for explicit connections
            connections = verbal_content.get("connections", [])
            visual_explanations = verbal_content.get("visual_explanations", [])

            # Base score
            base_score = 0.3

            # Boost for explanations
            if len(visual_explanations) >= len(visual_elements) * 0.8:
                base_score += 0.3

            # Boost for connections
            if len(connections) >= 2:
                base_score += 0.2

            # Boost for reflection
            if verbal_content.get("reflection_questions"):
                base_score += 0.2

            return min(base_score, 1.0)

        except Exception as e:
            return 0.5

    def _calculate_concept_coverage(self, visual_elements: List[Dict[str, Any]],
                                  verbal_content: Dict[str, Any],
                                  concepts: Dict[str, Any]) -> float:
        """Calculate how well the content covers the key concepts"""
        try:
            concept_names = [c["name"] for c in concepts.get("concepts", [])]

            # Check visual coverage
            visual_text = str(visual_elements).lower()
            visual_coverage = sum(1 for concept in concept_names if concept.lower() in visual_text)

            # Check verbal coverage
            verbal_text = str(verbal_content).lower()
            verbal_coverage = sum(1 for concept in concept_names if concept.lower() in verbal_text)

            total_possible = len(concept_names) * 2
            total_covered = visual_coverage + verbal_coverage

            return min(total_covered / total_possible, 1.0) if total_possible > 0 else 0.5

        except Exception as e:
            return 0.5

    async def _improve_visual_verbal_integration(
        self,
        visual_elements: List[Dict[str, Any]],
        verbal_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Improve the integration between visual and verbal content"""
        try:
            # Add explicit connections
            connections = []

            for element in visual_elements:
                element_type = element.get("type", "visual")
                connections.append(f"Il {element_type} mostra la struttura dei concetti principali")
                connections.append(f"Usa il {element_type} per identificare le relazioni tra gli elementi")

            # Add reflection questions
            reflection_questions = [
                "Come gli elementi visivi ti aiutano a comprendere meglio i concetti?",
                "Quali connessioni puoi trovare tra i diversi elementi mostrati?",
                "Come applicheresti questi concetti in una situazione reale?"
            ]

            improved_content = verbal_content.copy()
            improved_content["connections"].extend(connections)
            improved_content["reflection_questions"].extend(reflection_questions)

            return improved_content

        except Exception as e:
            return verbal_content

    async def _create_learning_interactions(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create interactive learning elements"""
        try:
            interactions = []

            # Visual-based interactions
            for visual in content.get("visual_elements", []):
                if visual.get("type") == "mind_map":
                    interactions.append({
                        "type": "mind_map_explore",
                        "title": "Esplora la Mappa Mentale",
                        "description": "Clicca sui nodi per esplorare i concetti correlati",
                        "visual_id": visual["id"],
                        "interaction_data": {
                            "clickable_nodes": True,
                            "expand_branches": True,
                            "show_details": True
                        }
                    })

                elif visual.get("type") == "flowchart":
                    interactions.append({
                        "type": "process_navigate",
                        "title": "Naviga il Processo",
                        "description": "Segui i passaggi del processo in ordine",
                        "visual_id": visual["id"],
                        "interaction_data": {
                            "step_by_step": True,
                            "highlight_current": True,
                            "show_connections": True
                        }
                    })

            # Verbal-based interactions
            verbal_content = content.get("verbal_content", {})
            if verbal_content.get("reflection_questions"):
                interactions.append({
                    "type": "reflection_prompts",
                    "title": "Domande di Riflessione",
                    "description": "Rifletti su queste domande per approfondire",
                    "interaction_data": {
                        "questions": verbal_content.get("reflection_questions", []),
                        "input_type": "text",
                        "feedback_type": "reflective"
                    }
                })

            # Concept connection interactions
            interactions.append({
                "type": "concept_matching",
                "title": "Collega i Concetti",
                "description": "Trascina i concetti per creare le giuste connessioni",
                "interaction_data": {
                    "draggable": True,
                    "auto_validate": True,
                    "show_feedback": True
                }
            })

            return interactions

        except Exception as e:
            print(f"Error creating learning interactions: {e}")
            return []

    async def get_dual_coding_analytics(self, user_id: str, course_id: str, period_days: int = 30) -> Dict[str, Any]:
        """Get analytics on dual coding usage and effectiveness"""
        try:
            # This would typically query a database
            # For now, return simulated analytics

            return {
                "success": True,
                "period_days": period_days,
                "dual_coding_sessions": 15,
                "visual_elements_created": 45,
                "preferred_visual_types": {
                    "mind_map": 40,
                    "flowchart": 25,
                    "table": 20,
                    "diagram": 15
                },
                "learning_outcomes": {
                    "concept_retention_improvement": 0.35,
                    "understanding_score": 0.78,
                    "engagement_level": 0.82
                },
                "cognitive_load_metrics": {
                    "average_load_score": 0.62,
                    "optimal_range_sessions": 12,
                    "overload_sessions": 3
                },
                "integration_quality": {
                    "visual_verbal_balance": 0.71,
                    "concept_coverage": 0.85,
                    "interaction_effectiveness": 0.73
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

# Initialize the dual coding service
dual_coding_service = DualCodingEngine(None, None)  # Will be initialized with proper services