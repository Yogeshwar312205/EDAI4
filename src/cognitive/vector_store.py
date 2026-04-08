"""
EDAI4 - Vector Store for Semantic Search
=========================================
Adds sentence-transformer embeddings for semantic search
over knowledge base and P&ID graph data.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Union
from enum import Enum
import json
import os

from src.utils import get_logger

logger = get_logger(__name__)


# Try to import sentence-transformers (optional dependency)
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not installed. Using fallback TF-IDF.")


@dataclass
class EmbeddedDocument:
    """A document with its embedding vector."""
    id: str
    content: str
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
        }


class VectorStore:
    """
    Vector store for semantic search using sentence embeddings.
    
    Features:
    - Sentence-transformer embeddings (if available)
    - Fallback to TF-IDF for environments without GPU
    - Cosine similarity search
    - Batch embedding for efficiency
    """
    
    # Default model - small and fast, good for engineering text
    DEFAULT_MODEL = "all-MiniLM-L6-v2"
    
    def __init__(
        self,
        model_name: str = None,
        use_gpu: bool = True,
    ):
        """
        Initialize vector store.
        
        Args:
            model_name: Sentence transformer model name
            use_gpu: Whether to use GPU for embeddings
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.use_gpu = use_gpu
        self.documents: Dict[str, EmbeddedDocument] = {}
        self._embeddings_matrix: Optional[np.ndarray] = None
        self._doc_ids: List[str] = []
        self._model = None
        self._tfidf_vectorizer = None
        self._tfidf_matrix = None
        
        # Initialize embedding model
        self._init_model()
    
    def _init_model(self):
        """Initialize the embedding model."""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                device = "cuda" if self.use_gpu else "cpu"
                self._model = SentenceTransformer(self.model_name, device=device)
                logger.info(f"Loaded sentence-transformer model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to load sentence-transformer: {e}. Using TF-IDF fallback.")
                self._init_tfidf()
        else:
            self._init_tfidf()
    
    def _init_tfidf(self):
        """Initialize TF-IDF fallback."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
            )
            logger.info("Using TF-IDF fallback for embeddings")
        except ImportError:
            logger.warning("sklearn not available. Search will use keyword matching.")
    
    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embed a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Embedding matrix (n_texts, embedding_dim)
        """
        if self._model is not None:
            # Use sentence-transformers
            embeddings = self._model.encode(
                texts,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            return embeddings
        elif self._tfidf_vectorizer is not None:
            # Use TF-IDF
            if not hasattr(self._tfidf_vectorizer, 'vocabulary_'):
                # Fit on first batch
                self._tfidf_matrix = self._tfidf_vectorizer.fit_transform(texts)
                return self._tfidf_matrix.toarray()
            else:
                return self._tfidf_vectorizer.transform(texts).toarray()
        else:
            # No embedding available - return zeros
            return np.zeros((len(texts), 100))
    
    def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any] = None,
    ) -> EmbeddedDocument:
        """
        Add a document to the store.
        
        Args:
            doc_id: Unique document ID
            content: Document text content
            metadata: Optional metadata dict
            
        Returns:
            The embedded document
        """
        embedding = self._embed_texts([content])[0]
        
        doc = EmbeddedDocument(
            id=doc_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {},
        )
        
        self.documents[doc_id] = doc
        self._rebuild_index()
        
        return doc
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[EmbeddedDocument]:
        """
        Add multiple documents efficiently (batch embedding).
        
        Args:
            documents: List of dicts with 'id', 'content', and optional 'metadata'
            
        Returns:
            List of embedded documents
        """
        if not documents:
            return []
        
        # Extract texts for batch embedding
        texts = [doc['content'] for doc in documents]
        embeddings = self._embed_texts(texts)
        
        # Create document objects
        result = []
        for i, doc_dict in enumerate(documents):
            doc = EmbeddedDocument(
                id=doc_dict['id'],
                content=doc_dict['content'],
                embedding=embeddings[i],
                metadata=doc_dict.get('metadata', {}),
            )
            self.documents[doc.id] = doc
            result.append(doc)
        
        self._rebuild_index()
        logger.info(f"Added {len(result)} documents to vector store")
        
        return result
    
    def _rebuild_index(self):
        """Rebuild the embedding matrix for efficient search."""
        if not self.documents:
            self._embeddings_matrix = None
            self._doc_ids = []
            return
        
        self._doc_ids = list(self.documents.keys())
        embeddings = [self.documents[doc_id].embedding for doc_id in self._doc_ids]
        self._embeddings_matrix = np.vstack(embeddings)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> List[Tuple[EmbeddedDocument, float]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)
            
        Returns:
            List of (document, similarity_score) tuples
        """
        if not self.documents or self._embeddings_matrix is None:
            return []
        
        # Embed query
        query_embedding = self._embed_texts([query])[0]
        
        # Compute cosine similarities
        similarities = self._cosine_similarity(
            query_embedding.reshape(1, -1),
            self._embeddings_matrix,
        )[0]
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Build results
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= threshold:
                doc_id = self._doc_ids[idx]
                results.append((self.documents[doc_id], score))
        
        return results
    
    def _cosine_similarity(
        self,
        a: np.ndarray,
        b: np.ndarray,
    ) -> np.ndarray:
        """Compute cosine similarity between vectors."""
        # Normalize
        a_norm = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-8)
        b_norm = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-8)
        
        # Dot product
        return np.dot(a_norm, b_norm.T)
    
    def get_document(self, doc_id: str) -> Optional[EmbeddedDocument]:
        """Get a document by ID."""
        return self.documents.get(doc_id)
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the store."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._rebuild_index()
            return True
        return False
    
    def clear(self):
        """Clear all documents."""
        self.documents.clear()
        self._embeddings_matrix = None
        self._doc_ids = []
    
    def save(self, path: str):
        """
        Save vector store to disk.
        
        Args:
            path: Directory path to save to
        """
        os.makedirs(path, exist_ok=True)
        
        # Save metadata
        metadata = {
            "model_name": self.model_name,
            "num_documents": len(self.documents),
        }
        with open(os.path.join(path, "metadata.json"), "w") as f:
            json.dump(metadata, f)
        
        # Save documents (without embeddings - will re-embed on load)
        docs_data = [doc.to_dict() for doc in self.documents.values()]
        with open(os.path.join(path, "documents.json"), "w") as f:
            json.dump(docs_data, f)
        
        # Save embeddings as numpy
        if self._embeddings_matrix is not None:
            np.save(os.path.join(path, "embeddings.npy"), self._embeddings_matrix)
            with open(os.path.join(path, "doc_ids.json"), "w") as f:
                json.dump(self._doc_ids, f)
        
        logger.info(f"Saved vector store to {path}")
    
    @classmethod
    def load(cls, path: str) -> "VectorStore":
        """
        Load vector store from disk.
        
        Args:
            path: Directory path to load from
            
        Returns:
            Loaded VectorStore instance
        """
        # Load metadata
        with open(os.path.join(path, "metadata.json"), "r") as f:
            metadata = json.load(f)
        
        store = cls(model_name=metadata["model_name"])
        
        # Load documents
        with open(os.path.join(path, "documents.json"), "r") as f:
            docs_data = json.load(f)
        
        # Load embeddings if available
        embeddings_path = os.path.join(path, "embeddings.npy")
        if os.path.exists(embeddings_path):
            embeddings = np.load(embeddings_path)
            with open(os.path.join(path, "doc_ids.json"), "r") as f:
                doc_ids = json.load(f)
            
            # Reconstruct documents with embeddings
            for i, doc_data in enumerate(docs_data):
                doc = EmbeddedDocument(
                    id=doc_data["id"],
                    content=doc_data["content"],
                    embedding=embeddings[i] if i < len(embeddings) else None,
                    metadata=doc_data.get("metadata", {}),
                )
                store.documents[doc.id] = doc
            
            store._doc_ids = doc_ids
            store._embeddings_matrix = embeddings
        else:
            # Re-embed documents
            store.add_documents(docs_data)
        
        logger.info(f"Loaded vector store from {path} ({len(store.documents)} documents)")
        return store
    
    def __len__(self) -> int:
        return len(self.documents)
    
    def summary(self) -> str:
        """Get a summary of the vector store."""
        model_type = "sentence-transformers" if self._model else "TF-IDF"
        embedding_dim = self._embeddings_matrix.shape[1] if self._embeddings_matrix is not None else 0
        
        return f"""Vector Store Summary:
