"""Template for testing new menu functions.

This template demonstrates best practices for testing interactive menu
components in OpenFatture. Use this as a starting point when adding
new menu functions or testing existing ones.

Key Principles:
1. Use Choice objects with explicit value parameters
2. Mock questionary.select to control menu behavior
3. Mock action handlers to prevent actual execution
4. Test both menu display and handler routing
5. Always test edge cases (None, back, cancel)

Example Usage:
--------------
Copy this template when adding a new menu, then:
1. Replace "example" with your menu name
2. Update action values to match your Choice values
3. Add tests for all menu options
4. Add integration tests for your specific workflow
"""

import pytest
from unittest.mock import MagicMock, patch
from questionary import Choice


# ============================================================================
# EXAMPLE: Testing a New Menu Function
# ============================================================================


def show_example_menu() -> str:
    """Example menu display function.

    This demonstrates the CORRECT way to create a menu with Choice objects.
    """
    import questionary
    from openfatture.cli.ui.styles import openfatture_style

    choices: list[str | Choice] = [
        Choice(title="➕ Create Item", value="action_create_item"),
        Choice(title="📋 List Items", value="action_list_items"),
        Choice(title="✏️  Edit Item", value="action_edit_item"),
        questionary.Separator(),
        Choice(title="← Back", value="action_back"),
    ]

    return questionary.select(
        "Example Menu",
        choices=choices,
        use_shortcuts=True,
        use_arrow_keys=True,
        style=openfatture_style,
        instruction="(Use number keys or arrows ↑↓, ENTER to confirm)",
    ).ask()


def handle_example_menu() -> None:
    """Example menu handler function.

    This demonstrates the CORRECT way to handle menu choices with exact matching.
    """
    while True:
        choice = show_example_menu()

        # CRITICAL: Use exact matching, not substring matching
        if choice == "action_back" or choice is None:
            break

        # Route to action handlers based on exact value match
        if choice == "action_create_item":
            action_create_item()
        elif choice == "action_list_items":
            action_list_items()
        elif choice == "action_edit_item":
            action_edit_item()


def action_create_item():
    """Placeholder action function."""
    pass


def action_list_items():
    """Placeholder action function."""
    pass


def action_edit_item():
    """Placeholder action function."""
    pass


# ============================================================================
# TEMPLATE: Unit Tests for Menu Display
# ============================================================================


class TestExampleMenuDisplay:
    """Test menu display function returns correct values."""

    def test_show_example_menu_returns_clean_value(self):
        """Test menu returns clean action value, not emoji-laden title.

        KEY POINT: The value should be a simple string like 'action_create_item',
        NOT the full title with emojis like '➕ Create Item'.
        """
        with patch("questionary.select") as mock_select:
            # Mock questionary to return a clean value
            mock_select.return_value.ask.return_value = "action_create_item"

            result = show_example_menu()

            # Assertions
            assert result == "action_create_item"
            assert isinstance(result, str)
            assert "➕" not in result  # No emoji in value
            assert "Create" not in result  # No title text in value

    def test_show_example_menu_back_option(self):
        """Test menu returns 'action_back' for back navigation."""
        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = "action_back"

            result = show_example_menu()

            assert result == "action_back"

    def test_show_example_menu_handles_cancel(self):
        """Test menu handles user cancel (Ctrl+C) returning None."""
        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = None

            result = show_example_menu()

            assert result is None


# ============================================================================
# TEMPLATE: Unit Tests for Menu Handler
# ============================================================================


class TestExampleMenuHandler:
    """Test menu handler routes to correct actions."""

    @pytest.fixture
    def mock_menu_select(self):
        """Fixture to mock show_example_menu."""
        with patch("__main__.show_example_menu") as mock:
            yield mock

    @pytest.fixture
    def mock_actions(self):
        """Fixture to mock all action functions."""
        with patch.multiple(
            "__main__",
            action_create_item=MagicMock(),
            action_list_items=MagicMock(),
            action_edit_item=MagicMock(),
        ) as mocks:
            yield mocks

    def test_routes_to_create_action(self, mock_menu_select, mock_actions):
        """Test handler calls create action when selected."""
        mock_menu_select.side_effect = ["action_create_item", "action_back"]

        handle_example_menu()

        mock_actions["action_create_item"].assert_called_once()

    def test_routes_to_list_action(self, mock_menu_select, mock_actions):
        """Test handler calls list action when selected."""
        mock_menu_select.side_effect = ["action_list_items", "action_back"]

        handle_example_menu()

        mock_actions["action_list_items"].assert_called_once()

    def test_routes_to_edit_action(self, mock_menu_select, mock_actions):
        """Test handler calls edit action when selected."""
        mock_menu_select.side_effect = ["action_edit_item", "action_back"]

        handle_example_menu()

        mock_actions["action_edit_item"].assert_called_once()

    def test_exits_on_back(self, mock_menu_select, mock_actions):
        """Test handler exits on action_back without calling actions."""
        mock_menu_select.return_value = "action_back"

        handle_example_menu()

        # No actions should be called
        for action in mock_actions.values():
            action.assert_not_called()

    def test_exits_on_none(self, mock_menu_select, mock_actions):
        """Test handler exits gracefully when user cancels (None)."""
        mock_menu_select.return_value = None

        handle_example_menu()

        # No actions should be called
        for action in mock_actions.values():
            action.assert_not_called()

    def test_handles_multiple_actions_in_loop(self, mock_menu_select, mock_actions):
        """Test handler can execute multiple actions before exiting."""
        mock_menu_select.side_effect = [
            "action_create_item",
            "action_list_items",
            "action_edit_item",
            "action_back",
        ]

        handle_example_menu()

        mock_actions["action_create_item"].assert_called_once()
        mock_actions["action_list_items"].assert_called_once()
        mock_actions["action_edit_item"].assert_called_once()


