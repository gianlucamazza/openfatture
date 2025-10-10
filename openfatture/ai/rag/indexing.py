"""Invoice indexing pipeline for RAG system.

This module handles indexing of invoices and related documents into the vector store.
"""

from openfatture.ai.rag.vector_store import VectorStore
from openfatture.storage.database.base import SessionLocal
from openfatture.storage.database.models import Fattura
from openfatture.utils.logging import get_logger

logger = get_logger(__name__)


class InvoiceIndexer:
    """Invoice indexing pipeline for RAG system.

    Handles:
    - Full invoice indexing (descriptions, metadata)
    - Incremental indexing (new/updated invoices)
    - Client context extraction
    - Batch processing for efficiency

    Example:
        >>> indexer = InvoiceIndexer(vector_store)
        >>> await indexer.index_all_invoices(batch_size=100)
        >>> await indexer.index_invoice(invoice_id=123)
    """

    def __init__(self, vector_store: VectorStore) -> None:
        """Initialize invoice indexer.

        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store

        logger.info("invoice_indexer_initialized")

    async def index_all_invoices(
        self,
        batch_size: int = 100,
        year: int | None = None,
    ) -> int:
        """Index all invoices in the database.

        Args:
            batch_size: Number of invoices to process per batch
            year: Optional year filter

        Returns:
            Number of invoices indexed
        """
        db = SessionLocal()

        try:
            # Query invoices
            query = db.query(Fattura)

            if year:
                query = query.filter(Fattura.anno == year)

            fatture = query.all()

            if not fatture:
                logger.warning("no_invoices_to_index")
                return 0

            logger.info(
                "indexing_invoices_started",
                total_count=len(fatture),
                batch_size=batch_size,
            )

            # Process in batches
            indexed_count = 0

            for i in range(0, len(fatture), batch_size):
                batch = fatture[i : i + batch_size]

                await self._index_invoice_batch(batch)

                indexed_count += len(batch)

                logger.info(
                    "batch_indexed",
                    batch_number=i // batch_size + 1,
                    batch_size=len(batch),
                    total_indexed=indexed_count,
                )

            logger.info(
                "indexing_invoices_completed",
                total_indexed=indexed_count,
            )

            return indexed_count

        except Exception as e:
            logger.error("indexing_invoices_failed", error=str(e))
            raise

        finally:
            db.close()

    async def index_invoice(self, invoice_id: int) -> str:
        """Index a single invoice.

        Args:
            invoice_id: Invoice ID

        Returns:
            Document ID
        """
        db = SessionLocal()

        try:
            fattura = db.query(Fattura).filter(Fattura.id == invoice_id).first()

            if not fattura:
                raise ValueError(f"Invoice {invoice_id} not found")

            document = self._create_invoice_document(fattura)
            metadata = self._create_invoice_metadata(fattura)
            doc_id = f"invoice-{fattura.id}"

            # Check if already indexed
            existing = self.vector_store.get_document(doc_id)

            if existing:
                # Update existing document
                await self.vector_store.update_document(
                    doc_id=doc_id,
                    document=document,
                    metadata=metadata,
                )

                logger.info("invoice_updated", invoice_id=invoice_id, doc_id=doc_id)

            else:
                # Add new document
                await self.vector_store.add_documents(
                    documents=[document],
                    metadatas=[metadata],
                    ids=[doc_id],
                )

                logger.info("invoice_indexed", invoice_id=invoice_id, doc_id=doc_id)

            return doc_id

        except Exception as e:
            logger.error(
                "index_invoice_failed",
                invoice_id=invoice_id,
                error=str(e),
            )
            raise

        finally:
            db.close()

    async def _index_invoice_batch(self, fatture: list[Fattura]) -> list[str]:
        """Index a batch of invoices.

        Args:
            fatture: List of Fattura objects

        Returns:
            List of document IDs
        """
        documents = []
        metadatas = []
        ids = []

        for fattura in fatture:
            documents.append(self._create_invoice_document(fattura))
            metadatas.append(self._create_invoice_metadata(fattura))
            ids.append(f"invoice-{fattura.id}")

        # Add to vector store
        doc_ids = await self.vector_store.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        return doc_ids

    def _create_invoice_document(self, fattura: Fattura) -> str:
        """Create searchable document text from invoice.

        Args:
            fattura: Fattura object

        Returns:
            Document text for embedding
        """
        parts = [
            f"Fattura {fattura.numero}/{fattura.anno}",
            f"Cliente: {fattura.cliente.denominazione}",
            f"Data: {fattura.data_emissione.strftime('%d/%m/%Y')}",
            f"Importo: €{fattura.totale:.2f}",
            f"Stato: {fattura.stato.value}",
        ]

        # Add invoice lines descriptions
        if fattura.righe:
            parts.append("Servizi:")
            for riga in fattura.righe:
                parts.append(f"- {riga.descrizione}")

        # Add client info for context
        if fattura.cliente.partita_iva:
            parts.append(f"P.IVA: {fattura.cliente.partita_iva}")

        return "\n".join(parts)

    def _create_invoice_metadata(self, fattura: Fattura) -> dict:
        """Create metadata for invoice document.

        Args:
            fattura: Fattura object

        Returns:
            Metadata dictionary
        """
        return {
            "type": "invoice",
            "invoice_id": fattura.id,
            "invoice_number": fattura.numero,
            "invoice_year": fattura.anno,
            "client_id": fattura.cliente_id,
            "client_name": fattura.cliente.denominazione,
            "client_vat": fattura.cliente.partita_iva or "",
            "date": fattura.data_emissione.isoformat(),
            "amount": float(fattura.totale),
            "status": fattura.stato.value,
            "has_lines": len(fattura.righe) > 0 if fattura.righe else False,
            "line_count": len(fattura.righe) if fattura.righe else 0,
        }

    async def delete_invoice(self, invoice_id: int) -> None:
        """Delete invoice from index.

        Args:
            invoice_id: Invoice ID
        """
        doc_id = f"invoice-{invoice_id}"

        await self.vector_store.delete_documents([doc_id])

        logger.info("invoice_deleted_from_index", invoice_id=invoice_id)

    async def reindex_year(self, year: int) -> int:
        """Reindex all invoices for a specific year.

        Args:
            year: Year to reindex

        Returns:
            Number of invoices reindexed
        """
        # Delete existing invoices for this year
        deleted = await self.vector_store.delete_by_filter(
            {"type": "invoice", "invoice_year": year}
        )

        logger.info("year_invoices_deleted", year=year, count=deleted)

        # Reindex
        count = await self.index_all_invoices(year=year)

        logger.info("year_reindexed", year=year, count=count)

        return count
