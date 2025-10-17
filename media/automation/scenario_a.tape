# Scenario A: Onboarding & Setup
# Generated from template - DO NOT EDIT MANUALLY
# Use: python media/automation/templates/base_template.py generate --scenario A

# VHS Settings
Set Shell "zsh"
Set FontFamily "JetBrains Mono"
Set FontSize 22
Set Width 1920
Set Height 1080
Set Theme "Dracula"
Set CursorBlink true
Set TypingSpeed 100ms"

Output media/output/scenario_a_openfatture_setup_demo_a.mp4

Sleep 1s

# Setup commands
Type "clear"
Enter
Sleep 500ms

Type "printf '\e[1;36mOpenFatture Setup Demo (Scenario A)\e[0m\\n'"
Enter
Sleep 1200ms

Type "git rev-parse --abbrev-ref HEAD"
Enter
Sleep 800ms

Type "./scripts/reset_demo.sh"
Enter
Sleep 8000ms

Type "cp .env.demo .env"
Enter
Sleep 800ms

# Show configuration file
Type "sed -n '1,18p' .env"
Enter
Sleep 1500ms

# Verify OpenFatture configuration
Type "uv run openfatture config show"
Enter
Sleep 3000ms

# Show version info
Type "uv run openfatture --version"
Enter
Sleep 800ms

# Completion message
Type "printf '\\n\e[1;32m✓ Scenario a completato!\e[0m\\n'"
Enter
Sleep 1200ms

Type "printf '\e[1;34mProssimo: Esegui \\'make media-scenarioa\\' per continuare\e[0m\\n'"
Enter
Sleep 1200ms

Sleep 500ms
