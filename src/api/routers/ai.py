"""
AI router with secure file handling and RAG integration
Secure replacement for AI endpoints with full RAG capabilities
"""
import os
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from api.schemas.ai import (
    ChatRequest,
    DocumentAnalysisRequest,
    ChatResponse,
    DocumentAnalysisResult,
    ResponseGenerationResult,
    GeneratedFilesResponse,
    AIStatusResponse,
    SectorAnalysis,
    CountryAnalysis,
    AIReportRequest,
    ReportGenerationResponse,
    ReportType,
    ReportTone,
    ReportLength
)
from api.schemas.common import SuccessResponse, FileInfo
from core.auth.supabase_auth import get_current_user, get_current_user_optional
from core.security.validators import FileValidator, PathValidator
from core.exceptions.handlers import AIProcessingException, SecurityException
from core.config.settings import settings
from core.logging.setup import get_logger

# Import AI components
from ai.storage.chroma_vector_store import get_vector_store
from ai.processors.document_processor import create_document_processor
from ai.generators.response_generator import create_response_generator

logger = get_logger("ai")
router = APIRouter(prefix="/ai", tags=["ai"])


class AIService:
    """Secure AI processing service with RAG integration"""
    
    def __init__(self):
        self.processing_sessions: Dict[str, Dict[str, Any]] = {}
        self.vector_store = None
        self.document_processor = None
        self.response_generator = None
    
    async def _initialize_components(self):
        """Initialize AI components lazily"""
        if self.vector_store is None:
            try:
                self.vector_store = get_vector_store()
                await self.vector_store.init_collection()
                
                self.document_processor = create_document_processor()
                self.response_generator = create_response_generator()
                
                logger.info("AI components initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize AI components: {str(e)}")
                raise AIProcessingException(f"AI initialization failed: {str(e)}")
    
    async def _analyze_sector_and_country(self, text: str) -> tuple[Optional[SectorAnalysis], Optional[CountryAnalysis]]:
        """Analyze sector and country from document text"""
        try:
            # Simple keyword-based analysis (can be enhanced with ML models)
            text_lower = text.lower()
            
            # Sector analysis
            sector_keywords = {
                "agriculture": ["semence", "agricole", "cultivation", "farming", "crop"],
                "technology": ["software", "digital", "IT", "technology", "système"],
                "infrastructure": ["construction", "building", "infrastructure", "route"],
                "media": ["radio", "television", "media", "broadcast"],
                "healthcare": ["santé", "medical", "hospital", "health"],
                "education": ["education", "training", "formation", "école"]
            }
            
            sector = None
            sector_confidence = 0.0
            sector_keywords_found = []
            
            for sector_name, keywords in sector_keywords.items():
                found_keywords = [kw for kw in keywords if kw in text_lower]
                if found_keywords:
                    confidence = len(found_keywords) / len(keywords)
                    if confidence > sector_confidence:
                        sector = sector_name.title()
                        sector_confidence = confidence
                        sector_keywords_found = found_keywords
            
            sector_analysis = SectorAnalysis(
                sector=sector,
                confidence=min(sector_confidence, 1.0),
                keywords=sector_keywords_found
            )
            
            # Country analysis
            country_keywords = {
                "Tunisia": ["tunisie", "tunisia", "tunis"],
                "Senegal": ["sénégal", "senegal", "dakar"],
                "Congo": ["congo", "brazzaville", "kinshasa"],
                "Niger": ["niger", "niamey"],
                "Chad": ["tchad", "chad", "ndjamena"],
                "France": ["france", "français", "paris"]
            }
            
            country = None
            country_confidence = 0.0
            
            for country_name, keywords in country_keywords.items():
                found = any(kw in text_lower for kw in keywords)
                if found:
                    country = country_name
                    country_confidence = 0.8  # Base confidence
                    break
            
            country_analysis = CountryAnalysis(
                country=country,
                confidence=country_confidence,
                region="MENA" if country in ["Tunisia", "Niger", "Chad"] else "West Africa" if country == "Senegal" else "Central Africa"
            )
            
            return sector_analysis, country_analysis
            
        except Exception as e:
            logger.warning(f"Sector/country analysis failed: {str(e)}")
            return None, None
    
    async def analyze_document(
        self,
        file: UploadFile,
        request: DocumentAnalysisRequest,
        user: Dict[str, Any]
    ) -> DocumentAnalysisResult:
        """Analyze uploaded document with RAG-powered analysis"""
        start_time = datetime.now()
        
        try:
            # Initialize AI components
            await self._initialize_components()
            
            # Validate file upload
            FileValidator.validate_file_upload(file)
            
            # Create secure temporary file
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=Path(file.filename).suffix,
                dir=settings.uploads_dir / "temp"
            ) as temp_file:
                
                # Read and save file securely
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                logger.info(
                    "Starting document analysis",
                    extra={
                        "filename": file.filename,
                        "file_size": len(content),
                        "user_id": user.get("user_id"),
                        "operation": request.operation.value
                    }
                )
                
                # Process document
                chunks = await self.document_processor.process_document(
                    temp_file_path, 
                    Path(file.filename).suffix
                )
                
                # Extract text for analysis
                full_text = "\n\n".join([chunk[1] for chunk in chunks])
                
                # Generate summary if requested
                summary = None
                if request.extract_summary:
                    summary = await self.response_generator.generate_tender_summary(full_text)
                
                # Analyze sector and country if requested
                sector_analysis = None
                country_analysis = None
                if request.analyze_sector or request.analyze_country:
                    sector_result, country_result = await self._analyze_sector_and_country(full_text)
                    if request.analyze_sector:
                        sector_analysis = sector_result
                    if request.analyze_country:
                        country_analysis = country_result
                
                # Extract key points and requirements
                key_points = self._extract_key_points(full_text)
                requirements = self._extract_requirements(full_text)
                deadlines = self._extract_deadlines(full_text)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                result = DocumentAnalysisResult(
                    summary=summary,
                    sector_analysis=sector_analysis,
                    country_analysis=country_analysis,
                    key_points=key_points,
                    requirements=requirements,
                    deadlines=deadlines,
                    document_type=Path(file.filename).suffix[1:],
                    processing_time=processing_time,
                    model_used=self.response_generator.model
                )
                
                logger.info(f"Document analysis completed in {processing_time:.2f}s")
                return result
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    logger.warning(f"Failed to delete temporary file: {temp_file_path}")
                
        except Exception as e:
            logger.error(f"Document analysis failed: {str(e)}")
            raise AIProcessingException(f"Document analysis failed: {str(e)}")
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from document text"""
        try:
            # Simple extraction based on patterns
            key_points = []
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if any(keyword in line.lower() for keyword in ['objectif', 'exigence', 'requirement', 'deliverable', 'livrable']):
                    if len(line) > 20 and len(line) < 200:
                        key_points.append(line)
                        if len(key_points) >= 10:  # Limit number of points
                            break
            
            return key_points[:5]  # Return top 5
            
        except Exception:
            return ["Document processed successfully"]
    
    def _extract_requirements(self, text: str) -> Optional[str]:
        """Extract requirements section from document"""
        try:
            # Look for requirements section
            text_lower = text.lower()
            requirements_start = -1
            
            for keyword in ['exigences', 'requirements', 'spécifications', 'specifications']:
                idx = text_lower.find(keyword)
                if idx != -1:
                    requirements_start = idx
                    break
            
            if requirements_start != -1:
                # Extract next 500 characters as requirements
                requirements_text = text[requirements_start:requirements_start + 500]
                return requirements_text.strip()
            
            return None
            
        except Exception:
            return None
    
    def _extract_deadlines(self, text: str) -> List[str]:
        """Extract deadline information from document"""
        try:
            import re
            deadlines = []
            
            # Look for date patterns
            date_patterns = [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',  # DD/MM/YYYY or DD-MM-YYYY
                r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD or YYYY-MM-DD
                r'\d{1,2}\s+\w+\s+\d{4}',       # DD Month YYYY
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, text)
                deadlines.extend(matches)
            
            # Remove duplicates and limit
            return list(set(deadlines))[:5]
            
        except Exception:
            return []
    
    async def generate_response(
        self,
        file: UploadFile,
        user: Dict[str, Any]
    ) -> ResponseGenerationResult:
        """Generate RAG-powered tender response"""
        start_time = datetime.now()
        
        try:
            # Initialize AI components
            await self._initialize_components()
            
            # Validate file upload
            FileValidator.validate_file_upload(file)
            
            # Create secure temporary file
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=Path(file.filename).suffix,
                dir=settings.uploads_dir / "temp"
            ) as temp_file:
                
                # Read and save file securely
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                logger.info(
                    "Starting RAG response generation",
                    extra={
                        "filename": file.filename,
                        "file_size": len(content),
                        "user_id": user.get("user_id")
                    }
                )
                
                # Process document
                chunks = await self.document_processor.process_document(
                    temp_file_path, 
                    Path(file.filename).suffix
                )
                
                # Extract text for processing
                full_text = "\n\n".join([chunk[1] for chunk in chunks])
                
                # Generate tender summary
                tender_summary = await self.response_generator.generate_tender_summary(full_text)
                
                # Search for similar chunks in vector store
                similar_chunks = await self.vector_store.search_similar_chunks(
                    full_text[:2000],  # Use first 2000 chars for similarity search
                    top_k=10,
                    user_id=user.get("user_id")
                )
                
                # Format context from similar chunks
                context = await self.response_generator.format_context_chunks(similar_chunks)
                
                # Load company profile (placeholder - should be from database/file)
                company_profile = """
                Topaza International est une entreprise de conseil spécialisée dans l'accompagnement 
                de projets de développement. Nous proposons une approche sur mesure, une expertise 
                sectorielle reconnue, des méthodologies éprouvées et un suivi rigoureux pour 
                garantir des résultats tangibles.
                """
                
                # Define response sections
                sections_config = [
                    {
                        "title": "1. Introduction, Objectifs et Démarche",
                        "requirements": """
                        Développez une introduction complète avec :
                        - Présentation détaillée de Topaza et ses valeurs
                        - Analyse des objectifs de la mission
                        - Démarche proposée structurée
                        - Compréhension des enjeux du projet
                        """
                    },
                    {
                        "title": "2. Méthodologie et Livrables", 
                        "requirements": """
                        Développez la méthodologie avec :
                        - Approche structurée en phases détaillées
                        - Description de chaque phase avec activités et outils
                        - Livrables détaillés pour chaque phase
                        - Planning et chronogramme
                        - Méthodes de suivi et d'évaluation
                        """
                    },
                    {
                        "title": "3. Risques, Équipe et Conclusion",
                        "requirements": """
                        Inclure obligatoirement :
                        - Tableau de gestion des risques avec colonnes : FACTEURS | Probabilité(/5) | Gravité(/5) | Criticité % | Eval. | Mesure(s)
                        - Tableau d'équipe avec colonnes : Nom et Prénom | Poste | Compétences | Expérience
                        - Conclusion professionnelle avec contacts Topaza
                        """
                    }
                ]
                
                # Generate each section
                generated_sections = []
                all_content = []
                
                for section_config in sections_config:
                    logger.info(f"Generating section: {section_config['title']}")
                    
                    section_content = await self.response_generator.generate_section(
                        tender_summary=tender_summary,
                        context=context,
                        company_profile=company_profile,
                        section_title=section_config["title"],
                        section_requirements=section_config["requirements"]
                    )
                    
                    generated_sections.append({
                        "title": section_config["title"],
                        "content": section_content
                    })
                    
                    all_content.append(f"# {section_config['title']}\n\n{section_content}")
                
                # Combine all sections
                final_content = "\n\n".join(all_content)
                
                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                base_name = Path(file.filename).stem
                response_filename = f"reponse_topaza_{timestamp}_{base_name}.docx"
                
                # Save to Word document
                response_path = await self.response_generator.save_to_docx(
                    content=final_content,
                    filename=response_filename,
                    output_dir=str(settings.data_dir / "ai_responses")
                )
                
                generation_time = (datetime.now() - start_time).total_seconds()
                
                result = ResponseGenerationResult(
                    response_file=FileInfo(
                        name=response_filename,
                        path=response_path,
                        size=os.path.getsize(response_path),
                        created_at=datetime.now()
                    ),
                    sections=generated_sections,
                    generation_time=generation_time,
                    model_used=self.response_generator.model
                )
                
                logger.info(f"RAG response generation completed in {generation_time:.2f}s")
                return result
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    logger.warning(f"Failed to delete temporary file: {temp_file_path}")
                
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            raise AIProcessingException(f"Response generation failed: {str(e)}")
    
    async def process_chat(
        self,
        request: ChatRequest,
        user: Dict[str, Any]
    ) -> ChatResponse:
        """Process RAG-powered chat/Q&A request"""
        start_time = datetime.now()
        
        try:
            # Initialize AI components
            await self._initialize_components()
            
            # Validate document path if provided
            document_text = ""
            if request.document_path:
                PathValidator.validate_file_path(
                    request.document_path,
                    settings.uploads_dir
                )
                # Load document text (simplified - in production, store processed docs)
                with open(request.document_path, 'r', encoding='utf-8') as f:
                    document_text = f.read()
            elif request.context:
                document_text = request.context
            
            logger.info(
                "Processing RAG chat request",
                extra={
                    "question_length": len(request.question),
                    "has_document": bool(document_text),
                    "user_id": user.get("user_id")
                }
            )
            
            # Search for relevant chunks if no specific document provided
            relevant_chunks = []
            if not document_text:
                relevant_chunks = await self.vector_store.search_similar_chunks(
                    request.question,
                    top_k=5,
                    user_id=user.get("user_id")
                )
                # Use chunks as context
                document_text = "\n\n".join([chunk["content"] for chunk in relevant_chunks])
            
            # Process question with document context
            answer = await self._process_question_with_context(
                request.question,
                document_text,
                user.get("user_id")
            )
            
            # Determine confidence based on context availability
            confidence = 0.8 if document_text else 0.3
            
            # Extract sources
            sources = []
            if relevant_chunks:
                sources = list(set([chunk.get("filename", "Unknown") for chunk in relevant_chunks[:3]]))
            elif request.document_path:
                sources = [Path(request.document_path).name]
            else:
                sources = ["General Knowledge"]
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            response = ChatResponse(
                answer=answer,
                confidence=confidence,
                sources=sources,
                processing_time=processing_time,
                model_used=self.response_generator.model
            )
            
            logger.info(f"Chat request processed in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Chat processing failed: {str(e)}")
            raise AIProcessingException(f"Chat processing failed: {str(e)}")
    
    async def _process_question_with_context(
        self,
        question: str,
        document_text: str,
        user_id: Optional[str] = None
    ) -> str:
        """Process question with document context using chunking"""
        try:
            import tiktoken
            
            # Chunk document if too large
            encoding = tiktoken.encoding_for_model("gpt-4")
            max_chunk_size = 4000
            overlap = 200
            
            if len(encoding.encode(document_text)) <= max_chunk_size:
                chunks = [document_text]
            else:
                # Split into chunks
                tokens = encoding.encode(document_text)
                chunks = []
                i = 0
                
                while i < len(tokens):
                    end = min(i + max_chunk_size, len(tokens))
                    chunk_tokens = tokens[i:end]
                    chunk_text = encoding.decode(chunk_tokens)
                    chunks.append(chunk_text)
                    i = end - overlap if end < len(tokens) else end
            
            # Process each chunk
            all_responses = []
            system_prompt = """
            Vous êtes un assistant spécialisé dans l'analyse d'appels d'offres pour l'entreprise Topaza.
            Votre rôle est de répondre aux questions concernant UNIQUEMENT le contenu fourni.
            
            Directives:
            1. Répondez UNIQUEMENT en vous basant sur les informations présentes dans le document.
            2. Répondez de manière précise et concise.
            3. Si l'information n'est pas présente, indiquez clairement qu'elle n'est pas mentionnée.
            4. Ne faites pas de suppositions non soutenues par le texte.
            5. Citez les sections pertinentes lorsque c'est approprié.
            """
            
            for i, chunk in enumerate(chunks):
                chunk_indicator = f"[Partie {i+1}/{len(chunks)}]" if len(chunks) > 1 else ""
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"""
                    {chunk_indicator}
                    
                    DOCUMENT:
                    {chunk}
                    
                    QUESTION: {question}
                    
                    Répondez à cette question en vous basant UNIQUEMENT sur les informations du document ci-dessus.
                    """}
                ]
                
                response = self.response_generator.openai_client.chat.completions.create(
                    model=self.response_generator.model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1000
                )
                
                chunk_response = response.choices[0].message.content.strip()
                all_responses.append(chunk_response)
            
            # Synthesize responses if multiple chunks
            if len(all_responses) > 1:
                synthesis_prompt = f"""
                Vous avez analysé un document en plusieurs parties et répondu à la question: "{question}"
                
                Voici vos réponses pour chaque partie:
                
                {' '.join([f"PARTIE {i+1}: {resp}" for i, resp in enumerate(all_responses)])}
                
                Veuillez synthétiser ces réponses en une seule réponse cohérente et complète.
                Si les différentes parties contiennent des informations contradictoires, mentionnez-le.
                Si certaines parties ne contiennent pas d'information pertinente, concentrez-vous sur celles qui en contiennent.
                """
                
                synthesis_response = self.response_generator.openai_client.chat.completions.create(
                    model=self.response_generator.model,
                    messages=[
                        {"role": "system", "content": "Vous êtes un assistant spécialisé dans la synthèse d'informations."},
                        {"role": "user", "content": synthesis_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )
                
                return synthesis_response.choices[0].message.content.strip()
            else:
                return all_responses[0]
                
        except Exception as e:
            logger.error(f"Question processing failed: {str(e)}")
            return f"Désolé, une erreur s'est produite lors du traitement de votre question: {str(e)}"
    
    async def get_generated_files(self, user: Dict[str, Any]) -> List[FileInfo]:
        """Get list of generated files for user"""
        try:
            files = []
            ai_responses_dir = settings.data_dir / "ai_responses"
            
            if ai_responses_dir.exists():
                for file_path in ai_responses_dir.glob("*.docx"):
                    # Filter by user if needed (implement user-specific files)
                    stat = file_path.stat()
                    files.append(FileInfo(
                        name=file_path.name,
                        path=str(file_path),
                        size=stat.st_size,
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                        modified_at=datetime.fromtimestamp(stat.st_mtime)
                    ))
            
            # Sort by creation time (newest first)
            files.sort(key=lambda x: x.created_at, reverse=True)
            
            logger.info(
                "Retrieved generated files",
                extra={
                    "file_count": len(files),
                    "user_id": user.get("user_id")
                }
            )
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to get generated files: {str(e)}")
            raise AIProcessingException(f"Failed to get generated files: {str(e)}")
    
    async def generate_configured_report(
        self,
        file: UploadFile,
        request: AIReportRequest,
        user: Dict[str, Any]
    ) -> ReportGenerationResponse:
        """Generate report with frontend configuration options"""
        start_time = datetime.now()
        
        try:
            # Initialize AI components
            await self._initialize_components()
            
            # Validate file upload
            FileValidator.validate_file_upload(file)
            
            # Create secure temporary file
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=Path(file.filename).suffix,
                dir=settings.uploads_dir / "temp"
            ) as temp_file:
                
                # Read and save file securely
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                logger.info(
                    "Starting configured report generation",
                    extra={
                        "filename": file.filename,
                        "report_type": request.configuration.report_type.value,
                        "tone": request.configuration.tone.value,
                        "length": request.configuration.length.value,
                        "user_id": user.get("user_id")
                    }
                )
                
                # Process document
                chunks = await self.document_processor.process_document(
                    temp_file_path, 
                    Path(file.filename).suffix
                )
                
                # Extract text for processing
                full_text = "\n\n".join([chunk[1] for chunk in chunks])
                
                # Generate report with configuration
                report_content = await self._generate_configured_content(
                    full_text=full_text,
                    config=request.configuration,
                    user=user,
                    tender_id=request.tender_id
                )
                
                # Generate filename with configuration
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                base_name = Path(file.filename).stem
                report_type = request.configuration.report_type.value
                report_filename = f"{report_type}_topaza_{timestamp}_{base_name}.docx"
                
                # Save to Word document
                response_path = await self.response_generator.save_to_docx(
                    content=report_content,
                    filename=report_filename,
                    output_dir=str(settings.data_dir / "ai_responses")
                )
                
                generation_time = (datetime.now() - start_time).total_seconds()
                
                # Generate report ID
                report_id = f"rpt_{timestamp}_{base_name}_{report_type}"
                
                # Calculate word count and page estimate
                word_count = len(report_content.split())
                page_count = max(1, word_count // 250)  # Estimate 250 words per page
                
                # Create response
                result = ReportGenerationResponse(
                    report_id=report_id,
                    status="completed",
                    download_url=f"/api/v1/ai/download/{report_filename}",
                    preview_content=report_content[:500] + "..." if len(report_content) > 500 else report_content,
                    metadata={
                        "report_type": request.configuration.report_type.value,
                        "tone": request.configuration.tone.value,
                        "length": request.configuration.length.value,
                        "custom_instructions": request.configuration.custom_instructions,
                        "tender_id": request.tender_id,
                        "filename": report_filename
                    },
                    generation_time=generation_time,
                    word_count=word_count,
                    page_count=page_count
                )
                
                logger.info(f"Configured report generation completed in {generation_time:.2f}s")
                return result
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    logger.warning(f"Failed to delete temporary file: {temp_file_path}")
                
        except Exception as e:
            logger.error(f"Configured report generation failed: {str(e)}")
            raise AIProcessingException(f"Configured report generation failed: {str(e)}")
    
    async def _generate_configured_content(
        self,
        full_text: str,
        config,
        user: Dict[str, Any],
        tender_id: Optional[str] = None
    ) -> str:
        """Generate content based on configuration"""
        
        # Generate tender summary
        tender_summary = await self.response_generator.generate_tender_summary(full_text)
        
        # Search for similar chunks in vector store
        similar_chunks = await self.vector_store.search_similar_chunks(
            full_text[:2000],
            top_k=10,
            user_id=user.get("user_id")
        )
        
        # Format context
        context = await self.response_generator.format_context_chunks(similar_chunks)
        
        # Load company profile
        company_profile = """
        Topaza International est une entreprise de conseil spécialisée dans l'accompagnement 
        de projets de développement. Nous proposons une approche sur mesure, une expertise 
        sectorielle reconnue, des méthodologies éprouvées et un suivi rigoureux pour 
        garantir des résultats tangibles.
        """
        
        # Configure sections based on report type and length
        sections_config = self._get_sections_config(config)
        
        # Generate each section with configuration
        generated_sections = []
        all_content = []
        
        for section_config in sections_config:
            logger.info(f"Generating section: {section_config['title']}")
            
            # Add configuration-specific instructions
            enhanced_requirements = self._enhance_section_requirements(
                section_config["requirements"],
                config
            )
            
            section_content = await self.response_generator.generate_section(
                tender_summary=tender_summary,
                context=context,
                company_profile=company_profile,
                section_title=section_config["title"],
                section_requirements=enhanced_requirements
            )
            
            generated_sections.append({
                "title": section_config["title"],
                "content": section_content
            })
            
            all_content.append(f"# {section_config['title']}\n\n{section_content}")
        
        # Add configuration note
        config_note = f"\n\n---\n\n*Rapport généré selon la configuration: {config.report_type.value.title()} | Ton: {config.tone.value} | Longueur: {config.length.value}*"
        if config.custom_instructions:
            config_note += f"\n*Instructions personnalisées: {config.custom_instructions}*"
        
        # Combine all sections
        final_content = "\n\n".join(all_content) + config_note
        
        return final_content
    
    def _get_sections_config(self, config) -> List[Dict[str, str]]:
        """Get sections configuration based on report type and length"""
        
        if config.report_type == ReportType.PROPOSAL:
            sections = [
                {
                    "title": "1. Proposition Technique et Méthodologique",
                    "requirements": "Développez une proposition technique détaillée avec méthodologie, approche et livrables."
                },
                {
                    "title": "2. Équipe et Capacités",
                    "requirements": "Présentez l'équipe projet, les compétences et l'expérience de Topaza."
                }
            ]
            
            if config.length in [ReportLength.DETAILED, ReportLength.COMPREHENSIVE]:
                sections.append({
                    "title": "3. Planning et Gestion des Risques",
                    "requirements": "Détaillez le planning, la gestion des risques et les mesures d'assurance qualité."
                })
                
        elif config.report_type == ReportType.ANALYSIS:
            sections = [
                {
                    "title": "1. Analyse du Marché et du Contexte",
                    "requirements": "Analysez le marché, le contexte sectoriel et les enjeux identifiés."
                },
                {
                    "title": "2. Évaluation des Opportunités",
                    "requirements": "Évaluez les opportunités, les défis et les recommandations stratégiques."
                }
            ]
            
        else:  # SUMMARY
            sections = [
                {
                    "title": "1. Résumé Exécutif",
                    "requirements": "Fournissez un résumé exécutif concis avec les points clés et recommandations."
                }
            ]
            
            if config.length != ReportLength.BRIEF:
                sections.append({
                    "title": "2. Points d'Action",
                    "requirements": "Détaillez les points d'action et prochaines étapes recommandées."
                })
        
        return sections
    
    def _enhance_section_requirements(self, base_requirements: str, config) -> str:
        """Enhance section requirements based on configuration"""
        
        # Add tone-specific instructions
        tone_instructions = {
            ReportTone.PROFESSIONAL: "Adoptez un ton professionnel et formel, en utilisant un vocabulaire métier approprié.",
            ReportTone.TECHNICAL: "Utilisez un langage technique précis avec des détails spécialisés et des références méthodologiques.",
            ReportTone.PERSUASIVE: "Adoptez un ton persuasif et convaincant, en mettant l'accent sur les avantages et la valeur ajoutée."
        }
        
        # Add length-specific instructions  
        length_instructions = {
            ReportLength.BRIEF: "Soyez concis et allez à l'essentiel. Limitez-vous aux points les plus importants.",
            ReportLength.DETAILED: "Développez les points importants avec des détails appropriés et des exemples.",
            ReportLength.COMPREHENSIVE: "Fournissez une analyse complète et approfondie avec tous les détails pertinents."
        }
        
        enhanced = base_requirements
        enhanced += f"\n\nTon requis: {tone_instructions.get(config.tone, '')}"
        enhanced += f"\nNiveau de détail: {length_instructions.get(config.length, '')}"
        
        if config.custom_instructions:
            enhanced += f"\n\nInstructions spécifiques: {config.custom_instructions}"
        
        return enhanced


# Service instance
ai_service = AIService()


@router.get("/status")
async def get_ai_status():
    """Get AI service status and capabilities"""
    try:
        # Initialize components to check if they work
        await ai_service._initialize_components()
        
        # Get vector store stats
        stats = await ai_service.vector_store.get_collection_stats()
        
        return {
            "status": "healthy",
            "vector_store": stats,
            "models": {
                "embedding": "text-embedding-3-large",
                "generation": "gpt-4-turbo"
            },
            "capabilities": [
                "document_analysis",
                "response_generation", 
                "chat_qa",
                "tender_analysis"
            ]
        }
    except Exception as e:
        logger.error(f"AI status check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.post("/analyze", response_model=DocumentAnalysisResult)
async def analyze_document(
    request: DocumentAnalysisRequest = Depends(),
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Analyze uploaded document
    
    Secure replacement for document analysis functionality
    """
    return await ai_service.analyze_document(file, request, current_user)


