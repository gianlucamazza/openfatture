# Glossary

> Key Italian finance and compliance terms used across OpenFatture. Handy for international teammates interpreting SDI/PEC workflows.

- **Bollo virtuale** — Fixed €2 stamp duty applied to invoices without VAT (importo > €77.47); encoded in the FatturaPA `DatiBollo` block.
- **Cedente/Prestatore** — Supplier issuing the invoice; their master data populates the “Company Data” section of configuration files.
- **Cessionario/Committente** — Customer receiving the invoice; required in the FatturaPA header and influences SDI delivery routing.
- **Codice Destinatario** — Seven-character channel code assigned by SDI to route electronic invoices when PEC delivery is not used.
- **Codice Fiscale** — Italian tax code (16 characters for individuals) required alongside the VAT number for FatturaPA compliance.
- **FatturaPA** — Official Italian electronic invoice schema (XML v1.9) mandated by the Agenzia delle Entrate; every invoice must comply before SDI submission.
- **Partita IVA** — Italian VAT number (11 digits) uniquely identifying companies and freelancers in SDI transactions.
- **PEC (Posta Elettronica Certificata)** — Certified email channel with legal value used to submit invoices to SDI and receive notifications.
- **Regime fiscale (RFxx)** — Two-letter codes (e.g., RF19 = forfait regime) embedded in FatturaPA to disclose the supplier’s VAT regime to SDI.
- **Reverse charge** — VAT mechanism (Art. 17 DPR 633/72) where the customer, not the supplier, accounts for the tax; common in construction and scrap.
- **Ritenuta d'acconto** — Withholding tax on professional services that reduces the payable amount; recorded in FatturaPA `DatiRitenuta`.
- **SDI (Sistema di Interscambio)** — Government hub that receives FatturaPA files, validates them, and forwards them to the recipient.
- **Split payment** — Scissione dei pagamenti (Art. 17-ter DPR 633/72) where public administrations pay the supplier net of VAT and remit VAT directly to the treasury.
- **CIG (Codice Identificativo Gara)** — Tender identification code required on invoices tied to Italian public procurement projects.
- **CUP (Codice Unico di Progetto)** — Project code for public works; necessary when invoicing government-related initiatives.
