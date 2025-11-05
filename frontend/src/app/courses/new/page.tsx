'use client'

import { useState, type ChangeEvent, type FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Save } from 'lucide-react'
import Link from 'next/link'

export default function NewCoursePage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    subject: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = event.target
    setFormData(prev => ({ ...prev, [name]: value }))
    if (error) setError('')
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setIsSubmitting(true)
    setError('')

    try {
      const response = await fetch('http://localhost:8000/courses', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      const data = await response.json()

      if (response.ok) {
        router.push(`/courses/${data.course.id}`)
      } else {
        setError(data.detail || 'Errore nella creazione del corso')
      }
    } catch (error) {
      console.error('Errore nella creazione del corso:', error)
      setError('Errore di connessione al server')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <Link
          href="/"
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Torna alla Home
        </Link>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Crea Nuovo Corso
        </h1>
        <p className="text-gray-600">
          Aggiungi un nuovo corso universitario per iniziare a studiare con l'AI Tutor
        </p>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="name" className="form-label">
              Nome del Corso *
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              placeholder="es: Analisi Matematica I"
              className="form-input"
            />
          </div>

          <div>
            <label htmlFor="subject" className="form-label">
              Materia *
            </label>
            <select
              id="subject"
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              required
              className="form-input"
            >
              <option value="">Seleziona una materia...</option>
              <option value="Matematica">Matematica</option>
              <option value="Fisica">Fisica</option>
              <option value="Informatica">Informatica</option>
              <option value="Ingegneria">Ingegneria</option>
              <option value="Economia">Economia</option>
              <option value="Statistica">Statistica</option>
              <option value="Chimica">Chimica</option>
              <option value="Biologia">Biologia</option>
              <option value="Lettere">Lettere</option>
              <option value="Filosofia">Filosofia</option>
              <option value="Storia">Storia</option>
              <option value="Altro">Altro</option>
            </select>
          </div>

          <div>
            <label htmlFor="description" className="form-label">
              Descrizione del Corso *
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              required
              rows={4}
              placeholder="Descrivi gli argomenti principali del corso, gli obiettivi di apprendimento e qualsiasi altra informazione rilevante..."
              className="form-input resize-none"
            />
          </div>

          <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
            <Link
              href="/"
              className="btn btn-secondary"
            >
              Annulla
            </Link>
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-primary flex items-center space-x-2 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <div className="loading-spinner h-4 w-4"></div>
                  <span>Creazione...</span>
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  <span>Crea Corso</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
