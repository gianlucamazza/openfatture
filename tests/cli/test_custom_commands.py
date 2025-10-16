"""Tests for custom slash commands system."""

import tempfile
from pathlib import Path

import pytest
import yaml

from openfatture.cli.commands.custom_commands import (
    CustomCommand,
    CustomCommandRegistry,
    get_command_registry,
)


class TestCustomCommand:
    """Tests for CustomCommand dataclass."""

    def test_basic_command_creation(self):
        """Test basic command creation with required fields."""
        cmd = CustomCommand(
            name="test",
            description="Test command",
            template="Hello {{ arg1 }}!",
        )

        assert cmd.name == "test"
        assert cmd.description == "Test command"
        assert cmd.category == "general"  # default
        assert cmd.aliases == []
        assert cmd.examples == []

    def test_command_with_all_fields(self):
        """Test command creation with all optional fields."""
        cmd = CustomCommand(
            name="full-test",
            description="Full test command",
            template="Template",
            category="testing",
            aliases=["ft", "fulltest"],
            examples=["/full-test arg1"],
            author="Test Author",
            version="1.0",
        )

        assert cmd.category == "testing"
        assert "ft" in cmd.aliases
        assert len(cmd.examples) == 1
        assert cmd.author == "Test Author"
        assert cmd.version == "1.0"

    def test_invalid_command_name(self):
        """Test that invalid command names raise ValueError."""
        with pytest.raises(ValueError, match="Invalid command name"):
            CustomCommand(
                name="test command",  # spaces not allowed
                description="Test",
                template="Test",
            )

        with pytest.raises(ValueError, match="Invalid command name"):
            CustomCommand(
                name="test/command",  # slashes not allowed
                description="Test",
                template="Test",
            )

    def test_invalid_template_syntax(self):
        """Test that invalid Jinja2 syntax raises ValueError."""
        with pytest.raises(ValueError, match="Invalid Jinja2 template syntax"):
            CustomCommand(
                name="test",
                description="Test",
                template="{{ unclosed",  # invalid Jinja2
            )

    def test_expand_with_positional_args(self):
        """Test template expansion with positional arguments."""
        cmd = CustomCommand(
            name="greet",
            description="Greet someone",
            template="Hello {{ arg1 }}! You are {{ arg2 }} years old.",
        )

        result = cmd.expand(args=["Alice", "25"])

        assert "Hello Alice!" in result
        assert "25 years old" in result

    def test_expand_with_default_value(self):
        """Test template expansion with default values."""
        cmd = CustomCommand(
            name="greet",
            description="Greet someone",
            template="Hello {{ arg1 | default('World') }}!",
        )

        # With argument
        result1 = cmd.expand(args=["Alice"])
        assert "Hello Alice!" in result1

        # Without argument (should use default)
        result2 = cmd.expand(args=[])
        assert "Hello World!" in result2

    def test_expand_with_kwargs(self):
        """Test template expansion with named arguments."""
        cmd = CustomCommand(
            name="invoice",
            description="Create invoice",
            template="Client: {{ client }}, Amount: {{ amount }}€",
        )

        result = cmd.expand(kwargs={"client": "Acme Corp", "amount": "1000"})

        assert "Client: Acme Corp" in result
        assert "Amount: 1000€" in result

    def test_expand_with_filters(self):
        """Test template expansion with Jinja2 filters."""
        cmd = CustomCommand(
            name="format",
            description="Format text",
            template="Upper: {{ arg1 | upper }}, Lower: {{ arg2 | lower }}",
        )

        result = cmd.expand(args=["hello", "WORLD"])

        assert "Upper: HELLO" in result
        assert "Lower: world" in result

    def test_expand_with_conditional(self):
        """Test template expansion with conditional logic."""
        cmd = CustomCommand(
            name="conditional",
            description="Conditional test",
            template="Name: {{ arg1 }}\n{% if arg2 %}Age: {{ arg2 }}{% endif %}",
        )

        # With second arg
        result1 = cmd.expand(args=["Alice", "25"])
        assert "Age: 25" in result1

        # Without second arg
        result2 = cmd.expand(args=["Bob"])
        assert "Age:" not in result2

    def test_expand_with_loop(self):
        """Test template expansion with loop."""
        cmd = CustomCommand(
            name="list",
            description="List items",
            template="Items:\n{% for item in args %}- {{ item }}\n{% endfor %}",
        )

        result = cmd.expand(args=["Apple", "Banana", "Cherry"])

        assert "- Apple" in result
        assert "- Banana" in result
        assert "- Cherry" in result


