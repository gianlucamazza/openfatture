"""OpenFatture Web UI - Modern Navigation Pattern (Best Practices 2025).

This is an EXAMPLE implementation showing how to use st.Page + st.navigation
instead of the pages/ directory pattern.

To use this instead of app.py:
    streamlit run openfatture/web/app_modern.py

Benefits over pages/ directory:
1. Dynamic navigation (show/hide pages based on config)
2. Grouped navigation for better UX
3. Shared layout (sidebar, footer) in one place
4. Programmatic navigation
5. More flexible and maintainable

Note: This is optional - the current pages/ directory pattern is still
valid and works well. This example shows the 2025 recommended approach.
"""

import streamlit as st

from openfatture.utils.config import get_settings
from openfatture.utils.logging import configure_dynamic_logging
from openfatture.web.navigation import (
    render_shared_footer,
    render_shared_sidebar,
    setup_navigation_with_conditions,
)
from openfatture.web.utils.state import init_state

# Page configuration MUST be first Streamlit command
st.set_page_config(
    page_title="OpenFatture - Fatturazione Elettronica",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/gianlucamazza/openfatture",
        "Report a bug": "https://github.com/gianlucamazza/openfatture/issues",
        "About": """
        # OpenFatture 🧾

        Open-source electronic invoicing for Italian freelancers.

        **Version:** 1.1.0
        **License:** MIT
        **Pattern:** st.Page + st.navigation (2025 Best Practice)
        """,
    },
)

# Initialize logging
settings = get_settings()
configure_dynamic_logging(settings.debug_config)


def main() -> None:
    """
    Main application entry point with modern navigation.

    Best Practice 2025:
    - Use st.navigation() for flexible page management
    - Render shared UI in the frame (this file)
    - Pages are self-contained modules
    - Dynamic navigation based on features/permissions
    """
    # Initialize app state
    init_state("initialized", True)
    init_state("navigation_pattern", "modern")

    # Render shared sidebar elements ABOVE navigation
    render_shared_sidebar()

    # Setup navigation (returns selected page)
    # This creates the navigation menu in sidebar
    page = setup_navigation_with_conditions()

    # Run the selected page
    # The page's code executes in the main content area
    page.run()

    # Render shared footer BELOW page content
    render_shared_footer()


if __name__ == "__main__":
    main()


# ============================================================================
# MIGRATION GUIDE: From pages/ directory to st.Page + st.navigation
# ============================================================================
#
# Current pattern (pages/ directory):
#   openfatture/web/
#   ├── app.py                     # Home page
#   └── pages/
#       ├── 1_📊_Dashboard.py      # Auto-discovered
#       ├── 2_🧾_Fatture.py
#       └── ...
#
# New pattern (st.Page + st.navigation):
#   openfatture/web/
#   ├── app_modern.py              # Frame with navigation
#   ├── navigation.py              # Navigation setup
#   └── pages/
#       ├── home.py                # Explicitly declared
#       ├── dashboard.py           # Explicitly declared
#       └── ...                    # No auto-discovery
#
# Steps to migrate:
#
# 1. Create navigation.py with page registry
# 2. Update app.py to use setup_navigation()
# 3. Remove numeric prefixes from page files (optional)
# 4. Test thoroughly
# 5. Deploy
#
# Benefits:
# - Group pages logically (Business, Finance, Settings)
# - Show/hide pages based on config (Lightning only if enabled)
# - Programmatic navigation (navigate_to("invoices"))
# - Shared sidebar/footer in one place
# - Better control over page order
#
# Considerations:
# - More code (navigation.py file)
# - Need to explicitly declare pages
# - No auto-discovery (pages/ directory feature)
# - But: More maintainable for large apps
#
# Verdict: Use st.navigation for apps with 7+ pages or dynamic features
# ============================================================================
