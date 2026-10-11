"""Reusable retrieval indexes; no network or model initialization."""
from collections import Counter
import unicodedata
import numpy as np


def normalize_trait(trait):
    return unicodedata.normalize('NFKC', str(trait)).strip().casefold()


class CosineIndex:
    """Validate and normalize the corpus once, then reuse it for queries."""
    def __init__(self, vectors):
        vectors=np.array(vectors, dtype=np.float64, copy=True)
        if vectors.ndim != 2 or not vectors.shape[0] or not vectors.shape[1]:
            raise ValueError('角色向量維度無效。')
        if not np.isfinite(vectors).all():
            raise ValueError('角色向量包含無效數值。')
        norms=np.linalg.norm(vectors, axis=1)
        if np.any(norms == 0):
            raise ValueError('角色資料包含零向量。')
        self.vectors=vectors / norms[:,None]
        self.vectors.setflags(write=False)

    def search(self, query, k=5):
        query=np.asarray(query, dtype=float)
        if query.ndim != 1 or query.size != self.vectors.shape[1]:
            raise ValueError('向量維度不一致，請使用相同模型重新產生角色向量。')
        if not np.isfinite(query).all():
            raise ValueError('查詢向量包含無效數值。')
        norm=np.linalg.norm(query)
        if norm == 0:
            raise ValueError('查詢包含零向量。')
        if not isinstance(k,int) or k < 1:
            raise ValueError('結果數量必須是正整數。')
        similarity=self.vectors @ (query / norm)
        span=np.ptp(similarity)
        scores=np.full_like(similarity,50.) if np.isclose(span,0) else (similarity-similarity.min()) / span * 100
        # Stable full sort is deliberate: at N=50 it is cheap and ties stay deterministic.
        indices=np.argsort(-scores, kind='stable')[:k]
        return [(int(i),float(scores[i])) for i in indices]


class TraitIndex:
    """Exact-tag IDF baseline. Rare overlapping traits contribute more."""
    def __init__(self, characters):
        self.traits=[{normalize_trait(t) for t in c.get('moe_traits',[]) if normalize_trait(t)} for c in characters]
        frequencies=Counter(t for traits in self.traits for t in traits)
        self.idf={t:float(np.log((len(characters)+1)/(count+1))+1) for t,count in frequencies.items()}
        self.postings={t:[] for t in frequencies}
        for i,traits in enumerate(self.traits):
            for trait in traits:
                self.postings[trait].append(i)

    def search(self, traits, k=5):
        if not isinstance(k,int) or k < 1:
            raise ValueError('結果數量必須是正整數。')
        scores=np.zeros(len(self.traits))
        query={normalize_trait(t) for t in traits}
        total=sum(self.idf.get(t,0.) for t in query)
        if not total:
            return []
        for trait in query:
            scores[self.postings.get(trait,[])]+=self.idf.get(trait,0.)
        indices=np.argsort(-scores,kind='stable')[:k]
        return [(int(i),float(scores[i]/total*100)) for i in indices if scores[i]>0]
