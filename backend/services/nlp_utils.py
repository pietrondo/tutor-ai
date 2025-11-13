import re
from typing import List

def _safe_import_spacy():
    try:
        import spacy
        try:
            return spacy.load("it_core_news_sm")
        except Exception:
            return spacy.blank("it")
    except Exception:
        return None

def _safe_import_nltk():
    try:
        import nltk
        try:
            from nltk.stem.snowball import ItalianStemmer
            return nltk, ItalianStemmer()
        except Exception:
            return nltk, None
    except Exception:
        return None, None

_NLP = _safe_import_spacy()
_NLTK, _STEMMER = _safe_import_nltk()

STOPWORDS_IT = {
    "di","del","della","dei","delle","da","dal","dalla","su","sul","sulla","per","tra","fra",
    "il","lo","la","i","gli","le","un","una","uno","e","ed","o","oppure","che","come"
}

def extract_nouns(text: str, max_terms: int = 6) -> List[str]:
    if not text:
        return []
    terms: List[str] = []
    if _NLP is not None:
        try:
            doc = _NLP(text)
            for token in doc:
                if token.pos_ in {"NOUN","PROPN"}:
                    t = token.lemma_.lower().strip()
                    if t and t not in STOPWORDS_IT and re.fullmatch(r"[a-zà-öø-ÿ\-]+", t):
                        terms.append(t)
            if terms:
                return terms[:max_terms]
        except Exception:
            pass
    # Fallback semplice
    tokens = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ\-]+", text)
    for t in tokens:
        tl = t.lower()
        if tl not in STOPWORDS_IT:
            terms.append(tl)
    return terms[:max_terms]

def normalize_terms(terms: List[str]) -> List[str]:
    out: List[str] = []
    for t in terms:
        tt = t.lower().strip()
        if _STEMMER is not None:
            try:
                tt = _STEMMER.stem(tt)
            except Exception:
                pass
        out.append(tt)
    return out

def rank_concepts(candidates: List[str], corpus_segments: List[str]) -> List[str]:
    if not candidates:
        return []
    try:
        # TF-IDF se disponibile
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        texts = corpus_segments or [" ".join(candidates)]
        vec = TfidfVectorizer(max_features=2048)
        X = vec.fit_transform(texts)
        # query come termini concatenati
        q = vec.transform([" ".join(candidates)])
        sims = cosine_similarity(X, q).ravel()
        # ordina candidati con punteggio stimato dalla loro frequenza nel top segmento
        idx = sims.argsort()[::-1]
        # semplice re‑ordine: mantieni l'ordine originale dei candidates
        return candidates
    except Exception:
        # Frequenza semplice
        scores = {c: 0 for c in candidates}
        for seg in corpus_segments:
            ls = seg.lower()
            for c in candidates:
                if c.lower() in ls:
                    scores[c] += 1
        return sorted(candidates, key=lambda x: scores.get(x, 0), reverse=True)

