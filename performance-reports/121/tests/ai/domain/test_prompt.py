"""Unit tests for AI domain prompt management."""

import pytest
import yaml

from openfatture.ai.domain.prompt import PromptManager, PromptTemplate, create_prompt_manager


class TestPromptTemplate:
    """Tests for PromptTemplate model."""

    def test_prompt_template_minimal(self):
        """Test prompt template with minimal fields."""
        template = PromptTemplate(
            name="test",
            description="Test template",
            system_prompt="You are a helpful assistant.",
            user_template="Help me with {{ task }}.",
        )

        assert template.name == "test"
        assert template.description == "Test template"
        assert template.system_prompt == "You are a helpful assistant."
        assert template.user_template == "Help me with {{ task }}."
        assert template.version == "1.0.0"  # Default
        assert template.few_shot_examples == []
        assert template.required_variables == []
        assert template.temperature is None
        assert template.max_tokens is None
        assert template.tags == []
        assert template.metadata == {}

    def test_prompt_template_complete(self):
        """Test prompt template with all fields."""
        examples = [
            {"input": "Test input", "output": "Test output"},
            {"input": "Another input", "output": "Another output"},
        ]

        template = PromptTemplate(
            name="invoice_assistant",
            description="Generate invoice descriptions",
            version="2.0.0",
            system_prompt="You are an expert.",
            user_template="Service: {{ service }}",
            few_shot_examples=examples,
            required_variables=["service", "hours"],
            temperature=0.7,
            max_tokens=500,
            tags=["invoice", "description"],
            metadata={"author": "test", "updated": "2025-01-01"},
        )

        assert template.name == "invoice_assistant"
        assert template.version == "2.0.0"
        assert len(template.few_shot_examples) == 2
        assert template.required_variables == ["service", "hours"]
        assert template.temperature == 0.7
        assert template.max_tokens == 500
        assert "invoice" in template.tags
        assert template.metadata["author"] == "test"


