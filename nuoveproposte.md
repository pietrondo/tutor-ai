# Nuove Proposte di Evoluzione Prodotto

## 1. Dashboard “Padronezza Concetti”
- **Obiettivo**: offrire a docenti e studenti una vista sintetica dello stato di apprendimento sui concetti di ogni corso.
- **Come implementarla**:
  1. **Backend**: aggiungere un endpoint aggregato (`/courses/{id}/concepts/overview`) che restituisca per ogni concetto punteggi medi, trend temporali e suggerimenti personalizzati.
  2. **Frontend**: creare una sezione dedicata nella tab “Quiz e Test” con grafici (linee/barre) che mostrino progressi, concetti a rischio e suggeriti per ripasso.
  3. **Notifiche**: integrare un sistema di alert che evidenzi concetti con punteggi decrescenti o tentativi insufficienti.

## 2. Missioni di Studio Settimanali
- **Obiettivo**: guidare gli studenti con obiettivi brevi e misurabili basati su libri e concetti.
- **Come implementarla**:
  1. **Generazione**: estendere lo `StudyPlannerService` per creare missioni settimanali che combinino capitoli, quiz e attività pratiche.
  2. **Tracking**: salvare stato di avanzamento missioni con sub-task (es. “Completa quiz concetto X”, “Rivedi capitolo Y”).
  3. **UI**: aggiungere una card “Missione Settimana” nel planner con checklist progressiva e badge motivazionali.

## 3. Assistente di Annotazione Intelligente
- **Obiettivo**: velocizzare la preparazione dei materiali generando evidenziazioni e domande guida dai PDF.
- **Come implementarla**:
  1. **Ingestione**: usare il RAG per estrarre sezioni chiave dai PDF e inviare all’LLM richieste di annotazione e Q&A.
  2. **Storage**: salvare annotazioni strutturate (capitolo, pagina, contenuto, domanda correlata) in un nuovo servizio `annotation_insights`.
  3. **UI**: nel dettaglio libro, mostrare un pannello “Annotazioni AI” e permettere all’utente di approvarle/modificarle.

## 4. Export Piano di Studio in Formato Calendario
- **Obiettivo**: sincronizzare le sessioni del piano con calendari esterni (Google/Outlook) per migliorare l’esecuzione.
- **Come implementarla**:
  1. **ICS Generator**: aggiungere un endpoint che converta il piano in file ICS, includendo sessioni, obiettivi e link materiali.
  2. **OAuth Integration**: opzionale, prevedere integrazione con API Google Calendar per inserimento diretto.
  3. **Frontend**: aggiungere pulsante “Esporta in Calendario” nel planner con feedback sullo stato del download/invio.

## 5. Analisi Predittiva dei Tempi di Studio
- **Obiettivo**: stimare in anticipo la durata effettiva necessaria per completare i piani, personalizzandoli sugli studenti.
- **Come implementarla**:
  1. **Data Collection**: arricchire le metriche registrando il tempo reale impiegato nelle sessioni e l’esito dei quiz.
  2. **Modeling**: introdurre un modulo (anche semplice regressione) che suggerisca durate reali per capitolo/concetto.
  3. **Feedback Loop**: adattare automaticamente le future sessioni (incremento/diminuzione minuti) e comunicare i motivi delle modifiche all’utente.
