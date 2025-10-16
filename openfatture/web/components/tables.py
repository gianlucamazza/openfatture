"""Reusable Table Components - Best Practices 2025.

Advanced table components with sorting, filtering, and pagination.
"""

from typing import Any

import pandas as pd
import streamlit as st


def data_table(
    data: pd.DataFrame | list[dict[str, Any]],
    columns: list[str] | None = None,
    sortable: bool = True,
    filterable: bool = False,
    paginate: bool = False,
    page_size: int = 20,
    key_prefix: str = "table",
    column_config: dict[str, Any] | None = None,
    hide_index: bool = True,
) -> pd.DataFrame:
    """
    Display an enhanced data table with optional features.

    Args:
        data: DataFrame or list of dicts
        columns: Columns to display (None = all)
        sortable: Enable sorting
        filterable: Enable column filtering
        paginate: Enable pagination
        page_size: Rows per page
        key_prefix: Unique prefix for widget keys
        column_config: Streamlit column configuration
        hide_index: Hide index column

    Returns:
        Filtered/paginated DataFrame

    Example:
        >>> data_table(
        ...     data=invoices_df,
        ...     sortable=True,
        ...     filterable=True,
        ...     paginate=True
        ... )
    """
    # Convert to DataFrame if needed
    if isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    # Select columns
    if columns:
        df = df[columns]

    # Filtering
    if filterable and not df.empty:
        with st.expander("🔍 Filtri", expanded=False):
            filter_cols = st.columns(min(3, len(df.columns)))

            for idx, col in enumerate(df.columns[:3]):  # Max 3 filter columns
                with filter_cols[idx]:
                    if df[col].dtype == "object":
                        # Text filter
                        filter_val = st.text_input(
                            f"Filtra {col}", key=f"{key_prefix}_filter_{col}"
                        )
                        if filter_val:
                            df = df[df[col].str.contains(filter_val, case=False, na=False)]
                    elif pd.api.types.is_numeric_dtype(df[col]):
                        # Numeric range filter
                        min_val = float(df[col].min())
                        max_val = float(df[col].max())
                        range_val = st.slider(
                            f"{col}",
                            min_val,
                            max_val,
                            (min_val, max_val),
                            key=f"{key_prefix}_range_{col}",
                        )
                        df = df[(df[col] >= range_val[0]) & (df[col] <= range_val[1])]

    # Sorting
    if sortable and not df.empty:
        col1, col2 = st.columns([3, 1])
        with col1:
            sort_col = st.selectbox(
                "Ordina per",
                options=[""] + list(df.columns),
                key=f"{key_prefix}_sort_col",
            )
        with col2:
            sort_order = st.radio(
                "Ordine",
                options=["↑ Asc", "↓ Desc"],
                key=f"{key_prefix}_sort_order",
                horizontal=True,
            )

        if sort_col:
            ascending = sort_order == "↑ Asc"
            df = df.sort_values(by=sort_col, ascending=ascending)

    # Pagination
    if paginate and len(df) > page_size:
        total_pages = (len(df) - 1) // page_size + 1
        page = st.number_input(
            f"Pagina (1-{total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1,
            key=f"{key_prefix}_page",
        )

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        df_display = df.iloc[start_idx:end_idx]

        st.caption(f"Mostrando {start_idx + 1}-{min(end_idx, len(df))} di {len(df)}")
    else:
        df_display = df

    # Display table
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=hide_index,
        column_config=column_config,
    )

    return df


def invoice_table(
    invoices: list[dict[str, Any]],
    show_actions: bool = True,
    on_view: Any = None,
) -> None:
    """
    Specialized table for invoices with predefined formatting.

    Args:
        invoices: List of invoice dicts
        show_actions: Show action buttons
        on_view: Callback for view action

    Example:
        >>> invoice_table(
        ...     invoices=[{"numero": "001", "totale": 1000, ...}],
        ...     on_view=lambda inv: print(inv["numero"])
        ... )
    """
    if not invoices:
        st.info("📭 Nessuna fattura trovata")
        return

    df = pd.DataFrame(invoices)

    # Column configuration
    config = {
        "numero": st.column_config.TextColumn("Numero", width="small"),
        "data_emissione": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
        "cliente_denominazione": st.column_config.TextColumn("Cliente", width="large"),
        "totale": st.column_config.NumberColumn("Totale", format="€%.2f"),
        "stato": st.column_config.TextColumn("Stato", width="small"),
    }

    # Display table
    data_table(
        data=df,
        columns=["numero", "data_emissione", "cliente_denominazione", "totale", "stato"],
        column_config=config,
        sortable=True,
        filterable=True,
    )

    # Action buttons
    if show_actions and on_view:
        st.markdown("---")
        selected = st.selectbox(
            "Seleziona fattura per dettagli",
            options=[""] + [f"{inv['numero']}/{inv.get('anno', '')}" for inv in invoices],
        )
        if selected and st.button("👁️ Vedi Dettagli"):
            # Find selected invoice
            for inv in invoices:
                if f"{inv['numero']}/{inv.get('anno', '')}" == selected:
                    on_view(inv)
                    break
