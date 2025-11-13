## Obiettivo e Ambito

* Rendere il sistema RAG robusto, veloce (<500ms P95), con concetti puliti e utili.

* Copre: NLP sui titoli, ranking, vector store, tooltip frontend, retrieval avanzato, prompt engineering, compressione embeddings, metriche/monitoraggio, logging, test, API docs, CI/CD, validazione parametri LLM e fallback.

## Architettura (Panoramica)

* Backend (Python/FastAPI): pipeline RAG → NLP (spaCy) → ranking (TF‑IDF/BERT) → deduplica (Jaro‑Winkler) → generazione LLM → mappa.

* Vector store: FAISS (locale) + colonna metadati (doc\_id, chunk\_idx, posizione). Compatibile con Pinecone opzionale.

* Frontend (React): Explorer + VisualMindmap + tooltip (Popper/Floating UI) con caching LocalStorage (TTL 1h).

* Observability: Prometheus/Grafana, ELK logging strutturato, SLA monitorato.

## Fase 1 – NLP sui Titoli

1. Tokenizzazione e POS tagging

* Usa spaCy `it_core_news_md` per italiano (fallback: `it_core_news_sm`).

* Estrai solo sostantivi (NOUN/PROPN) e composti nominali; preserva lemma.

1. Lemmatizzazione e Stemming

* Lemmatizzazione: spaCy (italiano).

* Stemming: SnowballStemmer("italian") (più adeguato di Porter per IT). Se richiesto, aggiungi Porter stem su layer opzionale.

1. Normalizzazione e Pulizia

* Rimuovi stopwords IT, numeri, punteggiatura, bibliografia (pattern). Limita a 2–6 termini (head keywords).

1. Secondo Pass

* Funzione `_refine_title_llm` → riformulazione LLM come sintagma nominale; poi applica filtro POS + stopwords.

1. Deduplica

* Jaro‑Winkler ≥0.90 su titoli normalizzati; merge di summary/attività/riferimenti; incrementa `recurrence`.

## Fase 2 – Ranking & Vector Store

1. Ranking

* TF‑IDF (scikit‑learn) per termine/concetto nelle finestre di contesto.

* Opzione BERT: sentence‑transformers IT per scoring semantico; combinalo con TF‑IDF (score 0.5/0.5).

* Ordinamento finale: priorità → ricorrenza → punteggio.

1. Persistenza Intermedia

* Memorizza features (tfidf, embeddings, titoli raffinati) in FAISS (flat L2 / IVFPQ per PQ) con metadati:

  * `doc_id`, `chunk_index`, `pos_start`, `pos_end`, `source_path`.

* Wrapper storage compatibile Pinecone (interfaccia astratta).

## Fase 3 – Frontend Tooltip UX

1. Tooltip sinonimi fusi

* Libreria Popper.js/Floating UI; overlay su hover/click del titolo nodo.

* Contenuto: lista sinonimi/varianti fusi, fonte, ricorrenza.

1. Origine ricorrenza

* Mostra metadati strutturati: `doc_id`, `chunk_index`, posizione; link deep‑link (se disponibile).

1. Caching client

* LocalStorage con TTL 1h (chiave basata su `node.id` + versione). Opzionale: Redis lato server per SSR.

1. Animazioni

* CSS transitions animate (opacity/transform) 150–250ms; rispettare CSP.

## Fase 4 – Retrieval Avanzato

1. Modello

* Integrazione DPR o ColBERT per dense retrieval (config togglable). Pipeline:

  * Indicizzazione: chunking → embedding DPR/ColBERT → FAISS/Pinecone.

  * Query: embedding → nearest neighbors → re‑ranking (BM25/TF‑IDF + BERT cross‑encoder opzionale).

1. Prompt Engineering

* Few‑shot: 3–5 esempi di trasformazione testo → concetto; includere istruzioni IT e negative examples.

* Struttura: vincoli lessicali (no numeri/citazioni), lunghezza (2–6 parole), tono accademico.

