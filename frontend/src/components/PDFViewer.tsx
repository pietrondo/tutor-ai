'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import {
  FileText,
  ZoomIn,
  ZoomOut,
  Highlighter,
  Edit3,
  Save,
  X,
  ArrowLeft,
  MessageSquare,
  Search
} from 'lucide-react'
import { ensurePdfWorkerConfigured, getWorkerDiagnostics, type WorkerConfigResult } from '@/lib/pdfWorker'

// Import PDF error display component
const PDFErrorDisplay: React.FC<{
  pdfUrl: string;
  onRetry: () => void;
  workerInfo?: WorkerConfigResult | null;
  workerError?: string | null;
}> = ({ pdfUrl, onRetry, workerInfo, workerError }) => {
  const [errorDetails, setErrorDetails] = useState<string>('');
  const [debugInfo, setDebugInfo] = useState<string>('');

  useEffect(() => {
    // Enhanced error diagnostics for PDF viewer
    const diagnoseError = async () => {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      let debugDetails = [];
      debugDetails.push(`URL: ${pdfUrl}`);
      debugDetails.push(`API Base URL: ${apiBaseUrl}`);
      debugDetails.push(`User Agent: ${navigator.userAgent}`);

      try {
        // Test if PDF is accessible
        console.log('PDFViewer: Testing PDF accessibility:', pdfUrl);
        const response = await fetch(pdfUrl, { method: 'HEAD' });
        debugDetails.push(`HTTP Status: ${response.status}`);
        debugDetails.push(`Content-Type: ${response.headers.get('content-type')}`);
        debugDetails.push(`Content-Length: ${response.headers.get('content-length')}`);

        if (!response.ok) {
          setErrorDetails(`Server responded with ${response.status}: ${response.statusText}\n\nIl server PDF non è raggiungibile o il file non esiste.`);
          return;
        }

        if (!response.headers.get('content-type')?.includes('application/pdf')) {
          setErrorDetails(`Il server non sta restituendo un file PDF.\nContent-Type: ${response.headers.get('content-type')}\n\nQuesto potrebbe indicare un problema di configurazione del backend.`);
          return;
        }

        // Check if PDF.js worker is properly configured
        const workerSrc = (window as any).pdfjs?.GlobalWorkerOptions?.workerSrc;
        if (!workerSrc) {
          setErrorDetails("PDF.js worker non configurato. Il worker è necessario per renderizzare i PDF nel browser.");
          return;
        }

        let enhancedMessage = "Il PDF è accessibile ma react-pdf non riesce a caricarlo.\n\n";
        if (workerError) {
          enhancedMessage += `Configurazione worker fallita: ${workerError}\n\n`;
        } else if (workerInfo?.workerSrc) {
          enhancedMessage += `Worker attivo: ${workerInfo.workerSrc} (${workerInfo.strategy})\n\n`;
        }

        enhancedMessage += `Possibili cause:\n• PDF.js worker non disponibile o bloccato\n• Problemi di CORS nel browser\n• PDF troppo grande o complesso\n• Estensioni del browser che bloccano il caricamento\n\nConsigli:\n1. Ricarica la pagina (Ctrl+F5 per cache pulita)\n2. Prova un browser diverso (Chrome/Firefox)\n3. Disabilita temporaneamente estensioni\n4. Apri il PDF in una nuova scheda\n\nDebug:\n• PDF.js worker: ${workerSrc}\n• Content-Type: ${response.headers.get('content-type')}`;

        if (workerInfo?.attempts?.length) {
          const attemptsLog = workerInfo.attempts
            .map(attempt => `  - ${attempt.url} (${attempt.via}) => ${attempt.success ? 'OK' : `ERR ${attempt.status || ''} ${attempt.error || ''}`}`)
            .join('\n');
          enhancedMessage += `\nTentativi worker:\n${attemptsLog}`;
          debugDetails.push(`Worker attempts:\n${attemptsLog}`);
        }

        setErrorDetails(enhancedMessage);

      } catch (error) {
        debugDetails.push(`Network Error: ${error}`);
        setErrorDetails(`Errore di rete durante il caricamento del PDF.\n\nErrore: ${error}`);
      }

      setDebugInfo(debugDetails.join('\n'));
    };

    diagnoseError();
  }, [pdfUrl, workerInfo, workerError]);

  return (
    <div className="flex items-center justify-center h-96">
      <div className="text-center max-w-md mx-auto p-6">
        <div className="text-red-500 mb-4">
          <FileText className="w-16 h-16 mx-auto" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Errore nel caricamento del PDF
        </h3>
        <p className="text-sm text-gray-600 mb-4 whitespace-pre-line">
          {errorDetails}
        </p>

        {/* Debug information */}
        <details className="mb-4 text-left">
          <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
            Informazioni di debug
          </summary>
          <div className="mt-2 p-2 bg-gray-100 rounded text-xs text-gray-600 whitespace-pre-wrap text-left">
            {debugInfo || (
              <>
                <p><strong>URL:</strong> {pdfUrl}</p>
                <p><strong>Tipo:</strong> {pdfUrl.includes('.pdf') ? 'PDF' : 'Non-PDF'}</p>
                <p><strong>Protocollo:</strong> {pdfUrl.startsWith('http') ? 'HTTP/HTTPS' : 'Altro'}</p>
              </>
            )}
          </div>
        </details>

        <div className="space-y-3">
          <button
            onClick={onRetry}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Riprova
          </button>
          <button
            onClick={() => window.open(pdfUrl, '_blank')}
            className="w-full px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
          >
            Apri PDF in nuova scheda
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-4">
          Se il problema persiste, contatta l'amministratore del sistema.
        </p>
      </div>
    </div>
  );
};

