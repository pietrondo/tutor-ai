'use client'

import { useState } from 'react'
import { FileText, Download, Trash2, Calendar, HardDrive } from 'lucide-react'

interface Material {
  filename: string
  size: number
  uploaded_at: string
  file_path: string
}

interface CourseMaterialsProps {
  materials: Material[]
  onRefresh: () => void
}

export function CourseMaterials({ materials, onRefresh }: CourseMaterialsProps) {
  const [deleting, setDeleting] = useState<string | null>(null)

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('it-IT', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleDownload = async (filename: string) => {
    // In una reale implementazione, questo scaricherebbe il file dal server
    // Per ora, mostriamo solo un messaggio
    alert(`Download di ${filename} - Funzionalità da implementare`)
  }

  const handleDelete = async (filename: string) => {
    if (!confirm(`Sei sicuro di voler eliminare "${filename}"?`)) {
      return
    }

    setDeleting(filename)
    try {
      // In una reale implementazione, questo eliminerebbe il file dal server
      // await fetch(`/api/materials/${filename}`, { method: 'DELETE' })

      // Per ora, simuliamo l'eliminazione
      await new Promise(resolve => setTimeout(resolve, 1000))

      onRefresh()
    } catch (error) {
      console.error('Errore nell\'eliminazione del file:', error)
      alert('Errore nell\'eliminazione del file')
    } finally {
      setDeleting(null)
    }
  }

  if (materials.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Nessun materiale caricato
        </h3>
        <p className="text-gray-500">
          Carica i tuoi file PDF per iniziare a studiare con il tutor AI
        </p>
      </div>
    )
  }

  return (
    <div>
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        Materiali Caricati ({materials.length})
      </h3>

      <div className="space-y-3">
        {materials.map((material, index) => (
          <div
            key={index}
            className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3 flex-1 min-w-0">
                <FileText className="h-5 w-5 text-blue-600 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {material.filename}
                  </p>
                  <div className="flex items-center space-x-4 mt-1">
                    <div className="flex items-center text-xs text-gray-500">
                      <HardDrive className="h-3 w-3 mr-1" />
                      {formatFileSize(material.size)}
                    </div>
                    <div className="flex items-center text-xs text-gray-500">
                      <Calendar className="h-3 w-3 mr-1" />
                      {formatDate(material.uploaded_at)}
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2 ml-4">
                <button
                  onClick={() => handleDownload(material.filename)}
                  className="text-gray-400 hover:text-blue-600 transition-colors p-2 rounded-lg hover:bg-blue-50"
                  title="Scarica file"
                >
                  <Download className="h-4 w-4" />
                </button>

                <button
                  onClick={() => handleDelete(material.filename)}
                  disabled={deleting === material.filename}
                  className="text-gray-400 hover:text-red-600 transition-colors p-2 rounded-lg hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Elimina file"
                >
                  {deleting === material.filename ? (
                    <div className="loading-spinner h-4 w-4"></div>
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 text-sm text-gray-500 text-center">
        Tutti i materiali vengono indicizzati automaticamente per la ricerca e il tutoring AI
      </div>
    </div>
  )
}