# Web UI translations - French
# Traductions complètes pour l'interface web Streamlit d'OpenFatture

## ============================================================================
## COMMON - Chaînes Communes de l'Interface Web
## ============================================================================

### Application
web-app-title = OpenFatture - Facturation Électronique
web-app-tagline = Système open source pour la facturation électronique italienne
web-app-version = Version { $version }
web-app-license = Licence MIT

### Navigation
web-nav-home = Accueil
web-nav-dashboard = Tableau de Bord
web-nav-invoices = Factures
web-nav-clients = Clients
web-nav-payments = Paiements
web-nav-ai-assistant = Assistant IA
web-nav-settings = Paramètres
web-nav-batch = Opérations par Lots
web-nav-reports = Rapports
web-nav-events = Événements
web-nav-health = État du Système
web-nav-lightning = Lightning
web-nav-hooks = Hooks

### Common Buttons
web-button-save = Enregistrer
web-button-cancel = Annuler
web-button-delete = Supprimer
web-button-edit = Modifier
web-button-create = Créer
web-button-update = Mettre à jour
web-button-search = Rechercher
web-button-filter = Filtrer
web-button-export = Exporter
web-button-import = Importer
web-button-refresh = Actualiser
web-button-close = Fermer
web-button-submit = Soumettre
web-button-reset = Réinitialiser
web-button-back = Retour
web-button-next = Suivant
web-button-finish = Terminer
web-button-download = Télécharger
web-button-upload = Charger
web-button-view = Voir
web-button-send = Envoyer

### Common Labels
web-label-name = Nom
web-label-description = Description
web-label-date = Date
web-label-amount = Montant
web-label-status = Statut
web-label-type = Type
web-label-total = Total
web-label-subtotal = Sous-total
web-label-tax = TVA
web-label-quantity = Quantité
web-label-price = Prix
web-label-client = Client
web-label-invoice = Facture
web-label-payment = Paiement
web-label-notes = Notes
web-label-actions = Actions
web-label-created = Créé
web-label-updated = Mis à jour
web-label-email = Email
web-label-phone = Téléphone
web-label-address = Adresse
web-label-city = Ville
web-label-country = Pays
web-label-search = Rechercher
web-label-filter = Filtrer
web-label-all = Tous
web-label-none = Aucun
web-label-yes = Oui
web-label-no = Non

### Common Messages
web-message-success = Opération réussie
web-message-error = Une erreur s'est produite
web-message-warning = Avertissement
web-message-info = Information
web-message-loading = Chargement en cours...
web-message-no-data = Aucune donnée disponible
web-message-no-results = Aucun résultat trouvé
web-message-confirm-delete = Êtes-vous sûr de vouloir supprimer cet élément ?
web-message-unsaved-changes = Il y a des modifications non enregistrées
web-message-saved = Enregistré
web-message-deleted = Supprimé
web-message-updated = Mis à jour
web-message-created = Créé

### Validation Messages
web-validation-required = Ce champ est obligatoire
web-validation-invalid = Valeur non valide
web-validation-email-invalid = Email non valide
web-validation-number-invalid = Nombre non valide
web-validation-date-invalid = Date non valide
web-validation-min-length = Longueur minimale : { $length } caractères
web-validation-max-length = Longueur maximale : { $length } caractères
web-validation-min-value = Valeur minimale : { $value }
web-validation-max-value = Valeur maximale : { $value }

### Error Messages
web-error-generic = Une erreur inattendue s'est produite
web-error-unexpected = 🚨 Une erreur inattendue s'est produite. Veuillez réessayer plus tard.
web-error-reload-page = 🔄 Recharger la Page
web-error-goto-health = 🏥 Aller au Tableau de Bord Santé
web-error-network = Erreur de connexion
web-error-timeout = Délai d'attente dépassé
web-error-unauthorized = Non autorisé
web-error-forbidden = Accès refusé
web-error-not-found = Ressource introuvable
web-error-server = Erreur du serveur
web-error-database = Erreur de base de données
web-error-loading = Erreur lors du chargement
web-error-saving = Erreur lors de l'enregistrement
web-error-deleting = Erreur lors de la suppression

### Sidebar
web-sidebar-quick-stats = 📊 Statistiques Rapides
web-sidebar-invoices = Factures
web-sidebar-clients = Clients
web-sidebar-revenue = Chiffre d'Affaires
web-sidebar-pending = En Attente
web-sidebar-configuration = ⚙️ Configuration
web-sidebar-company = Entreprise
web-sidebar-vat-number = N° TVA
web-sidebar-tax-regime = Régime
web-sidebar-ai-enabled = 🤖 IA Activée
web-sidebar-ai-disabled = IA Non Configurée
web-sidebar-ai-provider = Fournisseur
web-sidebar-advanced-ops = 🔧 Opérations Avancées
web-sidebar-error-loading-stats = Erreur de chargement des stats : { $error }

### Language Selector
web-lang-selector-title = 🌍 Langue
web-lang-selector-italian = Italiano
web-lang-selector-english = English
web-lang-selector-spanish = Español
web-lang-selector-french = Français
web-lang-selector-german = Deutsch
web-lang-selector-changed = Langue changée en { $language }

### Status Values
web-status-active = Actif
web-status-inactive = Inactif
web-status-pending = En Attente
web-status-completed = Terminé
web-status-failed = Échoué
web-status-draft = Brouillon
web-status-sent = Envoyé
web-status-paid = Payé
web-status-unpaid = Non Payé
web-status-overdue = En Retard
web-status-cancelled = Annulé

### Time & Date
web-time-today = Aujourd'hui
web-time-yesterday = Hier
web-time-this-week = Cette semaine
web-time-this-month = Ce mois-ci
web-time-this-year = Cette année
web-time-last-week = Semaine dernière
web-time-last-month = Mois dernier
web-time-last-year = Année dernière
web-time-custom = Personnalisé

### Pagination
web-pagination-showing = Affichage de { $start }-{ $end } sur { $total }
web-pagination-per-page = Par page
web-pagination-first = Première
web-pagination-last = Dernière
web-pagination-previous = Précédente
web-pagination-next = Suivante

### File Upload
web-upload-drag-drop = Glissez et déposez les fichiers ici
web-upload-or = ou
web-upload-browse = Parcourir
web-upload-max-size = Taille maximale : { $size }
web-upload-accepted-formats = Formats acceptés : { $formats }
web-upload-uploading = Chargement...
web-upload-success = Fichier chargé avec succès
web-upload-error = Erreur lors du chargement du fichier
