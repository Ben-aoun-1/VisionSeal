"""
Enhanced Vector Storage for VisionSeal RAG System
Integrates with VisionSeal-Refactored security and configuration
"""
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI
from weaviate import WeaviateClient
from weaviate.connect import ConnectionParams, ProtocolParams
from weaviate.classes.config import Property, DataType, Configure
from weaviate.util import generate_uuid5

from core.config.settings import settings
from core.logging.setup import get_logger
from core.exceptions.handlers import AIProcessingException

# Load environment variables
load_dotenv()

logger = get_logger("vector_store")


class VectorStore:
    """Enhanced vector storage with enterprise features"""
    
    def __init__(
        self, 
        openai_api_key: Optional[str] = None,
        embedding_model: str = "text-embedding-3-large",
        expected_dim: int = 3072,
        weaviate_host: str = "localhost",
        weaviate_port: int = 8090,
        collection_name: str = "TenderChunks"
    ):
        """Initialize vector store with configuration"""
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise AIProcessingException("OpenAI API key not provided")
            
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.embedding_model = embedding_model
        self.expected_dim = expected_dim
        self.collection_name = collection_name
        
        # Initialize Weaviate client
        try:
            self.weaviate_client = WeaviateClient(
                connection_params=ConnectionParams(
                    http=ProtocolParams(host=weaviate_host, port=weaviate_port, secure=False),
                    grpc=ProtocolParams(host=weaviate_host, port=50051, secure=False),
                )
            )
            self.weaviate_client.connect()
            logger.info(f"Connected to Weaviate at {weaviate_host}:{weaviate_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {str(e)}")
            raise AIProcessingException(f"Weaviate connection failed: {str(e)}")

    async def init_collection(self) -> bool:
        """Initialize Weaviate collection with proper schema"""
        try:
            if not self.weaviate_client.collections.exists(self.collection_name):
                self.weaviate_client.collections.create(
                    name=self.collection_name,
                    vectorizer_config=Configure.Vectorizer.none(),
                    properties=[
                        Property(name="content", data_type=DataType.TEXT),
                        Property(name="filename", data_type=DataType.TEXT),
                        Property(name="section", data_type=DataType.TEXT),
                        Property(name="type", data_type=DataType.TEXT),
                        Property(name="created_at", data_type=DataType.DATE),
                        Property(name="user_id", data_type=DataType.TEXT),
                        Property(name="document_id", data_type=DataType.TEXT),
                    ]
                )
                logger.info(f"Collection '{self.collection_name}' created successfully")
                return True
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")
                return True
        except Exception as e:
            logger.error(f"Failed to initialize collection: {str(e)}")
            raise AIProcessingException(f"Collection initialization failed: {str(e)}")

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
            
            if len(embedding) != self.expected_dim:
                raise ValueError(f"Unexpected embedding dimension: {len(embedding)} vs {self.expected_dim}")
            
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
        """Insert chunks with enhanced metadata and error handling"""
        try:
            collection = self.weaviate_client.collections.get(self.collection_name)
            inserted = 0
            skipped = 0
            errors = 0

            for section, chunk, typ in chunks:
                try:
                    data = {
                        "content": chunk,
                        "filename": filename,
                        "section": section,
                        "type": typ,
                        "created_at": settings.get_current_timestamp(),
                        "user_id": user_id or "system",
                        "document_id": document_id or filename,
                    }

                    uuid = generate_uuid5(data)
                    if collection.data.exists(uuid):
                        skipped += 1
                        continue

                    vector = await self.embed_text(chunk)
                    
                    collection.data.insert(
                        properties=data,
                        vector=vector,
                        uuid=uuid
                    )
                    inserted += 1
                    
                except Exception as chunk_error:
                    logger.warning(f"Failed to insert chunk: {str(chunk_error)}")
                    errors += 1
                    continue

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
            query_embedding = await self.embed_text(query_text)
            collection = self.weaviate_client.collections.get(self.collection_name)
            
            # Build where filter if criteria provided
            where_filter = None
            if filter_criteria:
                # Add user filtering if specified
                if user_id:
                    filter_criteria["user_id"] = user_id
                # Implement Weaviate where filter based on criteria
                # This would need to be expanded based on specific filter needs
            
            results = collection.query.near_vector(
                near_vector=query_embedding,
                limit=top_k,
                return_metadata=["certainty", "distance"],
                return_properties=["content", "filename", "section", "type", "created_at", "user_id", "document_id"],
                where=where_filter
            )
            
            chunks = []
            for obj in results.objects:
                chunks.append({
                    "content": obj.properties["content"],
                    "filename": obj.properties["filename"],
                    "section": obj.properties["section"],
                    "type": obj.properties["type"],
                    "created_at": obj.properties.get("created_at"),
                    "user_id": obj.properties.get("user_id"),
                    "document_id": obj.properties.get("document_id"),
                    "score": obj.metadata.certainty or 0,
                    "distance": obj.metadata.distance or 1.0
                })
            
            # Sort by score (certainty) in descending order
            chunks.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info(f"Retrieved {len(chunks)} similar chunks for query")
            return chunks
            
        except Exception as e:
            logger.error(f"Similarity search failed: {str(e)}")
            raise AIProcessingException(f"Similarity search failed: {str(e)}")

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            collection = self.weaviate_client.collections.get(self.collection_name)
            
            # Get total object count
            result = collection.aggregate.over_all(total_count=True)
            total_count = result.total_count if result else 0
            
            return {
                "collection_name": self.collection_name,
                "total_chunks": total_count,
                "embedding_model": self.embedding_model,
                "embedding_dimension": self.expected_dim
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {
                "collection_name": self.collection_name,
                "total_chunks": 0,
                "error": str(e)
            }

    def close(self):
        """Close Weaviate connection"""
        try:
            if hasattr(self, 'weaviate_client'):
                self.weaviate_client.close()
                logger.info("Weaviate connection closed")
        except Exception as e:
            logger.warning(f"Error closing Weaviate connection: {str(e)}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Singleton instance for application use
_vector_store_instance = None

def get_vector_store() -> VectorStore:
    """Get or create vector store singleton"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance