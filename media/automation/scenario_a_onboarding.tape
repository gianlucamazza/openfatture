# Scenario A · Onboarding & Setup
# Autogenera video CLI con dataset demo

Output media/output/scenario_a_onboarding.mp4
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

# Step 1: headline intro
Type "printf '\e[1;36mOpenFatture Setup Demo (Scenario A)\e[0m\\n'"
Enter
Sleep 1.2s

# Step 2: mostra stato repo e reset demo
Type "git rev-parse --abbrev-ref HEAD"
Enter
Sleep 800ms
Type "./scripts/reset_demo.sh"
Enter
Sleep 8s
# Wait for demo reset to complete

# Step 3: mostra .env demo
Type "cp .env.demo .env"
Enter
Sleep 600ms
Type "sed -n '1,18p' .env"
Enter
Sleep 2s

# Step 4: verifica configurazione
Type "uv run openfatture config show"
Enter
Sleep 2.5s

# Step 5: reminder proseguire
Type "printf '\\nProssimo passo: openfatture invoice create --interactive\\n'"
Enter
Sleep 1.5s

# End frame
Sleep 1.5s
