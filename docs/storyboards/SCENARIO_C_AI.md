# Scenario C · AI Assistant (Storyboard)

**Version:** v2025.02.03
**Owner:** AI/ML Guild (lead: Elisa Moretti)
**Target duration:** 2'45" ± 10s

## Shot Sequence
| # | Length | Video | Audio/VO | Overlay/Notes |
|---|--------|-------|----------|---------------|
| 1 | 0:04 | Animated logo + title “AI Assistant with Ollama” | Intro SFX | Brand palette |
| 2 | 0:12 | Speaker on camera | “Let’s automate descriptions and VAT suggestions with the AI assistant” | CTA “Step 1/4” |
| 3 | 0:18 | Terminal: `ollama serve` / health check | “Start the local Ollama model for deterministic demos” | Show health check output |
| 4 | 0:20 | Terminal: `openfatture --interactive` | “Launch the interactive dashboard” | Highlight AI menu entry |
| 5 | 0:30 | TUI: AI chat session | “Generate a professional line item description” | Display prompt + AI response |
| 6 | 0:35 | Terminal: `openfatture ai suggest-vat ...` | “Ask for VAT treatment with legal references” | Show confidence + citation |
| 7 | 0:20 | Terminal: `openfatture ai rag status` | “Check the knowledge base status and sources” | Focus on document counts |
| 8 | 0:16 | Terminal: `openfatture ai rag search "reverse charge edilizia"` | “Run a semantic search for compliance audit” | Display snippet + citation |
| 9 | 0:10 | Summary slide | “Configure provider, index KB, use AI responsibly” | Include privacy reminder |
|10 | 0:10 | Outro | “Next scenario: batch automation” | Link to Scenario D |

## Production Notes
- **AI config:** Ollama (`llama3.2`) with deterministic outputs; fallback to Anthropic if local setup unavailable.
- **Dataset:** invoice + customer data for 2024/2025 to provide context.
- **RAG manifest:** ensure `openfatture ai rag index` was executed before recording.
- **Terminal:** ensure `AI_MOCK_MODE=1` if using mocked responses.

## Required Assets
- `.env.demo` configured for Ollama.
- Script `scripts/check_ollama.sh` for health checks.
- Pre-generated screenshots of `rag status` and `rag search` results.
- Overlay for citation format `[1] DPR 633/72 art...`.

## Pre-Shoot Checklist
- [ ] `ollama serve` running locally with `llama3.2`.
- [ ] `openfatture ai rag index` executed successfully.
- [ ] Test `ai describe` and `ai suggest-vat` for consistent outputs.
- [ ] Validate `rag search` returns snippets with citations.
- [ ] Prepare TUI capture layout (Rich theme, full width).

## Post-Production
- Include lower-thirds describing AI commands and environment variables.
- Add callout reminding viewers about data-privacy and API keys.
- Export master + H.264 + vertical highlight (AI chat segment).
