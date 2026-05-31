# Traductions des commandes CLI
# FR

## MAIN CLI

### main - Textes principaux
cli-main-title = OpenFatture - Système Open Source de Facturation Électronique
cli-main-description = Système complet pour gérer les factures électroniques FatturaPA
cli-main-version = Version { $version }

### main - Groupes de commandes
cli-main-group-invoices = Gestion des Factures
cli-main-group-clients = Gestion des Clients
cli-main-group-products = Gestion des Produits
cli-main-group-pec = PEC & SDI
cli-main-group-batch = Opérations par Lot
cli-main-group-ai = Assistant IA
cli-main-group-payments = Suivi des Paiements
cli-main-group-preventivi = Devis
cli-main-group-events = Système d'Événements
cli-main-group-lightning = Lightning Network
cli-main-group-web = Interface Web

## Commandes FATTURA

### fattura - Textes d'aide
cli-fattura-help-numero = Numéro de facture
cli-fattura-help-cliente-id = ID du client
cli-fattura-help-anno = Année (par défaut : année actuelle)
cli-fattura-help-tipo-documento = Type de document (TD01, TD04, TD06, etc.)
cli-fattura-help-data = Date de facture (AAAA-MM-JJ)
cli-fattura-help-bollo = Timbre fiscal (€ 2,00)
cli-fattura-help-xml-path = Chemin du fichier XML
cli-fattura-help-formato = Format de sortie (table, json, yaml)
cli-fattura-help-all = Afficher toutes les factures, même les anciennes

### fattura - Sortie console
cli-fattura-create-title = [bold blue]Créer une Nouvelle Facture[/bold blue]
cli-fattura-select-client-title = [bold cyan]Sélection du Client[/bold cyan]
cli-fattura-no-clients-error = [red]Aucun client trouvé. Ajoutez-en d'abord avec « cliente add »[/red]
cli-fattura-available-clients = [cyan]Clients disponibles :[/cyan]
cli-fattura-client-prompt = Numéro du client
cli-fattura-client-selected = [green]Client : { $client_name }[/green]
cli-fattura-invalid-client-error = [red]Sélection de client invalide[/red]

cli-fattura-add-lines-title = [bold cyan]Lignes de Facture[/bold cyan]
cli-fattura-line-description-prompt = Description (vide pour terminer)
cli-fattura-line-quantity-prompt = Quantité
cli-fattura-line-unit-price-prompt = Prix unitaire (€)
cli-fattura-line-vat-rate-prompt = Taux IVA (%)
cli-fattura-line-added = [green]Ligne ajoutée : { $description } - € { $amount }[/green]

cli-fattura-payment-terms-title = [bold cyan]Conditions de Paiement[/bold cyan]
cli-fattura-payment-condition-prompt = Condition de paiement (TP01=Paiement dû, TP02=Payé)
cli-fattura-payment-method-prompt = Méthode de paiement (MP05=Virement bancaire, MP01=Espèces, MP08=Carte de crédit)
cli-fattura-payment-days-prompt = Délai de paiement (jours)
cli-fattura-payment-date-prompt = Date de paiement (AAAA-MM-JJ, vide=auto)
cli-fattura-payment-iban-prompt = IBAN (optionnel)

cli-fattura-summary-title = [bold yellow]Résumé de la Facture[/bold yellow]
cli-fattura-summary-client = Client : { $client_name }
cli-fattura-summary-lines = { $count } { $count ->
    [one] ligne
   *[other] lignes
}
cli-fattura-summary-subtotal = Sous-total : € { $subtotal }
cli-fattura-summary-vat = IVA : € { $vat }
cli-fattura-summary-total = [bold]Total : € { $total }[/bold]
cli-fattura-summary-stamp = Timbre fiscal : € { $stamp }

cli-fattura-confirm-prompt = [yellow]Confirmer la création ?[/yellow]
cli-fattura-created-success = [bold green]Facture créée avec succès ![/bold green]
cli-fattura-created-number = [green]Numéro de facture : { $numero }/{ $anno }[/green]
cli-fattura-created-xml = [green]XML enregistré : { $xml_path }[/green]

cli-fattura-list-title = [bold blue]Liste des Factures[/bold blue]
cli-fattura-list-empty = [yellow]Aucune facture trouvée[/yellow]

cli-fattura-show-title = [bold blue]Facture { $numero }/{ $anno }[/bold blue]
cli-fattura-show-not-found = [red]Facture non trouvée : { $numero }/{ $anno }[/red]

cli-fattura-delete-confirm = [yellow]Supprimer la facture { $numero }/{ $anno } ?[/yellow]
cli-fattura-delete-warning = [red]AVERTISSEMENT : Cette opération ne peut pas être annulée[/red]
cli-fattura-delete-status-restriction = [red]Impossible de supprimer la facture dans l'état '{ $status }'[/red]
cli-fattura-delete-success = [green]Facture { $numero }/{ $anno } supprimée[/green]
cli-fattura-delete-cancelled = [yellow]Opération annulée[/yellow]
cli-fattura-delete-cannot-delete-sent = [red]Impossible de supprimer les factures à l'état INVIATA ou CONSEGNATA[/red]

cli-fattura-validate-success = [green]Le XML est valide[/green]
cli-fattura-validate-error = [red]Erreurs de validation trouvées :[/red]

cli-fattura-table-numero = N°
cli-fattura-table-data = Date
cli-fattura-table-cliente = Client
cli-fattura-table-importo = Montant
cli-fattura-table-stato = État
cli-fattura-table-tipo = Type
cli-fattura-table-pagamento = Paiement
cli-fattura-table-iva = IVA
cli-fattura-table-totale = Total
cli-fattura-table-bollo = Timbre
cli-fattura-table-descrizione = Description
cli-fattura-table-quantita = Qté
cli-fattura-table-prezzo = Prix
cli-fattura-table-aliquota = Taux
cli-fattura-table-importo-riga = Montant

## Commandes CLIENTE

### cliente - Textes d'aide
cli-cliente-help-id = ID du client
cli-cliente-help-name = Nom du client/entreprise (omettre pour être invité en mode --interactive)
cli-cliente-help-denominazione = Nom de l'entreprise ou nom complet
cli-cliente-help-piva = Numéro de TVA (Partita IVA)
cli-cliente-help-partita-iva = Numéro IVA
cli-cliente-help-cf = Code fiscal (Codice Fiscale)
cli-cliente-help-codice-fiscale = Code fiscal
cli-cliente-help-sdi = Code SDI
cli-cliente-help-pec = Adresse PEC
cli-cliente-help-codice-destinatario = Code destinataire SDI
cli-cliente-help-interactive = Mode interactif
cli-cliente-help-formato = Format de sortie (table, json, yaml)
cli-cliente-help-search = Terme de recherche
cli-cliente-help-limite = Nombre maximum de résultats
cli-cliente-help-limit = Nombre maximum de résultats
cli-cliente-help-cliente-id = ID du client
cli-cliente-help-force = Ignorer la confirmation

### cliente - Sortie console
cli-cliente-name-required = [red]Erreur : Le nom du client est requis[/red]
cli-cliente-no-clients = [yellow]Aucun client trouvé. Ajoutez-en un avec 'cliente add'[/yellow]
cli-cliente-list-title = Clients ({ $count })
cli-cliente-list-empty = [yellow]Aucun client trouvé[/yellow]
cli-cliente-added-success = [green]Client ajouté avec succès (ID : { $id })[/green]
cli-cliente-updated-success = [green]Client mis à jour avec succès[/green]
cli-cliente-deleted-success = [green]Client supprimé avec succès[/green]
cli-cliente-deleted = [green]Client '{ $name }' supprimé[/green]
cli-cliente-cancelled = Annulé.
cli-cliente-not-found = [red]Client non trouvé : { $id }[/red]
cli-cliente-has-invoices = [yellow]Avertissement : Ce client a { $count } { $count ->
    [one] facture
   *[other] factures
}[/yellow]
cli-cliente-cannot-delete = [red]Impossible de supprimer un client avec des factures[/red]
cli-cliente-delete-confirm = [yellow]Supprimer le client { $denominazione } ?[/yellow]

### cliente - Invites
cli-cliente-prompt-denominazione = Nom de l'entreprise
cli-cliente-prompt-partita-iva = Numéro IVA
cli-cliente-prompt-codice-fiscale = Code fiscal
cli-cliente-prompt-indirizzo = Adresse
cli-cliente-prompt-cap = Code postal
cli-cliente-prompt-comune = Ville
cli-cliente-prompt-provincia = Province
cli-cliente-prompt-nazione = Pays
cli-cliente-prompt-pec = Adresse PEC
cli-cliente-prompt-codice-destinatario = Code destinataire SDI
cli-cliente-prompt-email = Email
cli-cliente-prompt-telefono = Téléphone
cli-cliente-prompt-regime-fiscale = Régime fiscal (RF01, RF19, etc.)

### cliente - Étiquettes du tableau
cli-cliente-table-id = ID
cli-cliente-table-denominazione = Nom
cli-cliente-table-partita-iva = IVA
cli-cliente-table-codice-fiscale = Code Fiscal
cli-cliente-table-comune = Ville
cli-cliente-table-provincia = Province
cli-cliente-table-pec = PEC
cli-cliente-table-codice-destinatario = Code SDI
cli-cliente-table-fatture = Factures
cli-cliente-table-indirizzo = Adresse
cli-cliente-table-cap = CP
cli-cliente-table-nazione = Pays
cli-cliente-table-email = Email

cli-cliente-column-id = ID
cli-cliente-column-name = Nom
cli-cliente-column-piva = N° TVA
cli-cliente-column-sdi-pec = SDI/PEC
cli-cliente-column-invoices = Factures

cli-cliente-label-id = ID
cli-cliente-label-name = Nom
cli-cliente-label-piva = Numéro de TVA
cli-cliente-label-cf = Code fiscal
cli-cliente-label-address = Adresse
cli-cliente-label-sdi = Code SDI
cli-cliente-label-pec = PEC
cli-cliente-label-email = Email
cli-cliente-label-phone = Téléphone
cli-cliente-label-total-invoices = Factures totales
cli-cliente-label-created = Créé

cli-cliente-show-title = [bold blue]Détails du client : { $name }[/bold blue]
cli-cliente-prompt-civic-number = Numéro civique (optionnel)
cli-cliente-prompt-pec-address = Adresse PEC (si SDI est 0000000)
cli-cliente-confirm-delete = Êtes-vous sûr de vouloir supprimer ?
cli-cliente-confirm-delete-client = Supprimer le client '{ $name }' ?

## ============================================================================
## Batch Commands - Opérations par Lot
## ============================================================================

### batch - Help Text
cli-batch-help-csv-file = Chemin du fichier CSV avec les factures
cli-batch-help-dry-run = Valider sans importer
cli-batch-help-send-summary = Envoyer le résumé par e-mail
cli-batch-help-output-file = Chemin du fichier CSV de sortie
cli-batch-help-anno = Filtrer par année
cli-batch-help-stato = Filtrer par état
cli-batch-help-limit = Nombre maximum de résultats

### batch - Console Output (import)
cli-batch-import-title = [bold blue]Importation par Lot de Factures[/bold blue]
cli-batch-file-not-found = [red]Fichier non trouvé : { $file }[/red]
cli-batch-file-info-name = [cyan]Fichier :[/cyan] { $name }
cli-batch-file-info-size = [cyan]Taille :[/cyan] { $size } octets
cli-batch-mode-dry-run = [cyan]Mode :[/cyan] Dry run (validation uniquement)
cli-batch-mode-import = [cyan]Mode :[/cyan] Importation
cli-batch-dry-run-warning = [yellow]Mode dry run - aucune donnée ne sera enregistrée[/yellow]
cli-batch-warning-dry-run = [yellow]Mode dry run - aucune donnée ne sera enregistrée[/yellow]

cli-batch-results-title = [bold]Résultats d'Importation :[/bold]
cli-batch-metric-total = Lignes totales
cli-batch-metric-processed = Traitées
cli-batch-metric-succeeded = Réussies
cli-batch-metric-failed = Échouées
cli-batch-metric-success-rate = Taux de réussite
cli-batch-metric-duration = Durée
cli-batch-metric-label = Métrique
cli-batch-metric-value = Valeur

cli-batch-errors-title = [bold red]Erreurs :[/bold red]
cli-batch-errors-more = [dim]... et { $count } erreurs supplémentaires[/dim]

cli-batch-success-all = [bold green]Toutes les factures importées avec succès ![/bold green]
cli-batch-warning-failed = [yellow]{ $count } factures non importées[/yellow]

cli-batch-email-not-configured = [yellow]Notification par e-mail non configurée.[/yellow]
cli-batch-sending-email = [dim]Envoi du résumé par e-mail...[/dim]
cli-batch-email-sending = [dim]Envoi du résumé par e-mail...[/dim]
cli-batch-email-sent = [dim]Résumé envoyé à { $email }[/dim]
cli-batch-email-failed = [yellow]Échec de l'envoi du résumé : { $error }[/yellow]

cli-batch-error-general = [red]Erreur : { $error }[/red]

### batch - Console Output (export)
cli-batch-export-title = [bold blue]Exportation par Lot de Factures[/bold blue]
cli-batch-filter-year = [cyan]Filtre :[/cyan] Année = { $anno }
cli-batch-filter-status = [cyan]Filtre :[/cyan] État = { $stato }
cli-batch-invalid-status = [red]État non valide : { $stato }[/red]
cli-batch-no-invoices = [yellow]Aucune facture trouvée[/yellow]
cli-batch-invoices-count = [cyan]Factures :[/cyan] { $count }

cli-batch-export-success = [bold green]{ $count } factures exportées ![/bold green]
cli-batch-export-file-path = [cyan]Fichier :[/cyan] { $path }
cli-batch-export-file = [cyan]Fichier :[/cyan] { $path }
cli-batch-export-file-size = [cyan]Taille :[/cyan] { $size } octets
cli-batch-export-size = [cyan]Taille :[/cyan] { $size } octets
cli-batch-export-failed = [red]Exportation échouée[/red]

### batch - Console Output (history)
cli-batch-history-title = [bold blue]Historique des Opérations par Lot[/bold blue]
cli-batch-history-not-implemented = [yellow]Suivi de l'historique pas encore complètement implémenté[/yellow]
cli-batch-history-future-features = [dim]En production, affichera :[/dim]
cli-batch-history-will-show = [dim]En production, affichera :[/dim]
cli-batch-history-feature-datetime = • Date/heure de l'opération
cli-batch-history-feature-type = • Type (import/export)
cli-batch-history-feature-records = • Enregistrements traités
cli-batch-history-feature-counts = • Comptes de réussite/échec
cli-batch-history-feature-errors = • Résumés d'erreurs

cli-batch-history-example-title = [bold]Exemple d'historique :[/bold]
cli-batch-history-example = [bold]Exemple d'historique :[/bold]
cli-batch-history-column-date = Date
cli-batch-history-col-date = Date
cli-batch-history-column-type = Type
cli-batch-history-col-type = Type
cli-batch-history-column-records = Enregistrements
cli-batch-history-col-records = Enregistrements
cli-batch-history-column-success = Réussis
cli-batch-history-col-success = Réussis
cli-batch-history-column-failed = Échoués
cli-batch-history-col-failed = Échoués

cli-batch-history-todo = [dim]À faire : Ajouter le modèle BatchOperation à la base de données[/dim]

## ============================================================================
## Preventivo Commands - Gestion des Devis
## ============================================================================

### preventivo - Help Text
cli-preventivo-help-cliente-id = ID du Client
cli-preventivo-help-validita = Période de validité en jours
cli-preventivo-help-stato = Filtrer par statut
cli-preventivo-help-anno = Filtrer par année
cli-preventivo-help-cliente = Filtrer par ID client
cli-preventivo-help-limit = Nombre maximum de résultats
cli-preventivo-help-preventivo-id = ID du Devis
cli-preventivo-help-force = Ignorer la confirmation
cli-preventivo-help-tipo-documento = Type de document de facture (TD01, TD06, etc.)
cli-preventivo-help-new-stato = Nouveau statut (brouillon, envoyé, accepté, refusé, expiré)

