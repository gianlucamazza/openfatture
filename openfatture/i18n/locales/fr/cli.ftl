### main - Textes principaux

## CONFIG Commands - Gestion de la Configuration
cli-config-help-key = Clé de configuration (ex. pec.address)
cli-config-help-value = Valeur de configuration
cli-config-show-title = Configuration d'OpenFatture
cli-config-column-setting = Paramètre
cli-config-column-value = Valeur
cli-config-label-app-version = Version de l'App
cli-config-label-debug-mode = Mode Debug
cli-config-label-database-url = URL de Base de Données
cli-config-label-data-dir = Répertoire de Données
cli-config-label-archive-dir = Répertoire d'Archive
cli-config-label-certificates-dir = Répertoire de Certificats
cli-config-label-company-name = Nom de l'Entreprise
cli-config-label-partita-iva = Partita IVA
cli-config-label-codice-fiscale = Codice Fiscale
cli-config-label-tax-regime = Régime Fiscal
cli-config-label-pec-address = Adresse PEC
cli-config-label-pec-smtp-server = Serveur SMTP PEC
cli-config-label-sdi-pec-address = Adresse PEC SDI
cli-config-label-notification-email = Email de Notifications
cli-config-label-notifications-enabled = Notifications Activées
cli-config-label-locale = Langue
cli-config-label-email-logo-url = URL du Logo Email
cli-config-label-primary-color = Couleur Primaire
cli-config-label-secondary-color = Couleur Secondaire
cli-config-label-email-footer = Pied de page Email
cli-config-label-ai-provider = Fournisseur IA
cli-config-label-ai-model = Modèle IA
cli-config-label-ai-base-url = URL de Base IA
cli-config-label-ai-api-key = Clé API IA
cli-config-label-chat-enabled = Chat Activé
cli-config-label-chat-auto-save = Sauvegarde Auto du Chat
cli-config-label-max-messages = Max Messages/Session
cli-config-label-max-tokens = Max Tokens/Session
cli-config-label-tools-enabled = Outils Activés
cli-config-label-tool-access = Accès aux Outils IA
cli-config-label-extra-tools = Outils Supplémentaires
cli-config-not-set = [red]Non défini[/red]
cli-config-not-set-optional = [yellow]Non défini[/yellow]
cli-config-set = [green]Défini[/green]
cli-config-yes = [green]Oui[/green]
cli-config-no = [red]Non[/red]
cli-config-auto-generated = [dim]Auto-généré[/dim]
cli-config-reload-success = [green]Configuration rechargée[/green]
cli-config-set-success = [green]Défini { $key } = { $value }[/green]
cli-config-saved-to = [dim]Enregistré dans { $path }[/dim]
cli-config-invalid-key = [red]Clé de configuration invalide : { $key }[/red]
cli-config-error = [red]Erreur : { $error }[/red]
cli-config-column-source = Origine
cli-config-source-env = environnement
cli-config-source-keyring = trousseau
cli-config-source-file = fichier d'identifiants
cli-config-source-config = config.toml
cli-config-source-default = défaut
cli-config-file-path = [dim]Fichier de configuration : { $path }[/dim]
cli-config-secret-backend = [dim]Secrets : { $backend }[/dim]
cli-config-secret-saved = [green]{ $key } enregistré dans : { $backend }[/green]
cli-config-env-override = [yellow]{ $key } est défini par une variable d'environnement : la valeur enregistrée est ignorée tant qu'elle reste définie.[/yellow]
cli-config-unset-success = [green]{ $key } supprimé[/green]
cli-config-unset-missing = [yellow]{ $key } n'était pas défini[/yellow]
cli-config-invalid-value = [red]Valeur invalide pour { $key } : { $error }[/red]
cli-config-migrate-moved = [green]Déplacés vers { $backend } : { $keys }[/green]
cli-config-migrate-imported = [green]Importés dans config.toml : { $keys }[/green]
cli-config-migrate-conflicts = [yellow]Déjà définis, non écrasés : { $keys }[/yellow]
cli-config-migrate-nothing = Rien à migrer.
cli-config-migrate-source-kept = [dim]{ $path } n'a pas été modifié : supprimez-le après vérification.[/dim]
cli-invoice-collected = Collected
cli-invoice-residual = Outstanding
cli-invoice-collection = Collection
cli-invoice-document = Document
cli-invoice-historical = Historical
cli-invoice-unpaid = Unpaid
cli-invoice-no-payment-record = Aucun encaissement enregistré
cli-invoice-partially-paid = Partiellement encaissée
cli-invoice-fully-paid = Encaissée
cli-invoice-historical-note = Issued elsewhere; sending blocked. SDI status unverified.
cli-invoice-total = Total

