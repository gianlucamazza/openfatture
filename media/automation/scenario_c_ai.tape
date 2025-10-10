# Scenario C · AI Assistant with Ollama
# Automated demo showing local AI integration

Output media/output/scenario_c_ai.mp4
Set Shell "zsh"
Set FontFamily "JetBrains Mono"
Set FontSize 22
Set Width 1920
Set Height 1080
Set Theme "Dracula"
Set CursorBlink true
Set TypingSpeed 100ms

Sleep 1s
Type "clear"
Enter
Sleep 500ms

# Step 1: Header
Type "printf '\e[1;36mScenario C: AI Assistant (Ollama Local)\e[0m\\n'"
Enter
Sleep 1.2s

# Step 2: Show AI provider config
Type "printf '\e[1;33m→ AI Provider: Ollama (llama3.2) - 100%% Local\e[0m\\n'"
Enter
Sleep 1s

# Step 3: AI chat command - generate description
Type "uv run openfatture ai chat 'Crea una descrizione professionale per una consulenza GDPR di 8 ore'"
Enter
Sleep 5s
# Ollama inference takes longer - wait for response

# Step 4: AI suggest VAT
Type "printf '\\n\e[1;32m→ Suggerimento aliquota IVA...\e[0m\\n'"
Enter
Sleep 800ms
Type "uv run openfatture ai suggest-vat 'Consulenza GDPR' --importo 1500 --categoria consulenza"
Enter
Sleep 3s

# Step 5: Show AI available commands
Type "printf '\\n\e[1;36m→ Altri comandi AI disponibili:\e[0m\\n'"
Enter
Sleep 800ms
Type "uv run openfatture ai --help"
Enter
Sleep 2s

# Step 6: Privacy reminder
Type "printf '\\n\e[1;32m✓ Privacy-First: tutti i dati restano locali (no cloud API)\e[0m\\n'"
Enter
Sleep 1.5s

# End frame
Sleep 1.5s
