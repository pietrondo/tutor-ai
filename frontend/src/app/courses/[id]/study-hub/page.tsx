"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  BookOpenIcon,
  ChartBarIcon,
  DocumentTextIcon,
  LightBulbIcon,
  QuestionMarkCircleIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  AcademicCapIcon,
  MapIcon,
  SparklesIcon
} from "@heroicons/react/24/outline";
import ConceptVisualization from "@/components/ConceptVisualization";
import { StudyProgress } from "@/components/StudyProgress";

interface Concept {
  id: string;
  name: string;
  summary: string;
  mastery_level: number;
  available_quizzes: string[];
  mindmap_node_ids: string[];
  recommended_minutes: number;
  learning_objectives: { id: string; description: string }[];
}

interface Quiz {
  id: string;
  title: string;
  difficulty: "easy" | "medium" | "hard";
  estimated_minutes: number;
  linked_concept_ids: string[];
  average_score?: number;
  user_scores?: number[];
  question_count: number;
}

interface Mindmap {
  id: string;
  title: string;
  linked_concept_ids: string[];
  total_nodes: number;
  views?: number;
  time_spent?: number;
}

interface LearningView {
  course_info: {
    id: string;
    name: string;
    book_id?: string;
  };
  concepts: Record<string, Concept>;
  quizzes: Record<string, Quiz>;
  mindmaps: Record<string, Mindmap>;
  connections: {
    concept_to_quizzes: Record<string, string[]>;
    concept_to_mindmaps: Record<string, string[]>;
    quiz_to_concepts: Record<string, string[]>;
    mindmap_to_concepts: Record<string, string[]>;
  };
  user_progress?: {
    concept_mastery: Record<string, number>;
    quiz_scores: Record<string, number[]>;
    study_sessions: number;
    total_study_time: number;
    strength_areas: string[];
    improvement_areas: string[];
  };
  recommendations?: {
    priority_concepts: Array<{
      concept_id: string;
      concept_name: string;
      current_mastery: number;
      recommended_quizzes: string[];
    }>;
    suggested_quizzes: string[];
    study_schedule: Array<{
      session: number;
      type: string;
      concept_name: string;
      estimated_minutes: number;
      activities: string[];
    }>;
  };
}