class TestPromptManager:
    """Tests for PromptManager."""

    @pytest.fixture
    def templates_dir(self, tmp_path):
        """Create a temporary templates directory."""
        templates_dir = tmp_path / "prompts"
        templates_dir.mkdir()
        return templates_dir

    @pytest.fixture
    def sample_template_file(self, templates_dir):
        """Create a sample template YAML file."""
        template_data = {
            "name": "test_template",
            "description": "A test template",
            "version": "1.0.0",
            "system_prompt": "You are a helpful assistant.",
            "user_template": "Help me with {{ task }}.",
            "required_variables": ["task"],
            "temperature": 0.7,
            "max_tokens": 500,
            "tags": ["test"],
        }

        template_path = templates_dir / "test_template.yaml"
        with open(template_path, "w") as f:
            yaml.dump(template_data, f)

        return template_path

    @pytest.fixture
    def prompt_manager(self, templates_dir):
        """Create a PromptManager instance."""
        return PromptManager(templates_dir)

    def test_prompt_manager_init_creates_directory(self, tmp_path):
        """Test PromptManager creates directory if it doesn't exist."""
        templates_dir = tmp_path / "new_prompts"

        assert not templates_dir.exists()

        manager = PromptManager(templates_dir)

        assert templates_dir.exists()
        assert manager.templates_dir == templates_dir

    def test_prompt_manager_init_existing_directory(self, templates_dir):
        """Test PromptManager with existing directory."""
        manager = PromptManager(templates_dir)

        assert manager.templates_dir == templates_dir
        assert manager.env is not None
        assert manager._cache == {}

    def test_load_template_success(self, prompt_manager, sample_template_file):
        """Test loading a template successfully."""
        template = prompt_manager.load_template("test_template")

        assert isinstance(template, PromptTemplate)
        assert template.name == "test_template"
        assert template.description == "A test template"
        assert template.system_prompt == "You are a helpful assistant."
        assert template.required_variables == ["task"]
        assert template.temperature == 0.7

    def test_load_template_caching(self, prompt_manager, sample_template_file):
        """Test template is cached after first load."""
        # Load twice
        template1 = prompt_manager.load_template("test_template")
        template2 = prompt_manager.load_template("test_template")

        # Should be the same object (cached)
        assert template1 is template2
        assert "test_template" in prompt_manager._cache

    def test_load_template_not_found(self, prompt_manager):
        """Test loading non-existent template raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            prompt_manager.load_template("nonexistent")

        assert "not found" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)

    def test_load_template_missing_system_prompt(self, templates_dir):
        """Test loading template without system_prompt raises ValueError."""
        # Create invalid template
        invalid_data = {
            "name": "invalid",
            "description": "Invalid template",
            "user_template": "Hello {{ name }}",
        }

        template_path = templates_dir / "invalid.yaml"
        with open(template_path, "w") as f:
            yaml.dump(invalid_data, f)

        manager = PromptManager(templates_dir)

        with pytest.raises(ValueError) as exc_info:
            manager.load_template("invalid")

        assert "system_prompt" in str(exc_info.value)

    def test_load_template_missing_user_template(self, templates_dir):
        """Test loading template without user_template raises ValueError."""
        invalid_data = {
            "name": "invalid",
            "description": "Invalid template",
            "system_prompt": "You are a helper.",
        }

        template_path = templates_dir / "invalid.yaml"
        with open(template_path, "w") as f:
            yaml.dump(invalid_data, f)

        manager = PromptManager(templates_dir)

        with pytest.raises(ValueError) as exc_info:
            manager.load_template("invalid")

        assert "user_template" in str(exc_info.value)

    def test_load_template_invalid_yaml(self, templates_dir):
        """Test loading template with invalid YAML raises ValueError."""
        template_path = templates_dir / "bad_yaml.yaml"
        with open(template_path, "w") as f:
            f.write("invalid: yaml: content:\n  - broken")

        manager = PromptManager(templates_dir)

        with pytest.raises(ValueError) as exc_info:
            manager.load_template("bad_yaml")

        assert "Invalid YAML" in str(exc_info.value) or "Error loading" in str(exc_info.value)

    def test_render_basic(self, prompt_manager, sample_template_file):
        """Test rendering a template with variables."""
        system_prompt, user_prompt = prompt_manager.render("test_template", {"task": "write code"})

        assert system_prompt == "You are a helpful assistant."
        assert user_prompt == "Help me with write code."

    def test_render_missing_required_variables(self, prompt_manager, sample_template_file):
        """Test render raises ValueError when required variables are missing."""
        with pytest.raises(ValueError) as exc_info:
            prompt_manager.render("test_template", {"wrong_var": "value"})

        assert "requires variables" in str(exc_info.value)
        assert "task" in str(exc_info.value)

    def test_render_skip_validation(self, prompt_manager, sample_template_file):
        """Test render with validation disabled allows missing variables."""
        # Should not raise even though 'task' is missing
        system_prompt, user_prompt = prompt_manager.render("test_template", {}, validate=False)

        assert system_prompt == "You are a helpful assistant."
        # Jinja2 renders missing variables as empty strings
        assert "Help me with" in user_prompt

    def test_render_with_jinja2_features(self, templates_dir):
        """Test rendering with Jinja2 conditionals and filters."""
        template_data = {
            "name": "advanced",
            "description": "Advanced template",
            "system_prompt": "You are an expert.",
            "user_template": (
                "Name: {{ name | upper }}\n"
                "{% if age %}Age: {{ age }}{% endif %}\n"
                "Items: {{ items | join(', ') }}"
            ),
        }

        template_path = templates_dir / "advanced.yaml"
        with open(template_path, "w") as f:
            yaml.dump(template_data, f)

        manager = PromptManager(templates_dir)

        system_prompt, user_prompt = manager.render(
            "advanced",
            {"name": "john", "age": 30, "items": ["A", "B", "C"]},
            validate=False,
        )

        assert "JOHN" in user_prompt  # Filter applied
        assert "Age: 30" in user_prompt  # Conditional rendered
        assert "A, B, C" in user_prompt  # List joined

    def test_render_with_examples(self, templates_dir):
        """Test render_with_examples includes few-shot examples."""
        template_data = {
            "name": "with_examples",
            "description": "Template with examples",
            "system_prompt": "You are a helpful assistant.",
            "user_template": "Task: {{ task }}",
            "few_shot_examples": [
                {"input": "Example input 1", "output": "Example output 1"},
                {"input": "Example input 2", "output": "Example output 2"},
            ],
        }

        template_path = templates_dir / "with_examples.yaml"
        with open(template_path, "w") as f:
            yaml.dump(template_data, f)

        manager = PromptManager(templates_dir)

        system_prompt, user_prompt = manager.render_with_examples(
            "with_examples", {"task": "test task"}
        )

        assert system_prompt == "You are a helpful assistant."
        assert "Examples:" in user_prompt
        assert "Example 1:" in user_prompt
        assert "Example input 1" in user_prompt
        assert "Example output 1" in user_prompt
        assert "Example 2:" in user_prompt
        assert "Task: test task" in user_prompt

    def test_render_with_examples_no_examples(self, prompt_manager, sample_template_file):
        """Test render_with_examples without examples (normal render)."""
        system_prompt, user_prompt = prompt_manager.render_with_examples(
            "test_template", {"task": "test"}
        )

        # Should render normally without examples section
        assert "Examples:" not in user_prompt
        assert "Help me with test" in user_prompt

    def test_list_templates(self, templates_dir):
        """Test listing available templates."""
        # Create multiple templates
        for i in range(3):
            template_data = {
                "name": f"template_{i}",
                "description": "Test",
                "system_prompt": "Test",
                "user_template": "Test",
            }
            template_path = templates_dir / f"template_{i}.yaml"
            with open(template_path, "w") as f:
                yaml.dump(template_data, f)

        manager = PromptManager(templates_dir)

        templates = manager.list_templates()

        assert len(templates) == 3
        assert "template_0" in templates
        assert "template_1" in templates
        assert "template_2" in templates
        assert templates == sorted(templates)  # Should be sorted

    def test_list_templates_empty_directory(self, prompt_manager):
        """Test listing templates in empty directory."""
        templates = prompt_manager.list_templates()

        assert templates == []

    def test_get_template_info(self, prompt_manager, sample_template_file):
        """Test getting template metadata."""
        info = prompt_manager.get_template_info("test_template")

        assert info["name"] == "test_template"
        assert info["description"] == "A test template"
        assert info["version"] == "1.0.0"
        assert info["required_variables"] == ["task"]
        assert info["temperature"] == 0.7
        assert info["max_tokens"] == 500
        assert info["tags"] == ["test"]
        assert info["has_examples"] is False

    def test_get_template_info_with_examples(self, templates_dir):
        """Test get_template_info with few-shot examples."""
        template_data = {
            "name": "with_examples",
            "description": "Has examples",
            "system_prompt": "Test",
            "user_template": "Test",
            "few_shot_examples": [{"input": "test", "output": "test"}],
        }

        template_path = templates_dir / "with_examples.yaml"
        with open(template_path, "w") as f:
            yaml.dump(template_data, f)

        manager = PromptManager(templates_dir)

        info = manager.get_template_info("with_examples")

        assert info["has_examples"] is True

    def test_clear_cache(self, prompt_manager, sample_template_file):
        """Test clearing template cache."""
        # Load template (caches it)
        prompt_manager.load_template("test_template")
        assert "test_template" in prompt_manager._cache

        # Clear cache
        prompt_manager.clear_cache()

        assert prompt_manager._cache == {}

    def test_reload_template(self, prompt_manager, sample_template_file):
        """Test reloading a template bypasses cache."""
        # Load template
        template1 = prompt_manager.load_template("test_template")

        # Modify the file
        with open(sample_template_file) as f:
            data = yaml.safe_load(f)

        data["description"] = "Modified description"

        with open(sample_template_file, "w") as f:
            yaml.dump(data, f)

        # Reload should get new version
        template2 = prompt_manager.reload_template("test_template")

        assert template2.description == "Modified description"
        assert template1.description != template2.description

    def test_reload_template_not_in_cache(self, prompt_manager, sample_template_file):
        """Test reloading template that was never cached."""
        # Reload without loading first
        template = prompt_manager.reload_template("test_template")

        assert template.name == "test_template"
        assert "test_template" in prompt_manager._cache


class TestCreatePromptManager:
    """Tests for create_prompt_manager factory function."""

    def test_create_prompt_manager_with_path(self, tmp_path):
        """Test creating prompt manager with custom path."""
        templates_dir = tmp_path / "custom_prompts"

        manager = create_prompt_manager(templates_dir)

        assert isinstance(manager, PromptManager)
        assert manager.templates_dir == templates_dir

    def test_create_prompt_manager_default_path(self):
        """Test creating prompt manager with default path."""
        manager = create_prompt_manager()

        assert isinstance(manager, PromptManager)
        assert "openfatture/ai/prompts" in str(manager.templates_dir)
