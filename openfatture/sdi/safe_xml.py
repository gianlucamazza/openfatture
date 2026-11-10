"""Parse XML from untrusted sources (PEC notifications, imported files).

No entity expansion, no DTD loading, no network access, no huge trees.
"""

from __future__ import annotations

from lxml import etree

_PARSER = etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    load_dtd=False,
    dtd_validation=False,
    huge_tree=False,
    remove_comments=True,
)

ParseError = etree.XMLSyntaxError


def parse_untrusted(content: str | bytes) -> etree._Element:
    """Parse ``content`` safely; raise :data:`ParseError` on malformed XML."""
    data = content.encode("utf-8") if isinstance(content, str) else content
    return etree.fromstring(data, parser=_PARSER)
