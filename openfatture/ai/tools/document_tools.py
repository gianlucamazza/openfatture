"""AI tool adapter over `openfatture.platform.opener`."""

from openfatture.ai.tools.models import Tool, ToolParameter, ToolParameterType, ToolRisk
from openfatture.platform.opener import open_document


def get_document_tools() -> list[Tool]:
    """Tools that act on documents OpenFatture has generated."""
    return [
        Tool(
            name="open_document",
            risk=ToolRisk.LOCAL_ARTIFACT,
            description=(
                "Open a generated document (PDF, FatturaPA XML, signed .p7m, CSV) or a "
                "folder with the user's default application. Only paths inside the "
                "exports or archive directory, such as a path just returned by "
                "generate_invoice_pdf, generate_invoice_summary_pdf, generate_invoice_xml, "
                "sign_invoice_xml or a CSV export; '.' is the exports folder. Use it when "
                "the user asks to open, view or show a document or folder. Returns "
                "opened=false when nobody can see it (no graphical session): then give "
                "the path instead. An error means the path is outside those directories, "
                "the file does not exist or is not one of those types, or no application "
                "handles it. The file is not modified."
            ),
            category="documents",
            parameters=[
                ToolParameter(
                    name="path",
                    type=ToolParameterType.STRING,
                    description=(
                        "Document or folder path returned by a tool, absolute or relative "
                        "to the exports directory; '.' opens the exports folder"
                    ),
                    required=True,
                ),
            ],
            func=open_document,
            examples=["open_document(path='riepiloghi/riepilogo_fatture_2026.pdf')"],
            tags=["document", "open", "pdf", "view"],
        ),
    ]
