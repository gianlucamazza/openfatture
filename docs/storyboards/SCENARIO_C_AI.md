# Scenario C · AI Assistant & Automazioni (Storyboard)

**Versione:** v2025.02.03
**Owner:** AI/ML Guild (lead: Elisa Moretti)
**Durata target:** 2'45" ± 10s

## Sequenza Shot
| # | Durata | Video | Audio/VO | Overlay/Note |
|---|--------|-------|----------|--------------|
| 1 | 0:04 | Logo animato + titolo "AI Assistant" | SFX intro breve | Badge "Powered by Ollama" |
| 2 | 0:12 | Speaker on cam | "OpenFatture integra AI locale con Ollama - zero API costs" | Callout "100% Local" |
| 3 | 0:18 | Terminale: `openfatture ai chat "crea descrizione per consulenza GDPR"` | "Generazione automatica descrizioni servizi" | Streaming response animation |
| 4 | 0:25 | Output AI con descrizione dettagliata | "L'AI genera testo professionale e compliant" | Highlight keywords GDPR |
| 5 | 0:20 | Terminale: `openfatture ai suggest-vat "Consulenza GDPR" --importo 1500` | "Suggerimento aliquota IVA corretta" | Lower-third "IVA 22% - Servizi professionali" |
| 6 | 0:18 | Terminale: `openfatture --interactive` → menu "AI Assistant" | "Modalità interattiva con chat persistente" | UI menu navigation |
| 7 | 0:22 | Chat interattiva con multi-turn conversation | "Conversazione contestuale per task complessi" | Callout context-aware |
| 8 | 0:20 | Esempio: "riepiloga fatture gennaio 2025" | "Query intelligenti sul database" | Badge tool-calling |
| 9 | 0:16 | Terminale: visualizzazione stats via AI | "L'AI accede ai dati e risponde con insights" | Chart overlay (opzionale) |
| 10 | 0:10 | Outro + note privacy | "Ollama locale: dati mai condivisi con cloud" | CTA scenario D |

## Note Produzione
- **AI Provider**: **Ollama locale** con modello `llama3.2` (configurato in `.env.demo`)
- **Prompts**: usare esempi realistici (consulenza, fatturazione, IVA)
- **Response timing**: l'AI locale è più lenta - lasciare 3-4s per inference
- **Privacy highlight**: enfatizzare che tutto rimane locale (no external API calls)
- **Screen capture**: OBS, terminale + eventuale split-screen per mostrare Ollama running

## Asset Necessari
- Ollama running con modello llama3.2 pulled
- Database demo popolato con fatture gennaio 2025
- Script `check_ollama.sh` eseguito con successo
- Callout Figma "100% Local AI - No API Costs"
- Badge "Privacy-First" overlay

## Checklist Pre-shoot
- [ ] Verificare Ollama service running (`./scripts/check_ollama.sh llama3.2`)
- [ ] Testare comandi AI manualmente e cronometrare response time
- [ ] Preparare 3-4 prompt pre-testati con output consistenti
- [ ] Verificare chat interattiva funzionante
- [ ] Confermare env var `AI_PROVIDER=ollama` in `.env.demo`

## Post-produzione
- Marker timeline: Intro (0:00), Chat (0:16), Suggest-VAT (0:59), Interactive (1:37), Query (2:17), Outro (2:35)
- Sottotitoli IT + EN (per enfasi internazionale su privacy/local AI)
- Export: Master ProRes + H.264 1080p + GIF animato per social (highlight AI response streaming)
- Nota: aggiungere disclaimer "AI output is for demonstration - always verify with accountant"
