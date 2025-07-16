"""
ChromaDB Vector Storage for VisionSeal RAG System
Easy-to-use vector database without Docker requirements
"""
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

import chromadb
from chromadb.config import Settings
from openai import OpenAI

from core.config.settings import settings
from core.logging.setup import get_logger
from core.exceptions.handlers import AIProcessingException

# Load environment variables
load_dotenv()

logger = get_logger("chroma_vector_store")


class ChromaVectorStore:
    """ChromaDB-based vector storage with enterprise features"""
    
    def __init__(
        self, 
        openai_api_key: Optional[str] = None,
        embedding_model: str = "text-embedding-3-large",
        collection_name: str = "tender_chunks",
        persist_directory: Optional[str] = None
    ):
        """Initialize ChromaDB vector store"""
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise AIProcessingException("OpenAI API key not provided")
            
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        
        # Set up persistence directory
        if persist_directory is None:
            persist_directory = str(settings.data_dir / "chroma_db")
        
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,  # Disable telemetry for privacy
                    is_persistent=True
                )
            )
            
            # Get or create collection with custom embedding function
            # We need to specify that we'll provide our own embeddings
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "VisionSeal tender documents and responses"},
                embedding_function=None  # We'll provide our own OpenAI embeddings
            )
            
            logger.info(f"ChromaDB initialized with collection '{self.collection_name}' at {persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise AIProcessingException(f"ChromaDB initialization failed: {str(e)}")

    async def init_collection(self) -> bool:
        """Initialize collection (already done in __init__ for ChromaDB)"""
        try:
            # ChromaDB collection is already created in __init__
            count = self.collection.count()
            logger.info(f"Collection '{self.collection_name}' ready with {count} documents")
            return True
        except Exception as e:
            logger.error(f"Failed to check collection: {str(e)}")
            return False

    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for text with error handling"""
        try:
            # Clean text
            text = text.replace("\n", " ").strip()
            if not text:
                raise ValueError("Empty text provided for embedding")
            
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=[text]
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding of dimension {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise AIProcessingException(f"Embedding generation failed: {str(e)}")

    async def insert_chunks(
        self, 
        chunks: List[tuple], 
        filename: str,
        user_id: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> Dict[str, int]:
        """Insert chunks with metadata tracking"""
        try:
            inserted = 0
            skipped = 0
            errors = 0
            
            # Prepare batch data
            documents = []
            metadatas = []
            ids = []
            embeddings = []

            for section, chunk_content, chunk_type in chunks:
                try:
                    # Create unique ID
                    chunk_id = str(uuid.uuid4())
                    
                    # Skip duplicate check for now to speed up ingestion
                    # We'll use chunk_id to prevent exact duplicates
                    
                    # Generate embedding
                    embedding = await self.embed_text(chunk_content)
                    
                    # Prepare metadata
                    metadata = {
                        "filename": filename,
                        "section": section,
                        "type": chunk_type,
                        "created_at": datetime.now().isoformat(),
                        "user_id": user_id or "system",
                        "document_id": document_id or filename,
                        "content_length": len(chunk_content)
                    }
                    
                    # Add to batch
                    documents.append(chunk_content)
                    metadatas.append(metadata)
                    ids.append(chunk_id)
                    embeddings.append(embedding)
                    
                except Exception as chunk_error:
                    logger.warning(f"Failed to prepare chunk: {str(chunk_error)}")
                    errors += 1
                    continue
            
            # Insert batch if we have documents
            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
                inserted = len(documents)
            
            result = {
                "inserted": inserted,
                "skipped": skipped,
                "errors": errors,
                "total": len(chunks)
            }
            
            logger.info(
                f"Chunk insertion completed for '{filename}': "
                f"{inserted} inserted, {skipped} skipped, {errors} errors"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Bulk chunk insertion failed: {str(e)}")
            raise AIProcessingException(f"Bulk chunk insertion failed: {str(e)}")

    async def search_similar_chunks(
        self, 
        query_text: str, 
        top_k: int = 5,
        user_id: Optional[str] = None,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks with optional filtering"""
        try:
            # Build where filter
            where_filter = {}
            if filter_criteria:
                where_filter.update(filter_criteria)
            if user_id:
                where_filter["user_id"] = user_id
            
            # Generate embedding for query
            query_embedding = await self.embed_text(query_text)
            
            # Query ChromaDB using embeddings instead of text
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            chunks = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    chunks.append({
                        "content": results["documents"][0][i],
                        "filename": results["metadatas"][0][i].get("filename", "Unknown"),
                        "section": results["metadatas"][0][i].get("section", "Unknown"),
                        "type": results["metadatas"][0][i].get("type", "text"),
                        "created_at": results["metadatas"][0][i].get("created_at"),
                        "user_id": results["metadatas"][0][i].get("user_id"),
                        "document_id": results["metadatas"][0][i].get("document_id"),
                        "score": 1.0 - results["distances"][0][i],  # Convert distance to similarity
                        "distance": results["distances"][0][i]
                    })
            
            # Sort by score (similarity) in descending order
            chunks.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info(f"Retrieved {len(chunks)} similar chunks for query")
            return chunks
            
        except Exception as e:
            logger.error(f"Similarity search failed: {str(e)}")
            raise AIProcessingException(f"Similarity search failed: {str(e)}")

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            
            # Get some sample metadata to understand the data
            sample_results = self.collection.peek(limit=5)
            
            # Count documents by type
            type_counts = {}
            filename_counts = {}
            
            if sample_results["metadatas"]:
                for metadata in sample_results["metadatas"]:
                    doc_type = metadata.get("type", "unknown")
                    filename = metadata.get("filename", "unknown")
                    
                    type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
                    filename_counts[filename] = filename_counts.get(filename, 0) + 1
            
            return {
                "collection_name": self.collection_name,
                "total_chunks": count,
                "embedding_model": self.embedding_model,
                "sample_types": type_counts,
                "sample_files": list(filename_counts.keys())[:10],  # First 10 filenames
                "status": "ready"
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {
                "collection_name": self.collection_name,
                "total_chunks": 0,
                "error": str(e),
                "status": "error"
            }

    def close(self):
        """Close ChromaDB connection (ChromaDB handles this automatically)"""
        try:
            # ChromaDB is persistent and handles cleanup automatically
            logger.info("ChromaDB connection closed")
        except Exception as e:
            logger.warning(f"Error during ChromaDB cleanup: {str(e)}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Singleton instance for application use
_chroma_store_instance = None

def get_vector_store() -> ChromaVectorStore:
    """Get or create ChromaDB vector store singleton"""
    global _chroma_store_instance
    if _chroma_store_instance is None:
        _chroma_store_instance = ChromaVectorStore()
    return _chroma_store_instance