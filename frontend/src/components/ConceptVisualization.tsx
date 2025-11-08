'use client'

import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface Concept {
  concept_id: string;
  name: string;
  x: number;
  y: number;
  size: number;
  color: string;
  mastery_level: number;
  has_sub_concepts: boolean;
  parent_id?: string;
}

interface Connection {
  from_concept_id: string;
  to_concept_id: string;
  strength: number;
  relationship_type: string;
}

interface ConceptVisualizationProps {
  courseId: string;
  userId: string;
  onConceptClick?: (concept: Concept) => void;
  onSubConceptRequest?: (parentConcept: Concept, context: string) => void;
}

const ConceptVisualization: React.FC<ConceptVisualizationProps> = ({
  courseId,
  userId,
  onConceptClick,
  onSubConceptRequest
}) => {
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConcept, setSelectedConcept] = useState<Concept | null>(null);
  const [stats, setStats] = useState<any>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    fetchVisualizationData();
  }, [courseId, userId]);

  const fetchVisualizationData = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/knowledge-areas/${courseId}/visualization/${userId}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success && data.visualization) {
        setConcepts(data.visualization.concepts || []);
        setConnections(data.visualization.connections || []);
        setStats(data.visualization.stats || {});
        setError(null);
      } else {
        setError(data.visualization?.error || 'Unknown error');
      }
    } catch (error) {
      console.error('Error fetching visualization data:', error);
      setError('Failed to load concept visualization');
    } finally {
      setLoading(false);
    }
  };

  const getMasteryColor = (masteryLevel: number): string => {
    if (masteryLevel >= 0.8) return '#10b981';  // Green
    if (masteryLevel >= 0.6) return '#3b82f6';  // Blue
    if (masteryLevel >= 0.4) return '#f59e0b';  // Amber
    return '#ef4444';  // Red
  };

  const getMasteryLabel = (masteryLevel: number): string => {
    if (masteryLevel >= 0.8) return 'Maestro';
    if (masteryLevel >= 0.6) return 'Buono';
    if (masteryLevel >= 0.4) return 'In sviluppo';
    return 'Da iniziare';
  };

  const handleConceptClick = (concept: Concept) => {
    setSelectedConcept(concept);
    onConceptClick?.(concept);
  };

  const handleAddSubConcept = () => {
    if (selectedConcept && onSubConceptRequest) {
      const context = prompt("In che contesto vuoi approfondire questo concetto?");
      if (context) {
        onSubConceptRequest(selectedConcept, context);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 bg-gray-50 rounded-lg p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p className="mt-4 text-gray-600">Caricamento visualizzazione concetti...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 bg-red-50 rounded-lg p-8">
        <div className="text-red-600 text-xl mb-2">⚠️ Errore</div>
        <p className="text-gray-700">{error}</p>
        <button
          onClick={fetchVisualizationData}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Riprova
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Mappa dei Concetti</h2>
        <div className="flex items-center space-x-4">
          {stats && (
            <div className="text-sm text-gray-600">
              <span className="font-medium">{stats.total_concepts}</span> concetti •
              <span className="font-medium ml-2">{stats.average_mastery.toFixed(1)}%</span> padronanza media
            </div>
          )}
          <button
            onClick={fetchVisualizationData}
            className="p-2 text-gray-600 hover:text-blue-600 transition-colors"
            title="Aggiorna"
          >
            🔄
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="mb-4 flex items-center space-x-6 text-sm">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-green-500 rounded-full"></div>
          <span>Maestro (&gt;80%)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
          <span>Buono (60-80%)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-amber-500 rounded-full"></div>
          <span>In sviluppo (40-60%)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-red-500 rounded-full"></div>
          <span>Da iniziare (&lt;40%)</span>
        </div>
      </div>

      {/* SVG Visualization */}
      <div className="relative bg-gray-50 rounded-lg overflow-hidden" style={{ height: '500px' }}>
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          viewBox="-400 -250 800 500"
          className="w-full h-full"
        >
          {/* Grid lines for reference */}
          <defs>
            <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#e5e7eb" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Connections */}
          <g className="connections">
            {connections.map((connection, index) => {
              const fromConcept = concepts.find(c => c.concept_id === connection.from_concept_id);
              const toConcept = concepts.find(c => c.concept_id === connection.to_concept_id);

              if (!fromConcept || !toConcept) return null;

              const isHierarchy = connection.relationship_type === 'hierarchy';
              const strokeWidth = connection.strength * 3;

              return (
                <g key={index}>
                  <line
                    x1={fromConcept.x}
                    y1={fromConcept.y}
                    x2={toConcept.x}
                    y2={toConcept.y}
                    stroke={isHierarchy ? '#6b7280' : '#d1d5db'}
                    strokeWidth={strokeWidth}
                    strokeDasharray={isHierarchy ? '0' : '5,5'}
                    opacity={connection.strength}
                  />
                  {isHierarchy && (
                    <polygon
                      points={`${toConcept.x},${toConcept.y} ${toConcept.x - 5},${toConcept.y - 8} ${toConcept.x + 5},${toConcept.y - 8}`}
                      fill="#6b7280"
                      transform={`rotate(${Math.atan2(toConcept.y - fromConcept.y, toConcept.x - fromConcept.x) * 180 / Math.PI} ${toConcept.x} ${toConcept.y})`}
                    />
                  )}
                </g>
              );
            })}
          </g>

          {/* Concepts */}
          <g className="concepts">
            {concepts.map((concept, index) => (
              <g key={concept.concept_id}>
                <motion.circle
                  cx={concept.x}
                  cy={concept.y}
                  r={concept.size}
                  fill={concept.color}
                  stroke="#ffffff"
                  strokeWidth="2"
                  style={{ cursor: 'pointer' }}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: index * 0.1, duration: 0.3 }}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleConceptClick(concept)}
                />

                <motion.text
                  x={concept.x}
                  y={concept.y}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="white"
                  fontSize="12"
                  fontWeight="bold"
                  style={{ pointerEvents: 'none' }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: index * 0.1 + 0.2, duration: 0.3 }}
                >
                  {concept.name.length > 15 ? concept.name.substring(0, 15) + '...' : concept.name}
                </motion.text>

                {concept.has_sub_concepts && (
                  <motion.circle
                    cx={concept.x + concept.size - 5}
                    cy={concept.y - concept.size + 5}
                    r="8"
                    fill="#fbbf24"
                    stroke="#ffffff"
                    strokeWidth="1"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: index * 0.1 + 0.3, duration: 0.3 }}
                  />
                )}

                {/* Mastery indicator */}
                <motion.text
                  x={concept.x}
                  y={concept.y + concept.size + 15}
                  textAnchor="middle"
                  fill={concept.color}
                  fontSize="10"
                  style={{ pointerEvents: 'none' }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: index * 0.1 + 0.4, duration: 0.3 }}
                >
                  {getMasteryLabel(concept.mastery_level)}
                </motion.text>
              </g>
            ))}
          </g>
        </svg>
      </div>

      {/* Selected Concept Details */}
      {selectedConcept && (
        <motion.div
          className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex justify-between items-start">
            <div>
              <h3 className="font-semibold text-blue-900 text-lg">{selectedConcept.name}</h3>
              <p className="text-blue-700 mt-1">Padronanza: {(selectedConcept.mastery_level * 100).toFixed(1)}%</p>
              <p className="text-sm text-blue-600 mt-1">
                {selectedConcept.has_sub_concepts ? 'Ha sotto-concetti' : 'Nessun sotto-concetto'}
              </p>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setSelectedConcept(null)}
                className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
              >
                Chiudi
              </button>
              {onSubConceptRequest && (
                <button
                  onClick={handleAddSubConcept}
                  className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  + Sotto-concetto
                </button>
              )}
            </div>
          </div>
        </motion.div>
      )}

      {/* Stats Summary */}
      {stats && (
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-800">{stats.total_concepts}</div>
            <div className="text-sm text-gray-600">Concetti totali</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{stats.main_concepts}</div>
            <div className="text-sm text-gray-600">Concetti principali</div>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{stats.sub_concepts}</div>
            <div className="text-sm text-gray-600">Sotto-concetti</div>
          </div>
          <div className="text-center p-3 bg-amber-50 rounded-lg">
            <div className="text-2xl font-bold text-amber-600">{(stats.average_mastery * 100).toFixed(1)}%</div>
            <div className="text-sm text-gray-600">Padronanza media</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConceptVisualization;