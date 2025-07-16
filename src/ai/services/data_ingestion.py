"""
Data Ingestion Service for VisionSeal RAG System
Processes and ingests documents into the vector database
"""
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ai.storage.chroma_vector_store import get_vector_store
from ai.processors.document_processor import create_document_processor
from core.config.settings import settings
from core.logging.setup import get_logger
from core.exceptions.handlers import AIProcessingException

logger = get_logger("data_ingestion")


class DataIngestionService:
    """Service for ingesting documents into the vector database"""
    
    def __init__(self):
        self.vector_store = None
        self.document_processor = None
        
    async def initialize(self):
        """Initialize components"""
        try:
            self.vector_store = get_vector_store()
            await self.vector_store.init_collection()
            
            self.document_processor = create_document_processor(
                chunk_size=1500,
                chunk_overlap=200,
                enable_ocr=False  # Disable OCR for faster processing
            )
            
            logger.info("Data ingestion service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize data ingestion service: {str(e)}")
            raise AIProcessingException(f"Data ingestion initialization failed: {str(e)}")
    
    async def ingest_directory(
        self, 
        directory_path: str,
        file_patterns: List[str] = ["*.pdf", "*.docx", "*.pptx"],
        user_id: Optional[str] = "system"
    ) -> Dict[str, Any]:
        """Ingest all documents from a directory"""
        try:
            directory = Path(directory_path)
            if not directory.exists():
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            # Find all matching files
            files_to_process = []
            for pattern in file_patterns:
                files_to_process.extend(directory.glob(pattern))
            
            if not files_to_process:
                logger.warning(f"No files found in {directory_path} matching patterns {file_patterns}")
                return {
                    "total_files": 0,
                    "processed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "details": []
                }
            
            logger.info(f"Found {len(files_to_process)} files to process in {directory_path}")
            
            # Process files
            results = {
                "total_files": len(files_to_process),
                "processed": 0,
                "failed": 0,
                "skipped": 0,
                "details": []
            }
            
            for file_path in files_to_process:
                try:
                    result = await self.ingest_file(str(file_path), user_id=user_id)
                    
                    if result["status"] == "success":
                        results["processed"] += 1
                    elif result["status"] == "skipped":
                        results["skipped"] += 1
                    else:
                        results["failed"] += 1
                    
                    results["details"].append({
                        "file": file_path.name,
                        "status": result["status"],
                        "chunks": result.get("chunks_inserted", 0),
                        "message": result.get("message", "")
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {str(e)}")
                    results["failed"] += 1
                    results["details"].append({
                        "file": file_path.name,
                        "status": "failed",
                        "chunks": 0,
                        "message": str(e)
                    })
            
            logger.info(
                f"Directory ingestion completed: {results['processed']} processed, "
                f"{results['failed']} failed, {results['skipped']} skipped"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Directory ingestion failed: {str(e)}")
            raise AIProcessingException(f"Directory ingestion failed: {str(e)}")
    
    async def ingest_file(
        self, 
        file_path: str,
        user_id: Optional[str] = "system",
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ingest a single file into the vector database"""
        try:
            file_path_obj = Path(file_path)
            filename = file_path_obj.name
            
            if not file_path_obj.exists():
                return {
                    "status": "failed",
                    "message": f"File not found: {file_path}",
                    "chunks_inserted": 0
                }
            
            # Skip duplicate check for now to speed up initial ingestion
            # In production, this would check if file was already processed
            
            logger.info(f"Processing file: {filename}")
            
            # Process document
            chunks = await self.document_processor.process_document(
                file_path, 
                file_path_obj.suffix
            )
            
            if not chunks:
                return {
                    "status": "failed",
                    "message": "No content extracted from document",
                    "chunks_inserted": 0
                }
            
            # Insert chunks into vector database
            ingestion_result = await self.vector_store.insert_chunks(
                chunks=chunks,
                filename=filename,
                user_id=user_id,
                document_id=document_id or filename
            )
            
            logger.info(
                f"File {filename} processed: {ingestion_result['inserted']} chunks inserted, "
                f"{ingestion_result['skipped']} skipped, {ingestion_result['errors']} errors"
            )
            
            return {
                "status": "success",
                "message": f"Successfully processed {len(chunks)} chunks",
                "chunks_inserted": ingestion_result["inserted"],
                "chunks_skipped": ingestion_result["skipped"],
                "chunks_errors": ingestion_result["errors"]
            }
            
        except Exception as e:
            logger.error(f"File ingestion failed for {file_path}: {str(e)}")
            return {
                "status": "failed",
                "message": str(e),
                "chunks_inserted": 0
            }
    
    async def ingest_sample_data(self) -> Dict[str, Any]:
        """Ingest sample data from VisionSeal-AI-main"""
        try:
            # Define sample data locations
            sample_directories = [
                {
                    "path": "/root/VisionSeal-AI-main/VisionSeal-AI-main/reponses_topaza",
                    "patterns": ["*.docx"],
                    "description": "Historical tender responses"
                },
                {
                    "path": "/root/VisionSeal-AI-main/VisionSeal-AI-main/appels_entrants", 
                    "patterns": ["*.pdf"],
                    "description": "Sample tender documents"
                }
            ]
            
            total_results = {
                "directories_processed": 0,
                "total_files": 0,
                "processed": 0,
                "failed": 0,
                "skipped": 0,
                "details": []
            }
            
            for directory_config in sample_directories:
                dir_path = directory_config["path"]
                
                if not Path(dir_path).exists():
                    logger.warning(f"Sample directory not found: {dir_path}")
                    continue
                
                logger.info(f"Processing {directory_config['description']}: {dir_path}")
                
                result = await self.ingest_directory(
                    directory_path=dir_path,
                    file_patterns=directory_config["patterns"],
                    user_id="sample_data"
                )
                
                total_results["directories_processed"] += 1
                total_results["total_files"] += result["total_files"]
                total_results["processed"] += result["processed"]
                total_results["failed"] += result["failed"]
                total_results["skipped"] += result["skipped"]
                
                total_results["details"].append({
                    "directory": directory_config["description"],
                    "path": dir_path,
                    "result": result
                })
            
            # Also ingest the company profile
            company_profile_path = "/root/VisionSeal-AI-main/VisionSeal-AI-main/TOPAZA.pptx"
            if Path(company_profile_path).exists():
                logger.info("Processing company profile: TOPAZA.pptx")
                profile_result = await self.ingest_file(
                    company_profile_path,
                    user_id="system",
                    document_id="topaza_profile"
                )
                
                total_results["total_files"] += 1
                if profile_result["status"] == "success":
                    total_results["processed"] += 1
                elif profile_result["status"] == "skipped":
                    total_results["skipped"] += 1
                else:
                    total_results["failed"] += 1
                
                total_results["details"].append({
                    "directory": "Company Profile",
                    "path": company_profile_path,
                    "result": {
                        "total_files": 1,
                        "processed": 1 if profile_result["status"] == "success" else 0,
                        "failed": 1 if profile_result["status"] == "failed" else 0,
                        "skipped": 1 if profile_result["status"] == "skipped" else 0,
                        "details": [profile_result]
                    }
                })
            
            logger.info(
                f"Sample data ingestion completed: {total_results['processed']} files processed, "
                f"{total_results['failed']} failed, {total_results['skipped']} skipped"
            )
            
            return total_results
            
        except Exception as e:
            logger.error(f"Sample data ingestion failed: {str(e)}")
            raise AIProcessingException(f"Sample data ingestion failed: {str(e)}")
    
    async def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get statistics about ingested data"""
        try:
            stats = await self.vector_store.get_collection_stats()
            return {
                "collection_stats": stats,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get ingestion stats: {str(e)}")
            return {
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }
    
    async def clear_collection(self, confirm: bool = False) -> Dict[str, Any]:
        """Clear all data from the vector collection (use with caution)"""
        if not confirm:
            return {
                "status": "cancelled",
                "message": "Operation cancelled - confirmation required"
            }
        
        try:
            # This would need to be implemented in the vector store
            # For now, we'll log the intent
            logger.warning("Collection clear requested - this feature needs implementation")
            return {
                "status": "not_implemented",
                "message": "Collection clearing not yet implemented"
            }
            
        except Exception as e:
            logger.error(f"Failed to clear collection: {str(e)}")
            return {
                "status": "failed",
                "message": str(e)
            }


# Factory function
async def create_data_ingestion_service() -> DataIngestionService:
    """Create and initialize data ingestion service"""
    service = DataIngestionService()
    await service.initialize()
    return service


# CLI functions for easy use
async def ingest_sample_data():
    """CLI function to ingest sample data"""
    try:
        service = await create_data_ingestion_service()
        result = await service.ingest_sample_data()
        
        print(f"Sample data ingestion completed:")
        print(f"  Total files: {result['total_files']}")
        print(f"  Processed: {result['processed']}")
        print(f"  Failed: {result['failed']}")
        print(f"  Skipped: {result['skipped']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Sample data ingestion failed: {str(e)}")
        print(f"Error: {str(e)}")
        return None


if __name__ == "__main__":
    # Allow running as script
    asyncio.run(ingest_sample_data())