# Historical: Lightning Network module (removed)

The experimental Lightning Network stack lived under `openfatture/lightning/`
and was never product-complete: LND gRPC calls raised `NotImplementedError`
without generated stubs; mock paths were fail-closed by default.

**Removed from main** when the product surface was narrowed to Italian
electronic invoicing, bank payments, and the agentic assistant.

These documents are **historical only** — not current setup guides.

| Document | Former path |
|----------|-------------|
| [LIGHTNING_NETWORK.md](LIGHTNING_NETWORK.md) | `docs/LIGHTNING_NETWORK.md` |
| [LIGHTNING_INTEGRATION.md](LIGHTNING_INTEGRATION.md) | `docs/LIGHTNING_INTEGRATION.md` |
| [LIGHTNING_COMPLIANCE_ITALIA.md](LIGHTNING_COMPLIANCE_ITALIA.md) | `docs/LIGHTNING_COMPLIANCE_ITALIA.md` |
| [LIGHTNING_TROUBLESHOOTING.md](LIGHTNING_TROUBLESHOOTING.md) | `docs/LIGHTNING_TROUBLESHOOTING.md` |

To recover the last code tree: search git history for
`openfatture/lightning/` before the removal commit.