## Fase 5 – Compressione Embeddings

* PCA (dim N→M, es. 768→256) per ridurre latenza e memoria.

* Product Quantization (IVFPQ) in FAISS per velocizzare ANN mantenendo recall.

* Valutazione offline (cosine sim, recall\@k) prima della messa in produzione.

## Fase 6 – Metriche & Monitoraggio

* Metriche Prometheus:

  * `rag_request_duration_seconds` (histogram), `rag_retrieval_hits`, `rag_llm_timeout_count`, `rag_cache_hit`.

* Dashboard Grafana per SLA 500ms P95 su endpoint `/mindmap/generate`.

* Alerting su P95 > 500ms o timeout LLM > 700ms.

## Fase 7 – Logging & ELK

* Logging JSON (structlog/loguru) con campi: request\_id, course\_id, book\_id, retrieval\_model, hits, duration\_ms.

* Spedizione a ELK (Filebeat) con index per RAG.

## Fase 8 – Test & Qualità

* Unit (pytest):

  * NLP (POS/lemma/stem), ranking, deduplica, filtri segmenti, vector store wrapper.

  * RAG service (local/hybrid/vector): segmenti presenti, fonti deduplicate.

* E2E (Cypress):

  * Generazione mappa libro/PDF, tooltip sinonimi, caching TTL.

* Coverage >90%: integra `pytest --cov` e `cypress-coverage`.

## Fase 9 – API Docs & Governance

* OpenAPI 3.0: documenta nuovi parametri (model\_name, temperature, max\_tokens, timeout, use\_dense).

* Swagger UI aggiornato; esempi di richieste/risposte con metadati.

##

## Fase 10 – Parametri LLM & Fallback

* Validazione automatica dei parametri `${model_name}`, `${temperature}`, `${max_tokens}` dalla pagina settings.

* Wrapper LLM:

  * Timeout 700ms; se scatta, ritorna risposta cached (ultimo titolo raffinato/minimap memorizzato).

  * Circuit breaker su 3 timeout consecutivi; metriche aggiornate.

## Dati & Migrazione

* Migra indici esistenti a FAISS con conversione embeddings; conserva Chroma/Pinecone interoperabilità.

* Backfill di sinonimi/varianti nei nodi esistenti per popolare `recurrence`.

## Sicurezza & CSP

* Nessun inline script; tooltip e animazioni conformi a CSP; font da `fonts.gstatic.com`/`fonts.googleapis.com`.

## Roadmap & Milestones

* S1 (Giorni 1–2): NLP titoli, filtri segmenti, deduplica, ranking TF‑IDF.

* S2 (Giorni 3–4): FAISS + compressione (PCA/PQ), integrazione DPR/ColBERT (staging).

* S3 (Giorni 5–6): Tooltip frontend, caching TTL, ordinamenti e badge ricorrenza.

* S4 (Giorni 7–8): Metriche Prometheus/Grafana, logging ELK, test Pytest+Cypress (>90%).

* S5 (Giorni 9): OpenAPI/Swagger, CI/CD, rollout canary.

## Criteri di Accettazione

* P95 < 500ms su `/mindmap/generate` in staging (dati campione).

* Nodi senza rumore (niente numeri/citazioni) in 95% dei casi (verifica manuale su 50 libri).

* Tooltip mostra sinonimi e metadati corretti; caching TTL 1h con invalidazione.

* Test coverage >90%; dashboard e alert attivi.

## Rischi & Mitigazione

* Latenza embedding DPR/ColBERT: usare PCA/PQ e batch; fallback TF‑IDF+BERT leggero.

* Qualità sinonimi in IT: aggiungere dizionari custom + LLM post‑processing.

* CSP: evitare inline; usare classi CSS/Popper compatibili.

## Rollback

* Toggle `use_dense=false` per tornare a TF‑IDF/BERT.

* Disabilita secondo pass NLP via feature flag.

Confermi che procedo secondo questa roadmap?