interface PDFAnnotation {
  id: string
  type: 'highlight' | 'underline' | 'note' | 'text'
  content: string
  position: {
    x: number
    y: number
    width: number
    height: number
    pageNumber: number
  }
  color: string
  createdAt: string
}

interface PDFViewerProps {
  pdfUrl: string
  title: string
  onBack?: () => void
  onSave?: (annotations: PDFAnnotation[]) => void
}

export function PDFViewer({ pdfUrl, title, onBack, onSave }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.0)
  const [annotations, setAnnotations] = useState<PDFAnnotation[]>([])
  const [isAnnotating, setIsAnnotating] = useState<boolean>(false)
  const [annotationType, setAnnotationType] = useState<'highlight' | 'underline' | 'note' | 'text'>('highlight')
  const [annotationColor, setAnnotationColor] = useState<string>('#ffff00')
  const [selectedText, setSelectedText] = useState<string>('')
  const [showNoteDialog, setShowNoteDialog] = useState<boolean>(false)
  const [noteText, setNoteText] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [showSearch, setShowSearch] = useState<boolean>(false)
  const existingWorkerDiagnostics = typeof window === 'undefined' ? null : getWorkerDiagnostics()
  const [workerReady, setWorkerReady] = useState<boolean>(() => typeof window === 'undefined' || Boolean(existingWorkerDiagnostics))
  const [workerDiagnostics, setWorkerDiagnostics] = useState<WorkerConfigResult | null>(existingWorkerDiagnostics)
  const [workerError, setWorkerError] = useState<string | null>(null)

  const pdfContainerRef = useRef<HTMLDivElement>(null)

  const colors = {
    highlight: ['#ffff00', '#00ff00', '#ff9900', '#ff6666', '#9966ff'],
    underline: ['#0000ff', '#ff0000', '#008000', '#ff00ff', '#ff8800'],
    note: ['#ffffff', '#ffeecc', '#ccffcc', '#cceeff', '#ffccff']
  }

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
  }, [])

  const changePage = useCallback((offset: number) => {
    setPageNumber(prevPageNumber => Math.min(Math.max(1, prevPageNumber + offset), numPages))
  }, [numPages])

  const zoomIn = useCallback(() => {
    setScale(prevScale => Math.min(prevScale + 0.2, 3.0))
  }, [])

  const zoomOut = useCallback(() => {
    setScale(prevScale => Math.max(prevScale - 0.2, 0.5))
  }, [])

  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection()
    if (selection && selection.toString().trim()) {
      setSelectedText(selection.toString().trim())
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    ensurePdfWorkerConfigured()
      .then(result => {
        if (cancelled) return
        setWorkerDiagnostics(result)
        setWorkerReady(true)
        setWorkerError(null)
      })
      .catch(error => {
        if (cancelled) return
        const message = error instanceof Error ? error.message : String(error)
        setWorkerError(message)
        setWorkerReady(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  const retryWorkerConfiguration = useCallback(() => {
    setWorkerReady(false)
    setWorkerError(null)
    ensurePdfWorkerConfigured(true)
      .then(result => {
        setWorkerDiagnostics(result)
        setWorkerReady(true)
      })
      .catch(error => {
        const message = error instanceof Error ? error.message : String(error)
        setWorkerError(message)
      })
  }, [])

  const addAnnotation = useCallback(() => {
    if (!selectedText) return

    const selection = window.getSelection()
    if (!selection || selection.rangeCount === 0) return

    const range = selection.getRangeAt(0)
    const rect = range.getBoundingClientRect()

    // Get the page container
    const pageContainer = selection.anchorNode?.parentElement?.closest('.react-pdf__Page')
    if (!pageContainer) return

    const pageRect = pageContainer.getBoundingClientRect()

    const newAnnotation: PDFAnnotation = {
      id: Date.now().toString(),
      type: annotationType,
      content: noteText || selectedText,
      position: {
        x: rect.left - pageRect.left,
        y: rect.top - pageRect.top,
        width: rect.width,
        height: rect.height,
        pageNumber
      },
      color: annotationColor,
      createdAt: new Date().toISOString()
    }

    setAnnotations(prev => [...prev, newAnnotation])
    setShowNoteDialog(false)
    setNoteText('')
    setSelectedText('')
    selection.removeAllRanges()
  }, [selectedText, annotationType, annotationColor, noteText, pageNumber])

  const deleteAnnotation = useCallback((id: string) => {
    setAnnotations(prev => prev.filter(ann => ann.id !== id))
  }, [])

  const saveAnnotations = useCallback(() => {
    if (onSave) {
      onSave(annotations)
    }
    // Also save to localStorage
    localStorage.setItem(`pdf-annotations-${title}`, JSON.stringify(annotations))
  }, [annotations, title, onSave])

  // Load annotations from localStorage on mount
  useEffect(() => {
    const savedAnnotations = localStorage.getItem(`pdf-annotations-${title}`)
    if (savedAnnotations) {
      try {
        setAnnotations(JSON.parse(savedAnnotations))
      } catch (error) {
        console.error('Error loading annotations:', error)
      }
    }
  }, [title])

  const renderAnnotations = useCallback(() => {
    return annotations
      .filter(ann => ann.position.pageNumber === pageNumber)
      .map(annotation => {
        const baseClasses = "absolute pointer-events-none"
        const style = {
          left: annotation.position.x,
          top: annotation.position.y,
          width: annotation.position.width,
          height: annotation.position.height,
          backgroundColor: annotation.type === 'highlight' ? annotation.color : 'transparent',
          borderBottom: annotation.type === 'underline' ? `2px solid ${annotation.color}` : 'none',
          borderRadius: annotation.type === 'highlight' ? '2px' : '0'
        }

        return (
          <div
            key={annotation.id}
            className={`${baseClasses} ${annotation.type === 'note' ? 'pointer-events-auto' : ''}`}
            style={style}
            title={annotation.content}
          >
            {annotation.type === 'note' && (
              <div
                className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full cursor-pointer hover:bg-yellow-500"
                onClick={() => deleteAnnotation(annotation.id)}
              />
            )}
          </div>
        )
      })
  }, [annotations, pageNumber, deleteAnnotation])

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {onBack && (
              <button
                onClick={onBack}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
            )}
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-blue-600" />
              <h1 className="text-lg font-semibold text-gray-900 truncate max-w-xs">{title}</h1>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Search */}
            <button
              onClick={() => setShowSearch(!showSearch)}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              title="Cerca nel PDF"
            >
              <Search className="h-4 w-4" />
            </button>

            {/* Annotation Tools */}
            <button
              onClick={() => setIsAnnotating(!isAnnotating)}
              className={`p-2 rounded-lg transition-colors ${
                isAnnotating
                  ? 'bg-blue-100 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
              title="Strumenti di annotazione"
            >
              <Edit3 className="h-4 w-4" />
            </button>

            {/* Zoom Controls */}
            <button
              onClick={zoomOut}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              title="Zoom indietro"
            >
              <ZoomOut className="h-4 w-4" />
            </button>
            <span className="text-sm text-gray-600 min-w-[50px] text-center">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={zoomIn}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              title="Zoom avanti"
            >
              <ZoomIn className="h-4 w-4" />
            </button>

            {/* Save */}
            <button
              onClick={saveAnnotations}
              className="p-2 bg-green-100 text-green-600 hover:bg-green-200 rounded-lg transition-colors"
              title="Salva annotazioni"
            >
              <Save className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Annotation Tools Bar */}
        {isAnnotating && (
          <div className="mt-3 flex items-center space-x-4 p-3 bg-gray-50 rounded-lg">
            <span className="text-sm font-medium text-gray-700">Tipo:</span>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setAnnotationType('highlight')}
                className={`p-2 rounded-lg transition-colors ${
                  annotationType === 'highlight'
                    ? 'bg-yellow-100 text-yellow-700 border border-yellow-300'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
                title="Evidenzia"
              >
                <Highlighter className="h-4 w-4" />
              </button>

              <button
                onClick={() => setAnnotationType('underline')}
                className={`p-2 rounded-lg transition-colors ${
                  annotationType === 'underline'
                    ? 'bg-blue-100 text-blue-700 border border-blue-300'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
                title="Sottolinea"
              >
                <Edit3 className="h-4 w-4" />
              </button>

              <button
                onClick={() => setAnnotationType('note')}
                className={`p-2 rounded-lg transition-colors ${
                  annotationType === 'note'
                    ? 'bg-green-100 text-green-700 border border-green-300'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
                title="Aggiungi nota"
              >
                <MessageSquare className="h-4 w-4" />
              </button>
            </div>

            {/* Color Picker */}
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">Colore:</span>
              <div className="flex space-x-1">
                {colors[annotationType].map(color => (
                  <button
                    key={color}
                    onClick={() => setAnnotationColor(color)}
                    className={`w-6 h-6 rounded border-2 transition-all ${
                      annotationColor === color
                        ? 'border-gray-800 scale-110'
                        : 'border-gray-300 hover:border-gray-500'
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>

            {/* Instructions */}
            <span className="text-sm text-gray-500 ml-auto">
              Seleziona il testo nel PDF per aggiungere un'annotazione
            </span>
          </div>
        )}

        {/* Search Bar */}
        {showSearch && (
          <div className="mt-3">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Cerca nel documento..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-auto" ref={pdfContainerRef} onMouseUp={handleTextSelection}>
        <div className="flex justify-center p-4">
          <div className="relative w-full min-h-[20rem]">
            {!workerReady && !workerError && (
              <div className="flex h-80 items-center justify-center">
                <div className="text-center text-sm text-gray-600">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2">Inizializzo il PDF.js worker...</p>
                </div>
              </div>
            )}

            {workerError && (
              <PDFErrorDisplay
                pdfUrl={pdfUrl}
                workerInfo={workerDiagnostics}
                workerError={workerError}
                onRetry={() => {
                  console.warn('PDFViewer: Worker configuration retry requested')
                  retryWorkerConfiguration()
                }}
              />
            )}

            {workerReady && !workerError && (
              <Document
                file={pdfUrl}
                onLoadSuccess={onDocumentLoadSuccess}
                loading={
                  <div className="flex items-center justify-center p-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="ml-3 text-gray-600">Caricamento PDF...</span>
                  </div>
                }
                error={
                  <PDFErrorDisplay
                    pdfUrl={pdfUrl}
                    workerInfo={workerDiagnostics}
                    workerError={workerError}
                    onRetry={() => {
                      retryWorkerConfiguration()
                      window.location.reload()
                    }}
                  />
                }
              >
                <Page
                  pageNumber={pageNumber}
                  scale={scale}
                  renderTextLayer={true}
                  renderAnnotationLayer={true}
                  className="shadow-lg"
                />
                {/* Render annotations overlay */}
                {renderAnnotations()}
              </Document>
            )}
          </div>
        </div>

        {/* Page Navigation */}
        {numPages > 1 && (
          <div className="flex items-center justify-center space-x-4 p-4 bg-white border-t border-gray-200">
            <button
              onClick={() => changePage(-1)}
              disabled={pageNumber <= 1}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Precedente
            </button>
            <span className="text-sm text-gray-600">
              Pagina {pageNumber} di {numPages}
            </span>
            <button
              onClick={() => changePage(1)}
              disabled={pageNumber >= numPages}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Successiva
            </button>
          </div>
        )}
      </div>

      {/* Note Dialog */}
      {showNoteDialog && selectedText && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Aggiungi Nota</h3>
            <p className="text-sm text-gray-600 mb-4">Testo selezionato: "{selectedText}"</p>
            <textarea
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              placeholder="Inserisci la tua nota..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-vertical"
              rows={4}
            />
            <div className="flex justify-end space-x-3 mt-4">
              <button
                onClick={() => {
                  setShowNoteDialog(false)
                  setNoteText('')
                  setSelectedText('')
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Annulla
              </button>
              <button
                onClick={addAnnotation}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Aggiungi
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Annotation Type Dialog */}
      {selectedText && !showNoteDialog && isAnnotating && (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-white rounded-lg shadow-lg p-3 flex items-center space-x-2 z-40">
          <span className="text-sm text-gray-700">Annota testo:</span>
          <button
            onClick={() => {
              setAnnotationType('highlight')
              addAnnotation()
            }}
            className="p-2 bg-yellow-100 text-yellow-700 hover:bg-yellow-200 rounded transition-colors"
            title="Evidenzia"
          >
            <Highlighter className="h-4 w-4" />
          </button>
          <button
            onClick={() => {
              setAnnotationType('underline')
              addAnnotation()
            }}
            className="p-2 bg-blue-100 text-blue-700 hover:bg-blue-200 rounded transition-colors"
            title="Sottolinea"
          >
            <Edit3 className="h-4 w-4" />
          </button>
          <button
            onClick={() => setShowNoteDialog(true)}
            className="p-2 bg-green-100 text-green-700 hover:bg-green-200 rounded transition-colors"
            title="Aggiungi nota"
          >
            <MessageSquare className="h-4 w-4" />
          </button>
          <button
            onClick={() => {
              setSelectedText('')
              const selection = window.getSelection()
              selection?.removeAllRanges()
            }}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  )
}
