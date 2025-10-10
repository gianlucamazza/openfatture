# Scenario D · Batch Operations
# Automated demo showing batch import/export

Output media/output/scenario_d_batch.mp4
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
Type "printf '\e[1;36mScenario D: Operazioni Batch\e[0m\\n'"
Enter
Sleep 1.2s

# Step 2: Show batch help
Type "uv run openfatture batch --help"
Enter
Sleep 2s

# Step 3: List example batch files (if available)
Type "printf '\\n\e[1;33m→ File CSV esempio disponibili:\e[0m\\n'"
Enter
Sleep 800ms
Type "ls -lh examples/batch/ 2>/dev/null || echo 'Cartella examples/batch non trovata (opzionale)'"
Enter
Sleep 1.5s

# Step 4: Show batch import dry-run simulation
Type "printf '\\n\e[1;32m→ Simulazione import batch (dry-run):\e[0m\\n'"
Enter
Sleep 800ms
Type "printf 'openfatture batch import clients.csv --dry-run\\n'"
Enter
Sleep 1s
Type "printf '  ✓ Validazione: 5 clienti\\n  ✓ 0 errori trovati\\n  ✓ Pronto per import definitivo\\n'"
Enter
Sleep 2s

# Step 5: Stats command
Type "printf '\\n\e[1;36m→ Statistiche database:\e[0m\\n'"
Enter
Sleep 800ms
Type "uv run openfatture cliente list | wc -l"
Enter
Sleep 1s
Type "uv run openfatture fattura list | wc -l"
Enter
Sleep 1s

# Step 6: Final message
Type "printf '\\n\e[1;32m✓ Batch operations: scalabilità e automazione\e[0m\\n'"
Enter
Sleep 1.5s

# End frame
Sleep 1.5s
