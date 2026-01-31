import json
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import os


class QAAgent:
    def __init__(self):
        # Load sentence embedding model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def retrieve(self, document_id: int, question: str, top_k: int = 5):
        # Resolve index and mapping paths
        index_path = Path("storage/indexes") / f"{document_id}.faiss"
        map_path = Path("storage/indexes") / f"{document_id}_map.json"

        # Ensure index exists
        if not index_path.exists() or not map_path.exists():
            raise ValueError("Vector index not found. Please index the document first.")

        # Load FAISS index and metadata
        index = faiss.read_index(str(index_path))
        mapping = json.loads(map_path.read_text())

        # Encode question embedding
        q_emb = self.model.encode([question])
        q_emb = np.array(q_emb).astype("float32")

        # Perform similarity search
        faiss.normalize_L2(q_emb)
        similarities, indices = index.search(q_emb, top_k)

        # Build ranked result set
        results = []
        for rank, idx in enumerate(indices[0]):
            if idx == -1:
                continue
            chunk_data = mapping.get(str(idx), {})
            results.append({
                "vector_id": int(idx),
                "similarity": float(similarities[0][rank]),
                "text": chunk_data.get("text", ""),
                "preview": chunk_data.get("text", "")[:200]
            })

        return results

    def answer_from_context(self, question: str, contexts: list[str]) -> str:
        """
        Generate intelligent answer using OpenAI with retrieved context.
        """
        if not contexts:
            return "I don't have enough information in the uploaded document to answer that question."

        # Use top 3 most relevant chunks
        
        context_text = "\n\n".join(contexts[:5])
        
        # IMPROVED PROMPT - More specific instructions
        system_prompt = """You are an expert document analyst. Your job is to answer questions using ONLY the specific information provided in the document context.

CRITICAL RULES:
1. Extract and synthesize information DIRECTLY from the context
2. Use specific examples, details, and explanations from the document
3. Quote or paraphrase the document's exact wording when relevant
4. If the context lacks sufficient information, explicitly state: "The document doesn't contain enough information to fully answer this question"
5. Do NOT add external knowledge or general information not in the context
6. Be comprehensive - use all relevant details from the context
7. Organize your answer clearly with specific examples from the document"""

        user_prompt = f"""DOCUMENT CONTEXT:
{context_text}

QUESTION: {question}

Provide a detailed, specific answer based exclusively on the information in the context above. Include concrete examples and details mentioned in the document."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,  # Increased from 500 for more detailed answers
                temperature=0.1  # Lower temperature (was 0.3) for more focused, less creative answers
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            return f"Error generating answer: {str(e)}\n\nRelevant context:\n{contexts[0][:300]}..."
