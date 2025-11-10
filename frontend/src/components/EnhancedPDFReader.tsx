/**
 * Enhanced PDF Reader
 * Componente avanzato per lettura PDF con annotazioni, note integrate e chat tutor
 */

'use client';

// Ensure Promise.withResolvers polyfill is loaded before PDF.js
if (typeof Promise !== 'undefined' && !Promise.withResolvers) {
  Promise.withResolvers = function <T>() {
    let resolve: (value: T | PromiseLike<T>) => void;
    let reject: (reason?: any) => void;
    const promise = new Promise<T>((res, rej) => {
      resolve = res;
      reject = rej;
    });
    return { promise, resolve: resolve!, reject: reject! };
  };
}

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import pdfWorkerSrc from 'pdfjs-dist/build/pdf.worker.min.js?url';
import { CustomHighlight, type HighlightPosition } from './CustomHighlight';
import {
  HighlighterIcon,
  UnderlineIcon,
  MessageSquareIcon,
  BookOpenIcon,
  Share2Icon,
  SaveIcon,
  Trash2Icon,
  PaletteIcon,
  DownloadIcon
} from 'lucide-react';

// Configura PDF.js - usa CDN per evitare problemi di worker locali
if (typeof window !== 'undefined' && pdfjs.GlobalWorkerOptions) {
  pdfjs.GlobalWorkerOptions.workerSrc = pdfWorkerSrc;
}

type AnnotationMode = 'highlight' | 'underline' | 'note';

interface ViewerAnnotation {
  id: string;
  type: AnnotationMode;
  selectedText: string;
  note: string;
  position: HighlightPosition;
  pageNumber: number;
  color: string;
  shareWithAI: boolean;
  tags: string[];
  createdAt?: string;
}

interface AnnotationDraft {
  id?: string;
  type: AnnotationMode;
  selectedText: string;
  position: HighlightPosition;
  color: string;
  shareWithAI: boolean;
  tags?: string[];
  isExisting?: boolean;
}

type BackendAnnotation = Record<string, unknown>;

interface EnhancedPDFReaderProps {
  pdfUrl: string;
  pdfFilename: string;
  pdfPath?: string;
  bookId: string;
  courseId: string;
  userId: string;
  onAnnotationCreate?: (annotation: BackendAnnotation) => void;
  onAnnotationUpdate?: (annotation: BackendAnnotation) => void;
  onChatWithContext?: (context: any) => void;
}

const COLORS = [
  { name: 'Giallo', value: '#FFEB3B' },
  { name: 'Verde', value: '#4CAF50' },
  { name: 'Blu', value: '#2196F3' },
  { name: 'Rosa', value: '#E91E63' },
  { name: 'Arancione', value: '#FF9800' },
  { name: 'Viola', value: '#9C27B0' }
];

// PDF Error Display Component
const PDFErrorDisplay: React.FC<{
  pdfUrl: string;
  onRetry: () => void;
}> = ({ pdfUrl, onRetry }) => {
  const [errorDetails, setErrorDetails] = useState<string>('');

  useEffect(() => {
    // Try to identify common PDF errors
    if (pdfUrl.includes('.pdf')) {
      if (pdfUrl.startsWith('http')) {
        setErrorDetails('Possibile problema di rete o file PDF corrotto.');
      } else {
        setErrorDetails('File PDF non trovato o percorso non valido.');
      }
    } else {
      setErrorDetails('Il file specificato non sembra essere un PDF valido.');
    }
  }, [pdfUrl]);

  return (
    <div className="flex items-center justify-center h-96">
      <div className="text-center max-w-md mx-auto p-6">
        <div className="text-red-500 mb-4">
          <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Errore nel caricamento del PDF
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          {errorDetails}
        </p>
        <div className="space-y-3">
          <button
            onClick={onRetry}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Riprova
          </button>
          <button
            onClick={() => window.open(pdfUrl, '_blank')}
            className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Apri in nuova scheda
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-4">
          Se il problema persiste, contatta l'amministratore del sistema.
        </p>
      </div>
    </div>
  );
};

