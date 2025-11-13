"use client"
import React, { useEffect, useMemo, useState } from "react"

const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export default function TTSPanel() {
  const [text, setText] = useState("")
  const [title, setTitle] = useState("")
  const [language, setLanguage] = useState("it")
  const [voice, setVoice] = useState("alloy")
  const [voices, setVoices] = useState<{id:string,name:string,language:string}[]>([])
  const [customVoices, setCustomVoices] = useState<{id:string,name:string,language:string,file_path?:string,samples?:string[],sample_count?:number}[]>([])
  const [speakerId, setSpeakerId] = useState<string>("")
  const [voiceFile, setVoiceFile] = useState<File | null>(null)
  const [sampleFile, setSampleFile] = useState<File | null>(null)
  const [voiceName, setVoiceName] = useState("")
  const [presetId, setPresetId] = useState("")
  const [speed, setSpeed] = useState(1.0)
  const [tone, setTone] = useState("neutral")
  const [loading, setLoading] = useState(false)
  const [resultUrl, setResultUrl] = useState<string | null>(null)

  const loadVoices = async () => {
    try {
      const all = await fetch(`${apiBase}/api/tts/voices`).then(r=>r.json())
      setVoices(all.filter((v:any)=>!v.file_path))
      const custom = await fetch(`${apiBase}/api/tts/voices/custom`).then(r=>r.json())
      setCustomVoices(custom)
    } catch {}
  }
  useEffect(() => { loadVoices() }, [])

  const presets = [
    { id: "narratore-caldo", name: "Narratore caldo", speed: 0.95, tone: "warm" },
    { id: "didattico-formale", name: "Didattico formale", speed: 1.05, tone: "formal" },
    { id: "conversazionale", name: "Conversazionale", speed: 1.0, tone: "neutral" },
    { id: "lettura-veloce", name: "Lettura veloce", speed: 1.25, tone: "neutral" }
  ] as const

  const applyPreset = (id: string) => {
    setPresetId(id)
    const p = presets.find(x => x.id === id)
    if (!p) return
    setSpeed(p.speed)
    setTone(p.tone)
  }

  const canSubmit = useMemo(() => text.trim().length > 0 && !loading, [text, loading])

  const submit = async () => {
    setLoading(true)
    setResultUrl(null)
    const payload = { text, title: title || undefined, language, voice, speed, tone, speaker_id: speakerId || undefined }
    const r = await fetch(`${apiBase}/api/tts/synthesize`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
    if (!r.ok) { setLoading(false); return }
    const data = await r.json()
    const url = `${apiBase}${data.url}`
    setResultUrl(url)
    setLoading(false)
  }

  return (
    <div className="rounded-xl border p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Sintesi Vocale</h3>
      </div>
      <input value={title} onChange={e=>setTitle(e.target.value)} placeholder="Titolo" className="w-full rounded border p-2" />
      <textarea value={text} onChange={e=>setText(e.target.value)} placeholder="Inserisci testo" rows={6} className="w-full rounded border p-2" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="flex flex-col">
          <label className="text-sm">Lingua</label>
          <select value={language} onChange={e=>setLanguage(e.target.value)} className="rounded border p-2">
            <option value="it">Italiano</option>
            <option value="en">Inglese</option>
            <option value="es">Spagnolo</option>
          </select>
        </div>
        <div className="flex flex-col">
          <label className="text-sm">Preset voce</label>
          <select value={presetId} onChange={e=>applyPreset(e.target.value)} className="rounded border p-2">
            <option value="">Nessuno</option>
            {presets.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>
        <div className="flex flex-col">
          <label className="text-sm">Voce</label>
          <select value={voice} onChange={e=>setVoice(e.target.value)} className="rounded border p-2">
            {voices.map(v=> <option key={v.id} value={v.id}>{v.name}</option>)}
          </select>
        </div>
        <div className="flex flex-col">
          <label className="text-sm">Velocità</label>
          <input type="range" min={0.8} max={1.4} step={0.05} value={speed} onChange={e=>setSpeed(parseFloat(e.target.value))} />
          <span className="text-xs">{speed.toFixed(2)}x</span>
        </div>
        <div className="flex flex-col">
          <label className="text-sm">Tono</label>
          <select value={tone} onChange={e=>setTone(e.target.value)} className="rounded border p-2">
            <option value="neutral">Neutro</option>
            <option value="warm">Caldo</option>
            <option value="formal">Formale</option>
          </select>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
        <div className="flex flex-col">
          <label className="text-sm">Voce personalizzata</label>
          <select value={speakerId} onChange={e=>setSpeakerId(e.target.value)} className="rounded border p-2">
            <option value="">Nessuna</option>
            {customVoices.map(v=> {
              const count = (v.sample_count ?? (v.samples ? v.samples.length : 0))
              return <option key={v.id} value={v.id}>{`${v.name} (${count})`}</option>
            })}
          </select>
        </div>
        <div className="flex flex-col">
          <label className="text-sm">File voce</label>
          <input type="file" accept="audio/*" onChange={e=>setVoiceFile(e.target.files?.[0] || null)} />
        </div>
        <div className="flex gap-2">
          <input value={voiceName} onChange={e=>setVoiceName(e.target.value)} placeholder="Nome voce" className="flex-1 rounded border p-2" />
          <button onClick={async ()=>{
            if (!voiceFile || !voiceName.trim()) return
            const fd = new FormData()
            fd.append("file", voiceFile)
            fd.append("name", voiceName)
            fd.append("language", language)
            const r = await fetch(`${apiBase}/api/tts/voices/custom`, { method: "POST", body: fd })
            if (r.ok) { setVoiceFile(null); setVoiceName(""); await loadVoices() }
          }} className="rounded bg-gray-100 px-3 py-2">Carica voce</button>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
        <div className="flex flex-col">
          <label className="text-sm">Aggiungi campione alla voce selezionata</label>
          <input type="file" accept="audio/*" onChange={e=>setSampleFile(e.target.files?.[0] || null)} />
        </div>
        <div className="flex items-end">
          <button onClick={async ()=>{
            if (!sampleFile || !speakerId) return
            const fd = new FormData()
            fd.append("file", sampleFile)
            const r = await fetch(`${apiBase}/api/tts/voices/custom/${speakerId}/samples`, { method: "POST", body: fd })
            if (r.ok) { setSampleFile(null); await loadVoices() }
          }} className="rounded bg-gray-100 px-3 py-2">Aggiungi campione</button>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button onClick={submit} disabled={!canSubmit} className="rounded bg-blue-600 text-white px-4 py-2 disabled:opacity-50">Genera MP3</button>
        {loading && <span>Elaborazione...</span>}
      </div>
      {resultUrl && (
        <div className="space-y-2">
          <span className="text-sm">Anteprima</span>
          <audio controls src={resultUrl} className="w-full" />
        </div>
      )}
    </div>
  )
}