# ============================================================================
# TEMPLATE: Integration Tests
# ============================================================================


class TestExampleMenuIntegration:
    """Test complete user workflows through the menu."""

    @pytest.fixture
    def mock_menu_select(self):
        """Fixture to mock show_example_menu."""
        with patch("__main__.show_example_menu") as mock:
            yield mock

    @pytest.fixture
    def mock_actions(self):
        """Fixture to mock all action functions."""
        with patch.multiple(
            "__main__",
            action_create_item=MagicMock(),
            action_list_items=MagicMock(),
            action_edit_item=MagicMock(),
        ) as mocks:
            yield mocks

    def test_create_then_list_workflow(self, mock_menu_select, mock_actions):
        """Test user creates an item then lists all items."""
        mock_menu_select.side_effect = [
            "action_create_item",
            "action_list_items",
            "action_back",
        ]

        handle_example_menu()

        # Verify actions called in order
        assert mock_actions["action_create_item"].call_count == 1
        assert mock_actions["action_list_items"].call_count == 1

    def test_rapid_back_navigation(self, mock_menu_select, mock_actions):
        """Test user immediately hits back."""
        mock_menu_select.return_value = "action_back"

        handle_example_menu()

        # Should complete without calling any actions
        for action in mock_actions.values():
            action.assert_not_called()


# ============================================================================
# TEMPLATE: Edge Case Tests
# ============================================================================


class TestExampleMenuEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def mock_menu_select(self):
        """Fixture to mock show_example_menu."""
        with patch("__main__.show_example_menu") as mock:
            yield mock

    def test_handles_unknown_choice(self, mock_menu_select):
        """Test handler handles unknown choice gracefully."""
        # This shouldn't happen with Choice objects, but test defensive code
        mock_menu_select.side_effect = ["unknown_action", "action_back"]

        # Should complete without crashing
        handle_example_menu()

    def test_handles_keyboard_interrupt(self, mock_menu_select):
        """Test menu handles Ctrl+C gracefully."""
        mock_menu_select.side_effect = KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            handle_example_menu()


# ============================================================================
# TEMPLATE: Regression Tests
# ============================================================================


class TestExampleMenuRegression:
    """Regression tests to prevent bugs from returning.

    Add tests here when bugs are fixed to ensure they don't come back.
    """

    def test_choice_value_is_string_not_object(self):
        """Regression test: Ensure Choice.value returns string, not OptionInfo.

        This prevents the bug where questionary returned OptionInfo objects
        instead of clean string values.
        """
        with patch("questionary.select") as mock_select:
            mock_select.return_value.ask.return_value = "action_create_item"

            result = show_example_menu()

            assert isinstance(result, str)
            assert result == "action_create_item"

    def test_exact_matching_not_substring(self):
        """Regression test: Ensure exact matching, not substring matching.

        Old buggy code used 'if \"Create\" in choice', which was fragile.
        New code uses 'if choice == \"action_create_item\"', which is exact.
        """
        with patch("__main__.show_example_menu") as mock_menu:
            with patch.multiple(
                "__main__",
                action_create_item=MagicMock(),
                action_list_items=MagicMock(),
            ) as mocks:
                # Exact match should work
                mock_menu.side_effect = ["action_create_item", "action_back"]
                handle_example_menu()
                mocks["action_create_item"].assert_called_once()

                # Substring match should NOT work
                mocks["action_create_item"].reset_mock()
                mock_menu.side_effect = ["create_something_else", "action_back"]
                handle_example_menu()
                mocks["action_create_item"].assert_not_called()


# ============================================================================
# BEST PRACTICES SUMMARY
# ============================================================================

"""
BEST PRACTICES FOR MENU TESTING:

1. **Always Use Choice Objects with Explicit Values**
   ✅ Choice(title="➕ Create", value="action_create")
   ❌ "➕ Create" (plain string)

2. **Use Exact Matching in Handlers**
   ✅ if choice == "action_create":
   ❌ if "Create" in choice:

3. **Mock questionary.select for Display Tests**
   mock_select.return_value.ask.return_value = "action_value"

4. **Mock Action Handlers for Handler Tests**
   with patch.multiple("module", action_create=MagicMock(), ...):

5. **Always Test Edge Cases**
   - User cancels (None)
   - User goes back (action_back)
   - Multiple actions in loop
   - Unknown choices (defensive code)

6. **Write Integration Tests for Workflows**
   - Test complete user journeys
   - Test common navigation patterns
   - Verify actions called in correct order

7. **Write Regression Tests for Fixed Bugs**
   - Document what bug was fixed
   - Test the fix still works
   - Prevent the bug from returning

8. **Use Descriptive Test Names**
   ✅ test_routes_to_create_action
   ✅ test_exits_on_none
   ❌ test_menu_1
   ❌ test_works

9. **Use Fixtures for Common Setup**
   - @pytest.fixture for mock_menu_select
   - @pytest.fixture for mock_actions
   - Reuse across test classes

10. **Target ≥95% Coverage**
    - Test all menu options
    - Test all handler branches
    - Test all edge cases
    - Run: pytest --cov=module --cov-report=term-missing
"""