## Assistant and status
assistant-describe-what-you-need = Décrivez ce dont vous avez besoin. /help pour les commandes · /exit pour quitter
assistant-thinking = Réflexion…
assistant-request-error = La requête a échoué. Utilisez --debug pour les détails.
assistant-confirm-operation = Confirmer cette opération ? [y/N]
assistant-help = Commandes slash
    /help     Afficher cette aide
    /exit     Quitter (aussi : exit, quit, q)
    /session  Afficher l'ID de session
    /clear    Effacer les messages de la session
assistant-input = Vous ›
assistant-operation = Opération : { $name }
assistant-tool-running = En cours · { $name }
assistant-incomplete = Réponse incomplète.
assistant-session = Session : { $session }
assistant-not-persisted = non enregistrée
assistant-cleared = Messages de la session effacés.
assistant-no-session = Aucune session enregistrée à effacer.
assistant-unknown-command = Commande inconnue : { $command }. Essayez /help.
assistant-turn-failed = Requête non terminée. Utilisez --debug pour les détails.
assistant-interrupted = Requête interrompue. Les opérations déjà lancées ont pu prendre effet : vérifiez leur état avant de réessayer.
assistant-missing-extra = Dépendances IA manquantes : réinstallez OpenFatture avec l'extra ai.
assistant-tool-completed = Terminé · { $name }
assistant-tool-failed = Non terminé · { $name }
status-blocking-fields = Champs qui bloquent la facturation
status-field = Champ
status-problem = Problème
status-missing = Manquant
status-invalid = Invalide
status-local-only = Les vérifications décrivent la configuration locale. L'authentification de l'IA et la livraison SDI ne sont pas vérifiées par cette commande.
cli-database-unavailable = Base de données indisponible. Vérifiez DATABASE_URL et les permissions ; utilisez --debug pour les détails.
assistant-reconciled = Résultat vérifié enregistré. Utilisez /resume pour continuer.
assistant-reconcile-invalid = Rapprochement invalide : call_id, result et evidence sont requis.
assistant-resolve-pending-first = Terminez le tour en attente avec /resume avant d'effacer l'historique.
assistant-resuming = Reprise du tour interrompu…
assistant-uncertain-tool = Résultat d'outil incertain : utilisez /pending et /reconcile avant /resume.
assistant-no-pending = Aucun tour en attente.

## Shared command output
cli-common-error = [red]Erreur :[/red] { $error }
cli-common-more-results = [dim]... et plus encore. Utilisez --limit pour afficher plus de résultats.[/dim]
cli-common-not-available = N/D
cli-common-number = Numéro
cli-common-date = Date
cli-common-status = Statut
cli-common-client = Client
cli-common-amount = Montant
cli-common-name = Nom
cli-common-notes = Notes
cli-common-vat-number = N° TVA
cli-common-tax-code = Code fiscal

