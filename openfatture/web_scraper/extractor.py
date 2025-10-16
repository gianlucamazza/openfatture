"""AI-powered content extractor for regulatory documents."""

import json
from typing import Any

import structlog

from ..ai.domain.message import Message, Role
from ..ai.providers import BaseLLMProvider
from .config import WebScraperConfig
from .models import RegulatoryDocument, RegulatorySource, UpdateStatus

logger = structlog.get_logger(__name__)


class ContentExtractor:
    """AI-powered content extractor for regulatory documents.

    Uses LLM to intelligently parse, classify, and structure regulatory content.
    Extracts entities, summarizes changes, and assesses impact.

    Features:
    - Entity extraction (dates, amounts, references)
    - Content classification and categorization
    - Change impact assessment
    - Regulatory compliance validation
    - Multi-language support (IT/EN)
    """

    def __init__(self, config: WebScraperConfig, llm_provider: BaseLLMProvider):
        """Initialize content extractor.

        Args:
            config: Web scraper configuration
            llm_provider: LLM provider for AI processing
        """
        self.config = config
        self.llm = llm_provider

        logger.info(
            "content_extractor_initialized",
            provider=llm_provider.provider_name,
            model=llm_provider.model,
        )

    async def extract_content(
        self, document: RegulatoryDocument, source: RegulatorySource
    ) -> RegulatoryDocument:
        """Extract and structure content from regulatory document.

        Args:
            document: Raw regulatory document
            source: Source configuration

        Returns:
            Enhanced document with extracted information
        """
        logger.info(
            "content_extraction_started",
            document_id=document.id,
            source_id=source.id,
            content_length=len(document.content),
        )

        try:
            # Extract entities and metadata
            entities = await self._extract_entities(document.content, source.jurisdiction)

            # Generate summary
            summary = await self._generate_summary(document.content, source.category)

            # Assess impact
            impact = await self._assess_impact(document.content, source.category)

            # Classify content
            classification = await self._classify_content(document.content)

            # Update document
            document.extracted_entities = entities
            document.summary = summary
            document.impact_assessment = impact
            document.status = UpdateStatus.EXTRACTING

            # Add classification to tags
            if classification and classification not in document.tags:
                document.tags.append(classification)

            logger.info(
                "content_extraction_completed",
                document_id=document.id,
                entities_count=len(entities) if entities else 0,
                summary_length=len(summary) if summary else 0,
            )

        except Exception as e:
            logger.error("content_extraction_failed", document_id=document.id, error=str(e))
            document.error_message = str(e)

        return document

    async def _extract_entities(self, content: str, jurisdiction: str) -> dict[str, Any]:
        """Extract entities from regulatory content using AI.

        Args:
            content: Document content
            jurisdiction: Jurisdiction (IT, EU, etc.)

        Returns:
            Dictionary of extracted entities
        """
        prompt = self._build_entity_extraction_prompt(content, jurisdiction)

        try:
            messages = [Message(role=Role.USER, content=prompt)]
            response = await self.llm.generate(messages, temperature=0.1, max_tokens=1000)

            # Parse JSON response
            entities = json.loads(response.content)

            # Validate and clean entities
            return self._validate_entities(entities)

        except Exception as e:
            logger.warning("entity_extraction_failed", error=str(e))
            return {}

    async def _generate_summary(self, content: str, category: str) -> str:
        """Generate concise summary of regulatory content.

        Args:
            content: Document content
            category: Content category

        Returns:
            Summary text
        """
        prompt = self._build_summary_prompt(content, category)

        try:
            messages = [Message(role=Role.USER, content=prompt)]
            response = await self.llm.generate(messages, temperature=0.3, max_tokens=300)
            return response.content.strip()

        except Exception as e:
            logger.warning("summary_generation_failed", error=str(e))
            return self._fallback_summary(content)

    async def _assess_impact(self, content: str, category: str) -> str:
        """Assess the impact of regulatory changes.

        Args:
            content: Document content
            category: Content category

        Returns:
            Impact assessment text
        """
        prompt = self._build_impact_prompt(content, category)

        try:
            messages = [Message(role=Role.USER, content=prompt)]
            response = await self.llm.generate(messages, temperature=0.2, max_tokens=400)
            return response.content.strip()

        except Exception as e:
            logger.warning("impact_assessment_failed", error=str(e))
            return "Impact assessment not available"

    async def _classify_content(self, content: str) -> str | None:
        """Classify regulatory content into categories.

        Args:
            content: Document content

        Returns:
            Content classification
        """
        prompt = self._build_classification_prompt(content)

        try:
            messages = [Message(role=Role.USER, content=prompt)]
            response = await self.llm.generate(messages, temperature=0.1, max_tokens=100)
            classification = response.content.strip().lower()

            # Map to standard categories
            return self._normalize_classification(classification)

        except Exception as e:
            logger.warning("content_classification_failed", error=str(e))
            return None

    def _build_entity_extraction_prompt(self, content: str, jurisdiction: str) -> str:
        """Build prompt for entity extraction."""
        return f"""Sei un esperto in normativa {jurisdiction}. Estrai entità rilevanti dal seguente testo normativo.

Testo:
{content[:4000]}...

Estrai le seguenti entità in formato JSON:
{{
    "dates": ["array di date importanti in formato YYYY-MM-DD"],
    "amounts": ["array di importi monetari"],
    "references": ["array di riferimenti normativi (es. 'art. 15 DPR 633/72')"],
    "entities": ["array di entità menzionate (persone, organizzazioni)"],
    "requirements": ["array di obblighi o requisiti imposti"],
    "deadlines": ["array di scadenze o termini"],
    "changes": ["array di modifiche o novità introdotte"]
}}

Rispondi SOLO con JSON valido, senza testo aggiuntivo."""

    def _build_summary_prompt(self, content: str, category: str) -> str:
        """Build prompt for summary generation."""
        return f"""Riassumi in italiano il seguente contenuto normativo della categoria "{category}".

Testo:
{content[:3000]}...

Fornisci un riassunto conciso ma completo che includa:
- Oggetto principale della normativa
- Principali cambiamenti o novità
- Impatti sui contribuenti
- Scadenze importanti (se presenti)

Riassunto:"""

    def _build_impact_prompt(self, content: str, category: str) -> str:
        """Build prompt for impact assessment."""
        return f"""Valuta l'impatto del seguente aggiornamento normativo nella categoria "{category}".

Testo:
{content[:3000]}...

Valuta:
1. Livello di impatto (Basso/Medio/Alto/Critico)
2. Categorie interessate (contribuenti, professionisti, aziende)
3. Urgenza di implementazione
4. Possibili conseguenze di mancata compliance

Valutazione dell'impatto:"""

    def _build_classification_prompt(self, content: str) -> str:
        """Build prompt for content classification."""
        return f"""Classifica il seguente contenuto normativo in una delle categorie:

- iva: aliquote IVA, fatturazione, detrazioni
- tax: imposte dirette, IRPEF, IRES
- invoice: fatturazione elettronica, FatturaPA
- social_security: contributi previdenziali, INPS
- business: attività economiche, partita IVA
- compliance: adempimenti, scadenze, sanzioni

Testo:
{content[:2000]}...

Categoria:"""

    def _validate_entities(self, entities: dict[str, Any]) -> dict[str, Any]:
        """Validate and clean extracted entities.

        Args:
            entities: Raw extracted entities

        Returns:
            Validated entities
        """
        validated = {}

        # Validate dates
        if "dates" in entities and isinstance(entities["dates"], list):
            validated["dates"] = [d for d in entities["dates"] if isinstance(d, str) and len(d) > 0]

        # Validate amounts
        if "amounts" in entities and isinstance(entities["amounts"], list):
            validated["amounts"] = [
                a for a in entities["amounts"] if isinstance(a, str) and len(a) > 0
            ]

        # Validate references
        if "references" in entities and isinstance(entities["references"], list):
            validated["references"] = [
                r for r in entities["references"] if isinstance(r, str) and len(r) > 0
            ]

        # Validate other arrays
        for key in ["entities", "requirements", "deadlines", "changes"]:
            if key in entities and isinstance(entities[key], list):
                validated[key] = [
                    item for item in entities[key] if isinstance(item, str) and len(item) > 0
                ]

        return validated

    def _normalize_classification(self, classification: str) -> str:
        """Normalize classification to standard categories.

        Args:
            classification: Raw classification

        Returns:
            Normalized classification
        """
        # Simple mapping - could be more sophisticated
        mapping = {
            "iva": "iva",
            "aliquote iva": "iva",
            "fatturazione": "invoice",
            "fattura": "invoice",
            "imposte": "tax",
            "irpef": "tax",
            "ires": "tax",
            "contributi": "social_security",
            "inps": "social_security",
            "partita iva": "business",
            "attivita": "business",
            "adempimenti": "compliance",
            "scadenze": "compliance",
            "sanzioni": "compliance",
        }

        return mapping.get(classification.lower().strip(), classification.lower().strip())

    def _fallback_summary(self, content: str) -> str:
        """Generate fallback summary when AI fails.

        Args:
            content: Document content

        Returns:
            Basic summary
        """
        # Simple extractive summary
        sentences = content.split(".")[:3]
        return ". ".join(sentences) + "." if sentences else "Riassunto non disponibile"
