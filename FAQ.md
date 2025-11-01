# ❓ Domande Frequenti - Tutor AI

## Setup e Installazione

### **D: Posso usare questo senza conoscere Python?**
R: Sì! Lo script `setup.sh` installa automaticamente tutto. Hai solo bisogno di:
- Python 3.8+ installato
- Node.js installato
- Una API key di OpenAI o Ollama installato

### **D: Funziona su Windows/Mac/Linux?**
R: Sì, funziona su tutti e tre. Lo script di setup rileva automaticamente il sistema operativo.

### **D: Devo pagare per usare OpenAI?**
R: Sì, OpenAI ha costi basati sull'uso. Alternative gratuite:
- Usa Ollama con modelli locali (completamente gratuito)
- Usa LM Studio con modelli open source

## Configurazione LLM

### **D: Come configuro Ollama?**
R: Segui questi passaggi:
1. Installa Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
2. Scarica un modello: `ollama pull llama3.1`
3. Configura `.env`: `LLM_TYPE=local`

### **D: Qual è il miglior modello LLM da usare?**
R: Dipende dalle tue esigenze:
- **OpenAI GPT-4o**: Migliore qualità, supporto multilingue perfetto
- **Llama 3.1**: Ottimo locale, gratuito
- **Mixtral**: Buono per ragionamento complesso
- **Qwen**: Ottimo per cinese e inglese

### **D: Posso cambiare LLM dopo aver iniziato?**
R: Sì! Basta modificare `backend/.env` e riavviare il backend.

## Utilizzo della Piattaforma

### **D: Quali formati di file sono supportati?**
R: Attualmente supportiamo solo PDF. Stiamo lavorando su:
- DOCX
- PPTX
- Immagini (con OCR)
- Video (con trascrizione)

### **D: Quanti PDF posso caricare?**
R: Non c'è limite tecnico. L'unico limite è lo spazio su disco.
Un tipico corso universitario può avere 50-100 PDF senza problemi.

### **D: L'AI tutor ricorda conversazioni precedenti?**
R: Sì, ogni conversazione è tracciata con un session ID. Il tutor ha memoria contestuale dentro la stessa sessione.

### **D: Posso esportare i miei dati?**
R: Sì, tutti i dati sono salvati localmente nelle cartelle:
- `data/courses/` - Materiali dei corsi
- `data/tracking/` - Progressi e sessioni
- `data/vector_db/` - Database vettoriale

## Privacy e Sicurezza

### **D: I miei dati sono sicuri?**
R: Assolutamente! Tutti i dati sono archiviati localmente sul tuo computer:
- Nessun dato viene inviato a server terzi
- Nessuna telemetry o analytics
- Tu controlli completamente i tuoi dati

### **D: I miei documenti PDF sono condivisi?**
R: No, i PDF vengono processati localmente. Solo tu hai accesso ai tuoi materiali.

### **D: OpenAI vede i miei documenti?**
R: No. OpenAI riceve solo le domande e il contesto rilevante, mai i documenti originali.

## Prestazioni e Limitazioni

### **D: Quanta RAM serve per farlo funzionare?**
R: Minimo raccomandato:
- 8GB RAM per uso base
- 16GB RAM per LLM locali
- 32GB RAM per modelli grandi (70B+)

### **D: Posso usarlo offline?**
R: Dipende dal LLM:
- **Ollama/LM Studio**: Sì, completamente offline
- **OpenAI**: No, serve connessione internet

### **D: Quanto velocemente indicizza i PDF?**
R: Dipende dalla dimensione:
- 10 pagine: ~5 secondi
- 100 pagine: ~30 secondi
- 500+ pagine: ~2-3 minuti

## Risoluzione Problemi

### **D: Il backend non si avvia**
R: Controlla:
1. Python 3.8+ installato: `python3 --version`
2. Ambiente virtuale attivato
3. Dipendenze installate: `pip install -r requirements.txt`
4. File `.env` configurato correttamente

### **D: Errore "API key not found"**
R: Assicurati che:
1. Il file `backend/.env` esista
2. Contenga `OPENAI_API_KEY=sk-...`
3. La API key sia valida e attiva

### **D: Il frontend non si connette al backend**
R: Verifica:
1. Backend in esecuzione su http://localhost:8000
2. Frontend in esecuzione su http://localhost:3000
3. Nessun firewall che blocchi le porte
4. Prova a refreshare la pagina del browser

### **D: L'AI non risponde o risponde male**
R: Possibili cause:
1. PDF non indicizzati correttamente
2. Modello LLM non funzionante
3. Domanda troppo vaga
4. Contesto insufficiente nei materiali

### **D: PDF non viene processato**
R: Controlla:
1. Il PDF non sia protetto da password
2. Il PDF contenga testo (non solo immagini)
3. Spazio su disco sufficiente
4. Prova a riavviare il backend

## Suggerimenti e Best Practices

### **D: Come ottenere le migliori risposte dall'AI?**
R:
- Sii specifico nelle domande
- Fai domande basate sui materiali caricati
- Usa terminologia del corso
- Chiedi spiegazioni passo-passo

### **D: Quanti corsi posso creare?**
R: Non c'è limite tecnico. Per prestazioni ottimali:
- 5-10 corsi attivi è ideale
- Ogni corso con 10-50 PDF
- Monitora l'uso di RAM e disco

### **D: Posso usare questo per lingue diverse dall'italiano?**
R: Sì! Supportiamo:
- Italiano (nativo)
- Inglese (eccellente)
- Spagnolo, francese, tedesco (buono)
- Altre lingue europee (discreto)

## Supporto Aggiuntivo

### **D: Dove posso trovare aiuto?**
R:
- GitHub Issues per problemi tecnici
- Documentazione completa nel README
- Guide video sul nostro canale YouTube
- Community Discord per supporto

### **D: Come contribuire al progetto?**
R:
- Segnala bug su GitHub
- Suggerisci nuove funzionalità
- Fai pull request
- Condividi il progetto

---

**Hai altre domande?** Contattaci o apri una issue su GitHub! 🎓✨