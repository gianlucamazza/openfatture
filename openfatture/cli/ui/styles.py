"""Custom styles for interactive UI."""

from questionary import Style

# OpenFatture custom style matching brand colors
openfatture_style = Style(
    [
        ("qmark", "fg:#1976D2 bold"),  # Question mark - Primary blue
        ("question", "bold"),  # Question text
        ("answer", "fg:#1976D2 bold"),  # User's answer
        ("pointer", "fg:#1976D2 bold"),  # Selection pointer
        ("highlighted", "fg:#1976D2 bold"),  # Highlighted menu item
        ("selected", "fg:#00C853 bold"),  # Selected item (green)
        ("separator", "fg:#666666"),  # Menu separators
        ("instruction", "fg:#666666 italic"),  # Instructions
        ("text", ""),  # Normal text
        ("disabled", "fg:#666666 italic"),  # Disabled items
        # Validation states
        ("validation-toolbar", "bg:#FF5252 fg:#ffffff bold"),  # Error messages
    ]
)

# Alternative minimal style (for users who prefer less color)
minimal_style = Style(
    [
        ("qmark", "bold"),
        ("question", "bold"),
        ("answer", "bold"),
        ("pointer", "bold"),
        ("highlighted", "underline"),
        ("selected", "bold"),
    ]
)
