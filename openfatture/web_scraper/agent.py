"""Regulatory Update Agent with ReAct orchestration."""

import json
from typing import Any

import structlog

from ..ai.domain.context import ChatContext
from ..ai.orchestration.react import ReActOrchestrator
from ..ai.providers import BaseLLMProvider
from ..ai.tools.registry import ToolRegistry
from .config import WebScraperConfig
from .extractor import ContentExtractor
from .models import RegulatoryDocument, RegulatorySource
from .scraper import RegulatoryWebScraper

logger = structlog.get_logger(__name__)


class RegulatoryUpdateAgent:
    """AI agent for orchestrating regulatory updates using ReAct pattern.

    This agent coordinates the entire regulatory update workflow:
    - Scraping regulatory sources
    - Content extraction and analysis
    - Change detection and validation
    - Knowledge base updates
    - Compliance verification

    Uses ReAct (Reasoning + Acting) orchestration for complex multi-step processes.
    """

    def __init__(
        self,
        config: WebScraperConfig,
        scraper: RegulatoryWebScraper,
        extractor: ContentExtractor,
        llm_provider: BaseLLMProvider,
    ):
        """Initialize regulatory update agent.

        Args:
            config: Web scraper configuration
            scraper: Web scraper instance
            extractor: Content extractor instance
            llm_provider: LLM provider for orchestration
        """
        self.config = config
        self.scraper = scraper
        self.extractor = extractor

        # Initialize tool registry and register regulatory tools
        self.tool_registry = ToolRegistry()
        self._register_regulatory_tools()

        # Initialize ReAct orchestrator with deterministic settings for regulatory work
        self.orchestrator = ReActOrchestrator(
            provider=llm_provider,
            tool_registry=self.tool_registry,
            max_iterations=8,  # Allow complex regulatory analysis
        )

        logger.info("regulatory_update_agent_initialized")

    def _register_regulatory_tools(self) -> None:
        """Register regulatory-specific tools in the tool registry."""
        from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType

        # Tool for scraping web pages
        scrape_tool = Tool(
            name="scrape_web_page",
            description="Scrape content from a regulatory web page",
            category="web_scraping",
            parameters=[
                ToolParameter(
                    name="url",
                    type=ToolParameterType.STRING,
                    description="URL to scrape",
                    required=True,
                ),
                ToolParameter(
                    name="selectors",
                    type=ToolParameterType.OBJECT,
                    description="CSS selectors for content extraction",
                    required=False,
                ),
            ],
            func=self._tool_scrape_web_page,
            examples=["Scrape the main content from https://agenziaentrate.gov.it"],
        )

        # Tool for extracting entities from content
        extract_tool = Tool(
            name="extract_entities",
            description="Extract regulatory entities from content",
            category="content_analysis",
            parameters=[
                ToolParameter(
                    name="content",
                    type=ToolParameterType.STRING,
                    description="Content to analyze",
                    required=True,
                ),
                ToolParameter(
                    name="entity_types",
                    type=ToolParameterType.ARRAY,
                    description="Types of entities to extract",
                    required=False,
                ),
            ],
            func=self._tool_extract_entities,
            examples=["Extract dates and amounts from this regulatory text"],
        )

        # Tool for comparing content versions
        compare_tool = Tool(
            name="compare_content",
            description="Compare two versions of regulatory content",
            category="content_analysis",
            parameters=[
                ToolParameter(
                    name="old_content",
                    type=ToolParameterType.STRING,
                    description="Previous content",
                    required=True,
                ),
                ToolParameter(
                    name="new_content",
                    type=ToolParameterType.STRING,
                    description="New content",
                    required=True,
                ),
            ],
            func=self._tool_compare_content,
            examples=["Compare old and new versions of IVA regulations"],
        )

        # Tool for assessing business impact
        impact_tool = Tool(
            name="assess_impact",
            description="Assess the business impact of regulatory changes",
            category="impact_analysis",
            parameters=[
                ToolParameter(
                    name="changes",
                    type=ToolParameterType.STRING,
                    description="Description of changes",
                    required=True,
                ),
                ToolParameter(
                    name="business_context",
                    type=ToolParameterType.STRING,
                    description="Business context",
                    required=False,
                ),
            ],
            func=self._tool_assess_impact,
            examples=["Assess impact of new IVA rules on our business"],
        )

        # Register tools
        self.tool_registry.register(scrape_tool)
        self.tool_registry.register(extract_tool)
        self.tool_registry.register(compare_tool)
        self.tool_registry.register(impact_tool)

        logger.info("regulatory_tools_registered", tool_count=4)

    async def _tool_scrape_web_page(
        self, url: str, selectors: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """Tool for scraping web pages."""
        try:
            # Use the scraper to get content
            async with self.scraper:
                # Create a temporary source for scraping
                from .models import ContentType, RegulatorySource

                temp_source = RegulatorySource(
                    id="temp_scrape",
                    name="Temporary Scrape",
                    url=url,
                    content_type=ContentType.HTML,
                    selectors=selectors or {},
                )

                documents = await self.scraper.scrape_source(temp_source)

                if documents:
                    doc = documents[0]
                    return {
                        "success": True,
                        "content": doc.content[:2000],  # Limit content length
                        "title": doc.title,
                        "url": doc.url,
                    }
                else:
                    return {"success": False, "error": "No content extracted"}

        except Exception as e:
            logger.error("tool_scrape_web_page_failed", url=url, error=str(e))
            return {"success": False, "error": str(e)}

    async def _tool_extract_entities(
        self, content: str, entity_types: list[str] | None = None
    ) -> dict[str, Any]:
        """Tool for extracting entities from content."""
        try:
            # Use the extractor to get entities
            entities = await self.extractor._extract_entities(content, "IT")

            # Filter by requested entity types if specified
            if entity_types:
                filtered_entities = {}
                for entity_type in entity_types:
                    if entity_type in entities:
                        filtered_entities[entity_type] = entities[entity_type]
                entities = filtered_entities

            return {"success": True, "entities": entities}

        except Exception as e:
            logger.error("tool_extract_entities_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def _tool_compare_content(self, old_content: str, new_content: str) -> dict[str, Any]:
        """Tool for comparing content versions."""
        try:
            # Simple text similarity comparison
            import re
            from difflib import SequenceMatcher

            # Clean content for comparison
            def clean_text(text: str) -> str:
                text = re.sub(r"\s+", " ", text.lower())
                return text.strip()

            old_clean = clean_text(old_content)
            new_clean = clean_text(new_content)

            # Calculate similarity
            similarity = SequenceMatcher(None, old_clean, new_clean).ratio()

            # Find differences
            diff = list(SequenceMatcher(None, old_clean, new_clean).get_opcodes())

            changes = []
            for tag, i1, i2, j1, j2 in diff:
                if tag != "equal":
                    changes.append(
                        {
                            "type": tag,
                            "old_text": old_clean[i1:i2][:200] if i1 < i2 else "",
                            "new_text": new_clean[j1:j2][:200] if j1 < j2 else "",
                        }
                    )

            return {
                "success": True,
                "similarity": similarity,
                "changes_detected": len([c for c in changes if c["type"] != "equal"]),
                "changes": changes[:10],  # Limit changes
            }

        except Exception as e:
            logger.error("tool_compare_content_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def _tool_assess_impact(self, changes: str, business_context: str = "") -> dict[str, Any]:
        """Tool for assessing business impact."""
        try:
            # Use the extractor to assess impact
            impact = await self.extractor._assess_impact(changes, "regulatory")

            # Simple impact classification
            impact_lower = impact.lower()
            if "critic" in impact_lower:
                level = "critical"
                urgency = "high"
            elif "alto" in impact_lower or "high" in impact_lower:
                level = "high"
                urgency = "medium"
            elif "medio" in impact_lower or "medium" in impact_lower:
                level = "medium"
                urgency = "low"
            else:
                level = "low"
                urgency = "low"

            return {
                "success": True,
                "impact_level": level,
                "urgency": urgency,
                "assessment": impact,
                "business_context": business_context,
            }

        except Exception as e:
            logger.error("tool_assess_impact_failed", error=str(e))
            return {"success": False, "error": str(e)}

    async def process_source_updates(self, source: RegulatorySource) -> dict[str, Any]:
        """Process updates for a regulatory source using ReAct orchestration.

        Args:
            source: Regulatory source to process

        Returns:
            Processing results with status and documents
        """
        logger.info("processing_source_updates", source_id=source.id, url=source.url)

        # Build context for ReAct orchestration
        context = ChatContext(
            user_input=self._build_processing_prompt(source),
            metadata={
                "source": source.model_dump(),
                "config": {
                    "require_human_review": self.config.require_human_review,
                    "auto_update_threshold": self.config.auto_update_threshold,
                    "similarity_threshold": self.config.similarity_threshold,
                },
            },
        )

        try:
            # Execute ReAct orchestration
            response = await self.orchestrator.execute(context)

            # Parse orchestration results
            results = self._parse_orchestration_results(response)

            logger.info(
                "source_processing_completed",
                source_id=source.id,
                documents_processed=results.get("documents_processed", 0),
                changes_detected=results.get("changes_detected", 0),
            )

            return results

        except Exception as e:
            logger.error("source_processing_failed", source_id=source.id, error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "documents_processed": 0,
                "changes_detected": 0,
            }

    async def validate_regulatory_changes(
        self, documents: list[RegulatoryDocument]
    ) -> dict[str, Any]:
        """Validate regulatory changes using AI analysis.

        Args:
            documents: Documents with detected changes

        Returns:
            Validation results
        """
        logger.info("validating_regulatory_changes", document_count=len(documents))

        validation_results = {
            "total_documents": len(documents),
            "approved": 0,
            "rejected": 0,
            "requires_review": 0,
            "validations": [],
        }

        for doc in documents:
            try:
                # Use ReAct for validation orchestration
                context = ChatContext(
                    user_input=self._build_validation_prompt(doc),
                    metadata={
                        "document": {
                            "id": doc.id,
                            "title": doc.title,
                            "content_hash": doc.content_hash,
                            "change_confidence": doc.change_confidence,
                        },
                        "config": {
                            "auto_update_threshold": self.config.auto_update_threshold,
                            "require_human_review": self.config.require_human_review,
                        },
                    },
                )

                response = await self.orchestrator.execute(context)
                validation = self._parse_validation_results(response)

                validation_results["validations"].append(
                    {
                        "document_id": doc.id,
                        "decision": validation.get("decision", "review"),
                        "confidence": validation.get("confidence", 0.0),
                        "reasoning": validation.get("reasoning", ""),
                    }
                )

                # Update counters
                decision = validation.get("decision", "review")
                if decision == "approved":
                    validation_results["approved"] += 1
                elif decision == "rejected":
                    validation_results["rejected"] += 1
                else:
                    validation_results["requires_review"] += 1

            except Exception as e:
                logger.warning("validation_failed", document_id=doc.id, error=str(e))
                validation_results["validations"].append(
                    {
                        "document_id": doc.id,
                        "decision": "review",
                        "confidence": 0.0,
                        "reasoning": f"Validation error: {str(e)}",
                    }
                )
                validation_results["requires_review"] += 1

        logger.info(
            "validation_completed",
            approved=validation_results["approved"],
            rejected=validation_results["rejected"],
            requires_review=validation_results["requires_review"],
        )

        return validation_results

    def _get_available_tools(self) -> list[dict[str, Any]]:
        """Get available tools for ReAct orchestration."""
        return [
            {
                "name": "scrape_web_page",
                "description": "Scrape content from a regulatory web page",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to scrape"},
                        "selectors": {
                            "type": "object",
                            "description": "CSS selectors for content extraction",
                        },
                    },
                    "required": ["url"],
                },
            },
            {
                "name": "extract_entities",
                "description": "Extract regulatory entities from content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Content to analyze"},
                        "entity_types": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["content"],
                },
            },
            {
                "name": "compare_content",
                "description": "Compare two versions of regulatory content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "old_content": {"type": "string", "description": "Previous content"},
                        "new_content": {"type": "string", "description": "New content"},
                    },
                    "required": ["old_content", "new_content"],
                },
            },
            {
                "name": "assess_impact",
                "description": "Assess the business impact of regulatory changes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "changes": {"type": "string", "description": "Description of changes"},
                        "business_context": {"type": "string", "description": "Business context"},
                    },
                    "required": ["changes"],
                },
            },
        ]

    def _build_processing_prompt(self, source: RegulatorySource) -> str:
        """Build prompt for source processing orchestration."""
        return f"""Sei un agente AI specializzato nell'aggiornamento di normative fiscali italiane.

Devi elaborare gli aggiornamenti per la fonte normativa: {source.name}
URL: {source.url}
Categoria: {source.category}
Giurisdizione: {source.jurisdiction}

Obiettivo: Rilevare e analizzare eventuali cambiamenti normativi.

Passi da seguire:
1. Verifica se la fonte è accessibile e se il contenuto è cambiato
2. Estrai il contenuto aggiornato utilizzando i selettori appropriati
3. Confronta con la versione precedente (se disponibile)
4. Valuta l'impatto dei cambiamenti
5. Determina se gli aggiornamenti richiedono revisione umana

Utilizza gli strumenti disponibili per completare l'analisi. Sii preciso e metodico.

Fonte precedente aggiornata: {source.last_updated.isoformat() if source.last_updated else "Mai"}"""

    def _build_validation_prompt(self, document: RegulatoryDocument) -> str:
        """Build prompt for change validation."""
        return f"""Valida i seguenti cambiamenti normativi per determinare se possono essere applicati automaticamente.

Documento: {document.title}
Fonte: {document.source_name}
Categoria: {document.category}
Confidenza del cambiamento: {document.change_confidence:.2f}

Contenuto estratto:
{document.content[:1000]}{"..." if len(document.content) > 1000 else ""}

Valutazione dell'impatto:
{document.impact_assessment or "Non disponibile"}

Criteri di validazione:
- I cambiamenti sono puramente tecnici o amministrativi?
- Ci sono nuove scadenze o obblighi che richiedono attenzione immediata?
- I cambiamenti influenzano aliquote, soglie o calcoli?
- È necessaria una revisione legale prima dell'applicazione?

Decidi: approved (può essere applicato automaticamente), rejected (non applicare), review (richiede revisione umana)"""

    def _parse_orchestration_results(self, content: str) -> dict[str, Any]:
        """Parse ReAct orchestration results."""
        try:
            # Try to extract JSON from the response
            # Look for JSON blocks in the content
            import re

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())

            # Fallback: extract key information from text
            return {
                "status": "completed",
                "documents_processed": 1,
                "changes_detected": 1 if "cambiamento" in content.lower() else 0,
                "requires_review": "revisione" in content.lower() or "review" in content.lower(),
            }

        except Exception as e:
            logger.warning("failed_to_parse_orchestration_results", error=str(e))
            return {
                "status": "completed",
                "documents_processed": 1,
                "changes_detected": 0,
                "requires_review": True,
            }

    def _parse_validation_results(self, content: str) -> dict[str, Any]:
        """Parse validation results from ReAct response."""
        try:
            # Look for decision keywords
            content_lower = content.lower()

            if "approved" in content_lower or "approvato" in content_lower:
                decision = "approved"
                confidence = 0.8
            elif "rejected" in content_lower or "rifiutato" in content_lower:
                decision = "rejected"
                confidence = 0.9
            else:
                decision = "review"
                confidence = 0.5

            return {"decision": decision, "confidence": confidence, "reasoning": content[:500]}

        except Exception as e:
            logger.warning("failed_to_parse_validation_results", error=str(e))
            return {
                "decision": "review",
                "confidence": 0.0,
                "reasoning": "Errore nel parsing della validazione",
            }
