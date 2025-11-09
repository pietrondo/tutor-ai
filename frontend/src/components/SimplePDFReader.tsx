/**
 * Simple PDF Reader using iframe
 * Fallback solution while react-pdf issues are being resolved
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  BookOpenIcon,
  ZoomInIcon,
  ZoomOutIcon,
  DownloadIcon,
  RotateCwIcon
} from 'lucide-react';

interface SimplePDFReaderProps {
  pdfUrl: string;
  bookId: string;
  courseId: string;
  userId: string;
  onAnnotationCreate?: (annotation: any) => void;
  onChatWithContext?: (context: any) => void;
}

const SimplePDFReader: React.FC<SimplePDFReaderProps> = ({
  pdfUrl,
  bookId,
  courseId,
  userId,
  onAnnotationCreate,
  onChatWithContext
}) => {
  const [scale, setScale] = useState(1.0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    setIsLoading(true);
    setError(null);
  }, [pdfUrl]);

  const handleIframeLoad = () => {
    setIsLoading(false);
  };

  const handleIframeError = () => {
    setIsLoading(false);
    setError('Errore caricamento PDF');
  };

  const zoomIn = () => {
    setScale(prev => Math.min(prev + 0.2, 3.0));
    if (iframeRef.current) {
      iframeRef.current.style.transform = `scale(${scale + 0.2})`;
    }
  };

  const zoomOut = () => {
    setScale(prev => Math.max(prev - 0.2, 0.5));
    if (iframeRef.current) {
      iframeRef.current.style.transform = `scale(${scale - 0.2})`;
    }
  };

  const resetZoom = () => {
    setScale(1.0);
    if (iframeRef.current) {
      iframeRef.current.style.transform = 'scale(1.0)';
    }
  };

  const downloadPDF = () => {
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = `book-${bookId}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
          <h3 className="text-lg font-medium text-gray-900">Lettore PDF</h3>
          <span className="text-sm text-gray-500">(Modalità Semplice)</span>
        </div>

        <div className="flex items-center space-x-2">
          {/* Zoom controls */}
          <div className="flex items-center space-x-1">
            <button
              onClick={zoomOut}
              className="p-2 rounded text-gray-700 hover:bg-gray-200"
              title="Riduci zoom"
            >
              <ZoomOutIcon className="h-4 w-4" />
            </button>
            <span className="text-sm text-gray-700 min-w-[50px] text-center">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={zoomIn}
              className="p-2 rounded text-gray-700 hover:bg-gray-200"
              title="Aumenta zoom"
            >
              <ZoomInIcon className="h-4 w-4" />
            </button>
            <button
              onClick={resetZoom}
              className="p-2 rounded text-gray-700 hover:bg-gray-200"
              title="Reset zoom"
            >
              <RotateCwIcon className="h-4 w-4" />
            </button>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-1 border-l border-gray-300 pl-2">
            <button
              onClick={downloadPDF}
              className="p-2 rounded text-gray-700 hover:bg-gray-200"
              title="Scarica PDF"
            >
              <DownloadIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* PDF Content */}
      <div className="flex-1 overflow-auto bg-gray-100 p-4">
        {isLoading && (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-2 text-sm text-gray-600">Caricamento PDF...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-center h-96">
            <div className="text-center text-red-600">
              <BookOpenIcon className="mx-auto h-12 w-12 text-red-400" />
              <p className="mt-2">{error}</p>
              <button
                onClick={() => window.open(pdfUrl, '_blank')}
                className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                Apri in nuova scheda
              </button>
            </div>
          </div>
        )}

        {/* PDF iframe */}
        <div className="flex justify-center">
          <div
            className="bg-white shadow-lg"
            style={{
              transform: `scale(${scale})`,
              transformOrigin: 'top center',
              transition: 'transform 0.2s ease-in-out'
            }}
          >
            <iframe
              ref={iframeRef}
              src={pdfUrl}
              className="border-0"
              style={{
                width: '800px',
                height: '1000px',
                display: isLoading ? 'none' : 'block'
              }}
              onLoad={handleIframeLoad}
              onError={handleIframeError}
              title="PDF Viewer"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimplePDFReader;