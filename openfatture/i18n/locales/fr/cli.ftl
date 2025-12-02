# Traductions des commandes CLI
# FR

## MAIN CLI

### main - Textes principaux
cli-main-title = OpenFatture - Système Open Source de Facturation Électronique
cli-main-description = Système complet pour gérer les factures électroniques FatturaPA
cli-main-version = Version { $version }

### main - Groupes de commandes
cli-main-group-invoices = 📄 Gestion des Factures
cli-main-group-clients = 👥 Gestion des Clients
cli-main-group-products = 📦 Gestion des Produits
cli-main-group-pec = 📧 PEC & SDI
cli-main-group-batch = 📊 Opérations par Lot
cli-main-group-ai = 🤖 Assistant IA
cli-main-group-payments = 💰 Suivi des Paiements
cli-main-group-preventivi = 📋 Devis
cli-main-group-events = 📅 Système d'Événements
cli-main-group-lightning = ⚡ Lightning Network
cli-main-group-web = 🌐 Interface Web

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
cli-fattura-create-title = [bold blue]🧾 Créer une Nouvelle Facture[/bold blue]
cli-fattura-select-client-title = [bold cyan]Sélection du Client[/bold cyan]
cli-fattura-no-clients-error = [red]Aucun client trouvé. Ajoutez-en d'abord avec « cliente add »[/red]
cli-fattura-available-clients = [cyan]Clients disponibles :[/cyan]
cli-fattura-client-prompt = Numéro du client
cli-fattura-client-selected = [green]✓ Client : { $client_name }[/green]
cli-fattura-invalid-client-error = [red]Sélection de client invalide[/red]

cli-fattura-add-lines-title = [bold cyan]Lignes de Facture[/bold cyan]
cli-fattura-line-description-prompt = Description (vide pour terminer)
cli-fattura-line-quantity-prompt = Quantité
cli-fattura-line-unit-price-prompt = Prix unitaire (€)
cli-fattura-line-vat-rate-prompt = Taux IVA (%)
cli-fattura-line-added = [green]✓ Ligne ajoutée : { $description } - € { $amount }[/green]

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
cli-fattura-created-success = [bold green]✓ Facture créée avec succès ![/bold green]
cli-fattura-created-number = [green]Numéro de facture : { $numero }/{ $anno }[/green]
cli-fattura-created-xml = [green]XML enregistré : { $xml_path }[/green]

cli-fattura-list-title = [bold blue]Liste des Factures[/bold blue]
cli-fattura-list-empty = [yellow]Aucune facture trouvée[/yellow]

cli-fattura-show-title = [bold blue]Facture { $numero }/{ $anno }[/bold blue]
cli-fattura-show-not-found = [red]Facture non trouvée : { $numero }/{ $anno }[/red]

cli-fattura-delete-confirm = [yellow]Supprimer la facture { $numero }/{ $anno } ?[/yellow]
cli-fattura-delete-warning = [red]AVERTISSEMENT : Cette opération ne peut pas être annulée[/red]
cli-fattura-delete-status-restriction = [red]Impossible de supprimer la facture dans l'état '{ $status }'[/red]
cli-fattura-delete-success = [green]✓ Facture { $numero }/{ $anno } supprimée[/green]
cli-fattura-delete-cancelled = [yellow]Opération annulée[/yellow]
cli-fattura-delete-cannot-delete-sent = [red]Impossible de supprimer les factures à l'état INVIATA ou CONSEGNATA[/red]

cli-fattura-validate-success = [green]✓ Le XML est valide[/green]
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
cli-cliente-help-denominazione = Nom de l'entreprise ou nom complet
cli-cliente-help-partita-iva = Numéro IVA
cli-cliente-help-codice-fiscale = Code fiscal
cli-cliente-help-pec = Adresse PEC
cli-cliente-help-codice-destinatario = Code destinataire SDI
cli-cliente-help-formato = Format de sortie (table, json, yaml)
cli-cliente-help-search = Terme de recherche
cli-cliente-help-limit = Nombre maximum de résultats

### cliente - Sortie console
cli-cliente-list-title = Clients ({ $count })
cli-cliente-list-empty = [yellow]Aucun client trouvé[/yellow]
cli-cliente-added-success = [green]✓ Client ajouté avec succès (ID : { $id })[/green]
cli-cliente-updated-success = [green]✓ Client mis à jour avec succès[/green]
cli-cliente-deleted-success = [green]✓ Client supprimé avec succès[/green]
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

### ai - Sortie console (describe)
cli-ai-describe-title = [bold cyan]🤖 Génération de Description de Facture par IA[/bold cyan]
cli-ai-describe-input-prompt = [cyan]Entrez une brève description :[/cyan]
cli-ai-describe-processing = [yellow]Traitement par IA...[/yellow]
cli-ai-describe-result-title = [bold green]Description Générée :[/bold green]
cli-ai-describe-result-text = [white]{ $text }[/white]
cli-ai-describe-copy-hint = [dim]Vous pouvez copier cette description lors de la création d'une facture[/dim]
cli-ai-describe-error = [red]Erreur lors de la génération de la description : { $error }[/red]

### ai - Sortie console (suggest-vat)
cli-ai-vat-title = [bold cyan]🧾 Suggestion de Taux IVA par IA[/bold cyan]
cli-ai-vat-input-prompt = [cyan]Description du service/produit :[/cyan]
cli-ai-vat-processing = [yellow]Analyse par IA...[/yellow]
cli-ai-vat-result-title = [bold green]Taux IVA Suggéré :[/bold green]
cli-ai-vat-rate = [white]{ $rate }%[/white]
cli-ai-vat-reasoning-title = [bold yellow]Raisonnement :[/bold yellow]
cli-ai-vat-reasoning-text = [white]{ $reasoning }[/white]
cli-ai-vat-warning = [yellow]⚠️  Vérifiez toujours auprès d'un conseiller fiscal pour les cas complexes[/yellow]
cli-ai-vat-error = [red]Erreur lors de la suggestion du taux IVA : { $error }[/red]

### ai - Sortie console (chat)
cli-ai-chat-title = [bold cyan]🎤 Chat Vocal IA[/bold cyan]
cli-ai-chat-welcome = [cyan]Bienvenue dans l'Assistant IA OpenFatture ![/cyan]
cli-ai-chat-welcome-help = [dim]Posez vos questions ou tapez « exit » pour quitter[/dim]
cli-ai-chat-session-loaded = [green]✓ Session chargée : { $session_id }[/green]
cli-ai-chat-session-created = [green]✓ Nouvelle session créée : { $session_id }[/green]
cli-ai-chat-prompt = [bold cyan]Vous :[/bold cyan]
cli-ai-chat-assistant-prefix = [bold green]Assistant :[/bold green]
cli-ai-chat-thinking = [yellow]Réflexion...[/yellow]
cli-ai-chat-tool-calling = [yellow]Exécution de l'outil : { $tool_name }[/yellow]
cli-ai-chat-tool-result = [dim]Résultat de l'outil : { $result }[/dim]
cli-ai-chat-session-saved = [green]✓ Session enregistrée[/green]
cli-ai-chat-goodbye = [cyan]Au revoir ! Session enregistrée.[/cyan]
cli-ai-chat-error = [red]Erreur : { $error }[/red]
cli-ai-chat-cost-info = [dim]Tokens : { $tokens } | Coût : €{ $cost }[/dim]

### ai - Sortie console (voice-chat)
cli-ai-voice-title = [bold cyan]🎤 Chat Vocal IA[/bold cyan]
cli-ai-voice-welcome = [cyan]Bienvenue dans le Chat Vocal ![/cyan]
cli-ai-voice-recording-prompt = [yellow]Appuyez sur ENTRÉE pour commencer l'enregistrement ({ $duration }s)...[/yellow]
cli-ai-voice-recording = [bold yellow]🔴 Enregistrement...[/bold yellow]
cli-ai-voice-processing = [yellow]Traitement de l'audio...[/yellow]
cli-ai-voice-transcription-title = [bold green]Vous avez dit :[/bold green]
cli-ai-voice-transcription-text = [white]{ $text }[/white]
cli-ai-voice-language-detected = [dim]Langue : { $language }[/dim]
cli-ai-voice-thinking = [yellow]L'assistant réfléchit...[/yellow]
cli-ai-voice-response-title = [bold green]Assistant :[/bold green]
cli-ai-voice-response-text = [white]{ $text }[/white]
cli-ai-voice-playing = [cyan]🔊 Lecture de la réponse...[/cyan]
cli-ai-voice-audio-saved = [dim]Audio enregistré : { $path }[/dim]
cli-ai-voice-goodbye = [cyan]Au revoir ![/cyan]
cli-ai-voice-error = [red]Erreur : { $error }[/red]

### ai - Sortie console (forecast)
cli-ai-forecast-title = [bold cyan]📊 Prévision de Trésorerie par IA[/bold cyan]
cli-ai-forecast-loading-data = [yellow]Chargement des données historiques...[/yellow]
cli-ai-forecast-data-stats = [cyan]Factures : { $invoices } | Paiements : { $payments }[/cyan]
cli-ai-forecast-training = [yellow]Entraînement des modèles ML...[/yellow]
cli-ai-forecast-training-progress = [yellow]{ $progress }%[/yellow]
cli-ai-forecast-predicting = [yellow]Génération de la prévision...[/yellow]
cli-ai-forecast-results-title = [bold green]📊 Prévision de Trésorerie - Les { $months } { $months ->
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
cli-ai-intelligence-title = [bold cyan]🧠 Analyse Business Intelligence[/bold cyan]
cli-ai-intelligence-analyzing = [yellow]Analyse des données métier...[/yellow]
cli-ai-intelligence-report-title = [bold green]Analyses Métier :[/bold green]
cli-ai-intelligence-section = [bold yellow]{ $section }[/bold yellow]
cli-ai-intelligence-insight = • { $insight }
cli-ai-intelligence-error = [red]Erreur d'analyse : { $error }[/red]

### ai - Sortie console (compliance)
cli-ai-compliance-title = [bold cyan]✅ Vérification de Conformité[/bold cyan]
cli-ai-compliance-checking = [yellow]Vérification de la facture { $numero }/{ $anno }...[/yellow]
cli-ai-compliance-passed = [bold green]✓ Tous les contrôles de conformité réussis[/bold green]
cli-ai-compliance-warnings = [yellow]⚠️  { $count } { $count ->
    [one] avertissement détecté
   *[other] avertissements détectés
}[/yellow]
cli-ai-compliance-errors = [red]❌ { $count } { $count ->
    [one] erreur détectée
   *[other] erreurs détectées
}[/red]
cli-ai-compliance-check-item = [{ $status }] { $message }
cli-ai-compliance-error = [red]Erreur de vérification de conformité : { $error }[/red]

### ai - Sortie console (rag)
cli-ai-rag-title = [bold cyan]📚 Recherche de Documents RAG[/bold cyan]
cli-ai-rag-indexing = [yellow]Indexation des documents...[/yellow]
cli-ai-rag-indexed = [green]✓ { $count } { $count ->
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
cli-ai-feedback-title = [bold cyan]📝 Retour d'IA[/bold cyan]
cli-ai-feedback-prompt-rating = [cyan]Évaluer la réponse (1-5) :[/cyan]
cli-ai-feedback-prompt-comment = [cyan]Commentaire (optionnel) :[/cyan]
cli-ai-feedback-thanks = [green]✓ Merci pour votre retour ![/green]
cli-ai-feedback-saved = [green]Retour enregistré dans la session { $session_id }[/green]
cli-ai-feedback-error = [red]Erreur de retour : { $error }[/red]
