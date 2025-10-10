# Scenario E · PEC & SDI Notifications
# Automated demo showing PEC config and SDI integration

Output media/output/scenario_e_pec.mp4
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
Type "printf '\e[1;36mScenario E: Invio PEC & Gestione SDI\e[0m\\n'"
Enter
Sleep 1.2s

# Step 2: PEC help
Type "uv run openfatture pec --help"
Enter
Sleep 2s

# Step 3: Show invoice ready for sending
Type "printf '\\n\e[1;33m→ Fattura demo pronta per invio:\e[0m\\n'"
Enter
Sleep 800ms
Type "uv run openfatture fattura show 1"
Enter
Sleep 2.5s

# Step 4: Simulate PEC send (won't actually send in demo)
Type "printf '\\n\e[1;32m→ Invio simulato al SDI via PEC:\e[0m\\n'"
Enter
Sleep 800ms
Type "printf 'openfatture fattura invia 1 --pec\\n'"
Enter
Sleep 1s
Type "printf '  ✓ XML generato: IT04567890123_00001.xml\\n'"
Enter
Sleep 500ms
Type "printf '  ✓ Invio PEC a: sdi01@pec.fatturapa.it\\n'"
Enter
Sleep 500ms
Type "printf '  ✓ ID trasmissione: 12345678\\n'"
Enter
Sleep 1.5s

# Step 5: Notifications help
Type "printf '\\n\e[1;36m→ Gestione notifiche SDI:\e[0m\\n'"
Enter
Sleep 800ms
Type "uv run openfatture notifiche --help"
Enter
Sleep 2s

# Step 6: Show notification files (if available)
Type "printf '\\n\e[1;33m→ Notifiche esempio disponibili:\e[0m\\n'"
Enter
Sleep 800ms
Type "ls -lh examples/sdi/ 2>/dev/null || echo 'Cartella examples/sdi non trovata (opzionale)'"
Enter
Sleep 1.5s

# Step 7: Final compliance message
Type "printf '\\n\e[1;32m✓ Conformità AgID e conservazione digitale garantita\e[0m\\n'"
Enter
Sleep 1.5s

# End frame
Sleep 1.5s
