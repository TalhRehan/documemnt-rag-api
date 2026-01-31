import json
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer


class IndexingAgent:
    def __init__(self):
        # Load sentence embedding model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def chunk_text(self, text: str, chunk_size=600, overlap=100):
        """
        Semantic chunking that respects sentence boundaries.
        No more mid-word cuts like 'mach' or 'lear'.
        """
        import re

        # Split into sentences (respects periods, question marks, exclamation marks)
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_length = len(sentence)

            # If adding this sentence exceeds chunk_size, save current chunk
            if current_length + sentence_length > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))

                # Keep last sentences for overlap (semantic continuity)
                overlap_sentences = []
                overlap_length = 0
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= overlap:
                        overlap_sentences.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break

                current_chunk = overlap_sentences
                current_length = overlap_length

            current_chunk.append(sentence)
            current_length += sentence_length

        # Add final chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def build_index(self, chunks: list[str], index_path: Path, map_path: Path):
        # Encode chunks into embeddings
        embeddings = self.model.encode(chunks, show_progress_bar=False)

        # Convert to float32 for FAISS
        embeddings = np.array(embeddings).astype("float32")

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        # Create FAISS Inner Product index (= cosine similarity after normalization)
        index = faiss.IndexFlatIP(embeddings.shape[1])
        # Add embeddings to index
        index.add(embeddings)

        # Persist index to disk
        faiss.write_index(index, str(index_path))

        # Create chunk index mapping
        mapping = {str(i): {"chunk_index": i} for i in range(len(chunks))}
        # Create chunk index mapping with text preview
        mapping = {str(i): {"chunk_index": i,"text": chunks[i] } # Store full chunk text for quick access
        for i in range(len(chunks))
         }
        

        # Save mapping file
        map_path.write_text(json.dumps(mapping, indent=2))

        # Return chunk count
        return len(chunks)
