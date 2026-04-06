import numpy as np

from job_researcher.models import ResumeMatch
from job_researcher.services.embeddings import EmbeddingsService


def chunk_text(text: str, max_chunk_size: int = 500) -> list[str]:
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if current and len(current) + len(para) + 2 > max_chunk_size:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para

    if current:
        chunks.append(current)

    return chunks


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return float(dot / norm)


async def compare_resume(
    embeddings_service: EmbeddingsService,
    jd_requirements: list[str],
    resume_chunks: list[str],
    resume_embeddings: list[np.ndarray],
) -> ResumeMatch:
    # Embed JD requirements
    jd_vectors = await embeddings_service.embed(jd_requirements)

    # For each JD requirement, find best matching resume chunk
    top_matches: list[dict[str, float]] = []
    similarities: list[float] = []

    for i, jd_vec in enumerate(jd_vectors):
        jd_arr = np.array(jd_vec)
        best_score = 0.0
        best_chunk = ""

        for j, resume_vec in enumerate(resume_embeddings):
            score = cosine_similarity(jd_arr, resume_vec)
            if score > best_score:
                best_score = score
                best_chunk = resume_chunks[j][:100]

        similarities.append(best_score)
        top_matches.append({
            "requirement": jd_requirements[i],
            "best_match": best_chunk,
            "score": round(best_score, 3),
        })

    overall = float(np.mean(similarities)) if similarities else 0.0

    return ResumeMatch(
        overall_similarity=round(overall, 3),
        top_matches=top_matches,
    )