const EnhancedPDFReader: React.FC<EnhancedPDFReaderProps> = ({
  pdfUrl,
  pdfFilename,
  pdfPath,
  bookId,
  courseId,
  userId,
  onAnnotationCreate,
  onAnnotationUpdate,
  onChatWithContext
}) => {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
  // Stati PDF
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.0);

  // Stati annotazioni
  const [annotations, setAnnotations] = useState<ViewerAnnotation[]>([]);
  const [panelAnnotation, setPanelAnnotation] = useState<AnnotationDraft | null>(null);
  const [selectedColor, setSelectedColor] = useState<string>('#FFEB3B');
  const [annotationMode, setAnnotationMode] = useState<AnnotationMode>('highlight');
  const [showColorPicker, setShowColorPicker] = useState<boolean>(false);

  // Stati UI
  const [showNotePanel, setShowNotePanel] = useState<boolean>(false);
  const [noteText, setNoteText] = useState<string>('');
  const [shareWithChat, setShareWithChat] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);

  
  const mapAnnotationFromBackend = useCallback((annotation: BackendAnnotation): ViewerAnnotation => {
    const position = annotation?.position || {};
    const page = position.pageNumber || annotation?.page_number || 1;

    return {
      id: annotation.id,
      type: (annotation.type || 'highlight') as AnnotationMode,
      selectedText: annotation.selected_text || annotation.text || '',
      note: annotation.content || '',
      position: {
        x: position.x ?? 0,
        y: position.y ?? 0,
        width: position.width ?? 0,
        height: position.height ?? 0,
        pageNumber: page
      },
      pageNumber: page,
      color: annotation.style?.color || '#FFEB3B',
      shareWithAI: annotation.share_with_ai ?? annotation.is_public ?? false,
      tags: annotation.tags || [],
      createdAt: annotation.created_at
    };
  }, []);

  const loadAnnotations = useCallback(async () => {
    try {
      setIsLoading(true);
      if (!pdfFilename) {
        setAnnotations([]);
        return;
      }

      const response = await fetch(`${API_BASE_URL}/annotations/${userId}/${encodeURIComponent(pdfFilename)}?course_id=${courseId}&book_id=${bookId}`);
      if (response.ok) {
        const data = await response.json();
        const normalized = (data.annotations || []).map(mapAnnotationFromBackend);
        setAnnotations(normalized);
      }
    } catch (error) {
      console.error('Errore caricamento annotazioni:', error);
    } finally {
      setIsLoading(false);
    }
  }, [API_BASE_URL, bookId, courseId, pdfFilename, userId, mapAnnotationFromBackend]);

  // Carica annotazioni esistenti
  useEffect(() => {
    loadAnnotations();
  }, [loadAnnotations]);

  // Gestione caricamento PDF
  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  };

  // Gestione selezione testo
  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim().length > 0) {
      createAnnotationFromSelection(selection);
    }
  }, []);

  const createAnnotationFromSelection = async (selection: Selection) => {
    const selectedText = selection.toString().trim();
    const range = selection.getRangeAt(0);
    const rects = range.getClientRects();

    if (rects.length === 0) return;

    // Calcola posizione relativa alla pagina
    const pageContainer = selection.anchorNode?.parentElement?.closest('.react-pdf__Page');
    if (!pageContainer) return;

    const pageRect = pageContainer.getBoundingClientRect();
    const firstRect = rects[0];
    const lastRect = rects[rects.length - 1];

    const draft: AnnotationDraft = {
      type: annotationMode,
      selectedText,
      position: {
        x: firstRect.left - pageRect.left,
        y: firstRect.top - pageRect.top,
        width: lastRect.right - firstRect.left,
        height: lastRect.bottom - firstRect.top,
        pageNumber
      },
      color: selectedColor,
      shareWithAI: true
    };

    setPanelAnnotation(draft);
    setShareWithChat(true);
    setShowNotePanel(true);
    setNoteText('');
  };

  // Salvataggio annotazione
  const saveAnnotation = async () => {
    if (!panelAnnotation || !pdfFilename) return;

    try {
      setIsLoading(true);

      const baseStyle = {
        color: panelAnnotation.color,
        opacity: panelAnnotation.type === 'underline' ? 0 : 0.3,
        stroke_color: panelAnnotation.color,
        stroke_width: panelAnnotation.type === 'underline' ? 2 : 1
      };

      const baseTags = panelAnnotation.isExisting
        ? panelAnnotation.tags || []
        : await generateTagsForAnnotation(panelAnnotation.selectedText);

      if (panelAnnotation.isExisting && panelAnnotation.id) {
        const response = await fetch(
          `${API_BASE_URL}/annotations/${userId}/${panelAnnotation.id}?pdf_filename=${encodeURIComponent(pdfFilename)}&course_id=${courseId}&book_id=${bookId}`,
          {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              type: panelAnnotation.type,
              content: noteText,
              style: baseStyle,
              tags: baseTags,
              is_public: shareWithChat,
              share_with_ai: shareWithChat
            })
          }
        );

        if (response.ok) {
          const data = await response.json();
          if (data.annotation) {
            const updated = mapAnnotationFromBackend(data.annotation);
            setAnnotations(prev => prev.map(ann => ann.id === updated.id ? updated : ann));
            onAnnotationUpdate?.(data.annotation);
          }
        }
      } else {
        const response = await fetch(`${API_BASE_URL}/annotations`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            course_id: courseId,
            book_id: bookId,
            pdf_filename: pdfFilename,
            pdf_path: pdfPath || pdfUrl,
            page_number: panelAnnotation.position.pageNumber,
            type: panelAnnotation.type,
            text: panelAnnotation.selectedText,
            selected_text: panelAnnotation.selectedText,
            content: noteText,
            position: panelAnnotation.position,
            style: baseStyle,
            tags: baseTags,
            is_public: shareWithChat,
            share_with_ai: shareWithChat
          })
        });

        if (response.ok) {
          const data = await response.json();
          if (data.annotation) {
            const normalized = mapAnnotationFromBackend(data.annotation);
            setAnnotations(prev => [normalized, ...prev]);
            onAnnotationCreate?.(data.annotation);

            if (shareWithChat && onChatWithContext) {
              onChatWithContext({
                type: 'pdf_annotation',
                bookId,
                pageNumber: panelAnnotation.position.pageNumber,
                text: panelAnnotation.selectedText,
                note: noteText,
                tags: baseTags,
                color: panelAnnotation.color
              });
            }
          }
        }
      }

      resetAnnotationState();
    } catch (error) {
      console.error('Errore salvataggio annotazione:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateTagsForAnnotation = async (text: string): Promise<string[]> => {
    try {
      const response = await fetch('/api/ai/generate-tags', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          course_id: courseId
        })
      });

      if (response.ok) {
        const data = await response.json();
        return data.tags || [];
      }
    } catch (error) {
      console.error('Errore generazione tag:', error);
    }

    return [];
  };

  // Eliminazione annotazione
  const deleteAnnotation = async (annotationId: string) => {
    try {
      setIsLoading(true);

      const response = await fetch(
        `${API_BASE_URL}/annotations/${userId}/${annotationId}?pdf_filename=${encodeURIComponent(pdfFilename)}&course_id=${courseId}&book_id=${bookId}`,
        { method: 'DELETE' }
      );

      if (response.ok) {
        setAnnotations(prev => prev.filter(ann => ann.id !== annotationId));
        if (panelAnnotation?.id === annotationId) {
          resetAnnotationState();
        }
      }
    } catch (error) {
      console.error('Errore eliminazione annotazione:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Esporta annotazioni
  const exportAnnotations = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/annotations/${userId}/export?format=markdown&course_id=${courseId}&book_id=${bookId}`);
      if (response.ok) {
        const data = await response.json();

        // Download file
        const blob = new Blob([data.markdown], { type: 'text/markdown' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `annotazioni_${bookId}_${new Date().toISOString().split('T')[0]}.md`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Errore esportazione annotazioni:', error);
    }
  };

  // Reset stato annotazione
  const resetAnnotationState = () => {
    setPanelAnnotation(null);
    setShowNotePanel(false);
    setNoteText('');
    setShareWithChat(true);
  };

  // Navigazione PDF
  const changePage = (offset: number) => {
    setPageNumber(prevPageNumber => Math.min(Math.max(1, prevPageNumber + offset), numPages));
  };

  const previousPage = () => changePage(-1);
  const nextPage = () => changePage(1);

  const zoomIn = () => setScale(prev => Math.min(prev + 0.2, 3.0));
  const zoomOut = () => setScale(prev => Math.max(prev - 0.2, 0.5));

  // Render annotazioni
  const renderAnnotation = (annotation: ViewerAnnotation) => {
    if (!annotation.position) {
      return null;
    }

    return (
      <CustomHighlight
        key={annotation.id}
        id={annotation.id}
        position={annotation.position}
        content={{ text: annotation.selectedText }}
        comment={{ emoji: '📝', text: annotation.note || '' }}
        color={annotation.color}
        type={annotation.type}
        isScrolledTo={false}
        onClick={() => {
          setAnnotationMode(annotation.type);
          setPanelAnnotation({
            id: annotation.id,
            type: annotation.type,
            selectedText: annotation.selectedText,
            position: annotation.position,
            color: annotation.color,
            shareWithAI: annotation.shareWithAI,
            tags: annotation.tags,
            isExisting: true
          });
          setShareWithChat(annotation.shareWithAI);
          setNoteText(annotation.note);
          setShowNotePanel(true);
        }}
      />
    );
  };

  if (!pdfUrl) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <BookOpenIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Nessun PDF selezionato</h3>
          <p className="mt-1 text-sm text-gray-500">Seleziona un libro per iniziare a leggere</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200">
        <div className="flex items-center space-x-2">
          {/* Strumenti annotazione */}
          <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setAnnotationMode('highlight')}
              className={`p-2 rounded ${annotationMode === 'highlight' ? 'bg-blue-500 text-white' : 'text-gray-700 hover:bg-gray-200'}`}
              title="Evidenzia"
            >
              <HighlighterIcon className="h-4 w-4" />
            </button>
            <button
              onClick={() => setAnnotationMode('underline')}
              className={`p-2 rounded ${annotationMode === 'underline' ? 'bg-blue-500 text-white' : 'text-gray-700 hover:bg-gray-200'}`}
              title="Sottolinea"
            >
              <UnderlineIcon className="h-4 w-4" />
            </button>
            <button
              onClick={() => setAnnotationMode('note')}
              className={`p-2 rounded ${annotationMode === 'note' ? 'bg-blue-500 text-white' : 'text-gray-700 hover:bg-gray-200'}`}
              title="Aggiungi nota"
            >
              <MessageSquareIcon className="h-4 w-4" />
            </button>
          </div>

          {/* Color picker */}
          <div className="relative">
            <button
              onClick={() => setShowColorPicker(!showColorPicker)}
              className="p-2 rounded text-gray-700 hover:bg-gray-200 border border-gray-300"
              title="Colore"
            >
              <PaletteIcon className="h-4 w-4" />
              <div
                className="absolute top-0 right-0 w-2 h-2 rounded-full border border-gray-400"
                style={{ backgroundColor: selectedColor }}
              />
            </button>

            {showColorPicker && (
              <div className="absolute top-10 left-0 bg-white border border-gray-200 rounded-lg shadow-lg p-2 z-50">
                {COLORS.map(color => (
                  <button
                    key={color.value}
                    onClick={() => {
                      setSelectedColor(color.value);
                      setShowColorPicker(false);
                    }}
                    className="block w-full text-left px-2 py-1 hover:bg-gray-100 rounded flex items-center space-x-2"
                  >
                    <div
                      className="w-4 h-4 rounded border border-gray-300"
                      style={{ backgroundColor: color.value }}
                    />
                    <span className="text-sm">{color.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Controlli navigazione */}
          <div className="flex items-center space-x-2">
            <button
              onClick={previousPage}
              disabled={pageNumber <= 1}
              className="p-2 rounded text-gray-700 hover:bg-gray-200 disabled:opacity-50"
            >
              ←
            </button>
            <span className="text-sm text-gray-700">
              Pagina {pageNumber} di {numPages}
            </span>
            <button
              onClick={nextPage}
              disabled={pageNumber >= numPages}
              className="p-2 rounded text-gray-700 hover:bg-gray-200 disabled:opacity-50"
            >
              →
            </button>
          </div>

          {/* Zoom */}
          <div className="flex items-center space-x-1">
            <button
              onClick={zoomOut}
              className="p-2 rounded text-gray-700 hover:bg-gray-200"
            >
              −
            </button>
            <span className="text-sm text-gray-700 min-w-[50px] text-center">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={zoomIn}
              className="p-2 rounded text-gray-700 hover:bg-gray-200"
            >
              +
            </button>
          </div>

          {/* Azioni */}
          <div className="flex items-center space-x-1 border-l border-gray-300 pl-2">
            <button
              onClick={exportAnnotations}
              className="p-2 rounded text-gray-700 hover:bg-gray-200"
              title="Esporta annotazioni"
            >
              <DownloadIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Area contenuto */}
      <div className="flex-1 flex">
        {/* PDF Viewer */}
        <div
          ref={containerRef}
          className="flex-1 overflow-auto bg-gray-100 relative"
          onMouseUp={handleTextSelection}
        >
          {isLoading && (
            <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                <p className="mt-2 text-sm text-gray-600">Caricamento...</p>
              </div>
            </div>
          )}

          <div className="flex justify-center p-8">
            <div className="relative">
              <Document
                file={pdfUrl}
                onLoadSuccess={onDocumentLoadSuccess}
                loading={
                  <div className="flex items-center justify-center h-96">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                      <p className="mt-2 text-sm text-gray-600">Caricamento PDF...</p>
                    </div>
                  </div>
                }
                error={
                  <PDFErrorDisplay
                    pdfUrl={pdfUrl}
                    onRetry={() => window.location.reload()}
                  />
                }
              >
                <Page
                  pageNumber={pageNumber}
                  scale={scale}
                  className="shadow-lg"
                  renderTextLayer={true}
                  renderAnnotationLayer={true}
                />
                {/* Render annotazioni */}
                {annotations
                  .filter(ann => ann.pageNumber === pageNumber)
                  .map(renderAnnotation)}
              </Document>
            </div>
          </div>
        </div>

        {/* Pannello note */}
        {showNotePanel && panelAnnotation && (
          <div className="w-80 bg-white border-l border-gray-200 p-4 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                {annotationMode === 'note' ? 'Aggiungi Nota' : 'Modifica Annotazione'}
              </h3>
              <button
                onClick={resetAnnotationState}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>

            <div className="space-y-4">
              {/* Testo selezionato */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Testo selezionato
                </label>
                <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-sm text-gray-900 italic">
                    "{panelAnnotation.selectedText}"
                  </p>
                </div>
              </div>

              {/* Nota personale */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  La tua nota
                </label>
                <textarea
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={4}
                  placeholder="Aggiungi qui le tue note personali..."
                />
              </div>

              {/* Opzioni condivisione */}
              <div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={shareWithChat}
                    onChange={(e) => setShareWithChat(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">
                    Condividi con il tutor AI
                  </span>
                </label>
                <p className="mt-1 text-xs text-gray-500">
                  Il tutor AI potrà usare questa nota per dare risposte più personalizzate
                </p>
              </div>

              {/* Pulsanti azione */}
              <div className="flex space-x-2 pt-4">
                <button
                  onClick={saveAnnotation}
                  disabled={isLoading || (panelAnnotation.type === 'note' && !noteText.trim())}
                  className="flex-1 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  <SaveIcon className="h-4 w-4" />
                  <span>Salva</span>
                </button>
                {panelAnnotation.id && (
                  <button
                    onClick={() => deleteAnnotation(panelAnnotation.id!)}
                    disabled={isLoading}
                    className="p-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50 disabled:opacity-50"
                  >
                    <Trash2Icon className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedPDFReader;
