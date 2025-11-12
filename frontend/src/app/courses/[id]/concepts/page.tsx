'use client'

import { useState, useEffect } from 'react';
import ConceptVisualization from '@/components/ConceptVisualization';

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

export default function ConceptsPage() {
  const [courseId] = useState('90a903c0-4ef6-4415-ae3b-9dbc70ad69a9');
  const [userId] = useState('demo-user');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleConceptClick = (concept: Concept) => {
    setMessage(`Hai cliccato sul concetto: ${concept.name}`);
  };

  const handleSubConceptRequest = async (parentConcept: Concept, context: string) => {
    setLoading(true);
    setMessage(`Creazione sotto-concetto per "${parentConcept.name}" nel contesto: ${context}`);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/knowledge-areas/create-sub-concept?` +
        new URLSearchParams({
          course_id: courseId,
          parent_concept_id: parentConcept.concept_id,
          user_id: userId,
          context: context,
          user_interaction: `L'utente vuole approfondire: ${context}`
        })
      );

      const data = await response.json();

      if (data.success) {
        setMessage(`✅ Sotto-concetto creato: ${data.sub_concept.name}`);
      } else {
        setMessage(`❌ Errore: ${data.message}`);
      }
    } catch (error) {
      console.error('Error creating sub-concept:', error);
      setMessage('❌ Errore nella creazione del sotto-concetto');
    } finally {
      setLoading(false);
    }
  };

  const extractNewConcepts = async () => {
    setLoading(true);
    setMessage('Estrazione concetti in corso...');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/knowledge-areas/90a903c0-4ef6-4415-ae3b-9dbc70ad69a9/extract-fast`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          course_id: courseId,
          force_regenerate: true
        })
      });

      const data = await response.json();

      if (data.success) {
        setMessage(`✅ Estratti ${data.areas[0]?.concepts?.length || 0} concetti principali`);
      } else {
        setMessage('❌ Errore nell\'estrazione');
      }
    } catch (error) {
      console.error('Error extracting concepts:', error);
      setMessage('❌ Errore durante l\'estrazione');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Visualizzazione Concetti
          </h1>
          <p className="text-gray-600">
            Mappa interattiva dei concetti del corso con indicatori di padronanza
          </p>
        </div>

        {/* Action Buttons */}
        <div className="mb-6 flex space-x-4">
          <button
            onClick={extractNewConcepts}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Elaborazione...' : '🔄 Estrai Nuovi Concetti'}
          </button>
        </div>

        {/* Status Message */}
        {message && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-800">{message}</p>
          </div>
        )}

        {/* Concept Visualization */}
        <ConceptVisualization
          courseId={courseId}
          userId={userId}
          onConceptClick={handleConceptClick}
          onSubConceptRequest={handleSubConceptRequest}
        />

        {/* Instructions */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Come funziona</h2>
          <div className="space-y-3 text-gray-600">
            <div className="flex items-start space-x-2">
              <span className="text-blue-600">🔵</span>
              <div>
                <strong>Concetti principali:</strong> Cerca i nodi più grandi nella mappa
              </div>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-amber-600">⭐</span>
              <div>
                <strong>Sotto-concetti:</strong> I nodi con un cerchio giallo hanno sotto-concetti
              </div>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-green-600">✅</span>
              <div>
                <strong>Padronanza:</strong> Il colore indica il tuo livello di conoscenza
              </div>
            </div>
            <div className="flex items-start space-x-2">
              <span className="text-gray-600">👆</span>
              <div>
                <strong>Interazione:</strong> Clicca su un concetto per vedere i dettagli o aggiungere sotto-concetti
              </div>
            </div>
          </div>
        </div>

        {/* Test Data Info */}
        <div className="mt-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
          <h3 className="font-semibold text-amber-800 mb-2">🧪 Dati di Test</h3>
          <p className="text-amber-700 text-sm">
            Questa visualizzazione usa dati reali del corso "Sebastiano Caboto" con {4} concetti principali estratti dai materiali.
            Puoi creare sotto-concetti dinamicamente e visualizzare il progresso di apprendimento.
          </p>
        </div>
      </div>
    </div>
  );
}