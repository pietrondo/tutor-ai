"use client"
import React, { useEffect, useState } from "react"

const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

type Recording = {
  id: string
  title: string
  language: string
  url: string
  created_at: string
  categories?: string[]
}

export default function AudioLibrary() {
  const [items, setItems] = useState<Recording[]>([])
  const [q, setQ] = useState("")
  const [language, setLanguage] = useState("")
  const [category, setCategory] = useState("")
  const [playlistName, setPlaylistName] = useState("")
  const [selected, setSelected] = useState<string | null>(null)

  const load = async () => {
    const params = new URLSearchParams()
    if (q) params.append("q", q)
    if (language) params.append("language", language)
    if (category) params.append("category", category)
    const r = await fetch(`${apiBase}/api/tts/recordings?${params.toString()}`)
    if (!r.ok) return
    const data = await r.json()
    setItems(data.map((d:any)=>({ ...d, url: `${apiBase}${d.url}` })))
  }

  useEffect(() => { load() }, [])

  const createPlaylist = async () => {
    if (!playlistName.trim() || !selected) return
    const r = await fetch(`${apiBase}/api/tts/playlists`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: playlistName }) })
    if (!r.ok) return
    const pl = await r.json()
    await fetch(`${apiBase}/api/tts/playlists/${pl.id}/items/${selected}`, { method: "POST" })
    setPlaylistName("")
    setSelected(null)
  }

  return (
    <div className="rounded-xl border p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Libreria Audio</h3>
        <button onClick={load} className="rounded bg-gray-100 px-3 py-1">Aggiorna</button>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Cerca" className="rounded border p-2" />
        <select value={language} onChange={e=>setLanguage(e.target.value)} className="rounded border p-2">
          <option value="">Tutte le lingue</option>
          <option value="it">Italiano</option>
          <option value="en">Inglese</option>
          <option value="es">Spagnolo</option>
        </select>
        <input value={category} onChange={e=>setCategory(e.target.value)} placeholder="Categoria" className="rounded border p-2" />
        <button onClick={load} className="rounded bg-blue-600 text-white px-4">Filtra</button>
      </div>
      <div className="space-y-3">
        {items.map(item => (
          <div key={item.id} className={`rounded border p-3 ${selected===item.id? 'ring-2 ring-blue-500':''}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">{item.title}</div>
                <div className="text-xs text-gray-500">{new Date(item.created_at).toLocaleString()} • {item.language}</div>
              </div>
              <button onClick={()=>setSelected(selected===item.id?null:item.id)} className="rounded bg-gray-100 px-3 py-1">{selected===item.id? 'Deseleziona':'Seleziona'}</button>
            </div>
            <audio controls src={item.url} className="w-full mt-2" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-3 items-center">
        <input value={playlistName} onChange={e=>setPlaylistName(e.target.value)} placeholder="Nuova playlist" className="rounded border p-2" />
        <button onClick={createPlaylist} className="rounded bg-green-600 text-white px-4 py-2">Crea e aggiungi</button>
        <span className="text-xs text-gray-500">Seleziona una registrazione per aggiungerla</span>
      </div>
    </div>
  )
}

