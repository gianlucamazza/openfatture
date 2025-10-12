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
Type "printf '\e[1;36mScenario D: Batch Operations\e[0m\\n'"
Enter
Sleep 1.2s

# Step 2: Show batch help
Type "uv run openfatture batch --help"
Enter
Sleep 2s

# Step 3: List example batch files (if available)
Type "printf '\\n\e[1;33m→ Example CSV files:\e[0m\\n'"
Enter
Sleep 800ms
Type "ls -lh examples/batch/ 2>/dev/null || echo 'examples/batch folder not found (optional)'"
Enter
Sleep 1.5s

# Step 4: Show batch import dry-run simulation
Type "printf '\\n\e[1;32m→ Batch import simulation (dry-run):\e[0m\\n'"
Enter
Sleep 800ms
Type "printf 'openfatture batch import clients.csv --dry-run\\n'"
Enter
Sleep 1s
Type "printf '  ✓ Validation: 5 customers\\n  ✓ 0 errors found\\n  ✓ Ready for final import\\n'"
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
Type "printf '\\n\e[1;32m✓ Batch operations: scalable and automated\e[0m\\n'"
Enter
Sleep 1.5s

# End frame
Sleep 1.5s
