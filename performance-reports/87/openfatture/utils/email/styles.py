"""
CSS styles for email templates.

Provides responsive, accessible styles optimized for email clients.
"""

from dataclasses import dataclass


@dataclass
class EmailBranding:
    """Email branding configuration."""

    primary_color: str = "#1976D2"  # Blue
    secondary_color: str = "#424242"  # Dark gray
    success_color: str = "#4CAF50"  # Green
    warning_color: str = "#FF9800"  # Orange
    error_color: str = "#F44336"  # Red
    text_color: str = "#333333"
    background_color: str = "#F5F5F5"
    logo_url: str | None = None
    footer_text: str | None = None


class EmailStyles:
    """
    Email CSS styles generator.

    Provides inline styles compatible with major email clients.
    """

    @staticmethod
    def get_base_css(branding: EmailBranding) -> str:
        """
        Get base CSS styles for emails.

        Args:
            branding: Branding configuration

        Returns:
            CSS string
        """
        return f"""
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: {branding.text_color};
            background-color: {branding.background_color};
        }}

        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }}

        .email-header {{
            background-color: {branding.primary_color};
            color: #ffffff;
            padding: 20px;
            text-align: center;
        }}

        .email-header img {{
            max-width: 200px;
            height: auto;
        }}

        .email-body {{
            padding: 30px 20px;
        }}

        .email-footer {{
            background-color: {branding.secondary_color};
            color: #ffffff;
            padding: 20px;
            text-align: center;
            font-size: 14px;
        }}

        .email-footer a {{
            color: #ffffff;
            text-decoration: underline;
        }}

        h1, h2, h3 {{
            color: {branding.primary_color};
            margin-top: 0;
        }}

        h1 {{
            font-size: 24px;
            margin-bottom: 20px;
        }}

        h2 {{
            font-size: 20px;
            margin-bottom: 15px;
        }}

        h3 {{
            font-size: 18px;
            margin-bottom: 10px;
        }}

        p {{
            margin: 0 0 15px 0;
        }}

        .alert {{
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
            border-left: 4px solid;
        }}

        .alert-success {{
            background-color: #E8F5E9;
            border-color: {branding.success_color};
            color: #2E7D32;
        }}

        .alert-warning {{
            background-color: #FFF3E0;
            border-color: {branding.warning_color};
            color: #EF6C00;
        }}

        .alert-error {{
            background-color: #FFEBEE;
            border-color: {branding.error_color};
            color: #C62828;
        }}

        .alert-info {{
            background-color: #E3F2FD;
            border-color: {branding.primary_color};
            color: #1565C0;
        }}

        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: {branding.primary_color};
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
            margin: 10px 0;
        }}

        .button:hover {{
            opacity: 0.9;
        }}

        .divider {{
            border-top: 1px solid #E0E0E0;
            margin: 20px 0;
        }}

        /* Responsive */
        @media only screen and (max-width: 600px) {{
            .email-container {{
                width: 100% !important;
            }}

            .email-body {{
                padding: 20px 15px !important;
            }}

            h1 {{
                font-size: 20px !important;
            }}
        }}
        """

    @staticmethod
    def get_table_css(branding: EmailBranding) -> str:
        """Get table styles for data display."""
        return f"""
        table.data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}

        table.data-table th {{
            background-color: {branding.primary_color};
            color: #ffffff;
            padding: 12px 8px;
            text-align: left;
            font-weight: bold;
        }}

        table.data-table td {{
            padding: 10px 8px;
            border-bottom: 1px solid #E0E0E0;
        }}

        table.data-table tr:hover {{
            background-color: #F5F5F5;
        }}

        table.summary-table {{
            width: 100%;
            margin: 15px 0;
        }}

        table.summary-table td {{
            padding: 8px 0;
            border-bottom: 1px solid #E0E0E0;
        }}

        table.summary-table td:first-child {{
            font-weight: bold;
            color: {branding.secondary_color};
            width: 40%;
        }}

        table.summary-table tr:last-child td {{
            border-bottom: 2px solid {branding.primary_color};
            padding-top: 12px;
            font-size: 18px;
            font-weight: bold;
        }}
        """

    @staticmethod
    def get_badge_css(branding: EmailBranding) -> str:
        """Get badge/label styles."""
        return f"""
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}

        .badge-success {{
            background-color: {branding.success_color};
            color: #ffffff;
        }}

        .badge-warning {{
            background-color: {branding.warning_color};
            color: #ffffff;
        }}

        .badge-error {{
            background-color: {branding.error_color};
            color: #ffffff;
        }}

        .badge-info {{
            background-color: {branding.primary_color};
            color: #ffffff;
        }}
        """

    @staticmethod
    def get_complete_css(branding: EmailBranding) -> str:
        """Get all CSS styles combined."""
        return "\n".join(
            [
                EmailStyles.get_base_css(branding),
                EmailStyles.get_table_css(branding),
                EmailStyles.get_badge_css(branding),
            ]
        )
