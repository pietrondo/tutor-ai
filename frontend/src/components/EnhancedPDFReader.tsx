/**
 * Enhanced PDF Reader
 * Componente avanzato per lettura PDF con annotazioni, note integrate e chat tutor
 */

'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { Highlight, Popup } from 'react-pdf-highlighter';
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

// Configura PDF.js
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

interface Annotation {
  id: string;
  type: 'highlight' | 'underline' | 'note';
  content: { text: string; image?: string };
  position: {
    boundingRect: any;
    rects: any[];
  };
  comment: string;
  color: string;
  pageNumber: number;
  isSharedWithChat: boolean;
  tags: string[];
  createdAt: Date;
}

interface EnhancedPDFReaderProps {
  pdfUrl: string;
  bookId: string;
  courseId: string;
  userId: string;
  onAnnotationCreate?: (annotation: Annotation) => void;
  onAnnotationUpdate?: (annotation: Annotation) => void;
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

const EnhancedPDFReader: React.FC<EnhancedPDFReaderProps> = ({
  pdfUrl,
  bookId,
  courseId,
  userId,
  onAnnotationCreate,
  onAnnotationUpdate,
  onChatWithContext
}) => {
  // Stati PDF
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.0);
  const [pdfLoaded, setPdfLoaded] = useState<boolean>(false);

  // Stati annotazioni
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [currentAnnotation, setCurrentAnnotation] = useState<Annotation | null>(null);
  const [selectedColor, setSelectedColor] = useState<string>('#FFEB3B');
  const [annotationMode, setAnnotationMode] = useState<'highlight' | 'underline' | 'note'>('highlight');
  const [showColorPicker, setShowColorPicker] = useState<boolean>(false);

  // Stati UI
  const [isSelecting, setIsSelecting] = useState<boolean>(false);
  const [showNotePanel, setShowNotePanel] = useState<boolean>(false);
  const [noteText, setNoteText] = useState<string>('');
  const [shareWithChat, setShareWithChat] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);

  // Carica annotazioni esistenti
  useEffect(() => {
    loadAnnotations();
  }, [bookId, userId]);

  const loadAnnotations = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/books/${bookId}/annotations?user_id=${userId}`);
      if (response.ok) {
        const data = await response.json();
        setAnnotations(data.annotations || []);
      }
    } catch (error) {
      console.error('Errore caricamento annotazioni:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Gestione caricamento PDF
  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setPdfLoaded(true);
  };

  // Gestione selezione testo
  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim().length > 0) {
      setIsSelecting(true);
      createAnnotationFromSelection(selection);
    }
  }, []);

  const createAnnotationFromSelection = async (selection: Selection) => {
    const selectedText = selection.toString().trim();
    const range = selection.getRangeAt(0);
    const rects = range.getClientRects();

    if (rects.length === 0) return;

    // Calcola posizione relativa alla pagina
    const containerRect = containerRef.current?.getBoundingClientRect();
    if (!containerRect) return;

    const boundingRect = {
      x1: rects[0].left - containerRect.left,
      y1: rects[0].top - containerRect.top,
      x2: rects[rects.length - 1].right - containerRect.left,
      y2: rects[rects.length - 1].bottom - containerRect.top,
      width: rects[rects.length - 1].right - rects[0].left,
      height: rects[rects.length - 1].bottom - rects[0].top
    };

    const newAnnotation: Annotation = {
      id: Date.now().toString(),
      type: annotationMode,
      content: { text: selectedText },
      position: {
        boundingRect,
        rects: Array.from(rects).map(rect => ({
          x: rect.left - containerRect.left,
          y: rect.top - containerRect.top,
          width: rect.width,
          height: rect.height
        }))
      },
      comment: '',
      color: selectedColor,
      pageNumber,
      isSharedWithChat: shareWithChat,
      tags: [],
      createdAt: new Date()
    };

    setCurrentAnnotation(newAnnotation);
    setShowNotePanel(true);
    setNoteText('');
  };

  // Salvataggio annotazione
  const saveAnnotation = async () => {
    if (!currentAnnotation) return;

    try {
      setIsLoading(true);

      // Genera tag automatici con AI
      const tags = await generateTagsForAnnotation(currentAnnotation.content.text);
      const annotationToSave = {
        ...currentAnnotation,
        comment: noteText,
        tags,
        isSharedWithChat: shareWithChat
      };

      // Salva sul backend
      const response = await fetch(`/api/books/${bookId}/annotations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          course_id: courseId,
          ...annotationToSave
        })
      });

      if (response.ok) {
        const savedAnnotation = await response.json();
        setAnnotations(prev => [...prev, savedAnnotation]);

        // Condividi con chat se richiesto
        if (shareWithChat && onChatWithContext) {
          onChatWithContext({
            type: 'pdf_annotation',
            bookId,
            pageNumber,
            text: currentAnnotation.content.text,
            note: noteText,
            tags,
            color: selectedColor
          });
        }

        // Notifica parent
        if (onAnnotationCreate) {
          onAnnotationCreate(savedAnnotation);
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

      const response = await fetch(`/api/books/${bookId}/annotations/${annotationId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setAnnotations(prev => prev.filter(ann => ann.id !== annotationId));
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
      const response = await fetch(`/api/books/${bookId}/annotations/export?user_id=${userId}&format=markdown`);
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
    setCurrentAnnotation(null);
    setShowNotePanel(false);
    setNoteText('');
    setIsSelecting(false);
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
  const renderAnnotation = (annotation: Annotation) => {
    return (
      <Highlight
        key={annotation.id}
        position={annotation.position}
        onClick={() => {
          setCurrentAnnotation(annotation);
          setShowNotePanel(true);
          setNoteText(annotation.comment);
        }}
        onMouseOver={(popup) => (
          <div
            className="annotation-popup"
            style={{
              position: 'absolute',
              left: popup.boundingRect.x1 + 'px',
              top: popup.boundingRect.y2 + 2 + 'px',
              backgroundColor: '#333',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              zIndex: 1000
            }}
          >
            {annotation.comment || 'Clicca per aggiungere nota...'}
          </div>
        )}
        style={{
          backgroundColor: annotation.color,
          opacity: annotation.type === 'underline' ? 0.3 : 0.5
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
                <div className="flex items-center justify-center h-96">
                  <div className="text-center text-red-600">
                    <p>Errore caricamento PDF</p>
                  </div>
                </div>
              }
            >
              <Page
                pageNumber={pageNumber}
                scale={scale}
                className="shadow-lg"
                renderTextLayer={true}
                renderAnnotationLayer={true}
              />
            </Document>
          </div>

          {/* Render annotazioni */}
          {annotations
            .filter(ann => ann.pageNumber === pageNumber)
            .map(renderAnnotation)}
        </div>

        {/* Pannello note */}
        {showNotePanel && currentAnnotation && (
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
                    "{currentAnnotation.content.text}"
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
                  disabled={isLoading || !noteText.trim()}
                  className="flex-1 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  <SaveIcon className="h-4 w-4" />
                  <span>Salva</span>
                </button>
                {currentAnnotation.id && (
                  <button
                    onClick={() => deleteAnnotation(currentAnnotation.id)}
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