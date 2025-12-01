"""Menu builder for interactive CLI."""

from dataclasses import dataclass
from typing import Any, Callable

import questionary
from questionary import Choice

from openfatture.cli.ui.styles import openfatture_style


@dataclass
class MenuOption:
    """Represents a single menu option."""

    title: str
    value: str
    handler: Callable[[], Any] | None = None
    is_separator: bool = False


class MenuBuilder:
    """Builder for interactive menus."""

    def __init__(self, title: str):
        """Initialize menu builder."""
        self.title = title
        self.options: list[MenuOption] = []
        self.back_option: MenuOption | None = None

    def add_option(
        self, title: str, value: str, handler: Callable[[], Any] | None = None
    ) -> "MenuBuilder":
        """Add a menu option."""
        self.options.append(MenuOption(title=title, value=value, handler=handler))
        return self

    def add_separator(self) -> "MenuBuilder":
        """Add a separator."""
        self.options.append(MenuOption(title="", value="", is_separator=True))
        return self

    def add_back_option(self, title: str = "← Torna indietro", value: str = "back") -> "MenuBuilder":
        """Add a back option."""
        self.back_option = MenuOption(title=title, value=value)
        return self

    def build_choices(self) -> list[Choice | Any]:
        """Build questionary choices."""
        choices = []
        for opt in self.options:
            if opt.is_separator:
                choices.append(questionary.Separator())
            else:
                choices.append(Choice(title=opt.title, value=opt.value))

        if self.back_option:
            choices.append(questionary.Separator())
            choices.append(Choice(title=self.back_option.title, value=self.back_option.value))

        return choices

    def show(self) -> str:
        """Show menu and return selected value."""
        return questionary.select(
            self.title,
            choices=self.build_choices(),
            use_shortcuts=True,
            use_arrow_keys=True,
            style=openfatture_style,
            instruction="(Usa i tasti numerici o frecce ↑↓, INVIO per confermare)",
        ).ask()

    def run(self) -> None:
        """Run the menu loop."""
        while True:
            choice_value = self.show()

            if not choice_value:
                break

            if self.back_option and choice_value == self.back_option.value:
                break

            # Find handler
            handler = None
            for opt in self.options:
                if opt.value == choice_value:
                    handler = opt.handler
                    break

            if handler:
                handler()