## FATTURA Commands
cli-fattura-none-found = [yellow]Aucune facture trouvée.[/yellow]
cli-fattura-list-title = Factures ({ $count })
cli-fattura-pec-to-verify = PEC : à vérifier
cli-fattura-statement = Déclaration : { $value } · source : { $source }
cli-fattura-show-title = [bold cyan]Facture n° { $id }[/bold cyan]
cli-fattura-submission-unverified = Résultat de l'envoi à vérifier ; ne répétez pas la transmission automatiquement.
cli-fattura-amounts = Montants
cli-fattura-taxable = Montant HT
cli-fattura-vat = TVA
cli-fattura-line-items = [bold]Lignes :[/bold] { $count } au total
cli-fattura-column-description = Description
cli-fattura-column-quantity = Qté
cli-fattura-column-unit-price = Prix unitaire
cli-fattura-column-vat-rate = TVA %
cli-fattura-created-id = ID de la facture : [cyan]{ $id }[/cyan]
cli-fattura-line = Ligne n° { $numero } : { $descrizione }
cli-fattura-invoice-total = Total de la facture
cli-fattura-pdf-generated = [green]✓[/green] PDF généré avec succès
cli-fattura-xml-generated = [green]✓[/green] XML généré avec succès
cli-fattura-xml-generated-dry-run = [green]✓[/green] XML généré avec succès (simulation, aucun fichier écrit)
cli-fattura-xml-content = [bold]Contenu XML :[/bold]
cli-fattura-output = Sortie : [cyan]{ $path }[/cyan]
cli-fattura-size = Taille : { $size } octets
cli-fattura-status-change = Statut : { $old } → { $new }
cli-fattura-credit-note-id = ID de l'avoir : [cyan]{ $id }[/cyan]
cli-fattura-document-type = Type de document
cli-fattura-source-invoice = [dim]Facture d'origine :[/dim]
cli-fattura-journal-submission = Envoi n° { $id } · facture { $invoice } · { $filename } · { $outcome }
cli-fattura-journal-receipt = Accusé n° { $id } · facture { $invoice } · { $outcome } · origine { $source }
cli-fattura-associate-confirm = Associer l'accusé { $receipt } à la facture { $invoice } ?
cli-fattura-receipt-associated = Accusé associé
cli-fattura-resolve-confirm = Confirmez-vous que l'envoi { $attempt } { $sent ->
        [yes] a été transmis
       *[no] n'a pas été transmis
    } ?
cli-fattura-submission-resolved = Vérification enregistrée

## CLIENTE Commands
cli-cliente-none-found = [yellow]Aucun client trouvé.[/yellow]
cli-cliente-list-title = Clients ({ $count })
cli-cliente-column-invoices = Factures
cli-cliente-show-title = [bold cyan]Client n° { $id }[/bold cyan]
cli-cliente-address = Adresse
cli-cliente-contacts = Contacts
cli-cliente-phone = Tél.
cli-cliente-invoices-total = [bold]Factures :[/bold] { $count } au total
cli-cliente-recent-invoices = Factures récentes
cli-cliente-created-id = ID du client : [cyan]{ $id }[/cyan]

## PAGAMENTO Commands
cli-pagamento-reverse-confirm = Annuler { $amount } de l'écriture { $entry } ?

## INIT Command
cli-init-title = [bold blue]Configuration d'OpenFatture[/bold blue]
cli-init-structured-needs-no-interactive = Utilisez --no-interactive avec un format de sortie structuré
cli-init-creating-dirs = [cyan]Création des répertoires...[/cyan]
cli-init-dirs-created = Répertoires de données créés
cli-init-initializing-db = [cyan]Initialisation de la base de données...[/cyan]
cli-init-backup = Sauvegarde avant la mise à niveau : { $path }
cli-init-database = Base de données { $state ->
        [empty] créée
        [current] déjà à jour
        [outdated] mise à niveau
        [unversioned] adoptée et mise à niveau
       *[other] { $state }
    } : { $url }
cli-init-configure-company = [bold yellow]Configurons les données de votre entreprise[/bold yellow]
cli-init-overwrite-confirm = [yellow]Un profil OpenFatture existe déjà. Écraser les paramètres entreprise et IA ?[/yellow]
cli-init-config-preserved = [green]Configuration existante conservée.[/green] Les répertoires et la base de données ont tout de même été vérifiés.
cli-init-company-section = [bold]Informations de l'entreprise (Cedente Prestatore)[/bold]
cli-init-prompt-name = Raison sociale ou votre nom
cli-init-prompt-partita-iva = Partita IVA (11 chiffres)
cli-init-invalid-partita-iva = [red]Partita IVA invalide. Veuillez réessayer.[/red]
cli-init-prompt-codice-fiscale = Codice fiscale (16 caractères)
cli-init-invalid-codice-fiscale = [red]Codice fiscale invalide. Veuillez réessayer.[/red]
cli-init-prompt-regime = Régime fiscal (utilisez votre code RF réel)
cli-init-invalid-regime = [red]Saisissez un régime fiscal pris en charge par FatturaPA.[/red]
cli-init-prompt-address = Adresse (rue)
cli-init-prompt-cap = Code postal (CAP)
cli-init-prompt-city = Commune (Comune)
cli-init-prompt-province = Province (2 lettres, ex. RM)
cli-init-pec-section = [bold]Configuration PEC[/bold]
cli-init-prompt-pec-address = Votre adresse PEC
cli-init-prompt-pec-password = Mot de passe PEC
cli-init-prompt-pec-smtp = Serveur SMTP PEC
cli-init-notifications-section = [bold]Notifications par e-mail[/bold]
cli-init-prompt-notification-email = E-mail pour les notifications (alertes SDI, récapitulatifs)
cli-init-prompt-locale = Langue (it/en/de/es/fr)
cli-init-ai-section = [bold]Configuration de l'IA (facultative)[/bold]
cli-init-ai-description = [dim]Configurez les fonctions d'IA : descriptions de factures, suggestions fiscales et assistant conversationnel.[/dim]
cli-init-ai-confirm = Configurer les fonctions d'IA maintenant ? (Vous pourrez aussi le faire plus tard avec openfatture config)
cli-init-ai-provider = Fournisseur d'IA
cli-init-ai-skip = Ignorer pour l'instant
cli-init-api-key-from = [cyan]{ $provider } sélectionné : obtenez une clé API ici :[/cyan]
cli-init-ollama-selected = [cyan]Ollama sélectionné : modèle local gratuit ![/cyan]
cli-init-ollama-install = Installer : [bold]ollama pull { $model }[/bold]
cli-init-ollama-start = Démarrer : [bold]ollama serve[/bold]
cli-init-prompt-api-key = Clé API (laissez vide pour la définir plus tard)
cli-init-config-saved = Configuration enregistrée dans : { $path }
cli-init-secrets-saved = Secrets enregistrés { $backend ->
        [keyring] dans le trousseau du système
       *[file] dans le fichier privé des identifiants
    }
cli-init-complete-title = Configuration terminée
cli-init-complete-body = [bold green]Configuration achevée[/bold green]

    Prochaines étapes :
      • Vérifier l'état : [cyan]openfatture status[/cyan]
      • Revoir les paramètres : [cyan]openfatture config show[/cyan]
      • Assistant (nécessite [cyan]uv sync --extra ai[/cyan]) : [cyan]openfatture assistant "Affiche les factures ouvertes"[/cyan]
      • Aide : [cyan]openfatture --help[/cyan]

## STATUS Command
cli-status-readiness = [bold]Disponibilité[/bold]  noyau : [cyan]{ $core ->
        [yes] prêt
       *[no] non prêt
    }[/cyan]  assistant : [cyan]{ $assistant ->
        [yes] configuré
       *[no] non configuré
    }[/cyan]
cli-status-title = État d'OpenFatture
cli-status-label-ai-api-key-configured = Clé API IA configurée
cli-status-label-assistant-backend = Backend de l'assistant
cli-status-label-assistant-backend-id = ID du backend de l'assistant
cli-status-label-config-file = Fichier de configuration
cli-status-label-secret-backend = Stockage des secrets
cli-status-checks-title = Contrôles de disponibilité
cli-status-column-check = Contrôle
cli-status-yes = oui
cli-status-no = non
cli-status-next-steps = [bold]Prochaines étapes[/bold]
cli-status-extras-title = Extras optionnels (modules fonctionnels)
cli-status-column-extra = Extra
cli-status-column-installed = Installé
cli-status-extensions-title = Extensions
cli-status-column-mechanism = Mécanisme
cli-status-column-detail = Détail
cli-status-hooks = hooks (pris en charge)
cli-status-hooks-detail = { $path } ({ $count ->
        [one] 1 script
       *[other] { $count } scripts
    })
cli-status-plugins = plugins in-process

## Global
cli-main-version = [bold blue]OpenFatture[/bold blue] version { $version }
cli-output-unsupported-format = Formats pris en charge : { $formats }

## Rich formatter
cli-formatter-error = [bold red]Erreur :[/bold red] { $error }
cli-formatter-unknown-error = Erreur inconnue
cli-formatter-ai-response = [bold]Réponse de l'IA[/bold]
cli-formatter-unknown = inconnu
cli-formatter-provider = Fournisseur : { $provider }
cli-formatter-model = Modèle : { $model }
cli-formatter-tokens = Jetons : { $tokens }
cli-formatter-cost = Coût : { $cost }
cli-formatter-latency = Latence : { $latency } ms