- Model: {self.model_name} ({model_type})
- Documents: {len(self.documents)}
- Embedding Dimension: {embedding_dim}
- GPU: {self.use_gpu and self._model is not None}"""


class SemanticKnowledgeBase:
    """
    Enhanced knowledge base with semantic search capabilities.
    
    Wraps the existing EngineeringKnowledgeBase and adds vector search.
    """
    
    def __init__(
        self,
        knowledge_base=None,
        vector_store: VectorStore = None,
    ):
        """
        Initialize semantic knowledge base.
        
        Args:
            knowledge_base: Existing EngineeringKnowledgeBase (or creates new)
            vector_store: Existing VectorStore (or creates new)
        """
        # Import here to avoid circular imports
        from src.cognitive.knowledge_base import (
            EngineeringKnowledgeBase,
            get_knowledge_base,
        )
        
        self.kb = knowledge_base or get_knowledge_base()
        self.vector_store = vector_store or VectorStore()
        
        # Index knowledge base entries
        self._index_knowledge_base()
    
    def _index_knowledge_base(self):
        """Index all knowledge base entries in vector store."""
        documents = []
        
        for entry in self.kb.entries.values():
            # Combine title and content for better embeddings
            full_text = f"{entry.title}\n\n{entry.content}"
            
            documents.append({
                "id": f"kb:{entry.id}",
                "content": full_text,
                "metadata": {
                    "type": "knowledge",
                    "category": entry.category.value,
                    "title": entry.title,
                    "kb_id": entry.id,
                },
            })
        
        if documents:
            self.vector_store.add_documents(documents)
            logger.info(f"Indexed {len(documents)} knowledge base entries")
    
    def add_pid_context(
        self,
        instruments: List[Dict[str, Any]],
        graph_summary: str = None,
    ):
        """
        Add P&ID context to the vector store for better retrieval.
        
        Args:
            instruments: List of instrument dicts with tag, type, description
            graph_summary: Optional text summary of the P&ID graph
        """
        documents = []
        
        # Add instruments
        for inst in instruments:
            tag = inst.get("tag", "Unknown")
            desc = inst.get("description", "")
            inst_type = inst.get("type", "instrument")
            
            content = f"Instrument {tag}: {desc}"
            if inst.get("measured_variable"):
                content += f"\nMeasured Variable: {inst['measured_variable']}"
            if inst.get("functions"):
                content += f"\nFunctions: {', '.join(inst['functions'])}"
            
            documents.append({
                "id": f"inst:{tag}",
                "content": content,
                "metadata": {
                    "type": "instrument",
                    "tag": tag,
                    "instrument_type": inst_type,
                },
            })
        
        # Add graph summary
        if graph_summary:
            documents.append({
                "id": "pid:summary",
                "content": graph_summary,
                "metadata": {"type": "pid_summary"},
            })
        
        if documents:
            self.vector_store.add_documents(documents)
            logger.info(f"Added {len(documents)} P&ID context documents")
    
    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
        filter_type: str = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Semantic search across knowledge and P&ID context.
        
        Args:
            query: Natural language query
            top_k: Number of results
            filter_type: Optional filter ('knowledge', 'instrument', 'pid_summary')
            
        Returns:
            List of (result_dict, score) tuples
        """
        results = self.vector_store.search(query, top_k=top_k * 2)  # Get extra for filtering
        
        filtered = []
        for doc, score in results:
            if filter_type and doc.metadata.get("type") != filter_type:
                continue
            
            result = {
                "id": doc.id,
                "content": doc.content,
                "score": score,
                **doc.metadata,
            }
            filtered.append((result, score))
            
            if len(filtered) >= top_k:
                break
        
        return filtered
    
    def build_context(
        self,
        query: str,
        max_tokens: int = 2000,
    ) -> str:
        """
        Build context string for RAG from semantic search results.
        
        Args:
            query: User query
            max_tokens: Approximate max tokens for context
            
        Returns:
            Context string for LLM
        """
        results = self.semantic_search(query, top_k=10)
        
        context_parts = []
        total_chars = 0
        char_limit = max_tokens * 4  # Rough chars per token
        
        for result, score in results:
            if score < 0.3:  # Skip low relevance
                continue
            
            content = result["content"]
            if total_chars + len(content) > char_limit:
                break
            
            # Format based on type
            if result.get("type") == "knowledge":
                context_parts.append(f"[Knowledge: {result.get('title', 'Unknown')}]\n{content}")
            elif result.get("type") == "instrument":
                context_parts.append(f"[Instrument: {result.get('tag', 'Unknown')}]\n{content}")
            else:
                context_parts.append(content)
            
            total_chars += len(content)
        
        return "\n\n---\n\n".join(context_parts)
    
    def summary(self) -> str:
        """Get summary of semantic knowledge base."""
        return f"""Semantic Knowledge Base:
- Knowledge Entries: {len(self.kb.entries)}
- Vector Store: {len(self.vector_store)} documents
{self.vector_store.summary()}"""