export default function StudyHubPage() {
  const params = useParams();
  const router = useRouter();
  const courseId = params.id as string;
  const [bookId, setBookId] = useState<string | null>(null);

  const [learningView, setLearningView] = useState<LearningView | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "concepts" | "quizzes" | "mindmaps" | "progress">("overview");
  const [selectedConcept, setSelectedConcept] = useState<Concept | null>(null);
  const [selectedQuiz, setSelectedQuiz] = useState<Quiz | null>(null);

  // Load available books for the course
  const [books, setBooks] = useState<Array<{ id: string; title: string }>>([]);

  useEffect(() => {
    if (!courseId) return;

    const loadCourseData = async () => {
      try {
        setLoading(true);

        // Load books for course
        const booksResponse = await fetch(`/api/courses/${courseId}/books`);
        if (booksResponse.ok) {
          const booksData = await booksResponse.json();
          setBooks(booksData.books || []);
        }

        // Load unified learning view
        const viewUrl = bookId
          ? `/api/unified-learning/view/course/${courseId}?book_id=${bookId}&user_id=demo_user`
          : `/api/unified-learning/view/course/${courseId}?user_id=demo_user`;

        const viewResponse = await fetch(viewUrl);
        if (viewResponse.ok) {
          const viewData = await viewResponse.json();
          setLearningView(viewData.data);
        }
      } catch (error) {
        console.error("Failed to load course data:", error);
      } finally {
        setLoading(false);
      }
    };

    loadCourseData();
  }, [courseId, bookId]);

  const handleTakeQuiz = (quiz: Quiz) => {
    // Navigate to quiz taking interface
    router.push(`/courses/${courseId}/quiz/${quiz.id}?book=${bookId || ''}`);
  };

  const handleGenerateQuiz = async (conceptId: string, difficulty: "easy" | "medium" | "hard" = "medium") => {
    try {
      const response = await fetch(`/api/unified-learning/quiz/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          course_id: courseId,
          topic: learningView?.concepts[conceptId]?.name || "General",
          difficulty,
          num_questions: 5,
          linked_concept_ids: [conceptId],
          book_id: bookId,
          user_id: "demo_user"
        })
      });

      if (response.ok) {
        // Reload the learning view to show the new quiz
        window.location.reload();
      }
    } catch (error) {
      console.error("Failed to generate quiz:", error);
    }
  };

  const handleOpenMindmap = (mindmapId: string) => {
    router.push(`/courses/${courseId}/books/${bookId}/mindmaps/${mindmapId}`);
  };

  const getMasteryColor = (mastery: number) => {
    if (mastery >= 0.8) return "text-green-600 bg-green-100";
    if (mastery >= 0.6) return "text-yellow-600 bg-yellow-100";
    if (mastery >= 0.3) return "text-orange-600 bg-orange-100";
    return "text-red-600 bg-red-100";
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case "easy": return "text-green-600 bg-green-100";
      case "medium": return "text-yellow-600 bg-yellow-100";
      case "hard": return "text-red-600 bg-red-100";
      default: return "text-gray-600 bg-gray-100";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ArrowPathIcon className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Caricamento hub di studio...</p>
        </div>
      </div>
    );
  }

  if (!learningView) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <XCircleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600">Impossibile caricare i dati di apprendimento</p>
        </div>
      </div>
    );
  }

  const concepts = Object.values(learningView.concepts);
  const quizzes = Object.values(learningView.quizzes);
  const mindmaps = Object.values(learningView.mindmaps);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {learningView.course_info.name}
              </h1>
              <p className="text-gray-600">Hub di Studio Integrato</p>
            </div>

            {/* Book Selector */}
            {books.length > 0 && (
              <div className="flex items-center space-x-4">
                <label className="text-sm font-medium text-gray-700">Libro:</label>
                <select
                  value={bookId || ""}
                  onChange={(e) => setBookId(e.target.value || null)}
                  className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Tutti i libri</option>
                  {books.map((book) => (
                    <option key={book.id} value={book.id}>
                      {book.title}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {[
              { id: "overview", label: "Panoramica", icon: ChartBarIcon },
              { id: "concepts", label: "Concetti", icon: LightBulbIcon },
              { id: "quizzes", label: "Quiz", icon: QuestionMarkCircleIcon },
              { id: "mindmaps", label: "Mappe Mentali", icon: MapIcon },
              { id: "progress", label: "Progresso", icon: AcademicCapIcon }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                <tab.icon className="h-5 w-5" />
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Tab */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center">
                  <LightBulbIcon className="h-8 w-8 text-yellow-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Concetti</p>
                    <p className="text-2xl font-bold text-gray-900">{concepts.length}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center">
                  <QuestionMarkCircleIcon className="h-8 w-8 text-blue-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Quiz Disponibili</p>
                    <p className="text-2xl font-bold text-gray-900">{quizzes.length}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center">
                  <MapIcon className="h-8 w-8 text-green-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Mappe Mentali</p>
                    <p className="text-2xl font-bold text-gray-900">{mindmaps.length}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center">
                  <AcademicCapIcon className="h-8 w-8 text-purple-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Sessioni di Studio</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {learningView.user_progress?.study_sessions || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recommendations */}
            {learningView.recommendations && (
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Piano di Studio Raccomandato</h3>
                <div className="space-y-3">
                  {learningView.recommendations.priority_concepts.map((concept, index) => (
                    <div key={concept.concept_id} className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="text-sm font-medium text-gray-700">Priorità {index + 1}</span>
                        <span className="font-medium">{concept.concept_name}</span>
                        <span className={`text-sm px-2 py-1 rounded-full ${getMasteryColor(concept.current_mastery)}`}>
                          {Math.round(concept.current_mastery * 100)}% padronanza
                        </span>
                      </div>
                      <button
                        onClick={() => handleGenerateQuiz(concept.concept_id)}
                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
                      >
                        Genera Quiz
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Concetti Recenti</h3>
                <div className="space-y-2">
                  {concepts.slice(0, 5).map((concept) => (
                    <div key={concept.id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                      <span className="text-sm font-medium text-gray-700">{concept.name}</span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getMasteryColor(concept.mastery_level)}`}>
                        {Math.round(concept.mastery_level * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quiz Disponibili</h3>
                <div className="space-y-2">
                  {quizzes.slice(0, 5).map((quiz) => (
                    <div key={quiz.id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                      <div>
                        <span className="text-sm font-medium text-gray-700">{quiz.title}</span>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className={`text-xs px-2 py-1 rounded ${getDifficultyColor(quiz.difficulty)}`}>
                            {quiz.difficulty}
                          </span>
                          <span className="text-xs text-gray-500">{quiz.question_count} domande</span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleTakeQuiz(quiz)}
                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                      >
                        Inizia
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Concepts Tab */}
        {activeTab === "concepts" && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Concetti del Corso</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {concepts.map((concept) => (
                  <div key={concept.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{concept.name}</h4>
                      <span className={`text-xs px-2 py-1 rounded-full ${getMasteryColor(concept.mastery_level)}`}>
                        {Math.round(concept.mastery_level * 100)}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{concept.summary}</p>

                    <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                      <span className="flex items-center">
                        <ClockIcon className="h-4 w-4 mr-1" />
                        {concept.recommended_minutes}min
                      </span>
                      <span>{concept.available_quizzes.length} quiz</span>
                    </div>

                    <div className="flex space-x-2">
                      {concept.available_quizzes.length > 0 && (
                        <button
                          onClick={() => {
                            const quiz = quizzes.find(q => q.id === concept.available_quizzes[0]);
                            if (quiz) handleTakeQuiz(quiz);
                          }}
                          className="flex-1 px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                        >
                          Quiz Rapido
                        </button>
                      )}
                      <button
                        onClick={() => handleGenerateQuiz(concept.id)}
                        className="flex-1 px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                      >
                        Genera Quiz
                      </button>
                      {concept.mindmap_node_ids.length > 0 && (
                        <button
                          onClick={() => {
                            const mindmap = mindmaps.find(m => concept.mindmap_node_ids.includes(m.id));
                            if (mindmap) handleOpenMindmap(mindmap.id);
                          }}
                          className="flex-1 px-2 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700"
                        >
                          Mappa
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {concepts.length > 0 && (
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Visualizzazione Concetti</h3>
                <ConceptVisualization
                  courseId={courseId}
                  bookId={bookId || undefined}
                />
              </div>
            )}
          </div>
        )}

        {/* Quizzes Tab */}
        {activeTab === "quizzes" && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Quiz Disponibili</h3>
                <button
                  onClick={() => handleGenerateQuiz("general", "medium")}
                  className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
                >
                  Genera Nuovo Quiz
                </button>
              </div>

              <div className="space-y-4">
                {quizzes.map((quiz) => (
                  <div key={quiz.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="font-medium text-gray-900">{quiz.title}</h4>
                        <div className="flex items-center space-x-3 mt-1 text-sm text-gray-600">
                          <span className={`px-2 py-1 rounded text-xs ${getDifficultyColor(quiz.difficulty)}`}>
                            {quiz.difficulty}
                          </span>
                          <span className="flex items-center">
                            <ClockIcon className="h-4 w-4 mr-1" />
                            {quiz.estimated_minutes}min
                          </span>
                          <span>{quiz.question_count} domande</span>
                        </div>
                      </div>
                      {quiz.average_score !== undefined && (
                        <div className="text-right">
                          <span className="text-sm text-gray-600">Media</span>
                          <span className="block text-lg font-semibold text-blue-600">
                            {Math.round(quiz.average_score * 100)}%
                          </span>
                        </div>
                      )}
                    </div>

                    {quiz.linked_concept_ids.length > 0 && (
                      <div className="mb-3">
                        <span className="text-xs text-gray-500">Concetti correlati:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {quiz.linked_concept_ids.map((conceptId) => {
                            const concept = concepts.find(c => c.id === conceptId);
                            return concept ? (
                              <span key={conceptId} className="text-xs bg-gray-100 px-2 py-1 rounded">
                                {concept.name}
                              </span>
                            ) : null;
                          })}
                        </div>
                      </div>
                    )}

                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleTakeQuiz(quiz)}
                        className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
                      >
                        {quiz.average_score !== undefined ? "Rifai Quiz" : "Inizia Quiz"}
                      </button>
                      {quiz.user_scores && quiz.user_scores.length > 0 && (
                        <button className="px-4 py-2 bg-gray-600 text-white text-sm rounded-md hover:bg-gray-700">
                          Risultati
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Mindmaps Tab */}
        {activeTab === "mindmaps" && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Mappe Mentali</h3>
                <button
                  onClick={() => router.push(`/courses/${courseId}/books/${bookId}/mindmaps/new`)}
                  className="px-4 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700"
                >
                  Crea Nuova Mappa
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {mindmaps.map((mindmap) => (
                  <div key={mindmap.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                    <h4 className="font-medium text-gray-900 mb-2">{mindmap.title}</h4>
                    <div className="text-sm text-gray-600 mb-3">
                      {mindmap.total_nodes} nodi • {mindmap.linked_concept_ids.length} concetti collegati
                    </div>

                    {mindmap.views !== undefined && (
                      <div className="text-xs text-gray-500 mb-3">
                        Visualizzazioni: {mindmap.views}
                        {mindmap.time_spent && ` • ${Math.round(mindmap.time_spent / 60)}min`}
                      </div>
                    )}

                    <button
                      onClick={() => handleOpenMindmap(mindmap.id)}
                      className="w-full px-3 py-2 bg-purple-600 text-white text-sm rounded hover:bg-purple-700"
                    >
                      Apri Mappa
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Progress Tab */}
        {activeTab === "progress" && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Il Tuo Progresso</h3>

              {learningView.user_progress ? (
                <div className="space-y-6">
                  {/* Overall Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {learningView.user_progress.study_sessions}
                      </div>
                      <div className="text-sm text-gray-600">Sessioni</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {Math.round(learningView.user_progress.total_study_time / 60)}min
                      </div>
                      <div className="text-sm text-gray-600">Tempo Totale</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {learningView.user_progress.strength_areas.length}
                      </div>
                      <div className="text-sm text-gray-600">Aree di Forza</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-orange-600">
                        {learningView.user_progress.improvement_areas.length}
                      </div>
                      <div className="text-sm text-gray-600">Da Migliorare</div>
                    </div>
                  </div>

                  {/* Progress Chart */}
                  <div>
                    <StudyProgress courseId={courseId} />
                  </div>

                  {/* Strength and Improvement Areas */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-3">Aree di Forza</h4>
                      <div className="space-y-2">
                        {learningView.user_progress.strength_areas.map((conceptId) => {
                          const concept = concepts.find(c => c.id === conceptId);
                          return concept ? (
                            <div key={conceptId} className="flex items-center justify-between p-2 bg-green-50 rounded">
                              <span className="text-sm font-medium text-green-800">{concept.name}</span>
                              <CheckCircleIcon className="h-5 w-5 text-green-600" />
                            </div>
                          ) : null;
                        })}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-medium text-gray-900 mb-3">Aree da Migliorare</h4>
                      <div className="space-y-2">
                        {learningView.user_progress.improvement_areas.map((conceptId) => {
                          const concept = concepts.find(c => c.id === conceptId);
                          return concept ? (
                            <div key={conceptId} className="flex items-center justify-between p-2 bg-orange-50 rounded">
                              <span className="text-sm font-medium text-orange-800">{concept.name}</span>
                              <button
                                onClick={() => handleGenerateQuiz(conceptId)}
                                className="px-2 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-700"
                              >
                                Pratica
                              </button>
                            </div>
                          ) : null;
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <AcademicCapIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">Inizia a studiare per vedere il tuo progresso</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}