@router.post("/generate", response_model=ResponseGenerationResult)
async def generate_response(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate AI response for uploaded tender document
    
    Secure replacement for:
    - /api/ai/generate
    """
    return await ai_service.generate_response(file, current_user)


@router.post("/generate-report", response_model=ReportGenerationResponse)
async def generate_ai_report(
    request: AIReportRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
) -> ReportGenerationResponse:
    """
    Generate intelligent AI report based on tender data with frontend configuration
    This endpoint matches exactly what the frontend expects - no file upload required
    """
    try:
        start_time = datetime.now()
        
        # Initialize AI service
        ai_service = AIService()
        await ai_service._initialize_components()
        
        user_id = current_user.get("user_id", "anonymous") if current_user else "anonymous"
        logger.info(f"Generating {request.length} {request.reportType} report for tender {request.tenderId} (user: {user_id})")
        
        # Get tender data from Supabase
        from core.database.supabase_client import supabase_manager
        
        # Try to fetch tender data
        tender_data = {}
        try:
            supabase_client = supabase_manager.get_client()
            response = supabase_client.table('tenders').select('*').eq('id', request.tenderId).single().execute()
            if response.data:
                tender_data = response.data
                logger.info(f"Found tender data: {tender_data.get('title', 'Unknown')}")
            else:
                logger.warning(f"No tender found with ID {request.tenderId}, using placeholder data")
                tender_data = {
                    "id": request.tenderId,
                    "title": f"Tender {request.tenderId}",
                    "description": "Tender description not available",
                    "organization": "Organization not specified",
                    "country": "Country not specified",
                    "deadline": "Deadline not specified",
                    "reference": request.tenderId
                }
        except Exception as e:
            logger.warning(f"Could not fetch tender data: {str(e)}, using placeholder")
            tender_data = {
                "id": request.tenderId,
                "title": f"Tender {request.tenderId}",
                "description": "Tender description not available",
                "organization": "Organization not specified", 
                "country": "Country not specified",
                "deadline": "Deadline not specified",
                "reference": request.tenderId
            }
        
        # Get RAG context if available
        rag_context = []
        try:
            if hasattr(ai_service, 'vector_store') and ai_service.vector_store:
                # Search for relevant context based on tender title and description
                search_query = f"{tender_data.get('title', '')} {tender_data.get('description', '')}"[:200]
                if search_query.strip():
                    similar_chunks = await ai_service.vector_store.similarity_search(
                        query=search_query,
                        k=5
                    )
                    rag_context = [chunk.get('content', '') for chunk in similar_chunks if chunk.get('content')]
                    logger.info(f"Retrieved {len(rag_context)} RAG context chunks")
        except Exception as e:
            logger.warning(f"Could not retrieve RAG context: {str(e)}")
        
        # Generate the report using our enhanced generator
        report_content = await ai_service.response_generator.generate_intelligent_report(
            tender_data=tender_data,
            report_type=request.reportType.value,
            tone=request.tone.value,
            length=request.length.value,
            custom_instructions=request.customInstructions,
            rag_context=rag_context
        )
        
        # Calculate metadata
        generation_time = (datetime.now() - start_time).total_seconds()
        word_count = len(report_content.split())
        sections_count = len([line for line in report_content.split('\n') if line.strip().startswith('##')])
        page_count = max(1, word_count // 400)  # Estimate 400 words per page
        
        # Generate unique report ID
        report_id = f"rpt_{request.tenderId}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save report to file system for download
        reports_dir = settings.data_dir / "ai_responses"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_filename = f"{report_id}.md"
        report_path = reports_dir / report_filename
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            download_url = f"/api/v1/ai/download/{report_filename}"
            logger.info(f"Report saved to {report_path}")
        except Exception as e:
            logger.error(f"Could not save report file: {str(e)}")
            download_url = None
        
        # Create response
        response = ReportGenerationResponse(
            report_id=report_id,
            status="completed",
            content=report_content,
            download_url=download_url,
            metadata={
                "tender_id": request.tenderId,
                "report_type": request.reportType.value,
                "tone": request.tone.value,
                "length": request.length.value,
                "custom_instructions": request.customInstructions,
                "rag_chunks_used": len(rag_context),
                "generated_at": datetime.now().isoformat()
            },
            generation_time=generation_time,
            word_count=word_count,
            page_count=page_count,
            sections_count=sections_count
        )
        
        logger.info(f"Report generation completed: {word_count} words, {sections_count} sections, {generation_time:.2f}s")
        
        # Debug: Log what we're returning to frontend
        logger.info(f"Returning response with content length: {len(report_content)}")
        logger.info(f"Response structure: report_id={response.report_id}, status={response.status}, has_content={bool(response.content)}")
        
        return response
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        error_report_id = f"err_{request.tenderId}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return ReportGenerationResponse(
            report_id=error_report_id,
            status="failed",
            content=f"# Erreur de Génération\n\nUne erreur s'est produite lors de la génération du rapport.\n\n**Erreur:** {str(e)}\n\nVeuillez réessayer ou contacter le support technique.",
            download_url=None,
            metadata={
                "error": str(e),
                "tender_id": request.tenderId,
                "failed_at": datetime.now().isoformat()
            },
            generation_time=0.0,
            word_count=0,
            page_count=0,
            sections_count=0
        )


@router.post("/chat", response_model=ChatResponse)
async def process_chat(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process Q&A with document context
    
    Secure replacement for:
    - /api/ai/chat
    """
    return await ai_service.process_chat(request, current_user)


@router.get("/generated-files", response_model=GeneratedFilesResponse)
async def get_generated_files(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get list of generated AI response files
    
    Secure replacement for:
    - /api/ai/generated-files
    """
    try:
        files = await ai_service.get_generated_files(current_user)
        
        return GeneratedFilesResponse(
            status="success",
            files=files,
            total_files=len(files),
            message="Generated files retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get generated files: {str(e)}")
        raise AIProcessingException(f"Failed to get generated files: {str(e)}")


@router.get("/download/{filename}")
async def download_file(
    filename: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Download generated AI response file
    
    Secure replacement for file download functionality
    """
    try:
        # Sanitize filename
        secure_filename = FileValidator.sanitize_filename(filename)
        if not secure_filename:
            raise SecurityException("Invalid filename")
        
        # Validate file path
        file_path = PathValidator.validate_file_path(
            secure_filename,
            settings.data_dir / "ai_responses"
        )
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        logger.info(
            "File download requested",
            extra={
                "filename": secure_filename,
                "user_id": current_user.get("user_id")
            }
        )
        
        return FileResponse(
            path=str(file_path),
            filename=secure_filename,
            media_type="application/octet-stream"
        )
        
    except Exception as e:
        logger.error(f"File download failed: {str(e)}")
        raise AIProcessingException(f"File download failed: {str(e)}")


# Add missing import
from datetime import datetime