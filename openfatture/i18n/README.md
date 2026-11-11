# openfatture.i18n

Terminal messages are [Project Fluent](https://projectfluent.org/) resources,
one `cli.ftl` per locale:

```
openfatture/i18n/
├── __init__.py      # public API: _, get_locale, set_locale
├── loader.py        # FluentBundle loading and caching
├── translator.py    # _() with locale fallback
├── locales/{it,en,de,es,fr}/cli.ftl
└── gettext/{it,de,es,fr}/LC_MESSAGES/openfatture-cli.{po,mo}
```

Italian is the default locale; `fallback_locale` (configuration) and English
are used when a message is missing. Email templates are localized separately
by JSON files in `openfatture/sdi/email/i18n/`.

Command-line help (`cli-help-*`) is resolved from the same locale when the CLI
starts. Click and Typer translate their own text (panel titles, `--help`,
usage errors) through stdlib `gettext`: `openfatture/cli/framework_i18n.py`
binds the `gettext/` catalogs and selects the configured locale. The `.po`
files are the sources; after editing one, compile it with
`uv run python scripts/compile_cli_catalogs.py`.
`tests/i18n/test_framework_catalogs.py` fails on a stale `.mo`, on a lost
placeholder, and when a Click/Typer upgrade adds an untranslated message.
Typer releases that vendor Click (`typer._click`, which a fresh install from
PyPI resolves) translate only Typer's own labels through gettext; Click's text
there is fixed English. The lines every help page shows (`--help`,
`--install-completion`, `--show-completion`) therefore come from Fluent
(`cli-help-help-option`, `cli-help-*-completion`) and are localized with either
Typer; rarer Click messages, such as some usage errors, can stay in English.

## Usage

```python
from openfatture.i18n import _

_("assistant-session", session=session_id)
_("cli-config-set-success", key=key, value=value)
```

## Rules

- Message ids are kebab-case and namespaced (`assistant-*`, `cli-config-*`,
  `cli-invoice-*`, `status-*`).
- Every id referenced by the code must exist in every locale, and no locale
  may define unused ids: `tests/i18n/test_cli_translations.py` enforces both.
- Ids are always string literals (map runtime values to ids with a dict,
  as `cli/output.py` does for service error codes) so the test sees them.
- Keep Italian fiscal terms (IVA, SDI, PEC, partita IVA) untranslated where
  they are the legal names.