### preventivo - Console Output (crea)
cli-preventivo-create-title = [bold blue]Créer un Nouveau Devis[/bold blue]
cli-preventivo-no-clients = [red]Aucun client trouvé. Ajoutez d'abord un client avec 'openfatture cliente add'[/red]
cli-preventivo-select-client = [cyan]Clients disponibles :[/cyan]
cli-preventivo-client-id-prompt = Sélectionnez l'ID du client
cli-preventivo-client-not-found = [red]Client { $id } non trouvé[/red]
cli-preventivo-client-selected = [green]Client : { $name }[/green]
cli-preventivo-validity-info = [dim]Validité : { $days } jours (expiration : { $date })[/dim]

cli-preventivo-add-items-title = [bold]Ajouter des lignes[/bold]
cli-preventivo-add-items-hint = [dim]Entrez une description vide pour terminer[/dim]
cli-preventivo-item-description-prompt = Description de l'article { $num }
cli-preventivo-item-quantity-prompt = Quantité
cli-preventivo-item-price-prompt = Prix unitaire (€)
cli-preventivo-item-vat-prompt = Taux de TVA (%)
cli-preventivo-item-unit-prompt = Unité de mesure
cli-preventivo-item-added = [green]Ajouté : { $desc } - €{ $total }[/green]

cli-preventivo-no-items = [yellow]Aucune ligne ajoutée. Création du devis annulée.[/yellow]
cli-preventivo-add-notes-prompt = Ajouter des notes ?
cli-preventivo-notes-prompt = Notes
cli-preventivo-add-conditions-prompt = Ajouter des termes et conditions ?
cli-preventivo-conditions-prompt = Termes et conditions

cli-preventivo-error-general = [red]Erreur : { $error }[/red]
cli-preventivo-created-success = [bold green]Devis créé avec succès ![/bold green]
cli-preventivo-next-convert = [dim]Suivant : openfatture preventivo converti { $id } (pour créer une facture)[/dim]

### preventivo - Console Output (lista)
cli-preventivo-invalid-status = [red]Statut non valide : { $stato }[/red]
cli-preventivo-valid-statuses = Valides : { $statuses }
cli-preventivo-no-preventivi = [yellow]Aucun devis trouvé[/yellow]
cli-preventivo-list-title = Devis ({ $count })

cli-preventivo-column-id = ID
cli-preventivo-column-number = Numéro
cli-preventivo-column-date = Date
cli-preventivo-column-expiration = Expiration
cli-preventivo-column-client = Client
cli-preventivo-column-total = Total
cli-preventivo-column-status = Statut

### preventivo - Console Output (show)
cli-preventivo-not-found = [red]Devis { $id } non trouvé[/red]
cli-preventivo-show-title = [bold blue]Devis { $numero }/{ $anno }[/bold blue]

cli-preventivo-field-client = Client
cli-preventivo-field-issue-date = Date d'émission
cli-preventivo-field-expiration = Date d'expiration
cli-preventivo-field-validity = Validité
cli-preventivo-field-validity-days = { $days } jours
cli-preventivo-field-status = Statut
cli-preventivo-warning-expired = [red]ATTENTION[/red]
cli-preventivo-expired = [red]Expiré ![/red]

cli-preventivo-line-items-title = [bold]Lignes :[/bold]
cli-preventivo-line-item-number = #
cli-preventivo-line-item-description = Description
cli-preventivo-line-item-quantity = Qté
cli-preventivo-line-item-price = Prix
cli-preventivo-line-item-vat = TVA%
cli-preventivo-line-item-total = Total

cli-preventivo-totals-title = [bold]Totaux :[/bold]
cli-preventivo-total-imponibile = Base imposable
cli-preventivo-total-iva = TVA
cli-preventivo-total-total = [bold]TOTAL[/bold]

cli-preventivo-notes-title = [bold]Notes :[/bold]
cli-preventivo-conditions-title = [bold]Termes et Conditions :[/bold]

### preventivo - Console Output (delete)
cli-preventivo-confirm-delete = Supprimer le devis { $numero }/{ $anno } ?
cli-preventivo-cancelled = Annulé.
cli-preventivo-deleted = [green]Devis { $numero }/{ $anno } supprimé[/green]

### preventivo - Console Output (converti)
cli-preventivo-convert-title = [bold blue]Conversion du Devis en Facture[/bold blue]
cli-preventivo-convert-summary-numero = [cyan]Devis : { $numero }/{ $anno }[/cyan]
cli-preventivo-convert-summary-client = [cyan]Client : { $name }[/cyan]
cli-preventivo-convert-summary-total = [cyan]Total : €{ $total }[/cyan]
cli-preventivo-invalid-doc-type = [red]Type de document non valide : { $tipo }[/red]
cli-preventivo-valid-doc-types = Valides : TD01, TD06, etc.
cli-preventivo-confirm-convert = Convertir en facture ?
cli-preventivo-convert-cancelled = [yellow]Annulé.[/yellow]
cli-preventivo-converted-success = [bold green]Devis converti avec succès ![/bold green]

cli-preventivo-invoice-title = Facture { $numero }/{ $anno }
cli-preventivo-invoice-field-client = Client
cli-preventivo-invoice-field-date = Date
cli-preventivo-invoice-field-doc-type = Type de document
cli-preventivo-invoice-field-items = Lignes
cli-preventivo-invoice-field-imponibile = Base imposable
cli-preventivo-invoice-field-iva = TVA
cli-preventivo-invoice-field-total = [bold]TOTAL[/bold]

cli-preventivo-invoice-id-info = [dim]ID Facture : { $id }[/dim]
cli-preventivo-original-preventivo-info = [dim]Devis original : { $numero }/{ $anno } (ID : { $id })[/dim]
cli-preventivo-next-send = [dim]Suivant : openfatture fattura invia { $id } --pec[/dim]

### preventivo - Console Output (aggiorna-stato)
cli-preventivo-status-updated = [green]Statut du devis mis à jour : { $stato }[/green]

## Commandes IA

### ai - Textes d'aide
cli-ai-help-text = Texte à traiter
cli-ai-help-invoice-id = ID de facture
cli-ai-help-provider = Fournisseur IA (openai, anthropic, ollama)
cli-ai-help-model = Nom du modèle IA
cli-ai-help-temperature = Température (0,0-2,0)
cli-ai-help-max-tokens = Tokens maximum
cli-ai-help-interactive = Mode interactif
cli-ai-help-session-id = ID de session de chat
cli-ai-help-stream = Activer le streaming
cli-ai-help-save-session = Enregistrer la session après le chat
cli-ai-help-list-sessions = Lister les sessions disponibles
cli-ai-help-months = Nombre de mois à prévoir
cli-ai-help-confidence = Niveau de confiance (0,0-1,0)
cli-ai-help-retrain = Réentraîner le modèle avec les dernières données
cli-ai-help-show-metrics = Afficher les métriques du modèle
cli-ai-help-invoice-numero = Numéro de facture
cli-ai-help-year = Année de facture
cli-ai-help-context = Contexte supplémentaire
cli-ai-help-language = Code de langue
cli-ai-help-format = Format de sortie
cli-ai-help-embedding-model = Modèle d'intégration
cli-ai-help-chunk-size = Taille de bloc pour les documents
cli-ai-help-collection = Nom de collection RAG
cli-ai-help-query = Requête de recherche
cli-ai-help-top-k = Nombre de résultats
cli-ai-help-rating = Évaluation (1-5)
cli-ai-help-comment = Texte du commentaire
cli-ai-help-duration = Durée d'enregistrement en secondes
cli-ai-help-save-audio = Enregistrer les fichiers audio pour le débogage
cli-ai-help-no-playback = Désactiver la lecture audio
cli-ai-help-sample-rate = Fréquence d'échantillonnage audio
cli-ai-help-service-description = Description du service à développer
cli-ai-help-hours-worked = Heures travaillées
cli-ai-help-hourly-rate = Tarif horaire (€)
cli-ai-help-project-name = Nom du projet
cli-ai-help-technologies = Technologies utilisées (séparées par des virgules)
cli-ai-help-json-output = Sortie au format JSON
cli-ai-help-stream = Streaming de réponse en temps réel
cli-ai-help-client-pa = Client est Administration Publique
cli-ai-help-client-foreign = Client étranger (hors Italie)
cli-ai-help-country-code = Code pays du client (IT, FR, DE, etc.)
cli-ai-help-service-category = Catégorie de service
cli-ai-help-amount-eur = Montant en euros
cli-ai-help-ateco-code = Code ATECO
cli-ai-help-chat-message = Message à envoyer au chat

### ai - Sortie console (describe)
cli-ai-describe-title = [bold cyan]Génération de Description de Facture par IA[/bold cyan]
cli-ai-describe-input-prompt = [cyan]Entrez une brève description :[/cyan]
cli-ai-describe-processing = [yellow]Traitement par IA...[/yellow]
cli-ai-describe-result-title = [bold green]Description Générée :[/bold green]
cli-ai-describe-result-text = [white]{ $text }[/white]
cli-ai-describe-copy-hint = [dim]Vous pouvez copier cette description lors de la création d'une facture[/dim]
cli-ai-describe-error = [red]Erreur lors de la génération de la description : { $error }[/red]
cli-ai-describe-activity = Activité : [yellow]{ $activity }[/yellow]
cli-ai-describe-generating = Génération d'une description détaillée...
cli-ai-describe-input-service = Service
cli-ai-describe-input-hours = Heures travaillées
cli-ai-describe-input-rate = Tarif horaire
cli-ai-describe-input-project = Projet
cli-ai-describe-input-technologies = Technologies
cli-ai-describe-input-client-pa = Client PA
cli-ai-describe-input-client-foreign = Client étranger
cli-ai-describe-input-country = Pays
cli-ai-describe-input-category = Catégorie
cli-ai-describe-input-amount = Montant
cli-ai-describe-input-ateco = Code ATECO

### ai - Sortie console (suggest-vat)
cli-ai-vat-title = [bold cyan]Suggestion de Taux IVA par IA[/bold cyan]
cli-ai-vat-input-prompt = [cyan]Description du service/produit :[/cyan]
cli-ai-vat-processing = [yellow]Analyse par IA...[/yellow]
cli-ai-vat-result-title = [bold green]Taux IVA Suggéré :[/bold green]
cli-ai-vat-rate = [white]{ $rate }%[/white]
cli-ai-vat-reasoning-title = [bold yellow]Raisonnement :[/bold yellow]
cli-ai-vat-reasoning-text = [white]{ $reasoning }[/white]
cli-ai-vat-warning = [yellow]Vérifiez toujours auprès d'un conseiller fiscal pour les cas complexes[/yellow]
cli-ai-vat-error = [red]Erreur lors de la suggestion du taux IVA : { $error }[/red]
cli-ai-vat-query = Requête : [yellow]{ $query }[/yellow]
cli-ai-vat-analyzing = Analyse de la réglementation TVA...
cli-ai-vat-disclaimer = [yellow]Ceci est une suggestion. Consultez toujours un comptable.[/yellow]
cli-ai-vat-processing = Traitement de la suggestion de TVA...
cli-ai-vat-input-service = Service
cli-ai-vat-input-client-pa = Client PA
cli-ai-vat-input-client-foreign = Client étranger
cli-ai-input-country = Pays
cli-ai-vat-input-category = Catégorie
cli-ai-vat-input-amount = Montant
cli-ai-vat-input-ateco = Code ATECO
cli-ai-vat-result-rate = Taux de TVA recommandé
cli-ai-vat-result-nature = Nature (si applicable)
cli-ai-vat-result-reasoning = Justification
cli-ai-vat-result-legal-ref = Référence légale
cli-ai-vat-result-confidence = Niveau de confiance
cli-ai-vat-result-warnings = Avertissements
cli-ai-vat-result-note = Note supplémentaire

### ai - Sortie console (chat)
cli-ai-chat-title = [bold cyan]Chat Vocal IA[/bold cyan]
cli-ai-chat-welcome = [cyan]Bienvenue dans l'Assistant IA OpenFatture ![/cyan]
cli-ai-chat-welcome-help = [dim]Posez vos questions ou tapez « exit » pour quitter[/dim]
cli-ai-chat-session-loaded = [green]Session chargée : { $session_id }[/green]
cli-ai-chat-session-created = [green]Nouvelle session créée : { $session_id }[/green]
cli-ai-chat-prompt = [bold cyan]Vous :[/bold cyan]
cli-ai-chat-assistant-prefix = [bold green]Assistant :[/bold green]
cli-ai-chat-thinking = [yellow]Réflexion...[/yellow]
cli-ai-chat-tool-calling = [yellow]Exécution de l'outil : { $tool_name }[/yellow]
cli-ai-chat-tool-result = [dim]Résultat de l'outil : { $result }[/dim]
cli-ai-chat-session-saved = [green]Session enregistrée[/green]
cli-ai-chat-goodbye = [cyan]Au revoir ! Session enregistrée.[/cyan]
cli-ai-chat-error = [red]Erreur : { $error }[/red]
cli-ai-chat-cost-info = [dim]Tokens : { $tokens } | Coût : €{ $cost }[/dim]
cli-ai-chat-assistant-response = [bold cyan]Assistant :[/bold cyan]
cli-ai-chat-you = [bold green]Vous :[/bold green]
cli-ai-chat-instructions = Instructions : Posez des questions sur les factures, clients, TVA ou gestion fiscale
cli-ai-chat-invalid-session = [red]Session introuvable : { $session_id }[/red]
cli-ai-chat-no-sessions = [yellow]Aucune session disponible[/yellow]
cli-ai-chat-exported = [green]Conversation exportée : { $path }[/green]
cli-ai-chat-export-error = [red]Erreur d'exportation : { $error }[/red]

### Métriques IA
cli-ai-metrics-provider = Fournisseur
cli-ai-metrics-model = Modèle
cli-ai-metrics-tokens = Tokens utilisés
cli-ai-metrics-cost = Coût estimé
cli-ai-metrics-latency = Latence

### Erreurs générales IA
cli-ai-error-unknown = Erreur inconnue lors de l'exécution de la commande IA
cli-ai-error-provider-init = Erreur d'initialisation du fournisseur IA : { $error }
cli-ai-error-context-load = Erreur de chargement du contexte métier : { $error }

### ai - Sortie console (voice-chat)
cli-ai-voice-title = [bold cyan]Chat Vocal IA[/bold cyan]
cli-ai-voice-welcome = [cyan]Bienvenue dans le Chat Vocal ![/cyan]
cli-ai-voice-recording-prompt = [yellow]Appuyez sur ENTRÉE pour commencer l'enregistrement ({ $duration }s)...[/yellow]
cli-ai-voice-recording = [bold yellow]Enregistrement...[/bold yellow]
cli-ai-voice-processing = [yellow]Traitement de l'audio...[/yellow]
cli-ai-voice-transcription-title = [bold green]Vous avez dit :[/bold green]
cli-ai-voice-transcription-text = [white]{ $text }[/white]
cli-ai-voice-language-detected = [dim]Langue : { $language }[/dim]
cli-ai-voice-thinking = [yellow]L'assistant réfléchit...[/yellow]
cli-ai-voice-response-title = [bold green]Assistant :[/bold green]
cli-ai-voice-response-text = [white]{ $text }[/white]
cli-ai-voice-playing = [cyan]Lecture de la réponse...[/cyan]
cli-ai-voice-audio-saved = [dim]Audio enregistré : { $path }[/dim]
cli-ai-voice-goodbye = [cyan]Au revoir ![/cyan]
cli-ai-voice-error = [red]Erreur : { $error }[/red]

### ai - Sortie console (forecast)
cli-ai-forecast-title = [bold cyan]Prévision de Trésorerie par IA[/bold cyan]
cli-ai-forecast-loading-data = [yellow]Chargement des données historiques...[/yellow]
cli-ai-forecast-data-stats = [cyan]Factures : { $invoices } | Paiements : { $payments }[/cyan]
cli-ai-forecast-training = [yellow]Entraînement des modèles ML...[/yellow]
cli-ai-forecast-training-progress = [yellow]{ $progress }%[/yellow]
cli-ai-forecast-predicting = [yellow]Génération de la prévision...[/yellow]
cli-ai-forecast-results-title = [bold green]Prévision de Trésorerie - Les { $months } { $months ->
    [one] mois prochain
   *[other] mois prochains
}[/bold green]
cli-ai-forecast-month = [cyan]{ $month }[/cyan]
cli-ai-forecast-predicted = Prévu : € { $amount }
cli-ai-forecast-confidence = Confiance : { $confidence }%
cli-ai-forecast-lower-bound = Borne inférieure : € { $lower }
cli-ai-forecast-upper-bound = Borne supérieure : € { $upper }
cli-ai-forecast-metrics-title = [bold yellow]Métriques du Modèle :[/bold yellow]
cli-ai-forecast-mae = MAE : { $mae }
cli-ai-forecast-rmse = RMSE : { $rmse }
cli-ai-forecast-mape = MAPE : { $mape }%
cli-ai-forecast-insufficient-data = [yellow]Données insuffisantes. Au moins { $required } factures/paiements nécessaires pour l'entraînement.[/yellow]
cli-ai-forecast-error = [red]Erreur de prévision : { $error }[/red]

### ai - Sortie console (intelligence)
cli-ai-intelligence-title = [bold cyan]Analyse Business Intelligence[/bold cyan]
cli-ai-intelligence-analyzing = [yellow]Analyse des données métier...[/yellow]
cli-ai-intelligence-report-title = [bold green]Analyses Métier :[/bold green]
cli-ai-intelligence-section = [bold yellow]{ $section }[/bold yellow]
cli-ai-intelligence-insight = • { $insight }
cli-ai-intelligence-error = [red]Erreur d'analyse : { $error }[/red]

### ai - Sortie console (compliance)
cli-ai-compliance-title = [bold cyan]Vérification de Conformité[/bold cyan]
cli-ai-compliance-checking = [yellow]Vérification de la facture { $numero }/{ $anno }...[/yellow]
cli-ai-compliance-passed = [bold green]Tous les contrôles de conformité réussis[/bold green]
cli-ai-compliance-warnings = [yellow]{ $count } { $count ->
    [one] avertissement détecté
   *[other] avertissements détectés
}[/yellow]
cli-ai-compliance-errors = [red]{ $count } { $count ->
    [one] erreur détectée
   *[other] erreurs détectées
}[/red]
cli-ai-compliance-check-item = [{ $status }] { $message }
cli-ai-compliance-error = [red]Erreur de vérification de conformité : { $error }[/red]

### ai - Sortie console (rag)
cli-ai-rag-title = [bold cyan]Recherche de Documents RAG[/bold cyan]
cli-ai-rag-indexing = [yellow]Indexation des documents...[/yellow]
cli-ai-rag-indexed = [green]{ $count } { $count ->
    [one] document indexé
   *[other] documents indexés
}[/green]
cli-ai-rag-searching = [yellow]Recherche dans la base de connaissances...[/yellow]
cli-ai-rag-results-title = [bold green]Résultats de la Recherche :[/bold green]
cli-ai-rag-result-item = { $rank }. [bold]{ $title }[/bold] (score : { $score })
cli-ai-rag-result-text = { $text }
cli-ai-rag-no-results = [yellow]Aucun résultat trouvé[/yellow]
cli-ai-rag-error = [red]Erreur RAG : { $error }[/red]

### ai - Sortie console (feedback)
cli-ai-feedback-title = [bold cyan]Retour d'IA[/bold cyan]
cli-ai-feedback-prompt-rating = [cyan]Évaluer la réponse (1-5) :[/cyan]
cli-ai-feedback-prompt-comment = [cyan]Commentaire (optionnel) :[/cyan]
cli-ai-feedback-thanks = [green]Merci pour votre retour ![/green]
cli-ai-feedback-saved = [green]Retour enregistré dans la session { $session_id }[/green]
cli-ai-feedback-error = [red]Erreur de retour : { $error }[/red]

## ============================================================================
## EVENTS Commands - Historique des Événements et Piste d'Audit
## ============================================================================

### Help Texts - Commandes et Options
cli-events-help = Afficher et analyser l'historique des événements

# list command
cli-events-list-help-type = Filtrer par type d'événement
cli-events-list-help-entity = Filtrer par type d'entité (facture, client, paiement, etc.)
cli-events-list-help-entity-id = Filtrer par ID d'entité
cli-events-list-help-last-hours = Afficher les événements des N dernières heures
cli-events-list-help-last-days = Afficher les événements des N derniers jours
cli-events-list-help-limit = Nombre maximum d'événements à afficher

# show command
cli-events-show-help-event-id = ID d'Événement (UUID)

# stats command
cli-events-stats-help-last-hours = Statistiques des N dernières heures
cli-events-stats-help-last-days = Statistiques des N derniers jours

# timeline command
cli-events-timeline-help-entity-type = Type d'entité (invoice, client, etc.)
cli-events-timeline-help-entity-id = ID d'Entité

# search command
cli-events-search-help-query = Chaîne de recherche
cli-events-search-help-limit = Nombre maximum de résultats

# dashboard command
cli-events-dashboard-help-days = Nombre de jours à analyser

# trends command
cli-events-trends-help-days = Nombre de jours à analyser
cli-events-trends-help-type = Filtrer par type d'événement

### Table Columns - En-têtes de Colonnes
cli-events-column-timestamp = Date/Heure
cli-events-column-event-type = Type d'Événement
cli-events-column-entity = Entité
cli-events-column-entity-type = Type d'Entité
cli-events-column-summary = Résumé
cli-events-column-count = Nombre
cli-events-column-percentage = Pourcentage
cli-events-column-match = Correspondance

### Titles and Headers - Titres et En-têtes
cli-events-list-title = Historique des Événements ({ $count } événements)
cli-events-show-panel-title = [bold]Détails de l'Événement : { $event_type }[/bold]
cli-events-stats-table-by-type = Événements par Type
cli-events-stats-table-by-entity = Événements par Type d'Entité
cli-events-stats-panel-title = [bold]Statistiques des Événements - { $range }[/bold]
cli-events-timeline-panel-title = [bold]Chronologie des Événements : { $entity_type } #{ $entity_id }[/bold]
cli-events-search-results-title = Résultats de Recherche : '{ $query }' ({ $count } événements)
cli-events-types-table-title = Types d'Événement Disponibles
cli-events-dashboard-panel-title = [bold]Tableau de Bord d'Analyse des Événements - { $days } Derniers Jours[/bold]
cli-events-dashboard-table-entity-activity = Activité par Entité
cli-events-trends-panel-title = [bold]Tendances des Événements - { $days } Derniers Jours[/bold]
cli-events-trends-panel-title-filtered = [bold]Tendances des Événements - { $days } Derniers Jours ({ $event_type })[/bold]

### Labels - Étiquettes de Champs
cli-events-show-label-event-id = ID d'Événement
cli-events-show-label-event-type = Type d'Événement
cli-events-show-label-occurred-at = Survenu le
cli-events-show-label-published-at = Publié le
cli-events-show-label-entity-type = Type d'Entité
cli-events-show-label-entity-id = ID d'Entité
cli-events-show-label-user-id = ID d'Utilisateur
cli-events-show-label-event-data = Données de l'Événement
cli-events-show-label-metadata = Métadonnées

### Dashboard Metrics - Métriques du Tableau de Bord
cli-events-dashboard-metric-total = Événements Totaux
cli-events-dashboard-metric-types = Types d'Événement
cli-events-dashboard-metric-velocity = Événements/Heure (24h)
cli-events-dashboard-metric-trend = Tendance
cli-events-dashboard-section-top-types = [bold]Principaux Types d'Événement[/bold]
cli-events-dashboard-column-events = Événements

### Messages - Messages de Sortie
cli-events-no-events = [yellow]Aucun événement trouvé correspondant aux critères[/yellow]
cli-events-show-not-found = [red]Événement avec ID '{ $event_id }' non trouvé[/red]
cli-events-filters-applied =
    [dim]Filtres : { $filters }[/dim]
cli-events-stats-all-time = Tout le Temps
cli-events-stats-last-hours = { $hours } Dernières Heures
cli-events-stats-last-days = { $days } Derniers Jours
cli-events-stats-total =
    [bold]Événements Totaux :[/bold] { $total }

cli-events-stats-most-recent = [bold]Événement le Plus Récent :[/bold] { $event_type } le { $timestamp }
cli-events-stats-oldest = [bold]Événement le Plus Ancien :[/bold] { $event_type } le { $timestamp }
cli-events-timeline-no-events = [yellow]Aucun événement trouvé pour { $entity_type } avec ID { $entity_id }[/yellow]
cli-events-timeline-total =
    [dim]Total des événements : { $total }[/dim]
cli-events-search-no-results = [yellow]Aucun événement trouvé correspondant à '{ $query }'[/yellow]
cli-events-types-no-events = [yellow]Aucun événement enregistré pour le moment[/yellow]
cli-events-dashboard-most-recent = [dim]Plus Récent : { $event_type } le { $timestamp }[/dim]
cli-events-trends-no-events = [yellow]Aucun événement trouvé pour la période spécifiée[/yellow]
cli-events-trends-summary = [dim]Total : { $total } événements | Moyenne : { $avg } événements/jour[/dim]

## ============================================================================
## LIGHTNING Commands - Lightning Network et Conformité
## ============================================================================

### Help Texts - Commandes et Options
cli-lightning-help = Gestion des paiements Lightning Network
cli-lightning-report-help = Générer des rapports de conformité
cli-lightning-aml-help = Gestion Lutte contre le Blanchiment

### Status Command
cli-lightning-status-title = Statut Lightning Network
cli-lightning-status-disabled = Statut : Désactivé
cli-lightning-status-disabled-hint-env = Définissez lightning_enabled=true dans .env pour activer les paiements Lightning
cli-lightning-status-disabled-hint-cmd = Utilisez 'openfatture config set lightning_enabled true' pour activer
cli-lightning-status-enabled = Statut : Activé
cli-lightning-status-host = Hôte : { $host }
cli-lightning-status-timeout = Délai d'expiration : { $timeout }s
cli-lightning-status-max-retries = Tentatives max : { $max_retries }
cli-lightning-status-btc-provider = Fournisseur BTC : { $provider }
cli-lightning-status-liquidity = Surveillance de liquidité : { $status }

cli-lightning-btc-provider-coingecko = CoinGecko
cli-lightning-btc-provider-cmc = CoinMarketCap
cli-lightning-btc-provider-fallback = Fallback
cli-lightning-liquidity-enabled = Activé
cli-lightning-liquidity-disabled = Désactivé

### Invoice Command
cli-lightning-disabled-error = Lightning est désactivé. Activez avec : openfatture config set lightning_enabled true
cli-lightning-invoice-title = Création de Facture Lightning
cli-lightning-invoice-not-available = Fonctionnalité pas encore disponible - Intégration Lightning en développement

### Channels Command
cli-lightning-channels-title = Canaux Lightning
cli-lightning-channels-not-available = Aucun canal configuré - Intégration Lightning en développement

### Liquidity Command
cli-lightning-liquidity-title = Liquidité des Canaux
cli-lightning-liquidity-not-available = Surveillance de liquidité non disponible - Intégration Lightning en développement

### Compliance Check Command
cli-lightning-compliance-opt-tax-year = Année fiscale à vérifier (par défaut : année en cours)
cli-lightning-compliance-opt-verbose = Afficher les informations détaillées

cli-lightning-compliance-title =

    [bold cyan]Vérification de Conformité Lightning - { $year }[/bold cyan]

cli-lightning-compliance-summary-title = [bold]Résumé de l'Année Fiscale[/bold]
cli-lightning-compliance-summary-payments = Nombre de paiements :
cli-lightning-compliance-summary-revenue = Revenus totaux (EUR) :
cli-lightning-compliance-summary-gains = Plus-values totales (EUR) :
cli-lightning-compliance-summary-tax = Impôts estimés (EUR) :

cli-lightning-compliance-aml-title = [bold]Conformité LCB (Seuil : 5 000 EUR)[/bold]
cli-lightning-compliance-aml-total = Total au-dessus du seuil :
cli-lightning-compliance-aml-verified = Vérifiés :
cli-lightning-compliance-aml-unverified = Non vérifiés :
cli-lightning-compliance-aml-status-ok = OK
cli-lightning-compliance-aml-status-require = { $count } NÉCESSITENT UNE VÉRIFICATION

cli-lightning-compliance-quadro-title = [bold]Déclaration Quadro RW (Obligatoire à partir de 2025)[/bold]
cli-lightning-compliance-quadro-count = Factures nécessitant une déclaration :
cli-lightning-compliance-action-required = Action requise :
cli-lightning-compliance-quadro-action = [yellow]Déclarer toutes les possessions crypto dans Quadro RW[/yellow]
cli-lightning-compliance-status = Statut :
cli-lightning-compliance-quadro-status-ok = [green]Aucune déclaration requise[/green]

cli-lightning-compliance-data-quality-title = [bold]Qualité des Données[/bold]
cli-lightning-compliance-data-quality-missing = Factures avec données fiscales manquantes :
cli-lightning-compliance-data-quality-action = [red]Ajouter le taux BTC/EUR et le montant EUR pour la conformité fiscale[/red]
cli-lightning-compliance-data-quality-status-ok = [green]Toutes les factures réglées ont des données fiscales[/green]

cli-lightning-compliance-issue-aml = { $count } paiement(s) LCB non vérifié(s)
cli-lightning-compliance-issue-missing-data = { $count } facture(s) sans données fiscales
cli-lightning-compliance-issues-found = [bold red]Problèmes de Conformité Trouvés : { $issues }[/bold red]

cli-lightning-compliance-passed = [bold green]Toutes les Vérifications de Conformité Réussies[/bold green]

cli-lightning-compliance-verbose-title = [bold]Paiements LCB Non Vérifiés :[/bold]
cli-lightning-compliance-verbose-item =   • { $hash }... - { $amount } EUR - Réglé : { $date }

cli-lightning-compliance-error = [bold red]Erreur lors de la vérification de conformité : { $error }[/bold red]

### Report Commands - Common Options
cli-lightning-report-opt-tax-year = Année fiscale pour le rapport
cli-lightning-report-opt-format = Format de sortie : json ou csv
cli-lightning-report-opt-output = Chemin du fichier de sortie (optionnel, imprime sur stdout si non fourni)

cli-lightning-report-invalid-format = [bold red]Format invalide. Utilisez 'json' ou 'csv'[/bold red]
cli-lightning-report-saved = [green]Rapport enregistré dans : { $path }[/green]

cli-lightning-report-summary = [cyan]Total de factures dans le rapport : { $count }[/cyan]

### Quadro RW Report
cli-lightning-report-quadro-title =

    [bold cyan]Génération du Rapport Quadro RW - { $year } ({ $format })[/bold cyan]

cli-lightning-report-quadro-error = [bold red]Erreur lors de la génération du rapport Quadro RW : { $error }[/bold red]

### Capital Gains Report
cli-lightning-report-gains-title =

    [bold cyan]Génération du Rapport Plus-Values - { $year } ({ $format })[/bold cyan]

cli-lightning-report-gains-summary-count = [cyan]Total de factures avec plus-values : { $count }[/cyan]
cli-lightning-report-gains-summary-total = [yellow]Plus-values totales : { $total } EUR[/yellow]
cli-lightning-report-gains-summary-tax = [red]Impôts estimés ({ $rate }%) : { $tax } EUR[/red]
cli-lightning-report-gains-error = [bold red]Erreur lors de la génération du rapport plus-values : { $error }[/bold red]

### AML Report
cli-lightning-aml-opt-threshold = Seuil LCB en EUR
cli-lightning-aml-opt-format = Format de sortie : json uniquement
cli-lightning-aml-opt-verbose = Afficher les informations détaillées

cli-lightning-aml-report-title =

    [bold cyan]Génération du Rapport de Conformité LCB (Seuil : { $threshold } EUR)[/bold cyan]

cli-lightning-aml-report-summary-total = [cyan]Total au-dessus du seuil : { $total }[/cyan]
cli-lightning-aml-report-summary-verified = [green]Vérifiés : { $verified }[/green]
cli-lightning-aml-report-summary-unverified-ok = Non vérifiés : 0
cli-lightning-aml-report-summary-unverified-warning = Non vérifiés : { $count }
cli-lightning-aml-report-summary-rate = [yellow]Taux de conformité : { $rate }%[/yellow]

cli-lightning-aml-report-action-required =

    [bold yellow]Action Requise : Vérifier les paiements non vérifiés avec le processus LCB[/bold yellow]
cli-lightning-aml-report-action-hint = [dim]Utilisez : openfatture lightning aml list-unverified pour voir les détails[/dim]

cli-lightning-aml-report-error = [bold red]Erreur lors de la génération du rapport LCB : { $error }[/bold red]

### AML List Unverified Command
cli-lightning-aml-list-title =

    [bold cyan]Paiements LCB Non Vérifiés (Seuil : { $threshold } EUR)[/bold cyan]

cli-lightning-aml-list-empty = [green]Aucun paiement non vérifié trouvé[/green]

cli-lightning-aml-list-table-title = Paiements Non Vérifiés ({ $count } au total)
cli-lightning-aml-list-col-hash = Hash de Paiement
cli-lightning-aml-list-col-amount = Montant (EUR)
cli-lightning-aml-list-col-settled = Réglé Le
cli-lightning-aml-list-col-fattura = ID Facture
cli-lightning-aml-list-col-client = ID Client
cli-lightning-aml-list-col-description = Description

cli-lightning-aml-list-action-required = [bold yellow]Action Requise : Ces paiements nécessitent une vérification d'identité du client[/bold yellow]
cli-lightning-aml-list-action-hint = [dim]Utilisez : openfatture lightning aml verify <payment-hash> --verified-by <email>[/dim]

cli-lightning-aml-list-error = [bold red]Erreur lors du listage des paiements non vérifiés : { $error }[/bold red]

### AML Verify Command
cli-lightning-aml-verify-arg-hash = Hash du paiement à vérifier
cli-lightning-aml-verify-opt-by = Email de la personne qui vérifie
cli-lightning-aml-verify-opt-notes = Notes de vérification (optionnel)
cli-lightning-aml-verify-opt-client = ID Client (optionnel)

cli-lightning-aml-verify-title =

    [bold cyan]Vérification du Paiement LCB : { $hash }...[/bold cyan]

cli-lightning-aml-verify-not-found = [bold red]Facture non trouvée : { $hash }[/bold red]
cli-lightning-aml-verify-already-verified = [yellow]Paiement déjà vérifié le { $date }[/yellow]
cli-lightning-aml-verify-below-threshold = [yellow]Le paiement ne dépasse pas le seuil LCB, mais est marqué comme vérifié quand même[/yellow]
cli-lightning-aml-verify-success = [green]Paiement vérifié avec succès[/green]

cli-lightning-aml-verify-label-hash = Hash de Paiement :
cli-lightning-aml-verify-label-amount = Montant (EUR) :
cli-lightning-aml-verify-label-settled = Réglé Le :
cli-lightning-aml-verify-label-by = Vérifié Par :
cli-lightning-aml-verify-label-at = Vérifié Le :
cli-lightning-aml-verify-label-notes = Notes :

cli-lightning-aml-verify-error = [bold red]Erreur lors de la vérification du paiement : { $error }[/bold red]

## ============================================================================
## REPORT Commands - Rapports et Statistiques
## ============================================================================

### Help Texts - Commandes et Options
cli-report-iva-help-anno = Année
cli-report-iva-help-trimestre = Trimestre (Q1-Q4)
cli-report-clienti-help-anno = Année
cli-report-scadenze-help-finestra = Nombre de jours considérés comme "bientôt échus" (par défaut : 14)

### Titles and Headers - TVA Report
cli-report-iva-title =

    [bold blue]Rapport TVA - { $anno }[/bold blue]

cli-report-iva-quarter =

    [cyan]Trimestre : { $trimestre } ({ $mese_inizio }-{ $mese_fine })[/cyan]

cli-report-iva-full-year =

    [cyan]Année complète[/cyan]

cli-report-iva-summary-title = Résumé TVA
cli-report-iva-breakdown-title =

    [bold]Répartition par taux de TVA :[/bold]

### Titles and Headers - Client Report
cli-report-clienti-title =

    [bold blue]Rapport de Chiffre d'Affaires Clients - { $anno }[/bold blue]

cli-report-clienti-table-title = Meilleurs Clients - { $anno }

### Titles and Headers - Due Dates Report
cli-report-scadenze-title =

    [bold blue]Aperçu des Dates d'Échéance[/bold blue]

### Table Columns - TVA Report
cli-report-iva-column-metric = Métrique
cli-report-iva-column-amount = Montant
cli-report-iva-column-vat-rate = Taux de TVA
cli-report-iva-column-imponibile = Base Imposable
cli-report-iva-column-vat = TVA

### Table Columns - Client Report
cli-report-clienti-column-rank = Rang
cli-report-clienti-column-client = Client
cli-report-clienti-column-invoices = Factures
cli-report-clienti-column-revenue = Chiffre d'Affaires

### Table Columns - Due Dates Report
cli-report-scadenze-column-invoice = Facture
cli-report-scadenze-column-client = Client
cli-report-scadenze-column-due-date = Date d'Échéance
cli-report-scadenze-column-days-delta = Δ jours
cli-report-scadenze-column-residual = Restant
cli-report-scadenze-column-paid = Payé
cli-report-scadenze-column-total = Total
cli-report-scadenze-column-status = Statut

### Labels - TVA Report
cli-report-iva-label-num-invoices = Nombre de factures
cli-report-iva-label-imponibile = Total base imposable
cli-report-iva-label-total-vat = Total TVA
cli-report-iva-label-total-revenue-bold = [bold]Chiffre d'affaires total[/bold]

### Messages - General
cli-report-no-invoices = [yellow]Aucune facture trouvée pour la période sélectionnée[/yellow]
cli-report-no-invoices-year = [yellow]Aucune facture trouvée pour l'année sélectionnée[/yellow]

### Messages - TVA Report
cli-report-iva-error-invalid-quarter = [red]Trimestre non valide. Utilisez Q1, Q2, Q3 ou Q4[/red]

### Messages - Client Report
cli-report-clienti-total-revenue =

    [bold]Chiffre d'affaires total : { $totale }[/bold]

### Messages - Due Dates Report
cli-report-scadenze-no-outstanding =

    [green]Aucun paiement en attente. Toutes les factures sont réglées ![/green]

cli-report-scadenze-hidden-upcoming =

    [dim]… { $count } paiements futurs supplémentaires non affichés. Utilisez --finestra ou exportez les données du module de paiement pour plus de détails.[/dim]

cli-report-scadenze-total-outstanding =

    [bold]Solde total restant : { $totale }[/bold]

### Section Titles - Due Dates Report
cli-report-scadenze-section-overdue = [red]En retard[/red]
cli-report-scadenze-section-due-soon = [yellow]Bientôt échus (<= { $finestra } jours)[/yellow]
cli-report-scadenze-section-upcoming = [cyan]Prochains paiements[/cyan]

cli-report-scadenze-section-total = [bold { $color }]Total restant : { $totale } • Paiements : { $count }[/]

### Payment Status Labels - Due Dates Report
cli-report-scadenze-status-overdue = En retard
cli-report-scadenze-status-partial = Partiel
cli-report-scadenze-status-due = À payer

## ============================================================================
## PEC Commands - Test et Configuration PEC
## ============================================================================

### Titles
cli-pec-test-title = [bold blue]Test de Configuration PEC[/bold blue]
cli-pec-info-title = [bold blue]Configuration PEC[/bold blue]

