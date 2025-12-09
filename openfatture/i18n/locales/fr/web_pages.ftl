# Web Pages translations - French
# Traductions spécifiques pour les pages de l'interface web Streamlit

## ============================================================================
## HOME PAGE (app.py)
## ============================================================================

page-home-title = 🏠 OpenFatture
page-home-welcome = Bienvenue sur OpenFatture
page-home-subtitle = Système de Facturation Électronique Open Source
page-home-description =
    OpenFatture est un système complet pour la gestion de la facturation électronique
    italienne, avec intégration SDI, IA et paiements Lightning.

page-home-features-title = ✨ Fonctionnalités Principales
page-home-feature-invoicing = Facturation électronique complète avec FatturaPA
page-home-feature-sdi = Intégration directe avec SDI (Système d'Échange)
page-home-feature-ai = Assistant IA pour descriptions et suggestions de TVA
page-home-feature-payments = Rapprochement automatique des paiements bancaires
page-home-feature-lightning = Support des paiements Lightning Network
page-home-feature-batch = Opérations par lots pour import/export massif

## Feature Grid
page-home-feature-grid-invoices-title = 🧾 Factures
page-home-feature-grid-invoices-item-1 = Création guidée
page-home-feature-grid-invoices-item-2 = Gestion des clients
page-home-feature-grid-invoices-item-3 = Génération XML
page-home-feature-grid-invoices-item-4 = Envoi SDI via PEC
page-home-feature-grid-invoices-item-5 = Suivi des notifications
page-home-feature-grid-invoices-button = 📝 Aller aux Factures

page-home-feature-grid-payments-title = 💰 Paiements
page-home-feature-grid-payments-item-1 = Importer les relevés bancaires
page-home-feature-grid-payments-item-2 = Rapprochement automatique
page-home-feature-grid-payments-item-3 = Réconciliation
page-home-feature-grid-payments-item-4 = Rappels d'échéance
page-home-feature-grid-payments-item-5 = Piste d'audit
page-home-feature-grid-payments-button = 💳 Aller aux Paiements

page-home-feature-grid-ai-title = 🤖 Assistant IA
page-home-feature-grid-ai-item-1 = Chat interactif
page-home-feature-grid-ai-item-2 = Descriptions automatiques
page-home-feature-grid-ai-item-3 = Conseil fiscal
page-home-feature-grid-ai-item-4 = Prévision du flux de trésorerie
page-home-feature-grid-ai-item-5 = Vérification de conformité
page-home-feature-grid-ai-button = 🚀 Essayer l'IA

## Quick Actions
page-home-quick-actions = ⚡ Actions Rapides
page-home-action-new-invoice = ➕ Nouvelle Facture
page-home-action-new-client = 👤 Nouveau Client
page-home-action-dashboard = 📊 Tableau de Bord
page-home-action-batch = 📦 Opérations par Lots

## Advanced Tools
page-home-advanced-tools = 🔧 Outils Avancés
page-home-advanced-reports = 📊 Rapports
page-home-advanced-hooks = 🪝 Hooks
page-home-advanced-events = 📋 Événements

## Getting Started
page-home-getting-started = 🚀 Pour Commencer
page-home-getting-started-title = Premiers Pas

page-home-step-1-title = 1. Configurez l'environnement
page-home-step-1-item-1 = Assurez-vous que `.env` est correctement configuré
page-home-step-1-item-2 = Vérifiez les données de l'entreprise (n° TVA, régime fiscal)
page-home-step-1-item-3 = Configurez les identifiants PEC pour l'envoi SDI

page-home-step-2-title = 2. Créez vos premiers clients
page-home-step-2-item-1 = Allez dans "👥 Clients" → "Ajouter un Client"
page-home-step-2-item-2 = Entrez les données fiscales (n° TVA, code fiscal)
page-home-step-2-item-3 = Spécifiez SDI ou PEC pour la réception des factures

page-home-step-3-title = 3. Émettez votre première facture
page-home-step-3-item-1 = "🧾 Factures" → "Nouvelle Facture"
page-home-step-3-item-2 = Sélectionnez le client et ajoutez des lignes
page-home-step-3-item-3 = Générez le XML et envoyez au SDI

page-home-step-4-title = 4. Explorez l'Assistant IA
page-home-step-4-item-1 = Essayez le chat pour les questions fiscales
page-home-step-4-item-2 = Générez des descriptions intelligentes
page-home-step-4-item-3 = Obtenez des suggestions de TVA automatiques

page-home-docs-title = Documentation

## Footer
page-home-footer-version = OpenFatture v{ $version }
page-home-footer-license = Licence MIT
page-home-footer-tagline = Fait avec ❤️ par des freelancers, pour des freelancers

page-home-help = 📚 Aide et Documentation
page-home-github = Dépôt GitHub
page-home-report-bug = Signaler un Bug
page-home-about = À propos

## ============================================================================
## DASHBOARD PAGE (1_📊_Dashboard.py)
## ============================================================================

page-dashboard-title = 📊 Tableau de Bord
page-dashboard-subtitle = Vue d'Ensemble de l'Entreprise en Temps Réel

### KPI Cards
page-dashboard-kpi-section = 📈 Métriques Principales
page-dashboard-kpi-total-invoices = 📄 Total Factures
page-dashboard-kpi-total-revenue = 💰 Chiffre d'Affaires Total
page-dashboard-kpi-total-clients = 👥 Clients Actifs
page-dashboard-kpi-revenue-month = 📅 Chiffre d'Affaires Mensuel
page-dashboard-kpi-pending-payments = Paiements en Attente
page-dashboard-kpi-avg-invoice = Montant Moyen par Facture
page-dashboard-kpi-this-month = Ce Mois-ci
page-dashboard-kpi-this-year = Cette Année
page-dashboard-kpi-growth = Croissance

### Charts
page-dashboard-chart-invoices-by-status = 📊 Factures par Statut
page-dashboard-chart-revenue-6-months = 📈 Chiffre d'Affaires 6 Derniers Mois
page-dashboard-chart-yaxis-revenue = Chiffre d'Affaires (€)
page-dashboard-chart-xaxis-month = Mois
page-dashboard-chart-revenue-title = Tendance du Chiffre d'Affaires
page-dashboard-chart-invoices-title = Factures par Mois
page-dashboard-chart-clients-title = Principaux Clients
page-dashboard-chart-status-title = Factures par Statut
page-dashboard-chart-payments-title = État des Paiements

### Tables
page-dashboard-top-clients = 👑 Top 5 Clients
page-dashboard-recent-invoices = 🕐 5 Dernières Factures
page-dashboard-col-client = Client
page-dashboard-col-num-invoices = Nbre Factures
page-dashboard-col-num-invoices-short = Factures
page-dashboard-col-revenue = Chiffre d'Affaires
page-dashboard-col-number = Numéro
page-dashboard-col-date = Date
page-dashboard-col-total = Total
page-dashboard-col-status = Statut
page-dashboard-col-invoice = Facture
page-dashboard-col-due-date = Échéance
page-dashboard-col-days = Jours
page-dashboard-col-days-delta = Δ Jours
page-dashboard-col-days-help = Jours jusqu'à échéance
page-dashboard-col-residual = Restant
page-dashboard-col-residual-amount = Montant Restant
page-dashboard-col-category = Catégorie

### Payment Tracking
page-dashboard-payment-tracking = 💳 Suivi des Paiements
page-dashboard-payment-unmatched = 🔍 Non Appariés
page-dashboard-payment-matched = ✅ Appariés
page-dashboard-payment-ignored = ⏭️ Ignorés
page-dashboard-payment-total = 📊 Total Transactions
page-dashboard-payment-due-30 = 💰 Échéances de Paiement (30 prochains jours)
page-dashboard-total-outstanding = 💸 Total Restant à Encaisser
page-dashboard-category-overdue = 🔴 En retard
page-dashboard-category-due-soon = 🟡 Échéance proche
page-dashboard-category-upcoming = 🟢 À venir

### Messages
page-dashboard-no-invoices = Aucune facture disponible
page-dashboard-no-data = Aucune donnée disponible
page-dashboard-no-clients = Aucun client disponible
page-dashboard-no-payments-due = ✅ Aucun paiement en attente
page-dashboard-error-loading = ❌ Erreur de chargement du tableau de bord: { $error }
page-dashboard-refresh-button = 🔄 Actualiser les Données

### Recent Activity
page-dashboard-recent-activity = Activité Récente

## ============================================================================
## INVOICES PAGE (2_🧾_Fatture.py)
## ============================================================================

page-invoices-title = 🧾 Gestion des Factures
page-invoices-subtitle = Visualisez et gérez toutes vos factures

### Sidebar Filters
page-invoices-filter-title = 🔍 Filtres
page-invoices-filter-year = Année
page-invoices-filter-all = Tous
page-invoices-filter-status = Statut
page-invoices-filter-max-results = Résultats maximum
page-invoices-no-invoices-in-db = Aucune facture disponible
page-invoices-filter-client = Client
page-invoices-filter-date-from = De la Date
page-invoices-filter-date-to = À la Date
page-invoices-filter-amount-min = Montant Min
page-invoices-filter-amount-max = Montant Max
page-invoices-filter-search = Rechercher des factures...

### Quick Actions
page-invoices-action-quick-title = ⚡ Actions Rapides
page-invoices-action-new-invoice = ➕ Nouvelle Facture
page-invoices-action-new-invoice-info =
    **Fonctionnalité en développement**

    Pour l'instant, créez des factures via CLI :
    ```bash
    uv run openfatture fattura crea
    ```

    La création guidée dans l'interface web sera bientôt disponible !
page-invoices-action-refresh = 🔄 Actualiser la Liste

### Main Content
page-invoices-list-title = ### 📋 Liste des Factures
page-invoices-no-invoices-found = 📭 Aucune facture trouvée avec les filtres sélectionnés

### Stats Metrics
page-invoices-stats-count = 📊 Factures Trouvées
page-invoices-stats-total = 💰 Total
page-invoices-stats-statuses = 📋 Statuts Différents
page-invoices-stats-average = 📈 Montant Moyen

### Table
page-invoices-table-title = #### 📋 Tableau des Factures
page-invoices-col-id = ID
page-invoices-col-number = Numéro
page-invoices-col-date = Date
page-invoices-col-client = Client
page-invoices-col-total-eur = Total €
page-invoices-col-status = Statut
page-invoices-col-lines = Lignes
page-invoices-col-amount = Montant
page-invoices-col-payment = Paiement
page-invoices-col-actions = Actions

### Invoice Detail Section
page-invoices-detail-title = ### 🔍 Détail de la Facture
page-invoices-detail-input-id = Saisissez l'ID de la facture à afficher
page-invoices-detail-show-button = 📄 Afficher le Détail
page-invoices-detail-error-not-found = ❌ Facture avec ID { $id } non trouvée
page-invoices-detail-success = ✅ Facture { $number }/{ $year }

### Detail Header Metrics
page-invoices-detail-number = Numéro
page-invoices-detail-date = Date d'Émission
page-invoices-detail-client = Client
page-invoices-detail-type = Type
page-invoices-detail-status = Statut
page-invoices-detail-sdi-number = Numéro SDI

### Detail Line Items
page-invoices-detail-lines-title = #### 📦 Lignes de Facture
page-invoices-detail-lines-col-num = #
page-invoices-detail-lines-col-desc = Description
page-invoices-detail-lines-col-qty = Quantité
page-invoices-detail-lines-col-price = Prix €
page-invoices-detail-lines-col-vat = TVA %
page-invoices-detail-lines-col-total = Total €
page-invoices-detail-lines-empty = Aucune ligne disponible

### Detail Totals
page-invoices-detail-totals-title = #### 💰 Totaux
page-invoices-detail-totals-taxable = Base Imposable
page-invoices-detail-totals-vat = TVA
page-invoices-detail-totals-withholding = Retenue
page-invoices-detail-totals-stamp = Timbre
page-invoices-detail-totals-total = **TOTAL**

### Detail Files
page-invoices-detail-files-title = #### 📁 Fichiers
page-invoices-detail-files-xml-exists = ✅ XML : `{ $path }`
page-invoices-detail-files-xml-missing = 📄 XML pas encore généré
page-invoices-detail-files-pdf-exists = ✅ PDF : `{ $path }`
page-invoices-detail-files-pdf-missing = 📄 PDF pas encore généré

### Detail Actions
page-invoices-detail-actions-title = #### ⚡ Actions
page-invoices-detail-actions-generate-xml = 📝 Générer XML
page-invoices-detail-actions-generating-xml = Génération du XML...
page-invoices-detail-actions-error = ❌ Erreur : { $error }
page-invoices-detail-actions-xml-success = ✅ XML généré avec succès !
page-invoices-detail-actions-send-sdi = 📤 Envoyer au SDI
page-invoices-detail-actions-generate-pdf = 📄 Générer PDF
page-invoices-detail-actions-cli-feature = Fonctionnalité CLI

### Error Messages
page-invoices-error-loading = ❌ Erreur de chargement des factures : { $error }

### Legacy (kept for compatibility)
page-invoices-action-view = Voir
page-invoices-action-edit = Modifier
page-invoices-action-delete = Supprimer
page-invoices-action-send = Envoyer au SDI
page-invoices-action-download-xml = Télécharger XML
page-invoices-action-download-pdf = Télécharger PDF
page-invoices-action-duplicate = Dupliquer
page-invoices-no-invoices = Aucune facture trouvée
page-invoices-create-first = Créez votre première facture
page-invoices-total-found = { $count } factures trouvées
page-invoices-selected = { $count } sélectionnées

## ============================================================================
## INVOICE CREATION PAGE (13_✏️_Crea_Fattura.py)
## ============================================================================

### Page Configuration
page-invoice-create-page-title = Créer Facture - OpenFatture
page-invoice-create-title = ✏️ Création Guidée de Facture

### Wizard Progress
page-invoice-create-wizard-title = 📋 Création de Facture - Étape { $step }/{ $total }

### Step Labels
page-invoice-create-step-1-label = 👥 Sélectionner Client
page-invoice-create-step-2-label = 📝 Détails Facture
page-invoice-create-step-3-label = 🛒 Ajouter Produits
page-invoice-create-step-4-label = 🤖 Assistance IA
page-invoice-create-step-5-label = ✅ Résumé et Créer

### Step 1: Select Client
page-invoice-create-step-1-header = 👥 Sélectionner Client
page-invoice-create-client-search-label = Rechercher client existant
page-invoice-create-client-search-placeholder = Nom entreprise, N° TVA...
page-invoice-create-client-search-help = Laisser vide pour voir tous les clients
page-invoice-create-client-existing-title = Clients existants
page-invoice-create-client-vat-label = N° TVA
page-invoice-create-client-select-label = Sélectionner client
page-invoice-create-client-select-help = Choisir un client existant ou en créer un nouveau
page-invoice-create-client-create-title = ➕ Ou créer nouveau client
page-invoice-create-client-create-expander = Créer nouveau client
page-invoice-create-client-name-label = Nom Entreprise *
page-invoice-create-client-name-placeholder = Nom entreprise ou personne
page-invoice-create-client-vat-input-label = Numéro TVA
page-invoice-create-client-vat-placeholder = 12345678901
page-invoice-create-client-fiscal-code-label = Code Fiscal
page-invoice-create-client-fiscal-code-placeholder = Code fiscal (si particulier)
page-invoice-create-client-address-label = Adresse
page-invoice-create-client-address-placeholder = 123 Rue Rome, 00100 Rome
page-invoice-create-client-email-label = Email
page-invoice-create-client-email-placeholder = client@email.com
page-invoice-create-client-phone-label = Téléphone
page-invoice-create-client-phone-placeholder = +33 1 23 45 67 89
page-invoice-create-client-regime-label = Régime Fiscal
page-invoice-create-client-regime-ordinary = RF01 - Ordinaire
page-invoice-create-client-regime-flat = RF19 - Forfaitaire
page-invoice-create-client-create-button = Créer Client
page-invoice-create-client-name-required = Le nom d'entreprise est obligatoire
page-invoice-create-client-create-success = Client '{ $name }' créé avec succès !
page-invoice-create-client-create-error = Erreur lors de la création du client : { $error }

### Step 2: Invoice Details
page-invoice-create-step-2-header = 📝 Détails Facture
page-invoice-create-details-client-selected = Client sélectionné : **{ $name }**
page-invoice-create-details-regime = Régime fiscal : { $regime }
page-invoice-create-details-number-label = Numéro Facture
page-invoice-create-details-number-help = Numéro séquentiel de la facture
page-invoice-create-details-year-label = Année
page-invoice-create-details-year-help = Année fiscale
page-invoice-create-details-date-label = Date d'Émission
page-invoice-create-details-date-help = Date d'émission de la facture
page-invoice-create-details-due-date-label = Date d'Échéance
page-invoice-create-details-due-date-help = Date d'échéance du paiement
page-invoice-create-details-additional-title = 📋 Détails Supplémentaires
page-invoice-create-details-subject-label = Objet/Description
page-invoice-create-details-subject-placeholder = Description générale de la facture...
page-invoice-create-details-subject-help = Description générale des services/produits
page-invoice-create-details-notes-label = Notes
page-invoice-create-details-notes-placeholder = Notes supplémentaires...
page-invoice-create-details-notes-help = Notes internes ou de facture

### Step 3: Invoice Lines
page-invoice-create-step-3-header = 🛒 Produits et Services
page-invoice-create-lines-title = Lignes de facture
page-invoice-create-lines-description-label = Description
page-invoice-create-lines-quantity-label = Quantité
page-invoice-create-lines-price-label = Prix Unitaire (€)
page-invoice-create-lines-row-total = Total ligne : { $total }
page-invoice-create-lines-remove-button = 🗑️ Supprimer
page-invoice-create-lines-add-title = ➕ Ajouter nouvelle ligne
page-invoice-create-lines-description-input-label = Description *
page-invoice-create-lines-description-placeholder = Description du produit/service...
page-invoice-create-lines-quantity-input-label = Quantité
page-invoice-create-lines-quantity-help = Quantité du produit/service
page-invoice-create-lines-price-input-label = Prix Unitaire (€)
page-invoice-create-lines-price-help = Prix unitaire hors TVA
page-invoice-create-lines-vat-label = Taux de TVA
page-invoice-create-lines-vat-help = Taux de TVA applicable
page-invoice-create-lines-add-button = Ajouter Ligne
page-invoice-create-lines-description-required = La description est obligatoire
page-invoice-create-lines-add-success = Ligne ajoutée !
page-invoice-create-lines-totals-title = 💰 Totaux
page-invoice-create-lines-subtotal-label = Montant HT
page-invoice-create-lines-vat-amount-label = TVA
page-invoice-create-lines-total-label = Total

### Step 4: AI Assistance
page-invoice-create-step-4-header = 🤖 Assistance IA
page-invoice-create-ai-description-title = 📝 Générer Descriptions avec IA
page-invoice-create-ai-description-button = 🎯 Suggérer descriptions pour les lignes
page-invoice-create-ai-description-no-lines = Ajoutez d'abord des lignes à la facture
page-invoice-create-ai-description-generating = Génération des descriptions...
page-invoice-create-ai-description-improved = Description de la ligne { $row } améliorée !
page-invoice-create-ai-description-error = Erreur génération description ligne { $row } : { $error }
page-invoice-create-ai-vat-title = 💼 Conseils TVA
page-invoice-create-ai-vat-button = 🧾 Vérifier taux de TVA
page-invoice-create-ai-vat-no-lines = Ajoutez d'abord des lignes à la facture
page-invoice-create-ai-vat-checking = Vérification des taux de TVA...
page-invoice-create-ai-vat-suggestion = 💡 Ligne { $row } : Taux TVA suggéré { $suggested }% au lieu de { $current }%
page-invoice-create-ai-vat-apply = Appliquer { $rate }% à la ligne { $row }
page-invoice-create-ai-vat-updated = Taux de TVA mis à jour !
page-invoice-create-ai-vat-info = Ligne { $row } : { $info }
page-invoice-create-ai-vat-error = Erreur vérification TVA ligne { $row } : { $error }
page-invoice-create-ai-compliance-title = ⚖️ Vérification Conformité
page-invoice-create-ai-compliance-button = 🔍 Vérifier conformité facture
page-invoice-create-ai-compliance-no-number = Numéro de facture manquant
page-invoice-create-ai-compliance-no-lines = Aucune ligne de facture
page-invoice-create-ai-compliance-line-no-desc = Ligne { $row } : description manquante
page-invoice-create-ai-compliance-line-qty-invalid = Ligne { $row } : la quantité doit être > 0
page-invoice-create-ai-compliance-line-price-invalid = Ligne { $row } : le prix unitaire doit être > 0
page-invoice-create-ai-compliance-issues-found = Problèmes trouvés
page-invoice-create-ai-compliance-success = ✅ La facture est conforme aux exigences de base !

### Step 5: Summary
page-invoice-create-step-5-header = ✅ Résumé et Création
page-invoice-create-summary-client-title = 👥 Client
page-invoice-create-summary-client-vat = N° TVA : { $vat }
page-invoice-create-summary-client-regime = Régime : { $regime }
page-invoice-create-summary-invoice-title = 📄 Facture
page-invoice-create-summary-invoice-date = Émission : { $date }
page-invoice-create-summary-invoice-due = Échéance : { $date }
page-invoice-create-summary-lines-title = 🛒 Lignes de Facture
page-invoice-create-summary-table-description = Description
page-invoice-create-summary-table-quantity = Qté
page-invoice-create-summary-table-price = Prix
page-invoice-create-summary-table-vat = TVA
page-invoice-create-summary-table-total = Total
page-invoice-create-summary-totals-title = 💰 Totaux
page-invoice-create-summary-totals-subtotal = Montant HT
page-invoice-create-summary-totals-vat = TVA
page-invoice-create-summary-totals-total = Total Facture
page-invoice-create-summary-create-button = 🚀 Créer Facture
page-invoice-create-summary-creating = Création de la facture...
page-invoice-create-summary-error-create-failed = Impossible de créer la facture
page-invoice-create-summary-success = ✅ Facture { $number }/{ $year } créée avec succès !
page-invoice-create-summary-next-steps =
    **Prochaines étapes :**
    1. **Valider** la facture : `openfatture fattura valida { $number }`
    2. **Envoyer** au SDI : `openfatture pec invia { $number }`
    3. **Surveiller** l'état dans la page Factures
page-invoice-create-summary-error = Erreur lors de la création de la facture : { $error }

### Navigation
page-invoice-create-nav-back = ⬅️ Retour
page-invoice-create-nav-next = Suivant ➡️
page-invoice-create-nav-success = 🎉 Facture créée avec succès !
page-invoice-create-nav-create-another = 🔄 Créer une autre facture

## ============================================================================
## CLIENTS PAGE (3_👥_Clienti.py)
## ============================================================================

page-clients-title = 👥 Gestion des Clients
page-clients-subtitle = Visualisez et gérez vos clients

### Filters
page-clients-search = Rechercher des clients...
page-clients-filter-type = Type
page-clients-filter-country = Pays

### Table Headers
page-clients-col-name = Nom/Raison Sociale
page-clients-col-vat = N° TVA
page-clients-col-email = Email
page-clients-col-phone = Téléphone
page-clients-col-invoices = Factures
page-clients-col-revenue = Chiffre d'Affaires
page-clients-col-actions = Actions

### Actions
page-clients-action-add = Ajouter un Client
page-clients-action-view = Voir
page-clients-action-edit = Modifier
page-clients-action-delete = Supprimer
page-clients-action-create-invoice = Créer une Facture

### Messages
page-clients-no-clients = Aucun client trouvé
page-clients-add-first = Ajoutez votre premier client
page-clients-total-found = { $count } clients trouvés

## ============================================================================
## ============================================================================
## PAYMENTS PAGE (4_💰_Pagamenti.py)
## ============================================================================

### Page Config
page-payments-page-title = Paiements - OpenFatture
page-payments-title = 💰 Suivi et Rapprochement des Paiements

### Sidebar Filters
page-payments-filter-title = 🔍 Filtres
page-payments-filter-bank-account = Compte Bancaire
page-payments-filter-all-accounts = Tous
page-payments-filter-status = Statut
page-payments-no-accounts-configured = Aucun compte bancaire configuré

### Status Labels
page-payments-status-all = Tous
page-payments-status-unmatched = À Rapprocher
page-payments-status-matched = Rapprochés
page-payments-status-ignored = Ignorés
page-payments-status-paired = Appariés

### Sidebar Actions
page-payments-action-import = 📥 Importer
page-payments-action-import-help = Importer un relevé bancaire
page-payments-action-refresh = 🔄 Actualiser

### Import Form
page-payments-import-title = 📥 Importer un Relevé Bancaire
page-payments-import-select-account = Sélectionner le compte bancaire *
page-payments-import-select-account-help = Choisissez le compte où importer les transactions
page-payments-import-no-account-error = Aucun compte bancaire configuré. Créez-en un avant d'importer.
page-payments-import-file-label = Sélectionner le fichier de relevé
page-payments-import-file-help = Supporte les formats: OFX, QFX, CSV, QIF
page-payments-import-bank-preset = Banque (pour CSV)
page-payments-import-bank-preset-help = Sélectionnez la banque pour l'analyse correcte du CSV
page-payments-import-auto-match = Auto-appariement des paiements
page-payments-import-auto-match-help = Tenter automatiquement d'apparier les transactions aux factures
page-payments-import-confidence = Seuil de confiance
page-payments-import-confidence-help = Confiance minimale pour l'auto-appariement
page-payments-import-button = 🚀 Importer les Transactions
page-payments-import-error-no-account = Sélectionnez un compte bancaire
page-payments-import-error-no-file = Sélectionnez un fichier à importer
page-payments-import-importing = Importation des transactions...
page-payments-import-metric-imported = Transactions Importées
page-payments-import-metric-errors = Erreurs
page-payments-import-metric-duplicates = Doublons
page-payments-import-format-detected = 📄 Format détecté: { $format }
page-payments-import-errors-title = ⚠️ Erreurs lors de l'importation
page-payments-import-success-refresh = 🔄 Données mises à jour!
page-payments-import-close = ❌ Fermer

### Bank Accounts Overview
page-payments-accounts-title = 🏦 Comptes Bancaires
page-payments-accounts-current-balance = Solde Actuel
page-payments-accounts-iban = IBAN: ...{ $last4 }
page-payments-accounts-bank = Banque: { $name }

### Payment Statistics
page-payments-stats-title = 📊 Statistiques des Paiements
page-payments-stats-accounts = Comptes Bancaires
page-payments-stats-transactions = Transactions Totales
page-payments-stats-balance = Solde Total
page-payments-stats-reconciled = Rapprochés
page-payments-stats-distribution-title = 📈 Distribution par Statut
page-payments-stats-distribution-status = Statut
page-payments-stats-distribution-transactions = Transactions

### Transactions List
page-payments-transactions-title = 📋 Transactions
page-payments-table-col-id = ID
page-payments-table-col-date = Date
page-payments-table-col-amount = Montant
page-payments-table-col-description = Description
page-payments-table-col-reference = Référence
page-payments-table-col-status = Statut
page-payments-table-col-invoice = Facture
page-payments-table-col-actions = Actions
page-payments-action-view-details = Voir les détails
page-payments-action-match = Rapprocher
page-payments-transactions-summary = 📊 **Total affiché:** { $total } sur { $count } transactions
page-payments-no-transactions-filtered = 🔍 Aucune transaction trouvée avec les filtres sélectionnés
page-payments-no-transactions = 📭 Aucune transaction présente

### Quick Start Guide
page-payments-quickstart-title = 🚀 Démarrer avec les paiements
page-payments-quickstart-content =
    ### Premiers Pas

    1. **Ajouter un compte bancaire**
       ```bash
       uv run openfatture payment account add "Compte Entreprise" --iban IT123...
       ```

    2. **Importer un relevé bancaire**
       ```bash
       uv run openfatture payment import releve.ofx --account 1
       ```

    3. **Rapprocher automatiquement**
       ```bash
       uv run openfatture payment match --auto-apply
       ```

    4. **Vérifier les rapprochements**
       ```bash
       uv run openfatture payment status
       ```

### Error Messages
page-payments-error-loading = ❌ Erreur lors du chargement des paiements: { $error }
page-payments-error-loading-hint = 💡 Vérifiez que la base de données est correctement initialisée

### Transaction Detail Modal
page-payments-detail-title = 👁️ Détails de la Transaction { $id }...
page-payments-detail-id = ID
page-payments-detail-date = Date
page-payments-detail-amount = Montant
page-payments-detail-description = Description
page-payments-detail-reference = Référence
page-payments-detail-counterparty = Contrepartie
page-payments-detail-status = Statut
page-payments-detail-confidence = Confiance d'Appariement
page-payments-detail-linked-invoice = Facture Liée
page-payments-detail-close = ❌ Fermer
page-payments-detail-not-found = Transaction non trouvée

### Match Transaction Modal
page-payments-match-title = 🔗 Rapprocher la Transaction { $amount }
page-payments-match-date = Date
page-payments-match-amount = Montant
page-payments-match-description = Description
page-payments-match-reference = Référence
page-payments-match-counterparty = Contrepartie
page-payments-match-status = Statut
page-payments-match-suggestions-title = 🎯 Appariements Suggérés
page-payments-match-client = Client: { $client }
page-payments-match-confidence = Confiance
page-payments-match-days-diff = ±{ $days } jours
page-payments-match-button = ✅ Apparier
page-payments-match-matching = Appariement en cours...
page-payments-match-success = ✅ Transaction appariée à la facture { $number }
page-payments-match-error = ❌ Erreur: { $error }
page-payments-match-no-suggestions = 🔍 Aucun appariement automatique trouvé
page-payments-match-manual-title = 🔍 Recherche Manuelle
page-payments-match-manual-search = Rechercher une facture
page-payments-match-manual-placeholder = Numéro de facture, client...
page-payments-match-manual-help = Saisissez le numéro de facture ou le nom du client
page-payments-match-manual-results = Résultats de recherche:
page-payments-match-manual-button = Apparier
page-payments-match-manual-success = ✅ Apparié!
page-payments-match-manual-no-results = Aucune facture trouvée
page-payments-match-close = ❌ Fermer

### Quick Stats Section
page-payments-quick-stats-title = ### 📊 Statistiques des Paiements
page-payments-quick-stats-unmatched = 🔍 Non Appariés
page-payments-quick-stats-matched = ✅ Appariés
page-payments-quick-stats-ignored = ⏭️ Ignorés
page-payments-quick-stats-total = 📊 Total
page-payments-quick-stats-error = Erreur de chargement des données: { $error }

### Payment Due Section
page-payments-due-title = ### 💳 Échéances 30 Prochains Jours
page-payments-due-col-invoice = Facture
page-payments-due-col-client = Client
page-payments-due-col-due-date = Échéance
page-payments-due-col-residual = En Attente
page-payments-due-col-status = Statut
page-payments-due-total-residual = 💸 Total en Attente
page-payments-due-no-payments = ✅ Aucun paiement en attente

### Legacy (kept for compatibility)
page-payments-tab-overview = Aperçu
page-payments-tab-reconciliation = Rapprochement
page-payments-tab-history = Historique
page-payments-total-received = Reçu
page-payments-total-pending = À Recevoir
page-payments-total-overdue = En Retard
page-payments-reconciliation-rate = Taux de Rapprochement
page-payments-import-bank = Importer un Relevé Bancaire
page-payments-match-automatic = Appariement Automatique
page-payments-match-manual = Appariement Manuel
page-payments-unmatched = Transactions Non Appariées
page-payments-matched = Transactions Appariées
page-payments-col-invoice = Facture
page-payments-col-client = Client
page-payments-col-amount = Montant
page-payments-col-due-date = Échéance
page-payments-col-paid-date = Date de Paiement
page-payments-col-status = Statut
page-payments-col-method = Méthode

## ============================================================================
## AI ASSISTANT PAGE (5_🤖_AI_Assistant.py)
## ============================================================================

### Page Config
page-ai-page-title = Assistant IA - OpenFatture
page-ai-title = 🤖 Assistant IA
page-ai-subtitle = Assistant Intelligent pour Facturation et Fiscalité
page-ai-not-configured =
    ⚠️ **IA non configurée**

    Pour activer l'Assistant IA :
    1. Configurez les identifiants dans le fichier `.env`
    2. Définissez `AI_PROVIDER` (openai/anthropic/ollama)
    3. Définissez `AI_API_KEY` (si nécessaire)
    4. Redémarrez l'application

    Consultez `docs/CONFIGURATION.md` pour plus de détails.

### Tabs
page-ai-tab-chat = Chat avec l'Assistant
page-ai-tab-description = Générer une Description
page-ai-tab-vat = Suggestion de TVA
page-ai-tab-voice = Chat Vocal

### General
page-ai-yes = ✓ OUI
page-ai-no = ✗ NON

### Retry Logic
page-ai-retry-message = 🔄 Tentative { $attempt }/{ $max_retries } échouée. Nouvelle tentative dans { $delay }s...

### Error Messages
page-ai-error-connection = 🌐 Erreur de connexion. Vérifiez votre connexion internet et réessayez.
page-ai-error-auth = 🔐 Erreur d'authentification. Vérifiez vos identifiants IA.
page-ai-error-rate-limit = ⏱️ Limite de débit atteinte. Réessayez dans quelques minutes.
page-ai-error-service-unavailable = 🚫 Service temporairement indisponible. Réessayez plus tard.
page-ai-error-generic = ❌ Erreur inattendue : { $error }...
page-ai-error-hint-connection = 💡 Astuce : Vérifiez votre connexion internet
page-ai-error-hint-auth = 💡 Astuce : Vérifiez les paramètres IA dans les préférences

### Slash Commands
page-ai-command-help-feedback =
    **🤖 Commandes Disponibles :**

    **Intégrées :**
    - `/help` - Afficher ce message
    - `/tools` - Lister les outils IA disponibles
    - `/stats` - Statistiques de conversation actuelle
    - `/custom` - Lister les commandes personnalisées
    - `/reload` - Recharger les commandes depuis le disque
    - `/clear` - Effacer l'historique du chat

    **Personnalisées :**
    Créer des commandes dans `~/.openfatture/commands/*.yaml`

    **Exemples :**
    - "Comment créer une facture ?"
    - "Quel est le taux de TVA pour le design web ?"
    - "Montre-moi les factures de ce mois"

page-ai-command-tools-feedback =
    **🔧 Outils IA Disponibles :**

    **Recherche et Consultation :**
    - Rechercher des factures par client, date, montant
    - Statistiques de revenus et paiements
    - Consultation de réglementation fiscale

    **Actions Disponibles :**
    - Créer des descriptions professionnelles de factures
    - Suggérer des taux de TVA corrects
    - Analyse de conformité des factures

    **Intégration de Données :**
    - Accès à la base de données clients et produits
    - Historique des paiements et échéances
    - Rapports et analyses d'entreprise

page-ai-command-stats-feedback =
    **📊 Statistiques de Conversation :**

    - **Messages totaux :** { $total_messages }
    - **Vos messages :** { $user_messages }
    - **Réponses IA :** { $assistant_messages }
    - **Caractères totaux :** { NUMBER($total_chars) }
    - **Tokens estimés :** { NUMBER($estimated_tokens) }

    **💡 Astuces :**
    - Utilisez `/clear` pour recommencer
    - Sauvegardez les conversations importantes avec 💾 Sauvegarder

page-ai-command-custom-no-commands = 📝 **Aucune commande personnalisée trouvée**\n\nCréez des commandes dans `~/.openfatture/commands/*.yaml`
page-ai-command-custom-header = 📝 **Commandes Personnalisées ({ $count }) :**
page-ai-command-custom-footer = 💡 Utilisez `/help` pour voir toutes les commandes
page-ai-command-reload-success = 🔄 **Commandes rechargées :** { $old_count } → { $new_count } ({ $added } ajoutées, { $removed } supprimées)
page-ai-command-reload-error = ❌ **Erreur de rechargement :** { $error }
page-ai-command-clear-feedback = 🗑️ **Historique effacé**\n\nLa conversation a été réinitialisée.
page-ai-command-custom-expanded = 🔧 **Commande étendue :** `/{ $command }` → { $length } caractères
page-ai-command-custom-error = ❌ **Erreur de commande :** { $error }
page-ai-command-unknown = ❓ **Commande inconnue :** `{ $command }`\n\nUtilisez `/help` pour voir les commandes disponibles

### Tab 1: Chat Assistant
page-ai-chat-title = Chat Interactif
page-ai-chat-description =
    Discutez avec l'assistant IA pour :
    - Questions sur la facturation et la réglementation
    - Conseils fiscaux et TVA
    - Gestion des paiements et échéances
    - Conseil d'entreprise général

page-ai-chat-save = Sauvegarder
page-ai-chat-save-help = Sauvegarder la conversation
page-ai-chat-session-title = Chat { $count } messages
page-ai-chat-saved = ✅ Sauvegardé : { $session_id }...
page-ai-chat-save-error = ❌ Erreur de sauvegarde
page-ai-chat-reload = Recharger
page-ai-chat-reload-help = Recharger les commandes personnalisées
page-ai-chat-reloaded = ✅ Rechargées : { $count } commandes
page-ai-chat-clear = Effacer

### Chat File Upload
page-ai-chat-file-upload-title = 📎 Joindre un Fichier (Optionnel)
page-ai-chat-file-upload-label = Téléchargez un document pour en discuter avec l'IA
page-ai-chat-file-upload-help = Supporte PDF, texte, images et autres documents
page-ai-chat-file-uploaded = 📄 Fichier téléchargé : { $name } ({ $size } octets)
page-ai-chat-files-attached = Fichiers Joints
page-ai-chat-files-clear-all = Tout Effacer
page-ai-chat-files-cleared = Fichiers effacés !

### Chat File Types
page-ai-chat-file-text-preview = - **{ $name }** (texte) : { $preview }
page-ai-chat-file-text = - **{ $name }** (texte, { $size } octets)
page-ai-chat-file-pdf = - **{ $name }** (PDF, { $size } octets) - Contenu à analyser
page-ai-chat-file-image = - **{ $name }** (image { $format }, { $size } octets) - Texte à extraire via OCR
page-ai-chat-file-other = - **{ $name }** ({ $type }, { $size } octets)
page-ai-chat-file-analysis-hint = L'IA analysera ces fichiers pour fournir une réponse plus précise.

### Custom Commands
page-ai-chat-custom-commands-title = 📝 Commandes Personnalisées
page-ai-chat-custom-commands-empty = Aucune commande personnalisée trouvée. Créez des commandes dans `~/.openfatture/commands/*.yaml`
page-ai-chat-custom-commands-count = **{ $count } commandes disponibles :**
page-ai-chat-custom-commands-description = **Description :** { $desc }
page-ai-chat-custom-commands-examples = Exemples
page-ai-chat-custom-commands-author = **Auteur :** { $author }
page-ai-chat-custom-commands-version = **Version :** { $version }

### Chat Sessions
page-ai-chat-sessions-title = 💾 Sessions Sauvegardées
page-ai-chat-sessions-empty = Aucune session sauvegardée. Utilisez le bouton 💾 Sauvegarder pour sauvegarder la conversation actuelle.
page-ai-chat-sessions-count = **{ $count } sessions disponibles :**
page-ai-chat-sessions-load = Charger
page-ai-chat-sessions-loaded = ✅ Session chargée : { $title }
page-ai-chat-sessions-load-error-empty = ❌ Session vide ou corrompue
page-ai-chat-sessions-load-error = ❌ Erreur de chargement : { $error }
page-ai-chat-sessions-rename = Renommer
page-ai-chat-sessions-rename-todo = Fonction de renommage à implémenter
page-ai-chat-sessions-delete = Supprimer
page-ai-chat-sessions-deleted = ✅ Session supprimée
page-ai-chat-sessions-delete-error = ❌ Erreur de suppression

### Chat Input & Messages
page-ai-chat-input-placeholder = Tapez votre message ou utilisez /commande...
page-ai-chat-attachments = Pièces jointes
page-ai-chat-thinking = Réflexion en cours...

### Chat Feedback
page-ai-chat-feedback-good = Bon
page-ai-chat-feedback-good-comment = Bonne réponse
page-ai-chat-feedback-bad = Mauvais
page-ai-chat-feedback-bad-comment = Réponse insatisfaisante
page-ai-chat-feedback-comment = Commentaire
page-ai-chat-feedback-comment-label = Laissez un commentaire sur la réponse :
page-ai-chat-feedback-submit = Envoyer le Commentaire
page-ai-chat-feedback-comment-sent = ✅ Commentaire envoyé !
page-ai-chat-feedback-comment-empty = Entrez un commentaire
page-ai-chat-feedback-thanks = ✅ Merci pour votre retour !
page-ai-chat-feedback-error = ❌ Erreur d'envoi du commentaire

### Tab 2: Description Generator
page-ai-desc-title = Générer une Description de Facture
page-ai-desc-description =
    Générez des descriptions professionnelles pour vos factures à l'aide de l'IA.
    Fournissez des informations sur le service et obtenez une description détaillée.

page-ai-desc-service-label = Service Fourni *
page-ai-desc-service-placeholder = ex., Conseil en développement d'application web e-commerce
page-ai-desc-service-help = Décrivez brièvement le service/produit
page-ai-desc-hours-label = Heures Travaillées
page-ai-desc-hours-help = Nombre d'heures (optionnel)
page-ai-desc-project-label = Nom du Projet
page-ai-desc-project-placeholder = ex., Projet E-Commerce XYZ
page-ai-desc-project-help = Nom du projet (optionnel)
page-ai-desc-rate-label = Taux Horaire (€)
page-ai-desc-rate-help = Taux horaire en euros (optionnel)
page-ai-desc-tech-label = Technologies
page-ai-desc-tech-placeholder = Python, FastAPI, PostgreSQL
page-ai-desc-tech-help = Technologies utilisées, séparées par des virgules (optionnel)
page-ai-desc-generate = Générer la Description
page-ai-desc-error-empty = ⚠️ Entrez une description du service
page-ai-desc-generating = 🤖 Génération d'une description professionnelle...
page-ai-desc-success = ✅ Description générée avec succès !
page-ai-desc-result-title = Description Professionnelle
page-ai-desc-deliverables = Livrables
page-ai-desc-skills = Compétences Techniques
page-ai-desc-duration = **⏱️ Durée :** { $hours } heures
page-ai-desc-notes = **📌 Notes :** { $notes }
page-ai-desc-result-generated = Description Générée

### Tab 3: VAT Suggestion
page-ai-vat-title = Suggestion de Taux de TVA
page-ai-vat-description =
    Obtenez des suggestions IA sur le taux de TVA correct et le traitement fiscal
    en fonction du type de service/produit et du client.

page-ai-vat-service-label = Description du Service/Produit *
page-ai-vat-service-placeholder = ex., Conseil informatique pour développement de logiciel de gestion
page-ai-vat-service-help = Décrivez le service ou produit à facturer
page-ai-vat-client-pa-label = Le Client est une Administration Publique
page-ai-vat-client-pa-help = Cochez si le client est AP
page-ai-vat-amount-label = Montant (€)
page-ai-vat-amount-help = Montant en euros (optionnel)
page-ai-vat-client-foreign-label = Client Étranger
page-ai-vat-client-foreign-help = Cochez si le client n'est pas résident en Italie
page-ai-vat-country-label = Pays du Client
page-ai-vat-country-placeholder = IT, FR, US...
page-ai-vat-country-help = Code pays ISO à 2 lettres
page-ai-vat-category-label = Catégorie de Service
page-ai-vat-category-help = Catégorie du service (optionnel)
page-ai-vat-category-consulting = Conseil
page-ai-vat-category-software = Développement Logiciel
page-ai-vat-category-training = Formation
page-ai-vat-category-design = Design/Graphisme
page-ai-vat-category-marketing = Marketing
page-ai-vat-category-maintenance = Maintenance
page-ai-vat-category-other = Autre
page-ai-vat-suggest = Obtenir une Suggestion de TVA
page-ai-vat-error-empty = ⚠️ Entrez une description du service/produit
page-ai-vat-analyzing = 🤖 Analyse du traitement fiscal...
page-ai-vat-success = ✅ Analyse terminée !
page-ai-vat-treatment-title = Traitement Fiscal
page-ai-vat-rate-metric = Taux de TVA
page-ai-vat-reverse-charge-metric = Autoliquidation
page-ai-vat-confidence-metric = Confiance
page-ai-vat-nature-code = **Code Nature TVA :** { $code }
page-ai-vat-split-payment = ⚠️ **Paiement Fractionné** applicable
page-ai-vat-special-regime = **Régime Spécial :** { $regime }
page-ai-vat-explanation-title = Explication
page-ai-vat-legal-reference-title = Référence Légale
page-ai-vat-invoice-note-title = Note pour Facture
page-ai-vat-recommendations-title = Recommandations
page-ai-vat-suggestion-title = Suggestion
page-ai-vat-error = ❌ Erreur : { $error }
page-ai-vat-error-generic = ❌ Erreur lors de l'analyse : { $error }

### Tab 4: Voice Chat
page-ai-voice-title = Chat Vocal avec IA
page-ai-voice-not-configured =
    ⚠️ **Chat Vocal non configuré**

    Pour activer le Chat Vocal :
    1. Configurez `OPENAI_API_KEY` dans le fichier `.env`
    2. Définissez `OPENFATTURE_VOICE_ENABLED=true`
    3. Redémarrez l'application

    Consultez la documentation pour plus de détails.

page-ai-voice-description =
    Parlez à l'assistant IA en utilisant votre voix :
    - 🎤 Enregistrez votre question
    - 🤖 L'IA transcrit et répond
    - 🔊 Écoutez la réponse vocale
    - 💬 Supporte les conversations avec contexte

### Voice Configuration
page-ai-voice-config-title = ⚙️ Configuration Vocale
page-ai-voice-config-provider = Fournisseur
page-ai-voice-config-stt = Modèle STT
page-ai-voice-config-tts-voice = Voix TTS
page-ai-voice-config-tts-model = **Modèle TTS :** { $model }
page-ai-voice-config-tts-speed = **Vitesse TTS :** { $speed }x
page-ai-voice-config-tts-format = **Format TTS :** { $format }
page-ai-voice-config-streaming = **Streaming :** { $enabled }

### Voice History
page-ai-voice-clear = Effacer la Voix
page-ai-voice-history-title = Historique de Conversation
page-ai-voice-user-message = **Vous :** { $text }
page-ai-voice-assistant-message = **Assistant :** { $text }
page-ai-voice-language-detected = Langue détectée : { $lang }
page-ai-voice-language = Langue : { $lang }
page-ai-voice-metric-stt = STT : { $ms }ms
page-ai-voice-metric-llm = LLM : { $ms }ms
page-ai-voice-metric-tts = TTS : { $ms }ms
page-ai-voice-metric-total = Total : { $ms }ms
page-ai-voice-metric-total-label = Total
page-ai-voice-history-empty = 👋 Pas encore de conversations vocales. Enregistrez votre première question !

### Voice Input
page-ai-voice-record-title = Enregistrez votre voix
page-ai-voice-record-label = Appuyez sur le bouton pour enregistrer
page-ai-voice-record-help = Parlez clairement dans le microphone. L'enregistrement s'arrête automatiquement après le silence.
page-ai-voice-recorded = ✅ Audio enregistré : { $size } octets
page-ai-voice-process = Envoyer et Traiter
page-ai-voice-processing = 🤖 Traitement de votre message vocal...
page-ai-voice-success = ✅ Message vocal traité avec succès !
page-ai-voice-transcription-title = Transcription
page-ai-voice-response-title = Réponse IA
page-ai-voice-audio-response-title = Réponse Vocale
page-ai-voice-metrics-title = Métriques
page-ai-voice-tech-details = ℹ️ Détails Techniques
page-ai-voice-error = ❌ Erreur lors du traitement : { $error }
page-ai-voice-error-hint-connection = 💡 Astuce : Vérifiez votre connexion internet
page-ai-voice-error-hint-auth = 💡 Astuce : Vérifiez les paramètres API dans la configuration
page-ai-voice-error-hint-rate = 💡 Astuce : Limite de débit atteinte. Réessayez dans quelques minutes

### Voice Help
page-ai-voice-help-title = ❓ Comment ça marche
page-ai-voice-help-content =
    **Flux de Chat Vocal :**

    1. **🎤 Enregistrement** : Appuyez sur le bouton et parlez dans le microphone
    2. **📝 Transcription (STT)** : OpenAI Whisper convertit la voix en texte
    3. **🤖 Traitement (LLM)** : L'IA comprend et génère une réponse
    4. **🔊 Synthèse (TTS)** : OpenAI TTS convertit la réponse en audio
    5. **▶️ Lecture** : Écoutez la réponse vocale

    **Support des Langues :**
    - Détection automatique parmi plus de 100 langues
    - Italien, Anglais, Français, Allemand, Espagnol et bien d'autres

    **Coûts Estimés :**
    - STT (Whisper) : ~0,006 $ par minute d'audio
    - TTS : ~0,015 $ par 1 000 caractères (tts-1) ou ~0,030 $ (tts-1-hd)
    - LLM : Tarification standard du modèle configuré

    **Exigences :**
    - Microphone fonctionnel
    - Navigateur moderne (Chrome, Firefox, Safari, Edge)
    - Connexion internet stable

### Metrics (shared across tabs)
page-ai-metric-provider = Fournisseur
page-ai-metric-tokens = Tokens
page-ai-metric-cost = Coût

### Footer
page-ai-footer-disclaimer =
    **💡 Astuce :** L'Assistant IA est un outil de support. Les informations fournies
    doivent toujours être vérifiées avec un comptable ou conseiller fiscal pour garantir
    la conformité aux réglementations en vigueur.

## ============================================================================
## CLIENTS PAGE (3_👥_Clienti.py)
## ============================================================================

page-clients-title = 👥 Gestion des Clients
page-clients-subtitle = Voir et gérer vos clients

### Sidebar Filters
page-clients-filter-title = 🔍 Filtres
page-clients-filter-search = Rechercher
page-clients-filter-search-placeholder = Raison Sociale, TVA, SIRET...
page-clients-filter-search-help = Rechercher par raison sociale, numéro de TVA ou SIRET

### Actions
page-clients-action-new = ➕ Nouveau Client
page-clients-action-refresh = 🔄 Actualiser
page-clients-action-view = Voir les détails
page-clients-action-edit = Modifier
page-clients-action-delete = Supprimer

### Add Client Form
page-clients-form-add-title = ➕ Nouveau Client
page-clients-form-denominazione = Raison Sociale *
page-clients-form-denominazione-placeholder = Nom de l'entreprise ou de la personne
page-clients-form-piva = Numéro de TVA
page-clients-form-piva-placeholder = 12345678901
page-clients-form-cf = Code Fiscal
page-clients-form-cf-placeholder = RSSMRA80A01H501U
page-clients-form-sdi = Code SDI
page-clients-form-sdi-placeholder = ABC1234
page-clients-form-pec = PEC
page-clients-form-pec-placeholder = client@pec.it
page-clients-form-address = Adresse
page-clients-form-address-placeholder = Rue de Rome 123
page-clients-form-zip = Code Postal
page-clients-form-zip-placeholder = 75001
page-clients-form-phone = Téléphone
page-clients-form-phone-placeholder = +33 1 23 45 67 89
page-clients-form-city = Ville
page-clients-form-city-placeholder = Paris
page-clients-form-province = Province
page-clients-form-province-placeholder = 75
page-clients-form-email = Email
page-clients-form-email-placeholder = client@email.com
page-clients-form-notes = Notes
page-clients-form-notes-placeholder = Notes supplémentaires...
page-clients-form-save = 💾 Enregistrer le Client
page-clients-form-cancel = ❌ Annuler

### Statistics
page-clients-stats-title = 📊 Statistiques
page-clients-stats-total = Total Clients
page-clients-stats-with-pec = Avec PEC
page-clients-stats-with-sdi = Avec SDI
page-clients-stats-with-piva = Avec TVA

### Client List
page-clients-list-title = 📋 Liste des Clients

### Table Columns
page-clients-table-col-id = ID
page-clients-table-col-denominazione = Raison Sociale
page-clients-table-col-piva = N° TVA
page-clients-table-col-cf = Code Fiscal
page-clients-table-col-sdi = SDI
page-clients-table-col-pec = PEC
page-clients-table-col-comune = Ville
page-clients-table-col-provincia = Dép.
page-clients-table-col-created = Créé le
page-clients-table-col-actions = Actions

### Empty State
page-clients-no-results = 🔍 Aucun client trouvé pour '{ $term }'
page-clients-empty-state = 📝 Aucun client trouvé. Créez votre premier client !

### Quick Add Form
page-clients-quick-add-title = 🚀 Créer votre premier client
page-clients-quick-add-description = Remplissez les informations essentielles :
page-clients-quick-add-pec-optional = PEC (optionnel)
page-clients-quick-add-button = ➕ Créer le Client

### Client Detail
page-clients-detail-title = 👁️ Détails du Client : { $name }
page-clients-detail-id = ID
page-clients-detail-denominazione = Raison Sociale
page-clients-detail-piva = N° TVA
page-clients-detail-cf = Code Fiscal
page-clients-detail-sdi = SDI
page-clients-detail-pec = PEC
page-clients-detail-phone = Téléphone
page-clients-detail-email = Email
page-clients-detail-address = Adresse
page-clients-detail-city = Ville
page-clients-detail-notes = Notes
page-clients-detail-na = N/A
page-clients-detail-close = ❌ Fermer

### Edit Client
page-clients-edit-title = ✏️ Modifier le Client : { $name }
page-clients-edit-save = 💾 Enregistrer les Modifications

### Delete Client
page-clients-delete-title = 🗑️ Supprimer le Client : { $name }
page-clients-delete-confirm = ⚠️ Êtes-vous sûr de vouloir supprimer le client '{ $name }' ?
page-clients-delete-warning = Cette action ne peut pas être annulée.
page-clients-delete-yes = 🗑️ Oui, Supprimer
page-clients-delete-no = ❌ Annuler

### Quick Preview
page-clients-preview-title = 📊 Aperçu Rapide
page-clients-preview-total = 👥 Total Clients
page-clients-preview-invoices = 📄 Total Factures
page-clients-preview-top5 = 👑 Top 5 Clients
page-clients-preview-col-client = Client
page-clients-preview-col-invoices = Nb Factures
page-clients-preview-col-revenue = Chiffre d'Affaires Total

### Success Messages
page-clients-success-created = ✅ Client '{ $name }' créé avec succès !
page-clients-success-updated = ✅ Client '{ $name }' mis à jour !
page-clients-success-deleted = ✅ Client '{ $name }' supprimé !
page-clients-success-quick-created = ✅ Client '{ $name }' créé !

### Error Messages
page-clients-error-denominazione-required = La raison sociale est obligatoire
page-clients-error-create = ❌ Erreur lors de la création du client : { $error }
page-clients-error-update = ❌ Erreur lors de la mise à jour : { $error }
page-clients-error-delete = ❌ Erreur lors de la suppression : { $error }
page-clients-error-not-found = Client non trouvé
page-clients-error-loading = ❌ Erreur lors du chargement des clients : { $error }
page-clients-error-loading-hint = 💡 Vérifiez que la base de données est correctement initialisée
page-clients-error-quick-create = ❌ Erreur : { $error }
page-clients-preview-error = Erreur de chargement des données : { $error }

### Legacy (kept for compatibility)
page-clients-search = Rechercher des clients...
page-clients-filter-type = Type
page-clients-filter-country = Pays
page-clients-col-name = Nom/Raison Sociale
page-clients-col-vat = N° TVA
page-clients-col-email = Email
page-clients-col-phone = Téléphone
page-clients-col-invoices = Factures
page-clients-col-revenue = Chiffre d'Affaires
page-clients-col-actions = Actions
page-clients-action-add = Ajouter un Client
page-clients-action-create-invoice = Créer une Facture
page-clients-no-clients = Aucun client trouvé
page-clients-add-first = Ajoutez votre premier client
page-clients-total-found = { $count } clients trouvés

## ============================================================================
## PAGE RAPPORTS (9_📊_Reports.py)
## ============================================================================

page-reports-page-title = Rapports - OpenFatture
page-reports-title = 📊 Rapports et Analyses
page-reports-subtitle = Rapports d'entreprise et analyses avancées
page-reports-no-data = ⚠️ Aucune donnée disponible pour les rapports
page-reports-no-data-info = Créez quelques factures pour voir les rapports

### Barre latérale
page-reports-filter-title = 🔍 Paramètres du Rapport
page-reports-filter-year = Année
page-reports-filter-quarter = Trimestre (facultatif)
page-reports-filter-quarter-all = Tous
page-reports-filter-quarter-q1 = T1
page-reports-filter-quarter-q2 = T2
page-reports-filter-quarter-q3 = T3
page-reports-filter-quarter-q4 = T4

### Onglets
page-reports-tab-revenue = 💰 Chiffre d'Affaires
page-reports-tab-vat = 📋 TVA
page-reports-tab-clients = 👥 Clients

### Onglet Chiffre d'Affaires
page-reports-revenue-title = 💰 Rapport de Chiffre d'Affaires
page-reports-revenue-total = Chiffre d'Affaires Total
page-reports-revenue-total-help = Période : { $period }
page-reports-revenue-vat-total = TVA Totale
page-reports-revenue-invoices = Factures Émises
page-reports-revenue-avg = Valeur Moyenne de Facture
page-reports-revenue-monthly = 📈 Tendance Mensuelle
page-reports-revenue-chart-title = Chiffre d'Affaires Mensuel
page-reports-revenue-chart-xaxis = Mois
page-reports-revenue-chart-yaxis = Chiffre d'Affaires (€)
page-reports-revenue-count-chart = Nombre de Factures Mensuelles
page-reports-revenue-count-yaxis = Nombre de Factures

### Onglet TVA
page-reports-vat-title = 📋 Rapport TVA
page-reports-vat-taxable = Base Imposable Totale
page-reports-vat-total = TVA Totale
page-reports-vat-revenue-total = Chiffre d'Affaires Total
page-reports-vat-breakdown-title = 📊 Répartition par Taux de TVA
page-reports-vat-pie-title = Distribution de la Base Imposable par Taux de TVA
page-reports-vat-detail-title = 📋 Détail par Taux
page-reports-vat-table-rate = Taux de TVA
page-reports-vat-table-taxable = Base Imposable
page-reports-vat-table-vat = TVA
page-reports-vat-table-total = Total

### Onglet Clients
page-reports-clients-title = 👥 Rapport Clients
page-reports-clients-active = Clients Actifs
page-reports-clients-active-help = Clients avec factures émises en { $year }
page-reports-clients-top-title = 🏆 Top Clients par Chiffre d'Affaires
page-reports-clients-table-client = Client
page-reports-clients-table-invoices = Factures
page-reports-clients-table-total = Total
page-reports-clients-table-last = Dernière Facture
page-reports-clients-chart-title = Top 10 Clients par Chiffre d'Affaires
page-reports-clients-chart-xaxis = Client
page-reports-clients-chart-yaxis = Chiffre d'Affaires (€)

### Export
page-reports-export-title = 📤 Exporter les Rapports
page-reports-export-revenue = 📊 Exporter Chiffre d'Affaires (CSV)
page-reports-export-vat = 📋 Exporter TVA (CSV)
page-reports-export-clients = 👥 Exporter Clients (CSV)
page-reports-export-download = Télécharger CSV

page-reports-footer = 📊 <strong>Rapports mis à jour automatiquement</strong> • Données basées sur les factures livrées ou acceptées

## ============================================================================
## PAGE HOOKS (10_🪝_Hooks.py)
## ============================================================================

page-hooks-page-title = Hooks et Automatisation - OpenFatture
page-hooks-title = 🪝 Hooks et Automatisation
page-hooks-subtitle = Gestion des workflows automatisés et des déclencheurs

### Métriques de Résumé
page-hooks-metric-total = Hooks Totaux
page-hooks-metric-enabled = Hooks Actifs
page-hooks-metric-pre = Pré-hooks
page-hooks-metric-post = Post-hooks

### Onglets
page-hooks-tab-overview = 📊 Vue d'Ensemble
page-hooks-tab-manage = ⚙️ Gérer
page-hooks-tab-create = ➕ Créer Hook
page-hooks-tab-test = 🧪 Tester

### Onglet Vue d'Ensemble
page-hooks-overview-title = 📊 Vue d'Ensemble des Hooks
page-hooks-overview-group-pre = 🎯
page-hooks-overview-group-post = ✅
page-hooks-overview-group-on = 👀
page-hooks-overview-status-active = ✅ Actif
page-hooks-overview-status-inactive = ⏸️ Inactif
page-hooks-overview-timeout = ⏱️ { $timeout }s
page-hooks-overview-empty = 🎣 Aucun hook trouvé. Créez votre premier hook dans l'onglet 'Créer Hook' !

### Onglet Gestion
page-hooks-manage-title = ⚙️ Gérer les Hooks
page-hooks-manage-toggle-title = Basculer l'État des Hooks
page-hooks-manage-toggle-label = Activer { $name }
page-hooks-manage-toggle-help = Activer/désactiver le hook { $name }
page-hooks-manage-toggle-enabled = ✅ Hook '{ $name }' activé
page-hooks-manage-toggle-disabled = ⏸️ Hook '{ $name }' désactivé
page-hooks-manage-toggle-error = ❌ Erreur lors de la mise à jour de l'état du hook
page-hooks-manage-details-button = 👁️ Détails
page-hooks-manage-details-help = Afficher les détails du hook
page-hooks-manage-details-title = Détails { $name }
page-hooks-manage-empty = 🎣 Aucun hook à gérer

### Onglet Création
page-hooks-create-title = ➕ Créer un Nouveau Hook
page-hooks-create-name-label = Nom du Hook
page-hooks-create-name-placeholder = ex. : post-invoice-send
page-hooks-create-name-help = Nom du hook (utilisez les préfixes pre-, post-, on-)
page-hooks-create-type-label = Type de Script
page-hooks-create-type-help = Type de script pour le hook
page-hooks-create-type-bash = bash
page-hooks-create-type-python = python
page-hooks-create-desc-label = Description
page-hooks-create-desc-placeholder = Que fait ce hook...
page-hooks-create-desc-help = Brève description du hook
page-hooks-create-event-label = Type d'Événement
page-hooks-create-event-help = Quand le hook est exécuté
page-hooks-create-event-pre = pre
page-hooks-create-event-post = post
page-hooks-create-event-on = on
page-hooks-create-preview-title = 📋 Aperçu du Modèle
page-hooks-create-preview-code = 👁️ Code du Modèle
page-hooks-create-button = 🚀 Créer Hook
page-hooks-create-error-name = ❌ Entrez un nom pour le hook
page-hooks-create-warning-prefix = 💡 Conseil : le nom devrait commencer par '{ $prefix }-'
page-hooks-create-success = ✅ { $message }
page-hooks-create-reload = 🔄 Rechargez la page pour voir le nouveau hook
page-hooks-create-error = ❌ { $message }

### Onglet Test
page-hooks-test-title = 🧪 Tester les Hooks
page-hooks-test-select-label = Sélectionner un Hook à Tester
page-hooks-test-select-help = Choisissez le hook à valider
page-hooks-test-info-title = 📋 Informations sur le Hook
page-hooks-test-metric-type = Type d'Événement
page-hooks-test-metric-status = Statut
page-hooks-test-metric-timeout = Timeout
page-hooks-test-metric-status-active = Actif
page-hooks-test-metric-status-inactive = Inactif
page-hooks-test-validate-button = 🧪 Valider Hook
page-hooks-test-validating = Validation du hook...
page-hooks-test-success = ✅ Hook validé avec succès !
page-hooks-test-metric-lines = Lignes de Code
page-hooks-test-metric-size = Taille
page-hooks-test-metric-size-value = { $size } octets
page-hooks-test-metric-executable = Exécutable
page-hooks-test-metric-executable-yes = Oui
page-hooks-test-metric-executable-no = Non
page-hooks-test-result-message = 💡 { $message }
page-hooks-test-error = ❌ Erreur de validation : { $error }
page-hooks-test-show-code = 📄 Afficher le Code
page-hooks-test-code-error = ❌ Fichier de hook non trouvé
page-hooks-test-read-error = ❌ Erreur de lecture du fichier : { $error }
page-hooks-test-empty = 🎣 Aucun hook disponible pour le test

page-hooks-footer =
    🪝 <strong>Système de Hooks :</strong> Automatisation de workflows basée sur les événements •
    📍 <strong>Répertoire :</strong> ~/.openfatture/hooks/ •
    📚 <strong>Documentation :</strong> Voir CLI pour des exemples avancés

## ============================================================================
## PAGE ÉVÉNEMENTS (11_📋_Events.py)
## ============================================================================

page-events-page-title = Événements et Piste d'Audit - OpenFatture
page-events-title = 📋 Événements et Piste d'Audit
page-events-subtitle = Suivi des événements système et piste d'audit

### Métriques de Résumé
page-events-metric-total = Événements Totaux
page-events-metric-total-help = Derniers { $days } jours
page-events-metric-daily-avg = Événements Quotidiens
page-events-metric-types = Types d'Événement
page-events-metric-entities = Entités Suivies

### Filtres de la Barre Latérale
page-events-filter-title = 🔍 Filtres d'Événements
page-events-filter-period = Période (jours)
page-events-filter-period-help = Nombre de jours à analyser
page-events-filter-type = Type d'Événement
page-events-filter-type-all = Tous
page-events-filter-type-help = Filtrer par type d'événement
page-events-filter-entity-type = Type d'Entité
page-events-filter-entity-type-help = Filtrer par type d'entité
page-events-filter-search = 🔎 Rechercher
page-events-filter-search-placeholder = Rechercher dans les événements...
page-events-filter-search-help = Rechercher par type d'événement ou entité

### Onglets
page-events-tab-recent = 🕐 Récents
page-events-tab-filtered = 🔍 Filtrés
page-events-tab-stats = 📊 Statistiques
page-events-tab-timeline = ⏰ Chronologie

### Onglet Récents
page-events-recent-title = 🕐 Événements Récents
page-events-table-timestamp = Horodatage
page-events-table-type = Type d'Événement
page-events-table-entity = Entité
page-events-table-description = Description
page-events-table-user = Utilisateur
page-events-table-user-system = Système
page-events-details-button = 👁️ Afficher les Détails
page-events-details-help = Afficher les détails complets de l'événement
page-events-details-title = Événement { $num } : { $desc }
page-events-empty = 📭 Aucun événement trouvé dans la base de données

### Onglet Filtrés
page-events-filtered-title = 🔍 Événements Filtrés
page-events-filtered-found = ✅ Trouvé { $count } événements
page-events-export-button = 📤 Exporter CSV
page-events-export-help = Exporter les résultats filtrés au format CSV
page-events-export-download = Télécharger CSV
page-events-filtered-empty = 🔍 Aucun événement trouvé avec les filtres sélectionnés

### Onglet Statistiques
page-events-stats-title = 📊 Statistiques d'Événements
page-events-stats-by-type = 📈 Événements par Type
page-events-stats-type-col = Type d'Événement
page-events-stats-count-col = Nombre
page-events-stats-by-entity = 🏢 Événements par Entité
page-events-stats-entity-col = Type d'Entité
page-events-stats-daily = 📅 Activité Quotidienne (7 Derniers Jours)

### Onglet Chronologie
page-events-timeline-title = ⏰ Chronologie d'Entité
page-events-timeline-entity-type = Type d'Entité
page-events-timeline-entity-type-help = Sélectionner le type d'entité
page-events-timeline-entity-id = ID d'Entité
page-events-timeline-entity-id-placeholder = ex. : INV-001, CLI-001
page-events-timeline-entity-id-help = Entrez l'ID de l'entité à suivre
page-events-timeline-found = ✅ Trouvé { $count } événements pour { $type } { $id }
page-events-timeline-event-time = 🕐 **{ $time }**
page-events-timeline-event-type = 📋 { $type }
page-events-timeline-event-details = 📄 Détails
page-events-timeline-empty = 📭 Aucun événement trouvé pour { $type } { $id }
page-events-timeline-info = 💡 Sélectionnez un type d'entité et entrez un ID pour voir la chronologie

page-events-footer =
    📋 <strong>Système d'Événements :</strong> Piste d'audit complète pour la conformité et le débogage •
    🔍 <strong>Recherche :</strong> Filtrer par type, entité et période •
    📊 <strong>Analyses :</strong> Statistiques d'activité et chronologie d'entité

## ============================================================================
## PAGE SANTÉ (12_🏥_Health.py)
## ============================================================================

page-health-page-title = Santé du Système - OpenFatture
page-health-title = 🏥 Tableau de Bord de Santé du Système
page-health-subtitle = Surveillance et diagnostics en temps réel

### Métriques d'Utilisation
page-health-usage-title = 📊 Métriques d'Utilisation
page-health-metric-visits = Visites Totales de Pages
page-health-metric-unique = Pages Uniques
page-health-metric-session = Début de Session

### Statistiques de Cache
page-health-cache-title = 💾 Statistiques de Cache
page-health-cache-cleanup = 🧹 Nettoyé { $count } entrées de cache expirées
page-health-metric-entries = Entrées de Cache Totales
page-health-metric-functions = Fonctions en Cache
page-health-clear-all = 🗑️ Vider Tous les Caches
page-health-clear-success = ✅ Tous les caches ont été vidés !
page-health-cache-breakdown = Répartition du Cache par Fonction
page-health-table-function = Fonction
page-health-table-entries = Entrées
page-health-cache-management = Gestion Sélective du Cache
page-health-clear-invoices = 🧾 Vider Caches des Factures
page-health-clear-clients = 👥 Vider Caches des Clients
page-health-clear-payments = 💰 Vider Caches des Paiements
page-health-cleared-category = ✅ Vidé { $count } caches de { $category }

### Visites de Pages
page-health-visits-breakdown = Répartition des Visites de Pages
page-health-table-page = Page
page-health-table-visits = Visites

### API Santé
page-health-api-title = 🔌 Point de Terminaison API Santé
page-health-api-info =
    Pour la surveillance externe, utilisez la fonction `quick_health_check()` :

    ```python
    from openfatture.web.utils.health import quick_health_check

    health = quick_health_check()
    # Renvoie : {"status": "healthy|degraded|unhealthy", "checks": [...]}
    ```

    Cela peut être exposé via un point de terminaison API pour les outils de surveillance tels que :
    - Prometheus
    - Datadog
    - New Relic
    - Tableaux de bord de surveillance personnalisés

page-health-api-sample = 🔍 Afficher l'Exemple JSON de Vérification de Santé
page-health-best-practice =
    **💡 Meilleure Pratique :** Surveillez ce tableau de bord régulièrement pour détecter les problèmes tôt.
    Configurez des alertes pour les statuts "unhealthy" ou "degraded" en production.
