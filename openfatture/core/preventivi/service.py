"""Preventivo service layer with business logic."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from openfatture.storage.database.models import (
    Cliente,
    Fattura,
    Preventivo,
    RigaFattura,
    RigaPreventivo,
    StatoFattura,
    StatoPreventivo,
    TipoDocumento,
)
from openfatture.utils.config import Settings


class PreventivoService:
    """Service for preventivo (quote/estimate) operations."""

    def __init__(self, settings: Settings):
        """Initialize service."""
        self.settings = settings

    def create_preventivo(
        self,
        db: Session,
        cliente_id: int,
        righe: list[dict],
        validita_giorni: int = 30,
        note: str | None = None,
        condizioni: str | None = None,
    ) -> tuple[Preventivo | None, str | None]:
        """
        Create a new preventivo.

        Args:
            db: Database session
            cliente_id: Client ID
            righe: List of line items (each dict with: descrizione, quantita, prezzo_unitario, aliquota_iva, unita_misura)
            validita_giorni: Validity period in days (default: 30)
            note: Optional notes
            condizioni: Optional terms and conditions

        Returns:
            tuple[Optional[Preventivo], Optional[str]]: (preventivo, error_message)
        """
        try:
            # Verify client exists
            cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
            if not cliente:
                return None, f"Client with ID {cliente_id} not found"

            # Generate numero (sequential per year)
            anno = date.today().year
            ultimo_preventivo = (
                db.query(Preventivo)
                .filter(Preventivo.anno == anno)
                .order_by(Preventivo.numero.desc())
                .first()
            )

            if ultimo_preventivo:
                prossimo_numero = int(ultimo_preventivo.numero) + 1
            else:
                prossimo_numero = 1

            # Calculate expiration date
            data_emissione = date.today()
            data_scadenza = data_emissione + timedelta(days=validita_giorni)

            # Create preventivo
            preventivo = Preventivo(
                numero=str(prossimo_numero),
                anno=anno,
                data_emissione=data_emissione,
                data_scadenza=data_scadenza,
                cliente_id=cliente_id,
                validita_giorni=validita_giorni,
                note=note,
                condizioni=condizioni,
                stato=StatoPreventivo.BOZZA,
            )

            db.add(preventivo)
            db.flush()  # Get ID without committing

            # Add righe (line items)
            totale_imponibile = Decimal("0")
            totale_iva = Decimal("0")

            for idx, riga_data in enumerate(righe, start=1):
                quantita = Decimal(str(riga_data["quantita"]))
                prezzo_unitario = Decimal(str(riga_data["prezzo_unitario"]))
                aliquota_iva = Decimal(str(riga_data["aliquota_iva"]))

                imponibile = quantita * prezzo_unitario
                iva = imponibile * aliquota_iva / Decimal("100")
                totale = imponibile + iva

                riga = RigaPreventivo(
                    preventivo_id=preventivo.id,
                    numero_riga=idx,
                    descrizione=riga_data["descrizione"],
                    quantita=quantita,
                    prezzo_unitario=prezzo_unitario,
                    unita_misura=riga_data.get("unita_misura", "ore"),
                    aliquota_iva=aliquota_iva,
                    imponibile=imponibile,
                    iva=iva,
                    totale=totale,
                )

                db.add(riga)

                totale_imponibile += imponibile
                totale_iva += iva

            # Update preventivo totals
            preventivo.imponibile = totale_imponibile
            preventivo.iva = totale_iva
            preventivo.totale = totale_imponibile + totale_iva

            db.commit()
            db.refresh(preventivo)

            return preventivo, None

        except Exception as e:
            db.rollback()
            return None, f"Error creating preventivo: {e}"

    def get_preventivo(self, db: Session, preventivo_id: int) -> Preventivo | None:
        """Get preventivo by ID."""
        return db.query(Preventivo).filter(Preventivo.id == preventivo_id).first()

    def list_preventivi(
        self,
        db: Session,
        stato: StatoPreventivo | None = None,
        cliente_id: int | None = None,
        anno: int | None = None,
        limit: int = 50,
    ) -> list[Preventivo]:
        """
        List preventivi with optional filters.

        Args:
            db: Database session
            stato: Filter by status
            cliente_id: Filter by client ID
            anno: Filter by year
            limit: Maximum results (default: 50)

        Returns:
            List of Preventivo objects
        """
        query = db.query(Preventivo).order_by(Preventivo.anno.desc(), Preventivo.numero.desc())

        if stato:
            query = query.filter(Preventivo.stato == stato)

        if cliente_id:
            query = query.filter(Preventivo.cliente_id == cliente_id)

        if anno:
            query = query.filter(Preventivo.anno == anno)

        return query.limit(limit).all()

    def update_stato(
        self, db: Session, preventivo_id: int, nuovo_stato: StatoPreventivo
    ) -> tuple[bool, str | None]:
        """
        Update preventivo status.

        Args:
            db: Database session
            preventivo_id: Preventivo ID
            nuovo_stato: New status

        Returns:
            tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            preventivo = self.get_preventivo(db, preventivo_id)
            if not preventivo:
                return False, f"Preventivo {preventivo_id} not found"

            # Validation: cannot change status if already converted
            if preventivo.stato == StatoPreventivo.CONVERTITO:
                return False, "Cannot change status of converted preventivo"

            preventivo.stato = nuovo_stato
            db.commit()

            return True, None

        except Exception as e:
            db.rollback()
            return False, f"Error updating status: {e}"

    def delete_preventivo(self, db: Session, preventivo_id: int) -> tuple[bool, str | None]:
        """
        Delete a preventivo.

        Args:
            db: Database session
            preventivo_id: Preventivo ID

        Returns:
            tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            preventivo = self.get_preventivo(db, preventivo_id)
            if not preventivo:
                return False, f"Preventivo {preventivo_id} not found"

            # Prevent deletion of converted preventivo
            if preventivo.stato == StatoPreventivo.CONVERTITO:
                return False, "Cannot delete converted preventivo"

            db.delete(preventivo)
            db.commit()

            return True, None

        except Exception as e:
            db.rollback()
            return False, f"Error deleting preventivo: {e}"

    def check_scadenza(self, db: Session, preventivo_id: int) -> tuple[bool, str | None]:
        """
        Check if preventivo is expired and update status if needed.

        Args:
            db: Database session
            preventivo_id: Preventivo ID

        Returns:
            tuple[bool, Optional[str]]: (is_expired, error_message)
        """
        try:
            preventivo = self.get_preventivo(db, preventivo_id)
            if not preventivo:
                return False, f"Preventivo {preventivo_id} not found"

            # Check expiration
            if preventivo.data_scadenza < date.today() and preventivo.stato not in [
                StatoPreventivo.CONVERTITO,
                StatoPreventivo.SCADUTO,
            ]:
                preventivo.stato = StatoPreventivo.SCADUTO
                db.commit()
                return True, None

            return False, None

        except Exception as e:
            db.rollback()
            return False, f"Error checking expiration: {e}"

    def converti_a_fattura(
        self, db: Session, preventivo_id: int, tipo_documento: TipoDocumento = TipoDocumento.TD01
    ) -> tuple[Fattura | None, str | None]:
        """
        Convert preventivo to fattura (invoice).

        Args:
            db: Database session
            preventivo_id: Preventivo ID
            tipo_documento: Invoice document type (default: TD01)

        Returns:
            tuple[Optional[Fattura], Optional[str]]: (fattura, error_message)
        """
        try:
            preventivo = self.get_preventivo(db, preventivo_id)
            if not preventivo:
                return None, f"Preventivo {preventivo_id} not found"

            # Validate stato
            if preventivo.stato == StatoPreventivo.CONVERTITO:
                return None, "Preventivo already converted to invoice"

            if preventivo.stato == StatoPreventivo.SCADUTO:
                return None, "Cannot convert expired preventivo"

            # Check expiration
            if preventivo.data_scadenza < date.today():
                return None, "Preventivo is expired"

            # Generate invoice number (sequential per year)
            anno = date.today().year
            ultima_fattura = (
                db.query(Fattura)
                .filter(Fattura.anno == anno)
                .order_by(Fattura.numero.desc())
                .first()
            )

            if ultima_fattura:
                prossimo_numero = int(ultima_fattura.numero) + 1
            else:
                prossimo_numero = 1

            # Create fattura
            fattura = Fattura(
                numero=str(prossimo_numero),
                anno=anno,
                data_emissione=date.today(),
                tipo_documento=tipo_documento,
                cliente_id=preventivo.cliente_id,
                preventivo_id=preventivo.id,
                imponibile=preventivo.imponibile,
                iva=preventivo.iva,
                totale=preventivo.totale,
                stato=StatoFattura.BOZZA,
                note=preventivo.note,
            )

            db.add(fattura)
            db.flush()  # Get ID without committing

            # Copy righe from preventivo to fattura
            for riga_prev in preventivo.righe:
                riga_fatt = RigaFattura(
                    fattura_id=fattura.id,
                    numero_riga=riga_prev.numero_riga,
                    descrizione=riga_prev.descrizione,
                    quantita=riga_prev.quantita,
                    prezzo_unitario=riga_prev.prezzo_unitario,
                    unita_misura=riga_prev.unita_misura,
                    aliquota_iva=riga_prev.aliquota_iva,
                    imponibile=riga_prev.imponibile,
                    iva=riga_prev.iva,
                    totale=riga_prev.totale,
                )
                db.add(riga_fatt)

            # Update preventivo status
            preventivo.stato = StatoPreventivo.CONVERTITO

            db.commit()
            db.refresh(fattura)

            return fattura, None

        except Exception as e:
            db.rollback()
            return None, f"Error converting preventivo to fattura: {e}"