### Labels
cli-pec-label-address = [cyan]Adresse PEC :[/cyan]
cli-pec-label-smtp-server = [cyan]Serveur SMTP :[/cyan]
cli-pec-label-smtp-port = [cyan]Port SMTP :[/cyan]
cli-pec-label-template = [cyan]Modèle :[/cyan] test/test_email.html + .txt
cli-pec-label-locale = [cyan]Langue :[/cyan]
cli-pec-label-password = Mot de passe
cli-pec-label-sdi-pec = PEC SDI

### Table Headers
cli-pec-table-setting = Paramètre
cli-pec-table-value = Valeur

### Error Messages
cli-pec-error-no-address = [red]Adresse PEC non configurée[/red]
cli-pec-error-no-address-hint = Exécutez : [cyan]openfatture init[/cyan] pour configurer
cli-pec-error-no-password = [red]Mot de passe PEC non configuré[/red]
cli-pec-error-no-password-hint = Définissez-le dans votre fichier .env : PEC_PASSWORD=votre_mot_de_passe

### Test Messages
cli-pec-sending-test = Envoi d'un email de test avec modèle professionnel...
cli-pec-test-success = [bold green]Email de test envoyé avec succès ![/bold green]
cli-pec-test-check-inbox = Vérifiez votre boîte PEC : { $pec_address }
cli-pec-test-email-includes = [dim]L'email comprend :[/dim]
cli-pec-test-feature-html = • HTML professionnel + texte brut
cli-pec-test-feature-branding = • Branding de votre entreprise
cli-pec-test-feature-language = • Langue : { $language }
cli-pec-test-more-testing = [dim]Pour plus de tests d'email :[/dim]
cli-pec-test-cmd-email-test = [cyan]openfatture email test[/cyan]  - Test email complet
cli-pec-test-cmd-email-preview = [cyan]openfatture email preview[/cyan] - Aperçu des modèles

cli-pec-test-failed =
    [red]Test échoué : { $error }[/red]
cli-pec-test-common-issues = [yellow]Problèmes courants :[/yellow]
cli-pec-issue-credentials = • Identifiants PEC incorrects
cli-pec-issue-smtp = • Serveur SMTP incorrect
cli-pec-issue-firewall = • Pare-feu bloquant le port 465
cli-pec-issue-mailbox = • Boîte PEC pleine

### Info Messages
cli-pec-not-set = [red]Non défini[/red]
cli-pec-password-set = [green]Défini[/green]

## ============================================================================
## NOTIFICHE Commands - Gestion des Notifications SDI
## ============================================================================

### Help Text
cli-notifiche-help-file-path = Chemin vers le fichier XML de notification SDI
cli-notifiche-help-no-email = Ignorer la notification automatique par email
cli-notifiche-help-tipo = Filtrer par type (AT, RC, NS, MC, NE)
cli-notifiche-help-limit = Nombre maximum de résultats
cli-notifiche-help-notification-id = ID de Notification

### Titles
cli-notifiche-process-title = [bold blue]Traitement de Notification SDI[/bold blue]
cli-notifiche-list-title = [bold blue]Notifications SDI[/bold blue]
cli-notifiche-show-title = [bold blue]{ $emoji } Notification { $id } : { $tipo }[/bold blue]

### Table Headers
cli-notifiche-table-field = Champ
cli-notifiche-table-value = Valeur
cli-notifiche-column-id = ID
cli-notifiche-column-type = Type
cli-notifiche-column-date = Date
cli-notifiche-column-invoice = Facture
cli-notifiche-column-client = Client
cli-notifiche-column-sdi-id = ID SDI

### Labels
cli-notifiche-label-type = Type
cli-notifiche-label-sdi-id = ID SDI
cli-notifiche-label-file = Fichier
cli-notifiche-label-date = Date
cli-notifiche-label-message = Message
cli-notifiche-label-errors = Erreurs
cli-notifiche-label-invoice = Facture
cli-notifiche-label-client = Client
cli-notifiche-label-invoice-status = État de la Facture
cli-notifiche-label-received = Reçu
cli-notifiche-label-description = Description
cli-notifiche-label-xml-path = Chemin XML

### Messages
cli-notifiche-file-not-found = [red]Fichier non trouvé : { $file_path }[/red]
cli-notifiche-file-label = [cyan]Fichier :[/cyan] { $name }
cli-notifiche-size-label = [cyan]Taille :[/cyan] { $size } octets
cli-notifiche-auto-email-enabled =
    [dim]Email automatique activé { $email }[/dim]

cli-notifiche-processing = Traitement de la notification...
cli-notifiche-error =
    [red]Erreur : { $error }[/red]
cli-notifiche-success = [bold green]Notification traitée avec succès ![/bold green]
cli-notifiche-errors-count = { $count } erreur(s)
cli-notifiche-email-sent =
    [dim]Notification par email envoyée à { $email }[/dim]

cli-notifiche-no-notifications = [yellow]Aucune notification trouvée[/yellow]
cli-notifiche-process-hint = [dim]Traitez les notifications avec :[/dim]
cli-notifiche-process-cmd = [cyan]openfatture notifiche process <fichier.xml>[/cyan]
cli-notifiche-list-table-title = Notifications ({ $count })

cli-notifiche-not-found = [red]Notification { $notification_id } non trouvée[/red]

## ============================================================================
## CONFIG Commands - Gestion de la Configuration
## ============================================================================

### Help Text
cli-config-help-key = Clé de configuration (ex. pec.address)
cli-config-help-value = Valeur de configuration

### Titles
cli-config-show-title = Configuration d'OpenFatture

### Table Headers
cli-config-column-setting = Paramètre
cli-config-column-value = Valeur

### Section Labels - Application
cli-config-label-app-version = Version de l'App
cli-config-label-debug-mode = Mode Debug

### Section Labels - Database
cli-config-label-database-url = URL de Base de Données

### Section Labels - Paths
cli-config-label-data-dir = Répertoire de Données
cli-config-label-archive-dir = Répertoire d'Archive
cli-config-label-certificates-dir = Répertoire de Certificats

### Section Labels - Company Data
cli-config-label-company-name = Nom de l'Entreprise
cli-config-label-partita-iva = Partita IVA
cli-config-label-codice-fiscale = Codice Fiscale
cli-config-label-tax-regime = Régime Fiscal

### Section Labels - PEC
cli-config-label-pec-address = Adresse PEC
cli-config-label-pec-smtp-server = Serveur SMTP PEC
cli-config-label-sdi-pec-address = Adresse PEC SDI

### Section Labels - Email & Notifications
cli-config-label-notification-email = Email de Notifications
cli-config-label-notifications-enabled = Notifications Activées
cli-config-label-locale = Langue
cli-config-label-email-logo-url = URL du Logo Email
cli-config-label-primary-color = Couleur Primaire
cli-config-label-secondary-color = Couleur Secondaire
cli-config-label-email-footer = Pied de page Email

### Section Labels - AI Configuration
cli-config-label-ai-provider = Fournisseur IA
cli-config-label-ai-model = Modèle IA
cli-config-label-ai-base-url = URL de Base IA
cli-config-label-ai-api-key = Clé API IA
cli-config-label-chat-enabled = Chat Activé
cli-config-label-chat-auto-save = Sauvegarde Auto du Chat
cli-config-label-max-messages = Max Messages/Session
cli-config-label-max-tokens = Max Tokens/Session
cli-config-label-tools-enabled = Outils Activés
cli-config-label-enabled-tools = Outils Activés

### Status Values
cli-config-not-set = [red]Non défini[/red]
cli-config-not-set-optional = [yellow]Non défini[/yellow]
cli-config-set = [green]Défini[/green]
cli-config-yes = [green]Oui[/green]
cli-config-no = [red]Non[/red]
cli-config-auto-generated = [dim]Auto-généré[/dim]
cli-config-all-tools = tous
cli-config-tools-count = { $count } outils

### Messages
cli-config-reload-success = [green]Configuration rechargée[/green]
cli-config-set-success = [green]Défini { $key } = { $value }[/green]
cli-config-saved-to = [dim]Enregistré dans { $path }[/dim]
cli-config-invalid-key = [red]Clé de configuration invalide : { $key }[/red]
cli-config-error = [red]Erreur : { $error }[/red]
