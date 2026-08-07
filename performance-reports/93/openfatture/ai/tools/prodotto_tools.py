"""Tools for product/service catalog management."""

from decimal import Decimal
from typing import Any

from pydantic import validate_call

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType
from openfatture.storage.database.base import get_session
from openfatture.storage.database.models import Prodotto
from openfatture.storage.database.models import RigaFattura as Riga
from openfatture.utils.logging import get_logger
from openfatture.utils.security import validate_integer_input

logger = get_logger(__name__)


# =============================================================================
# READ Tools
# =============================================================================


@validate_call
def search_prodotti(
    categoria: str | None = None,
    is_servizio: bool | None = None,
    codice_contains: str | None = None,
    descrizione_contains: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Search products/services in catalog with filters.

    Args:
        categoria: Filter by category (optional)
        is_servizio: Filter by product type (True=service, False=product)
        codice_contains: Filter by product code (partial match)
        descrizione_contains: Filter by description (partial match)
        limit: Maximum results (default 20, max 100)

    Returns:
        Dictionary with search results
    """
    # Validate inputs
    limit = validate_integer_input(limit, min_value=1, max_value=100)

    db = get_session()
    try:
        # Build query
        query = db.query(Prodotto)

        # Apply filters
        if categoria:
            query = query.filter(Prodotto.categoria == categoria)
        if is_servizio is not None:
            query = query.filter(Prodotto.is_servizio == is_servizio)
        if codice_contains:
            query = query.filter(Prodotto.codice.ilike(f"%{codice_contains}%"))
        if descrizione_contains:
            query = query.filter(Prodotto.descrizione.ilike(f"%{descrizione_contains}%"))

        # Execute query
        prodotti = query.order_by(Prodotto.codice).limit(limit).all()

        # Format results
        results = []
        for p in prodotti:
            results.append(
                {
                    "prodotto_id": p.id,
                    "codice": p.codice,
                    "descrizione": p.descrizione,
                    "prezzo_unitario": float(p.prezzo_unitario),
                    "aliquota_iva": float(p.aliquota_iva),
                    "unita_misura": p.unita_misura,
                    "categoria": p.categoria,
                    "is_servizio": p.is_servizio,
                    "tipo": "Servizio" if p.is_servizio else "Prodotto",
                }
            )

        return {
            "count": len(results),
            "prodotti": results,
            "has_more": len(prodotti) == limit,
        }

    except Exception as e:
        logger.error("search_prodotti_failed", error=str(e))
        return {"error": str(e), "count": 0, "prodotti": []}
    finally:
        db.close()


@validate_call
def get_prodotto_details(prodotto_id: int) -> dict[str, Any]:
    """
    Get detailed information about a specific product/service.

    Args:
        prodotto_id: Product ID

    Returns:
        Dictionary with product details and usage statistics
    """
    # Validate input
    prodotto_id = validate_integer_input(prodotto_id, min_value=1)

    db = get_session()
    try:
        prodotto = db.query(Prodotto).filter(Prodotto.id == prodotto_id).first()

        if not prodotto:
            return {"error": f"Prodotto {prodotto_id} not found"}

        # Calculate usage statistics
        righe_count = db.query(Riga).filter(Riga.prodotto_id == prodotto_id).count()

        # Get recent invoices using this product
        recent_righe = (
            db.query(Riga)
            .filter(Riga.prodotto_id == prodotto_id)
            .order_by(Riga.id.desc())
            .limit(5)
            .all()
        )

        recent_invoices = []
        for riga in recent_righe:
            if riga.fattura:
                recent_invoices.append(
                    {
                        "fattura_id": riga.fattura.id,
                        "numero": f"{riga.fattura.numero}/{riga.fattura.anno}",
                        "data_emissione": riga.fattura.data_emissione.isoformat(),
                        "quantita": float(riga.quantita),
                        "prezzo_unitario": float(riga.prezzo_unitario),
                    }
                )

        return {
            "prodotto_id": prodotto.id,
            "codice": prodotto.codice,
            "descrizione": prodotto.descrizione,
            "prezzo_unitario": float(prodotto.prezzo_unitario),
            "aliquota_iva": float(prodotto.aliquota_iva),
            "unita_misura": prodotto.unita_misura,
            "categoria": prodotto.categoria,
            "is_servizio": prodotto.is_servizio,
            "tipo": "Servizio" if prodotto.is_servizio else "Prodotto",
            "note": prodotto.note,
            "usage_stats": {
                "times_used": righe_count,
                "recent_invoices": recent_invoices,
            },
        }

    except Exception as e:
        logger.error("get_prodotto_details_failed", prodotto_id=prodotto_id, error=str(e))
        return {"error": str(e)}
    finally:
        db.close()


# =============================================================================
# WRITE Tools
# =============================================================================


@validate_call
def create_prodotto(
    codice: str,
    descrizione: str,
    prezzo_unitario: float,
    aliquota_iva: float = 22.0,
    unita_misura: str = "ore",
    categoria: str | None = None,
    is_servizio: bool = True,
    note: str | None = None,
) -> dict[str, Any]:
    """
    Create a new product/service in catalog.

    Args:
        codice: Unique product code (max 50 chars)
        descrizione: Product description (max 500 chars)
        prezzo_unitario: Unit price (must be positive)
        aliquota_iva: VAT rate (default 22%)
        unita_misura: Unit of measure (default "ore")
        categoria: Optional category
        is_servizio: True for service, False for product (default True)
        note: Optional notes

    Returns:
        Dictionary with creation result
    """
    # Validate inputs
    if not codice or len(codice) > 50:
        return {"success": False, "error": "codice must be 1-50 characters"}

    if not descrizione or len(descrizione) > 500:
        return {"success": False, "error": "descrizione must be 1-500 characters"}

    if prezzo_unitario <= 0:
        return {"success": False, "error": "prezzo_unitario must be positive"}

    if aliquota_iva < 0 or aliquota_iva > 100:
        return {"success": False, "error": "aliquota_iva must be between 0 and 100"}

    if len(unita_misura) > 10:
        return {"success": False, "error": "unita_misura must be max 10 characters"}

    if categoria and len(categoria) > 100:
        return {"success": False, "error": "categoria must be max 100 characters"}

    db = get_session()
    try:
        # Check if codice already exists
        existing = db.query(Prodotto).filter(Prodotto.codice == codice).first()
        if existing:
            return {
                "success": False,
                "error": f"Prodotto con codice '{codice}' già esistente (ID: {existing.id})",
            }

        # Create product
        prodotto = Prodotto(
            codice=codice,
            descrizione=descrizione,
            prezzo_unitario=Decimal(str(prezzo_unitario)),
            aliquota_iva=Decimal(str(aliquota_iva)),
            unita_misura=unita_misura,
            categoria=categoria,
            is_servizio=is_servizio,
            note=note,
        )

        db.add(prodotto)
        db.commit()
        db.refresh(prodotto)

        logger.info(
            "prodotto_created",
            prodotto_id=prodotto.id,
            codice=codice,
            is_servizio=is_servizio,
        )

        return {
            "success": True,
            "prodotto_id": prodotto.id,
            "codice": prodotto.codice,
            "descrizione": prodotto.descrizione,
            "prezzo_unitario": float(prodotto.prezzo_unitario),
            "aliquota_iva": float(prodotto.aliquota_iva),
            "message": f"Prodotto '{codice}' creato con successo",
        }

    except Exception as e:
        db.rollback()
        logger.error("create_prodotto_failed", error=str(e))
        return {"success": False, "error": str(e)}
    finally:
        db.close()


@validate_call
def update_prodotto(
    prodotto_id: int,
    descrizione: str | None = None,
    prezzo_unitario: float | None = None,
    aliquota_iva: float | None = None,
    unita_misura: str | None = None,
    categoria: str | None = None,
    is_servizio: bool | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """
    Update product/service information (selective updates).

    Args:
        prodotto_id: Product ID to update
        descrizione: New description (optional)
        prezzo_unitario: New unit price (optional)
        aliquota_iva: New VAT rate (optional)
        unita_misura: New unit of measure (optional)
        categoria: New category (optional)
        is_servizio: New product type (optional)
        note: New notes (optional)

    Returns:
        Dictionary with update result
    """
    # Validate inputs
    prodotto_id = validate_integer_input(prodotto_id, min_value=1)

    if descrizione is not None and (not descrizione or len(descrizione) > 500):
        return {"success": False, "error": "descrizione must be 1-500 characters"}

    if prezzo_unitario is not None and prezzo_unitario <= 0:
        return {"success": False, "error": "prezzo_unitario must be positive"}

    if aliquota_iva is not None and (aliquota_iva < 0 or aliquota_iva > 100):
        return {"success": False, "error": "aliquota_iva must be between 0 and 100"}

    if unita_misura is not None and len(unita_misura) > 10:
        return {"success": False, "error": "unita_misura must be max 10 characters"}

    if categoria is not None and len(categoria) > 100:
        return {"success": False, "error": "categoria must be max 100 characters"}

    db = get_session()
    try:
        prodotto = db.query(Prodotto).filter(Prodotto.id == prodotto_id).first()

        if not prodotto:
            return {"success": False, "error": f"Prodotto {prodotto_id} not found"}

        # Track changes
        changes = []

        # Update fields if provided
        if descrizione is not None:
            prodotto.descrizione = descrizione
            changes.append("descrizione")

        if prezzo_unitario is not None:
            prodotto.prezzo_unitario = Decimal(str(prezzo_unitario))
            changes.append("prezzo_unitario")

        if aliquota_iva is not None:
            prodotto.aliquota_iva = Decimal(str(aliquota_iva))
            changes.append("aliquota_iva")

        if unita_misura is not None:
            prodotto.unita_misura = unita_misura
            changes.append("unita_misura")

        if categoria is not None:
            prodotto.categoria = categoria
            changes.append("categoria")

        if is_servizio is not None:
            prodotto.is_servizio = is_servizio
            changes.append("is_servizio")

        if note is not None:
            prodotto.note = note
            changes.append("note")

        if not changes:
            return {
                "success": False,
                "error": "No fields to update (all parameters are None)",
            }

        db.commit()
        db.refresh(prodotto)

        logger.info(
            "prodotto_updated",
            prodotto_id=prodotto_id,
            codice=prodotto.codice,
            changes=changes,
        )

        return {
            "success": True,
            "prodotto_id": prodotto.id,
            "codice": prodotto.codice,
            "changes": changes,
            "message": f"Prodotto '{prodotto.codice}' aggiornato ({len(changes)} campi)",
        }

    except Exception as e:
        db.rollback()
        logger.error("update_prodotto_failed", prodotto_id=prodotto_id, error=str(e))
        return {"success": False, "error": str(e)}
    finally:
        db.close()


@validate_call
def delete_prodotto(
    prodotto_id: int,
    force: bool = False,
) -> dict[str, Any]:
    """
    Delete a product/service from catalog.

    CRITICAL: This operation is irreversible. Use with caution.

    Args:
        prodotto_id: Product ID to delete
        force: Force deletion even if used in invoices (default False)

    Returns:
        Dictionary with deletion result
    """
    # Validate input
    prodotto_id = validate_integer_input(prodotto_id, min_value=1)

    db = get_session()
    try:
        prodotto = db.query(Prodotto).filter(Prodotto.id == prodotto_id).first()

        if not prodotto:
            return {"success": False, "error": f"Prodotto {prodotto_id} not found"}

        # Check if product is used in invoices
        usage_count = db.query(Riga).filter(Riga.prodotto_id == prodotto_id).count()

        if usage_count > 0 and not force:
            return {
                "success": False,
                "error": f"Prodotto usato in {usage_count} righe fattura. Usa force=True per eliminare comunque.",
                "usage_count": usage_count,
            }

        # Store info for response
        codice = prodotto.codice
        descrizione = prodotto.descrizione

        # If force=True and product is used, set righe.prodotto_id to NULL
        if usage_count > 0 and force:
            db.query(Riga).filter(Riga.prodotto_id == prodotto_id).update({"prodotto_id": None})

        # Delete product
        db.delete(prodotto)
        db.commit()

        logger.warning(
            "prodotto_deleted",
            prodotto_id=prodotto_id,
            codice=codice,
            was_used=usage_count > 0,
            usage_count=usage_count,
            forced=force,
        )

        return {
            "success": True,
            "prodotto_id": prodotto_id,
            "codice": codice,
            "descrizione": descrizione,
            "was_used": usage_count > 0,
            "usage_count": usage_count,
            "message": f"Prodotto '{codice}' eliminato"
            + (f" ({usage_count} riferimenti rimossi)" if usage_count > 0 else ""),
        }

    except Exception as e:
        db.rollback()
        logger.error("delete_prodotto_failed", prodotto_id=prodotto_id, error=str(e))
        return {"success": False, "error": str(e)}
    finally:
        db.close()


# =============================================================================
# Tool Definitions
# =============================================================================


def get_prodotto_tools() -> list[Tool]:
    """
    Get all product/service catalog tools.

    Returns:
        List of Tool instances
    """
    return [
        Tool(
            name="search_prodotti",
            description="Search products/services in catalog with optional filters (category, type, code, description)",
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="categoria",
                    type=ToolParameterType.STRING,
                    description="Filter by category",
                    required=False,
                ),
                ToolParameter(
                    name="is_servizio",
                    type=ToolParameterType.BOOLEAN,
                    description="Filter by type (True=service, False=product)",
                    required=False,
                ),
                ToolParameter(
                    name="codice_contains",
                    type=ToolParameterType.STRING,
                    description="Filter by product code (partial match)",
                    required=False,
                ),
                ToolParameter(
                    name="descrizione_contains",
                    type=ToolParameterType.STRING,
                    description="Filter by description (partial match)",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum results (default 20)",
                    required=False,
                    default=20,
                ),
            ],
            func=search_prodotti,
            examples=[
                "search_prodotti()",
                "search_prodotti(categoria='Consulting', is_servizio=True)",
                "search_prodotti(codice_contains='WEB', limit=10)",
            ],
            tags=["search", "prodotto", "catalog"],
        ),
        Tool(
            name="get_prodotto_details",
            description="Get detailed information about a specific product/service including usage statistics",
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="prodotto_id",
                    type=ToolParameterType.INTEGER,
                    description="Product ID",
                    required=True,
                ),
            ],
            func=get_prodotto_details,
            examples=["get_prodotto_details(prodotto_id=1)"],
            tags=["prodotto", "details", "catalog"],
        ),
        Tool(
            name="create_prodotto",
            description="Create a new product/service in catalog with pricing and VAT information",
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="codice",
                    type=ToolParameterType.STRING,
                    description="Unique product code (max 50 chars)",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="Product description (max 500 chars)",
                    required=True,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="Unit price (must be positive)",
                    required=True,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="VAT rate (default 22%)",
                    required=False,
                    default=22.0,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="Unit of measure (default 'ore')",
                    required=False,
                    default="ore",
                ),
                ToolParameter(
                    name="categoria",
                    type=ToolParameterType.STRING,
                    description="Optional category",
                    required=False,
                ),
                ToolParameter(
                    name="is_servizio",
                    type=ToolParameterType.BOOLEAN,
                    description="True for service, False for product (default True)",
                    required=False,
                    default=True,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="Optional notes",
                    required=False,
                ),
            ],
            func=create_prodotto,
            requires_confirmation=True,
            examples=[
                'create_prodotto(codice="WEB-CONS", descrizione="Web consulting hourly rate", prezzo_unitario=80.0)',
                'create_prodotto(codice="GDPR-AUD", descrizione="GDPR audit service", prezzo_unitario=150.0, categoria="Compliance", aliquota_iva=22.0)',
            ],
            tags=["create", "prodotto", "catalog", "write"],
        ),
        Tool(
            name="update_prodotto",
            description="Update product/service information (selective field updates)",
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="prodotto_id",
                    type=ToolParameterType.INTEGER,
                    description="Product ID to update",
                    required=True,
                ),
                ToolParameter(
                    name="descrizione",
                    type=ToolParameterType.STRING,
                    description="New description",
                    required=False,
                ),
                ToolParameter(
                    name="prezzo_unitario",
                    type=ToolParameterType.NUMBER,
                    description="New unit price",
                    required=False,
                ),
                ToolParameter(
                    name="aliquota_iva",
                    type=ToolParameterType.NUMBER,
                    description="New VAT rate",
                    required=False,
                ),
                ToolParameter(
                    name="unita_misura",
                    type=ToolParameterType.STRING,
                    description="New unit of measure",
                    required=False,
                ),
                ToolParameter(
                    name="categoria",
                    type=ToolParameterType.STRING,
                    description="New category",
                    required=False,
                ),
                ToolParameter(
                    name="is_servizio",
                    type=ToolParameterType.BOOLEAN,
                    description="New product type",
                    required=False,
                ),
                ToolParameter(
                    name="note",
                    type=ToolParameterType.STRING,
                    description="New notes",
                    required=False,
                ),
            ],
            func=update_prodotto,
            requires_confirmation=True,
            examples=[
                "update_prodotto(prodotto_id=1, prezzo_unitario=90.0)",
                'update_prodotto(prodotto_id=2, descrizione="Updated description", categoria="New Category")',
            ],
            tags=["update", "prodotto", "catalog", "write"],
        ),
        Tool(
            name="delete_prodotto",
            description="CRITICAL: Delete product/service from catalog (irreversible operation)",
            category="prodotti",
            parameters=[
                ToolParameter(
                    name="prodotto_id",
                    type=ToolParameterType.INTEGER,
                    description="Product ID to delete",
                    required=True,
                ),
                ToolParameter(
                    name="force",
                    type=ToolParameterType.BOOLEAN,
                    description="Force deletion even if used in invoices (default False)",
                    required=False,
                    default=False,
                ),
            ],
            func=delete_prodotto,
            requires_confirmation=True,
            examples=[
                "delete_prodotto(prodotto_id=5)",
                "delete_prodotto(prodotto_id=10, force=True)",
            ],
            tags=["delete", "prodotto", "catalog", "write", "critical"],
        ),
    ]
