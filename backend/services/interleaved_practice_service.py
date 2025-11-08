"""
Interleaved Practice Service
Implements interleaved practice scheduling based on cognitive science research
for optimal learning sequence and concept discrimination
"""

import asyncio
import json
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
import uuid
import numpy as np
from collections import defaultdict, Counter

class InterleavedPracticeScheduler:
    """
    Advanced interleaved practice scheduler that implements evidence-based
    sequencing algorithms for optimal learning and concept discrimination
    """

    def __init__(self):
        # Cognitive science-based configuration
        self.min_concepts_per_session = 2
        self.max_concepts_per_session = 4
        self.interleaving_ratio = 0.7  # 70% interleaved, 30% blocked
        self.difficulty_variance_threshold = 0.3
        self.similarity_threshold = 0.6

        # Spacing parameters for interleaved practice
        self.inter_concept_spacing = 3  # minutes between different concepts
        self.review_spacing_factor = 2.5  # multiplier for review scheduling

        # Concept similarity metrics
        self.concept_relationship_weights = {
            "hierarchical": 0.3,
            "causal": 0.5,
            "comparative": 0.8,
            "contrasting": 0.9,
            "sequential": 0.4
        }

        # Learning effectiveness factors
        self.interleaving_benefits = {
            "concept_discrimination": 0.25,
            "transfer_ability": 0.30,
            "long_term_retention": 0.20,
            "problem_solving": 0.35
        }

    async def create_interleaved_schedule(
        self,
        user_id: str,
        course_id: str,
        concepts: List[Dict[str, Any]],
        session_duration_minutes: int = 60,
        learning_objectives: List[str] = None,
        difficulty_preference: str = "adaptive"
    ) -> Dict[str, Any]:
        """
        Create an optimized interleaved practice schedule
        """
        try:
            # Step 1: Analyze concepts and their relationships
            concept_analysis = await self._analyze_concepts(concepts)

            # Step 2: Determine optimal interleaving strategy
            interleaving_strategy = await self._determine_interleaving_strategy(
                concepts, concept_analysis, learning_objectives
            )

            # Step 3: Generate practice sequence
            practice_sequence = await self._generate_practice_sequence(
                concept_analysis, interleaving_strategy, session_duration_minutes
            )

            # Step 4: Optimize cognitive load and spacing
            optimized_sequence = await self._optimize_sequence_spacing(
                practice_sequence, session_duration_minutes
            )

            # Step 5: Add reflection and consolidation points
            final_schedule = await self._add_reflection_points(optimized_sequence)

            # Step 6: Calculate learning effectiveness predictions
            effectiveness_metrics = await self._calculate_effectiveness_metrics(
                concepts, interleaving_strategy, final_schedule
            )

            return {
                "success": True,
                "schedule_id": str(uuid.uuid4()),
                "user_id": user_id,
                "course_id": course_id,
                "concept_analysis": concept_analysis,
                "interleaving_strategy": interleaving_strategy,
                "practice_sequence": final_schedule,
                "effectiveness_metrics": effectiveness_metrics,
                "metadata": {
                    "session_duration": session_duration_minutes,
                    "concepts_count": len(concepts),
                    "interleaving_ratio": self.interleaving_ratio,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _analyze_concepts(self, concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze concepts and their relationships for optimal interleaving"""
        try:
            # Extract concept metadata
            concept_data = {}
            for concept in concepts:
                concept_id = concept.get("id", str(uuid.uuid4()))
                concept_data[concept_id] = {
                    "name": concept.get("name", ""),
                    "difficulty": concept.get("difficulty", 0.5),
                    "mastery_level": concept.get("mastery_level", 0.0),
                    "last_practiced": concept.get("last_practiced"),
                    "importance": concept.get("importance", 0.5),
                    "category": concept.get("category", "general"),
                    "tags": concept.get("tags", [])
                }

            # Calculate concept similarities
            similarity_matrix = await self._calculate_concept_similarities(concept_data)

            # Identify optimal interleaving pairs
            interleaving_pairs = await self._identify_interleaving_pairs(
                concept_data, similarity_matrix
            )

            # Determine concept groupings
            concept_groups = await self._group_concepts(concept_data, similarity_matrix)

            return {
                "concepts": concept_data,
                "similarity_matrix": similarity_matrix,
                "interleaving_pairs": interleaving_pairs,
                "concept_groups": concept_groups,
                "total_concepts": len(concepts),
                "average_difficulty": np.mean([c["difficulty"] for c in concept_data.values()]),
                "difficulty_variance": np.var([c["difficulty"] for c in concept_data.values()])
            }

        except Exception as e:
            print(f"Error analyzing concepts: {e}")
            return {"concepts": {}, "similarity_matrix": {}, "interleaving_pairs": [], "concept_groups": []}

    async def _calculate_concept_similarities(self, concepts: Dict[str, Any]) -> Dict[str, float]:
        """Calculate similarity scores between concepts"""
        try:
            similarities = {}
            concept_ids = list(concepts.keys())

            for i, concept1_id in enumerate(concept_ids):
                for j, concept2_id in enumerate(concept_ids[i+1:], i+1):
                    concept1 = concepts[concept1_id]
                    concept2 = concepts[concept2_id]

                    # Calculate similarity based on multiple factors
                    similarity = 0.0

                    # Category similarity
                    if concept1["category"] == concept2["category"]:
                        similarity += 0.3

                    # Tag overlap
                    tags1 = set(concept1["tags"])
                    tags2 = set(concept2["tags"])
                    if tags1 and tags2:
                        jaccard_similarity = len(tags1 & tags2) / len(tags1 | tags2)
                        similarity += 0.4 * jaccard_similarity

                    # Difficulty similarity (close difficulty = more interleavable)
                    difficulty_diff = abs(concept1["difficulty"] - concept2["difficulty"])
                    difficulty_similarity = 1.0 - min(difficulty_diff, 1.0)
                    similarity += 0.3 * difficulty_similarity

                    # Concept name similarity (simple heuristic)
                    name1_words = set(concept1["name"].lower().split())
                    name2_words = set(concept2["name"].lower().split())
                    if name1_words and name2_words:
                        name_similarity = len(name1_words & name2_words) / len(name1_words | name2_words)
                        similarity += 0.2 * name_similarity

                    similarities[f"{concept1_id}-{concept2_id}"] = min(similarity, 1.0)

            return similarities

        except Exception as e:
            print(f"Error calculating similarities: {e}")
            return {}

    async def _identify_interleaving_pairs(self, concepts: Dict[str, Any],
                                        similarities: Dict[str, float]) -> List[Dict[str, Any]]:
        """Identify optimal concept pairs for interleaving"""
        try:
            pairs = []
            concept_ids = list(concepts.keys())

            for i, concept1_id in enumerate(concept_ids):
                for j, concept2_id in enumerate(concept_ids[i+1:], i+1):
                    similarity_key = f"{concept1_id}-{concept2_id}"
                    reverse_key = f"{concept2_id}-{concept1_id}"

                    similarity = similarities.get(similarity_key, similarities.get(reverse_key, 0.0))

                    # Determine interleaving suitability
                    suitability = await self._calculate_interleaving_suitability(
                        concepts[concept1_id], concepts[concept2_id], similarity
                    )

                    if suitability > 0.5:  # Threshold for good interleaving
                        pairs.append({
                            "concept1_id": concept1_id,
                            "concept2_id": concept2_id,
                            "similarity": similarity,
                            "suitability": suitability,
                            "interleaving_type": self._determine_interleaving_type(similarity),
                            "recommended_spacing": self._calculate_recommended_spacing(
                                concepts[concept1_id], concepts[concept2_id]
                            )
                        })

            # Sort by suitability score
            pairs.sort(key=lambda x: x["suitability"], reverse=True)

            return pairs

        except Exception as e:
            print(f"Error identifying interleaving pairs: {e}")
            return []

    async def _calculate_interleaving_suitability(self, concept1: Dict[str, Any],
                                                concept2: Dict[str, Any],
                                                similarity: float) -> float:
        """Calculate how suitable two concepts are for interleaving"""
        try:
            suitability = 0.0

            # Similarity factor (moderate similarity is best for interleaving)
            if 0.3 <= similarity <= 0.7:  # Sweet spot for interleaving
                suitability += 0.4
            elif similarity > 0.7:
                suitability += 0.2  # Too similar might cause confusion
            else:
                suitability += 0.1  # Too different might not benefit from interleaving

            # Difficulty difference (moderate difference is beneficial)
            difficulty_diff = abs(concept1["difficulty"] - concept2["difficulty"])
            if 0.2 <= difficulty_diff <= 0.5:
                suitability += 0.3
            elif difficulty_diff > 0.5:
                suitability += 0.2
            else:
                suitability += 0.1

            # Mastery level difference (interleave practiced with less practiced)
            mastery_diff = abs(concept1["mastery_level"] - concept2["mastery_level"])
            if 0.2 <= mastery_diff <= 0.6:
                suitability += 0.3
            elif mastery_diff > 0.6:
                suitability += 0.2

            return min(suitability, 1.0)

        except Exception as e:
            print(f"Error calculating suitability: {e}")
            return 0.0

    def _determine_interleaving_type(self, similarity: float) -> str:
        """Determine the type of interleaving based on similarity"""
        if similarity >= 0.7:
            return "contrasting"  # Similar concepts benefit from contrasting
        elif similarity >= 0.4:
            return "integrative"  # Moderately similar benefit from integration
        else:
            return "sequential"  # Different concepts work well sequentially

    def _calculate_recommended_spacing(self, concept1: Dict[str, Any],
                                     concept2: Dict[str, Any]) -> int:
        """Calculate recommended spacing between concepts in minutes"""
        # Base spacing on difficulty and mastery levels
        avg_difficulty = (concept1["difficulty"] + concept2["difficulty"]) / 2
        avg_mastery = (concept1["mastery_level"] + concept2["mastery_level"]) / 2

        # Higher difficulty and lower mastery = more spacing
        spacing = self.inter_concept_spacing * (1 + avg_difficulty) * (1 + (1 - avg_mastery))

        return int(spacing)

    async def _group_concepts(self, concepts: Dict[str, Any],
                            similarities: Dict[str, float]) -> List[List[str]]:
        """Group concepts for optimal interleaving"""
        try:
            # Simple clustering based on similarities
            groups = []
            ungrouped = set(concepts.keys())

            while ungrouped:
                current_group = [ungrouped.pop()]

                # Find similar concepts to add to current group
                for concept_id in list(ungrouped):
                    is_similar = False

                    for group_concept in current_group:
                        similarity_key = f"{concept_id}-{group_concept}"
                        reverse_key = f"{group_concept}-{concept_id}"
                        similarity = similarities.get(similarity_key, similarities.get(reverse_key, 0.0))

                        if similarity >= 0.4:  # Similarity threshold for grouping
                            is_similar = True
                            break

                    if is_similar and len(current_group) < 3:  # Max group size
                        current_group.append(concept_id)
                        ungrouped.remove(concept_id)

                groups.append(current_group)

            return groups

        except Exception as e:
            print(f"Error grouping concepts: {e}")
            return [[concept_id] for concept_id in concepts.keys()]

    async def _determine_interleaving_strategy(self, concepts: List[Dict[str, Any]],
                                            concept_analysis: Dict[str, Any],
                                            learning_objectives: List[str]) -> Dict[str, Any]:
        """Determine the optimal interleaving strategy"""
        try:
            num_concepts = len(concepts)
            avg_difficulty = concept_analysis.get("average_difficulty", 0.5)
            difficulty_variance = concept_analysis.get("difficulty_variance", 0.0)

            # Determine strategy based on concept characteristics
            if num_concepts <= 2:
                strategy_type = "simple_interleaving"
            elif num_concepts <= 4:
                strategy_type = "moderate_interleaving"
            else:
                strategy_type = "complex_interleaving"

            # Adjust based on difficulty variance
            if difficulty_variance > self.difficulty_variance_threshold:
                strategy_type += "_adaptive"

            # Determine practice pattern
            pattern = await self._determine_practice_pattern(
                concept_analysis, learning_objectives
            )

            return {
                "strategy_type": strategy_type,
                "pattern": pattern,
                "interleaving_intensity": min(num_concepts / 4, 1.0),
                "difficulty_adaptation": difficulty_variance > self.difficulty_variance_threshold,
                "recommended_blocks": await self._calculate_recommended_blocks(concepts, concept_analysis),
                "transition_activities": await self._suggest_transition_activities(concept_analysis)
            }

        except Exception as e:
            print(f"Error determining strategy: {e}")
            return {"strategy_type": "simple_interleaving", "pattern": "ABAB"}

    async def _determine_practice_pattern(self, concept_analysis: Dict[str, Any],
                                        learning_objectives: List[str]) -> str:
        """Determine the optimal practice pattern"""
        try:
            num_concepts = concept_analysis.get("total_concepts", 2)

            if num_concepts == 2:
                return "ABAB"  # Simple alternating
            elif num_concepts == 3:
                return "ABCABC"  # Three-way interleaving
            elif num_concepts == 4:
                return "ABCDABCD"  # Four-way interleaving
            else:
                return "mixed"  # Complex pattern with variations

        except Exception as e:
            print(f"Error determining pattern: {e}")
            return "ABAB"

    async def _calculate_recommended_blocks(self, concepts: List[Dict[str, Any]],
                                          concept_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate recommended practice blocks"""
        try:
            blocks = []
            concept_groups = concept_analysis.get("concept_groups", [[c.get("id") for c in concepts]])

            for i, group in enumerate(concept_groups):
                block_duration = 60 / len(concept_groups)  # Equal time distribution

                block = {
                    "block_id": str(uuid.uuid4()),
                    "concepts": group,
                    "duration_minutes": block_duration,
                    "practice_type": "interleaved" if len(group) > 1 else "focused",
                    "difficulty_level": np.mean([concepts[c.get("id")]["difficulty"]
                                               if c.get("id") in concepts else 0.5
                                               for c in concepts]),
                    "position": i
                }
                blocks.append(block)

            return blocks

        except Exception as e:
            print(f"Error calculating blocks: {e}")
            return []

    async def _suggest_transition_activities(self, concept_analysis: Dict[str, Any]) -> List[str]:
        """Suggest transition activities between concepts"""
        try:
            activities = [
                "concept_comparison",
                "quick_review",
                "connection_identification",
                "self_explanation",
                "analogical_reasoning"
            ]

            # Select activities based on concept complexity
            avg_difficulty = concept_analysis.get("average_difficulty", 0.5)
            if avg_difficulty > 0.7:
                activities.extend(["guided_reflection", "scaffolded_transfer"])

            return activities[:3]  # Return top 3 activities

        except Exception as e:
            print(f"Error suggesting activities: {e}")
            return ["quick_review"]

    async def _generate_practice_sequence(self, concept_analysis: Dict[str, Any],
                                        strategy: Dict[str, Any],
                                        session_duration: int) -> List[Dict[str, Any]]:
        """Generate the actual practice sequence"""
        try:
            sequence = []
            concepts = concept_analysis["concepts"]
            pattern = strategy["pattern"]
            blocks = strategy["recommended_blocks"]

            # Generate sequence based on pattern
            if pattern == "ABAB":
                sequence = await self._generate_abab_pattern(concepts, blocks)
            elif pattern == "ABCABC":
                sequence = await self._generate_abc_pattern(concepts, blocks)
            elif pattern == "ABCDABCD":
                sequence = await self._generate_abcd_pattern(concepts, blocks)
            else:
                sequence = await self._generate_mixed_pattern(concepts, blocks)

            return sequence

        except Exception as e:
            print(f"Error generating sequence: {e}")
            return []

    async def _generate_abab_pattern(self, concepts: Dict[str, Any],
                                   blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate ABAB interleaving pattern"""
        try:
            sequence = []
            concept_ids = list(concepts.keys())[:2]  # Take first 2 concepts

            if len(concept_ids) < 2:
                # Fallback to single concept
                concept_ids = list(concepts.keys())[:1]

            # Create alternating sequence
            repetitions = 4  # ABAB pattern
            for i in range(repetitions):
                for concept_id in concept_ids:
                    segment = {
                        "segment_id": str(uuid.uuid4()),
                        "concept_id": concept_id,
                        "duration_minutes": 10,
                        "practice_type": "active_practice",
                        "position": len(sequence),
                        "transition_to_next": "quick_review"
                    }
                    sequence.append(segment)

            return sequence

        except Exception as e:
            print(f"Error generating ABAB pattern: {e}")
            return []

    async def _generate_abc_pattern(self, concepts: Dict[str, Any],
                                  blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate ABCABC interleaving pattern"""
        try:
            sequence = []
            concept_ids = list(concepts.keys())[:3]  # Take first 3 concepts

            if len(concept_ids) < 3:
                # Fallback to available concepts
                concept_ids = list(concepts.keys())

            # Create three-way interleaving
            repetitions = 3  # ABCABC pattern
            for i in range(repetitions):
                for concept_id in concept_ids:
                    segment = {
                        "segment_id": str(uuid.uuid4()),
                        "concept_id": concept_id,
                        "duration_minutes": 8,
                        "practice_type": "mixed_practice",
                        "position": len(sequence),
                        "transition_to_next": "comparison" if i < repetitions - 1 else "summary"
                    }
                    sequence.append(segment)

            return sequence

        except Exception as e:
            print(f"Error generating ABC pattern: {e}")
            return []

    async def _generate_abcd_pattern(self, concepts: Dict[str, Any],
                                   blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate ABCDABCD interleaving pattern"""
        try:
            sequence = []
            concept_ids = list(concepts.keys())[:4]  # Take first 4 concepts

            if len(concept_ids) < 4:
                # Fallback to available concepts
                concept_ids = list(concepts.keys())

            # Create four-way interleaving
            repetitions = 2  # ABCDABCD pattern
            for i in range(repetitions):
                for concept_id in concept_ids:
                    segment = {
                        "segment_id": str(uuid.uuid4()),
                        "concept_id": concept_id,
                        "duration_minutes": 6,
                        "practice_type": "discrimination_practice",
                        "position": len(sequence),
                        "transition_to_next": "connection_mapping"
                    }
                    sequence.append(segment)

            return sequence

        except Exception as e:
            print(f"Error generating ABCD pattern: {e}")
            return []

    async def _generate_mixed_pattern(self, concepts: Dict[str, Any],
                                    blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate mixed/complex interleaving pattern"""
        try:
            sequence = []
            concept_ids = list(concepts.keys())

            # Create a complex pattern with variations
            patterns = [
                concept_ids[:2],  # AB
                concept_ids[1:3] if len(concept_ids) > 2 else concept_ids[:2],  # BC
                concept_ids[:3],  # ABC
                concept_ids[2:4] if len(concept_ids) > 3 else concept_ids[-2:],  # CD
            ]

            for pattern in patterns:
                # Shuffle the pattern for randomness
                shuffled_pattern = pattern.copy()
                random.shuffle(shuffled_pattern)

                for concept_id in shuffled_pattern:
                    segment = {
                        "segment_id": str(uuid.uuid4()),
                        "concept_id": concept_id,
                        "duration_minutes": 7,
                        "practice_type": "adaptive_practice",
                        "position": len(sequence),
                        "transition_to_next": "meta_cognitive_check"
                    }
                    sequence.append(segment)

            return sequence

        except Exception as e:
            print(f"Error generating mixed pattern: {e}")
            return []

    async def _optimize_sequence_spacing(self, sequence: List[Dict[str, Any]],
                                       session_duration: int) -> List[Dict[str, Any]]:
        """Optimize spacing and timing within the sequence"""
        try:
            # Calculate total time and adjust durations
            total_planned_time = sum(seg["duration_minutes"] for seg in sequence)
            time_scale_factor = session_duration / total_planned_time

            # Adjust segment durations
            for segment in sequence:
                segment["duration_minutes"] = int(segment["duration_minutes"] * time_scale_factor)
                segment["start_time"] = sum(seg["duration_minutes"] for seg in sequence[:sequence.index(segment)])
                segment["end_time"] = segment["start_time"] + segment["duration_minutes"]

            # Add micro-breaks between concept switches
            optimized_sequence = []
            for i, segment in enumerate(sequence):
                optimized_sequence.append(segment)

                # Add break if next segment is different concept
                if i < len(sequence) - 1 and sequence[i]["concept_id"] != sequence[i+1]["concept_id"]:
                    break_segment = {
                        "segment_id": str(uuid.uuid4()),
                        "concept_id": "transition_break",
                        "duration_minutes": 1,
                        "practice_type": "transition",
                        "position": len(optimized_sequence),
                        "transition_to_next": "refresh"
                    }
                    optimized_sequence.append(break_segment)

            return optimized_sequence

        except Exception as e:
            print(f"Error optimizing sequence: {e}")
            return sequence

    async def _add_reflection_points(self, sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add reflection and consolidation points"""
        try:
            enhanced_sequence = []

            # Add reflection points at strategic positions
            reflection_positions = [len(sequence) // 3, 2 * len(sequence) // 3, len(sequence) - 1]

            for i, segment in enumerate(sequence):
                enhanced_sequence.append(segment)

                # Add reflection if at reflection position
                if i in reflection_positions and i < len(sequence) - 1:
                    reflection = {
                        "segment_id": str(uuid.uuid4()),
                        "concept_id": "reflection",
                        "duration_minutes": 2,
                        "practice_type": "reflection",
                        "position": len(enhanced_sequence),
                        "transition_to_next": "consolidated_practice"
                    }
                    enhanced_sequence.append(reflection)

            return enhanced_sequence

        except Exception as e:
            print(f"Error adding reflection points: {e}")
            return sequence

    async def _calculate_effectiveness_metrics(self, concepts: List[Dict[str, Any]],
                                            strategy: Dict[str, Any],
                                            schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate predicted learning effectiveness metrics"""
        try:
            num_concepts = len(concepts)
            interleaving_intensity = strategy.get("interleaving_intensity", 0.5)

            # Base effectiveness calculations
            concept_discrimination = 0.6 + (0.3 * interleaving_intensity)
            transfer_ability = 0.5 + (0.4 * interleaving_intensity)
            long_term_retention = 0.7 + (0.2 * interleaving_intensity)
            problem_solving = 0.55 + (0.35 * interleaving_intensity)

            # Adjust based on concept diversity
            diversity_factor = min(num_concepts / 4, 1.0)
            concept_discrimination *= (0.8 + 0.2 * diversity_factor)

            # Calculate overall effectiveness score
            overall_effectiveness = (concept_discrimination + transfer_ability +
                                   long_term_retention + problem_solving) / 4

            return {
                "concept_discrimination": min(concept_discrimination, 1.0),
                "transfer_ability": min(transfer_ability, 1.0),
                "long_term_retention": min(long_term_retention, 1.0),
                "problem_solving": min(problem_solving, 1.0),
                "overall_effectiveness": min(overall_effectiveness, 1.0),
                "interleaving_benefit_score": interleaving_intensity,
                "recommended_practice_frequency": self._calculate_practice_frequency(overall_effectiveness),
                "expected_improvement_timeline": self._estimate_improvement_timeline(overall_effectiveness)
            }

        except Exception as e:
            print(f"Error calculating effectiveness metrics: {e}")
            return {"overall_effectiveness": 0.5}

    def _calculate_practice_frequency(self, effectiveness: float) -> str:
        """Calculate recommended practice frequency"""
        if effectiveness > 0.8:
            return "daily"
        elif effectiveness > 0.6:
            return "every_other_day"
        elif effectiveness > 0.4:
            return "twice_weekly"
        else:
            return "weekly"

    def _estimate_improvement_timeline(self, effectiveness: float) -> str:
        """Estimate timeline for seeing improvement"""
        if effectiveness > 0.8:
            return "1-2 weeks"
        elif effectiveness > 0.6:
            return "2-4 weeks"
        elif effectiveness > 0.4:
            return "4-6 weeks"
        else:
            return "6-8 weeks"

    async def get_interleaving_analytics(self, user_id: str, course_id: str,
                                      period_days: int = 30) -> Dict[str, Any]:
        """Get analytics on interleaved practice effectiveness"""
        try:
            # This would typically query database for actual user data
            # For now, return simulated analytics

            return {
                "success": True,
                "period_days": period_days,
                "interleaved_sessions": 12,
                "total_concepts_practiced": 18,
                "concept_discrimination_score": 0.78,
                "transfer_improvement": 0.65,
                "retention_rate": 0.82,
                "practice_efficiency": 0.71,
                "most_effective_patterns": ["ABAB", "ABCABC", "mixed"],
                "improvement_areas": ["concept_connections", "application_transfer"],
                "recommendations": [
                    "Increase interleaving intensity for similar concepts",
                    "Add more reflection points between concept switches",
                    "Focus on contrasting activities for highly similar concepts"
                ]
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

# Initialize the interleaved practice service
interleaved_practice_service = InterleavedPracticeScheduler()