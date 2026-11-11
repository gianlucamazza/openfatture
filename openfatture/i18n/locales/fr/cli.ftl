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
## FATTURA Commands
cli-fattura-journal-submission = Envoi n° { $id } · facture { $invoice } · { $filename } · { $outcome }
cli-fattura-journal-receipt = Accusé n° { $id } · facture { $invoice } · { $outcome } · origine { $source }
cli-fattura-journal-empty = Aucun envoi ni accusé SDI enregistré.
cli-fattura-associate-confirm = Associer l'accusé { $receipt } à la facture { $invoice } ?
cli-fattura-receipt-associated = Accusé associé
cli-fattura-resolve-confirm = Confirmez-vous que l'envoi { $attempt } { $sent ->
        [yes] a été transmis
       *[no] n'a pas été transmis
    } ?
cli-fattura-submission-resolved = Vérification enregistrée

## CLIENTE Commands
## PAGAMENTO Commands
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

## Localized refusals of application services (error_code)
cli-error-receipt-not-associable = L'accusé n'existe pas ou est déjà associé.
cli-error-evidence-required = Une preuve vérifiée est requise (--evidence).
cli-error-submission-not-found = Tentative d'envoi introuvable.
cli-error-submission-already-resolved = La tentative d'envoi est déjà résolue.
cli-error-sdi-evidence-contradicts = Les preuves SDI enregistrées contredisent le résultat « non envoyé ».
cli-error-submission-concurrent-update = La tentative a été résolue entre-temps : rechargez et réessayez.

## Command-line help
cli-help-app = Facturation électronique avec assistant. Lancez openfatture pour converser.
cli-help-epilog = Exemples : openfatture · openfatture assistant "Affiche les factures impayées"
cli-help-version = Affiche la version et quitte.
cli-help-debug = Affiche les journaux de diagnostic et les tracebacks.
cli-help-format = Format de sortie : rich, json, markdown, stream-json, html
cli-help-panel-assistant = Assistant
cli-help-panel-setup = Configuration et diagnostic
cli-help-panel-sdi = Vérifications SDI
cli-help-assistant = Envoie une demande ou reprend une session
cli-help-init = Initialise OpenFatture
cli-help-config = Gère la configuration
cli-help-status = Vérifie la configuration et la disponibilité
cli-help-fattura = Journal SDI et résolutions avec preuve manuelle
cli-help-assistant-message = Demande pour l'assistant.
cli-help-assistant-stream = Affiche la réponse pendant sa génération.
cli-help-assistant-json = Renvoie la réponse en JSON.
cli-help-assistant-session = Reprend une session enregistrée par son ID (active l'enregistrement).
cli-help-init-interactive = Assistant de configuration interactif
cli-help-status-json = Renvoie l'état en JSON.
cli-help-config-show =
    Affiche la configuration effective.

    Pour chaque valeur, indique la source : environnement, trousseau ou fichier d'identifiants, config.toml, défaut.
cli-help-config-reload = Recharge la configuration depuis l'environnement, le coffre de secrets et config.toml.
cli-help-config-set =
    Définit une valeur de configuration.

    Seule KEY est écrite. Les secrets (clés API, mots de passe) vont dans le trousseau du système, ou dans le fichier privé d'identifiants s'il n'y a pas de trousseau ; les autres valeurs dans config.toml. Les clés imbriquées utilisent des points, par exemple debug_config.enable_debug_logging.
cli-help-config-unset = Supprime KEY de config.toml ou du coffre de secrets et rétablit la valeur par défaut.
cli-help-config-migrate =
    Sort les secrets en clair de config.toml et importe éventuellement un fichier .env.

    Les secrets vont dans le trousseau (ou le fichier privé d'identifiants) ; les autres valeurs de --env-file sont ajoutées à config.toml seulement si elles ne sont pas déjà définies. Le fichier source n'est jamais modifié.
cli-help-config-env-file = Importe les réglages d'un fichier dotenv (les valeurs existantes sont conservées).
cli-help-invoice-id = ID de la facture
cli-help-sdi-journal = Affiche les envois PEC et les accusés SDI enregistrés, sans rien envoyer.
cli-help-associate-receipt = Associe un accusé non résolu à une facture, après une vérification manuelle.
cli-help-receipt-id = ID de l'accusé SDI
cli-help-receipt-evidence = Preuve vérifiée (par ex. une référence)
cli-help-resolve-submission = Résout un envoi PEC incertain, après vérification du résultat du transport.
cli-help-attempt-id = ID de la tentative d'envoi
cli-help-resolve-sent = Résultat vérifié : envoyé ou non envoyé
cli-help-resolve-evidence = Preuve vérifiée (par ex. la référence du fournisseur)
cli-help-install-completion = Installe la complétion pour le shell courant.
cli-help-show-completion = Affiche la complétion pour le shell courant, pour la copier ou la personnaliser.
cli-help-help-option = Affiche ce message et quitte.
