# Scenario B · Creazione Fattura CLI
# Automated demo showing invoice creation workflow

Output media/output/scenario_b_invoice.mp4
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
Type "printf '\e[1;36mScenario B: Creazione Fattura CLI\e[0m\\n'"
Enter
Sleep 1.2s

# Step 2: List clients
Type "uv run openfatture cliente list"
Enter
Sleep 2s

# Step 3: List existing invoices
Type "uv run openfatture fattura list"
Enter
Sleep 2s

# Step 4: Show invoice details (existing demo invoice)
Type "uv run openfatture fattura show 1"
Enter
Sleep 2.5s

# Step 5: Generate XML
Type "printf '\\n\e[1;32m→ Generazione XML FatturaPA...\e[0m\\n'"
Enter
Sleep 800ms
Type "uv run openfatture fattura xml 1"
Enter
Sleep 2s

# Step 6: Generate PDF
Type "printf '\\n\e[1;32m→ Generazione PDF professionale...\e[0m\\n'"
Enter
Sleep 800ms
Type "uv run openfatture fattura pdf 1 --template professional"
Enter
Sleep 2.5s

# Step 7: Final message
Type "printf '\\n\e[1;36m✓ Fattura elettronica completa!\e[0m\\n'"
Enter
Sleep 1.5s

# End frame
Sleep 1.5s
