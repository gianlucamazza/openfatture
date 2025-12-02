# Email templates translations
# Italian (default locale)

## Email footer
email-footer-generated-by = Generato automaticamente da
email-footer-do-not-reply = Questa è una email automatica. Si prega di non rispondere.
email-footer-link-sdi = Portale SDI
email-footer-link-help = Guida

## Common email terms
email-common-invoice = Fattura
email-common-client = Cliente
email-common-date = Data
email-common-amount = Importo
email-common-status = Stato
email-common-details = Dettagli
email-common-view-details = Visualizza Dettagli
email-common-total = Totale
email-common-subtotal = Imponibile
email-common-vat = IVA
email-common-errors = Errori
email-common-error = Errore
email-common-success = Successo
email-common-warning = Attenzione

## SDI - Invio Fattura
email-sdi-invio-subject = Invio Fattura { $numero }/{ $anno } a SDI
email-sdi-invio-title = Trasmissione Fattura Elettronica
email-sdi-invio-intro = La fattura è stata inviata al Sistema di Interscambio (SDI) per la consegna al destinatario.
email-sdi-invio-invoice-details = Dettagli Fattura
email-sdi-invio-sender-info = Informazioni Mittente
email-sdi-invio-attached-file = File allegato
email-sdi-invio-next-steps = Prossimi Passi
email-sdi-invio-next-steps-text = Riceverai una notifica quando la fattura sarà consegnata al destinatario. Il processo può richiedere alcune ore.

## SDI - Notifica Attestazione (RC)
email-sdi-attestazione-subject = 📨 Fattura { $numero }/{ $anno } - Trasmissione Confermata
email-sdi-attestazione-title = Attestazione di Trasmissione
email-sdi-attestazione-intro = Il Sistema di Interscambio (SDI) conferma la ricezione della fattura.
email-sdi-attestazione-message = La fattura è stata accettata dal sistema e verrà inoltrata al destinatario.
email-sdi-attestazione-sdi-id = Identificativo SDI

## SDI - Notifica Consegna (NS)
email-sdi-consegna-subject = ✅ Fattura { $numero }/{ $anno } Consegnata
email-sdi-consegna-title = Fattura Consegnata con Successo
email-sdi-consegna-intro = La fattura è stata consegnata con successo al destinatario.
email-sdi-consegna-message = Il Sistema di Interscambio ha confermato la consegna della fattura al sistema del cliente.
email-sdi-consegna-delivered-at = Consegnata il
email-sdi-consegna-next-steps = Attendi ora l'esito da parte del committente (accettazione o rifiuto).

## SDI - Notifica Scarto (NS rifiuto)
email-sdi-scarto-subject = ❌ Fattura { $numero }/{ $anno } Scartata da SDI
email-sdi-scarto-title = Fattura Scartata
email-sdi-scarto-intro = La fattura è stata scartata dal Sistema di Interscambio a causa di errori di validazione.
email-sdi-scarto-error-list = Lista Errori
email-sdi-scarto-action-required = Azione Richiesta
email-sdi-scarto-action-text = Correggi gli errori indicati e reinvia la fattura al Sistema di Interscambio.
email-sdi-scarto-error-count = { $count ->
    [one] { $count } errore rilevato
   *[other] { $count } errori rilevati
}

## SDI - Mancata Consegna (MC)
email-sdi-mancata-consegna-subject = ⚠️ Fattura { $numero }/{ $anno } - Mancata Consegna
email-sdi-mancata-consegna-title = Mancata Consegna
email-sdi-mancata-consegna-intro = Il Sistema di Interscambio non è riuscito a consegnare la fattura al destinatario.
email-sdi-mancata-consegna-reason = Motivo
email-sdi-mancata-consegna-action-required = Azione Richiesta
email-sdi-mancata-consegna-action-text = Verifica i dati del destinatario (PEC o Codice Destinatario) e reinvia la fattura con le informazioni corrette.

## SDI - Esito Committente Accettata (EC01)
email-sdi-esito-accettata-subject = ✅ Fattura { $numero }/{ $anno } Accettata dal Cliente
email-sdi-esito-accettata-title = Fattura Accettata
email-sdi-esito-accettata-intro = Il committente ha accettato la fattura.
email-sdi-esito-accettata-message = La fattura è stata validata e accettata dal destinatario. Il processo di fatturazione è completato con successo.
email-sdi-esito-accettata-outcome = Esito Committente
email-sdi-esito-accettata-accepted = Accettata (EC01)

## SDI - Esito Committente Rifiutata (EC02)
email-sdi-esito-rifiutata-subject = ⚠️ Fattura { $numero }/{ $anno } Rifiutata dal Cliente
email-sdi-esito-rifiutata-title = Fattura Rifiutata
email-sdi-esito-rifiutata-intro = Il committente ha rifiutato la fattura.
email-sdi-esito-rifiutata-message = Il destinatario ha respinto la fattura. Contatta il cliente per chiarimenti.
email-sdi-esito-rifiutata-outcome = Esito Committente
email-sdi-esito-rifiutata-rejected = Rifiutata (EC02)
email-sdi-esito-rifiutata-reason = Motivazione
email-sdi-esito-rifiutata-action-required = Azione Richiesta
email-sdi-esito-rifiutata-action-text = Contatta il cliente per comprendere i motivi del rifiuto. Potrebbe essere necessario emettere una nota di credito.

## Batch Operations
email-batch-summary-subject = Riepilogo Operazione Batch - { $operation }
email-batch-summary-title = Riepilogo Operazione Batch
email-batch-summary-operation = Operazione
email-batch-summary-started-at = Iniziata alle
email-batch-summary-completed-at = Completata alle
email-batch-summary-duration = Durata
email-batch-summary-metrics = Metriche
email-batch-summary-total-items = Elementi Totali
email-batch-summary-processed = Elaborati
email-batch-summary-succeeded = Riusciti
email-batch-summary-failed = Falliti
email-batch-summary-success-rate = Tasso di Successo
email-batch-summary-errors = Errori Rilevati
email-batch-summary-no-errors = Nessun errore
email-batch-summary-results = Risultati
email-batch-summary-download-csv = Scarica Report CSV

## Test Email
email-test-subject = Test Configurazione PEC - OpenFatture
email-test-title = Test Configurazione PEC
email-test-intro = Questo è un messaggio di test per verificare la configurazione PEC.
email-test-success = Se ricevi questo messaggio, la configurazione è corretta!
email-test-server-info = Informazioni Server
email-test-smtp-server = Server SMTP
email-test-smtp-port = Porta SMTP
email-test-pec-address = Indirizzo PEC
email-test-time = Test effettuato il
