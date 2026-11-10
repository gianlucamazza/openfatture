# openfatture.i18n

Terminal messages are [Project Fluent](https://projectfluent.org/) resources,
one `cli.ftl` per locale:

```
openfatture/i18n/
├── __init__.py      # public API: _, get_locale, set_locale
├── loader.py        # FluentBundle loading and caching
├── translator.py    # _() with locale fallback
└── locales/{it,en,de,es,fr}/cli.ftl
```

Italian is the default locale; `fallback_locale` (configuration) and English
are used when a message is missing. Email templates are localized separately
by JSON files in `openfatture/sdi/email/i18n/`.

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
  as `cli/commands/fattura.py` does for payment statuses) so the test sees them.
- Keep Italian fiscal terms (IVA, SDI, PEC, partita IVA) untranslated where
  they are the legal names.