# Convenience function
def create_semantic_kb(use_gpu: bool = True) -> SemanticKnowledgeBase:
    """
    Create a semantic knowledge base with default settings.
    
    Args:
        use_gpu: Whether to use GPU for embeddings
        
    Returns:
        Configured SemanticKnowledgeBase
    """
    vector_store = VectorStore(use_gpu=use_gpu)
    return SemanticKnowledgeBase(vector_store=vector_store)


if __name__ == "__main__":
    # Test the vector store
    print("Testing Vector Store...")
    
    store = VectorStore(use_gpu=False)
    
    # Add some test documents
    store.add_documents([
        {"id": "1", "content": "Flow transmitters measure fluid flow rate in pipes."},
        {"id": "2", "content": "Pressure indicators show the pressure in a vessel."},
        {"id": "3", "content": "Temperature controllers regulate process temperature."},
        {"id": "4", "content": "Level switches detect high or low liquid levels."},
        {"id": "5", "content": "Control valves adjust flow based on controller output."},
    ])
    
    print(f"\nAdded {len(store)} documents")
    print(store.summary())
    
    # Test search
    print("\n--- Search Tests ---")
    queries = [
        "How do I measure flow?",
        "What shows pressure?",
        "temperature control",
    ]
    
    for q in queries:
        print(f"\nQuery: '{q}'")
        results = store.search(q, top_k=3)
        for doc, score in results:
            print(f"  [{score:.3f}] {doc.content[:60]}...")