class TestCustomCommandRegistry:
    """Tests for CustomCommandRegistry."""

    @pytest.fixture
    def temp_commands_dir(self):
        """Create a temporary directory for test commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_command_file(self, temp_commands_dir):
        """Create a sample command YAML file."""
        command_data = {
            "name": "test-cmd",
            "description": "Test command",
            "template": "Hello {{ arg1 }}!",
            "category": "testing",
            "aliases": ["tc"],
        }

        file_path = temp_commands_dir / "test-cmd.yaml"
        with open(file_path, "w") as f:
            yaml.dump(command_data, f)

        return file_path

    def test_registry_initialization(self, temp_commands_dir):
        """Test registry initialization."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)

        assert registry.commands_dir == temp_commands_dir
        assert isinstance(registry._commands, dict)
        assert isinstance(registry._aliases, dict)

    def test_registry_creates_directory(self):
        """Test that registry creates commands directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent = Path(tmpdir) / "new_dir" / "commands"
            registry = CustomCommandRegistry(commands_dir=non_existent)

            assert non_existent.exists()
            assert non_existent.is_dir()

    def test_load_command_from_file(self, temp_commands_dir, sample_command_file):
        """Test loading command from YAML file."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)

        assert "test-cmd" in registry._commands
        cmd = registry._commands["test-cmd"]
        assert cmd.description == "Test command"
        assert cmd.category == "testing"

    def test_load_command_with_alias(self, temp_commands_dir, sample_command_file):
        """Test that aliases are registered correctly."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)

        assert "tc" in registry._aliases
        assert registry._aliases["tc"] == "test-cmd"

    def test_execute_command_by_name(self, temp_commands_dir, sample_command_file):
        """Test executing command by name."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)

        result = registry.execute("test-cmd", args=["World"])

        assert "Hello World!" in result

    def test_execute_command_by_alias(self, temp_commands_dir, sample_command_file):
        """Test executing command by alias."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)

        result = registry.execute("tc", args=["World"])

        assert "Hello World!" in result

    def test_execute_nonexistent_command(self, temp_commands_dir):
        """Test that executing nonexistent command raises ValueError."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)

        with pytest.raises(ValueError, match="Command 'nonexistent' not found"):
            registry.execute("nonexistent")

    def test_get_command(self, temp_commands_dir, sample_command_file):
        """Test getting command by name."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)

        cmd = registry.get_command("test-cmd")

        assert cmd is not None
        assert cmd.name == "test-cmd"

    def test_get_command_by_alias(self, temp_commands_dir, sample_command_file):
        """Test getting command by alias."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)

        cmd = registry.get_command("tc")

        assert cmd is not None
        assert cmd.name == "test-cmd"

    def test_get_nonexistent_command(self, temp_commands_dir):
        """Test getting nonexistent command returns None."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)

        cmd = registry.get_command("nonexistent")

        assert cmd is None

    def test_has_command(self, temp_commands_dir, sample_command_file):
        """Test checking if command exists."""
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)

        assert registry.has_command("test-cmd")
        assert registry.has_command("tc")  # alias
        assert not registry.has_command("nonexistent")

    def test_list_commands(self, temp_commands_dir):
        """Test listing all commands."""
        # Create multiple commands
        for i in range(3):
            command_data = {
                "name": f"cmd{i}",
                "description": f"Command {i}",
                "template": f"Test {i}",
                "category": "testing" if i % 2 == 0 else "other",
            }
            file_path = temp_commands_dir / f"cmd{i}.yaml"
            with open(file_path, "w") as f:
                yaml.dump(command_data, f)

        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)
        commands = registry.list_commands()

        assert len(commands) == 3
        # Should be sorted by category, then name
        assert commands[0].category == "other"
        assert commands[1].category == "testing"
        assert commands[2].category == "testing"

    def test_list_commands_by_category(self, temp_commands_dir):
        """Test listing commands filtered by category."""
        # Create commands in different categories
        for i, category in enumerate(["cat1", "cat2", "cat1"]):
            command_data = {
                "name": f"cmd{i}",
                "description": f"Command {i}",
                "template": f"Test {i}",
                "category": category,
            }
            file_path = temp_commands_dir / f"cmd{i}.yaml"
            with open(file_path, "w") as f:
                yaml.dump(command_data, f)

        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)
        cat1_commands = registry.list_commands(category="cat1")

        assert len(cat1_commands) == 2
        assert all(cmd.category == "cat1" for cmd in cat1_commands)

    def test_get_categories(self, temp_commands_dir):
        """Test getting all command categories."""
        # Create commands in different categories
        categories = ["invoicing", "tax", "clients", "invoicing"]
        for i, category in enumerate(categories):
            command_data = {
                "name": f"cmd{i}",
                "description": f"Command {i}",
                "template": f"Test {i}",
                "category": category,
            }
            file_path = temp_commands_dir / f"cmd{i}.yaml"
            with open(file_path, "w") as f:
                yaml.dump(command_data, f)

        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)
        categories_list = registry.get_categories()

        assert len(categories_list) == 3  # unique categories
        assert set(categories_list) == {"clients", "invoicing", "tax"}  # sorted

    def test_reload_commands(self, temp_commands_dir):
        """Test reloading commands from disk."""
        # Create initial command
        command_data = {
            "name": "initial",
            "description": "Initial command",
            "template": "Initial",
        }
        file_path = temp_commands_dir / "initial.yaml"
        with open(file_path, "w") as f:
            yaml.dump(command_data, f)

        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)
        assert len(registry.list_commands()) == 1

        # Add new command file
        new_command_data = {
            "name": "new",
            "description": "New command",
            "template": "New",
        }
        new_file_path = temp_commands_dir / "new.yaml"
        with open(new_file_path, "w") as f:
            yaml.dump(new_command_data, f)

        # Reload
        registry.reload()

        assert len(registry.list_commands()) == 2
        assert registry.has_command("new")

    def test_duplicate_command_name(self, temp_commands_dir):
        """Test that duplicate command names are skipped."""
        # Create two files with same command name
        command_data = {
            "name": "duplicate",
            "description": "First",
            "template": "First",
        }

        file1 = temp_commands_dir / "file1.yaml"
        file2 = temp_commands_dir / "file2.yaml"

        with open(file1, "w") as f:
            yaml.dump(command_data, f)
        with open(file2, "w") as f:
            yaml.dump(command_data, f)

        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)

        # Only one should be loaded
        assert len(registry.list_commands()) == 1

    def test_invalid_yaml_file(self, temp_commands_dir):
        """Test that invalid YAML files are skipped."""
        invalid_file = temp_commands_dir / "invalid.yaml"
        with open(invalid_file, "w") as f:
            f.write("{ invalid yaml }")

        # Should not raise, just skip invalid file
        registry = CustomCommandRegistry(commands_dir=temp_commands_dir)

        assert len(registry.list_commands()) == 0


def test_get_command_registry_singleton():
    """Test that get_command_registry returns singleton instance."""
    registry1 = get_command_registry()
    registry2 = get_command_registry()

    assert registry1 is registry2  # Same instance
