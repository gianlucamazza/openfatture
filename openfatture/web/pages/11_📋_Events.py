"""Events & Audit Trail page.

View system events and audit trails.
"""

import pandas as pd
import streamlit as st

from openfatture.web.services.events_service import StreamlitEventsService

st.set_page_config(page_title="Events & Audit Trail - OpenFatture", page_icon="📋", layout="wide")

# Title
st.title("📋 Events & Audit Trail")
st.markdown("### Tracciamento eventi e audit trail di sistema")

# Initialize service
events_service = StreamlitEventsService()

# Get statistics
stats = events_service.get_event_statistics()

# Summary cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Eventi Totali", f"{stats['total_events']:,}", f"Ultimi {stats['period_days']} giorni"
    )

with col2:
    st.metric("Eventi Giornalieri", f"{stats['avg_daily_events']:.1f}")

with col3:
    st.metric("Tipi Evento", len(stats["event_types"]))

with col4:
    st.metric("Entità Tracciate", len(stats["entity_types"]))

# Sidebar filters
st.sidebar.subheader("🔍 Filtri Eventi")

# Date range
days_options = [1, 7, 30, 90]
selected_days = st.sidebar.selectbox(
    "Periodo (giorni)",
    days_options,
    index=1,  # Default to 7 days
    help="Numero di giorni da analizzare",
)

# Event type filter
available_event_types = events_service.get_available_event_types()
if available_event_types:
    event_type_filter = st.sidebar.multiselect(
        "Tipo Evento",
        ["Tutti"] + available_event_types,
        default=["Tutti"],
        help="Filtra per tipo di evento",
    )
    if "Tutti" in event_type_filter:
        event_type_filter = None
else:
    event_type_filter = None

# Entity type filter
available_entity_types = events_service.get_available_entity_types()
if available_entity_types:
    entity_type_filter = st.sidebar.multiselect(
        "Tipo Entità",
        ["Tutti"] + available_entity_types,
        default=["Tutti"],
        help="Filtra per tipo di entità",
    )
    if "Tutti" in entity_type_filter:
        entity_type_filter = None
else:
    entity_type_filter = None

# Search
search_term = st.sidebar.text_input(
    "🔎 Cerca", placeholder="Cerca negli eventi...", help="Cerca per tipo evento o entità"
)

# Tabs for different views
tab_recent, tab_filtered, tab_stats, tab_timeline = st.tabs(
    ["🕐 Recenti", "🔍 Filtrati", "📊 Statistiche", "⏰ Timeline"]
)

with tab_recent:
    st.subheader("🕐 Eventi Recenti")

    # Get recent events
    recent_events = events_service.get_recent_events(limit=50)

    if recent_events:
        # Display as table
        events_df = pd.DataFrame(
            [
                {
                    "Timestamp": event["timestamp"].strftime("%d/%m/%Y %H:%M"),
                    "Tipo Evento": event["event_type"],
                    "Entità": (
                        f"{event['entity_type']} {event['entity_id']}"
                        if event["entity_id"]
                        else event["entity_type"] or "Sistema"
                    ),
                    "Descrizione": event["description"],
                    "Utente": event["user_id"] or "Sistema",
                }
                for event in recent_events
            ]
        )

        st.dataframe(
            events_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Timestamp": st.column_config.DatetimeColumn("Timestamp", width="medium"),
                "Tipo Evento": st.column_config.TextColumn("Tipo Evento", width="medium"),
                "Entità": st.column_config.TextColumn("Entità", width="medium"),
                "Descrizione": st.column_config.TextColumn("Descrizione", width="large"),
                "Utente": st.column_config.TextColumn("Utente", width="small"),
            },
        )

        # Show details for selected event
        if st.button("👁️ Mostra Dettagli", help="Mostra dettagli completi degli eventi"):
            for i, event in enumerate(recent_events[:5]):  # Show first 5
                with st.expander(f"Evento {i + 1}: {event['description']}", expanded=False):
                    st.json(event)

    else:
        st.info("📭 Nessun evento trovato nel database")

with tab_filtered:
    st.subheader("🔍 Eventi Filtrati")

    # Apply filters
    filtered_events = events_service.get_events_filtered(
        event_type=(
            event_type_filter[0] if event_type_filter and len(event_type_filter) == 1 else None
        ),
        entity_type=(
            entity_type_filter[0] if entity_type_filter and len(entity_type_filter) == 1 else None
        ),
        days=selected_days,
    )

    # Apply search if provided
    if search_term:
        filtered_events = events_service.search_events(search_term)

    if filtered_events:
        st.success(f"✅ Trovati {len(filtered_events)} eventi")

        # Display filtered results
        filtered_df = pd.DataFrame(
            [
                {
                    "Timestamp": event["timestamp"].strftime("%d/%m/%Y %H:%M"),
                    "Tipo Evento": event["event_type"],
                    "Entità": (
                        f"{event['entity_type']} {event['entity_id']}"
                        if event["entity_id"]
                        else event["entity_type"] or "Sistema"
                    ),
                    "Descrizione": event["description"],
                }
                for event in filtered_events
            ]
        )

        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        # Export option
        if st.button("📤 Esporta CSV", help="Esporta risultati filtrati come CSV"):
            csv_data = filtered_df.to_csv(index=False)
            st.download_button(
                label="Scarica CSV",
                data=csv_data,
                file_name=f"events_filtered_{selected_days}days.csv",
                mime="text/csv",
                use_container_width=True,
            )

    else:
        st.info("🔍 Nessun evento trovato con i filtri selezionati")

with tab_stats:
    st.subheader("📊 Statistiche Eventi")

    # Event types breakdown
    if stats["event_types"]:
        st.markdown("### 📈 Eventi per Tipo")

        event_types_df = pd.DataFrame(
            [
                {"Tipo Evento": event_type, "Conteggio": count}
                for event_type, count in stats["event_types"].items()
            ]
        ).sort_values("Conteggio", ascending=False)

        st.dataframe(event_types_df, use_container_width=True, hide_index=True)

        # Simple bar chart
        st.bar_chart(
            event_types_df.set_index("Tipo Evento")["Conteggio"],
            use_container_width=True,
            height=300,
        )

    # Entity types breakdown
    if stats["entity_types"]:
        st.markdown("### 🏢 Eventi per Entità")

        entity_types_df = pd.DataFrame(
            [
                {"Tipo Entità": entity_type, "Conteggio": count}
                for entity_type, count in stats["entity_types"].items()
            ]
        ).sort_values("Conteggio", ascending=False)

        st.dataframe(entity_types_df, use_container_width=True, hide_index=True)

    # Daily activity
    if stats["daily_activity"]:
        st.markdown("### 📅 Attività Giornaliera (Ultimi 7 Giorni)")

        daily_df = pd.DataFrame(stats["daily_activity"])
        daily_df["date"] = pd.to_datetime(daily_df["date"])
        daily_df = daily_df.sort_values("date")

        st.line_chart(daily_df.set_index("date")["count"], use_container_width=True, height=250)

with tab_timeline:
    st.subheader("⏰ Timeline Entità")

    # Entity selection
    col1, col2 = st.columns(2)

    with col1:
        timeline_entity_type = st.selectbox(
            "Tipo Entità",
            ["fattura", "cliente", "payment"] + (available_entity_types or []),
            help="Seleziona il tipo di entità",
        )

    with col2:
        timeline_entity_id = st.text_input(
            "ID Entità",
            placeholder="es: INV-001, CLI-001",
            help="Inserisci l'ID dell'entità da tracciare",
        )

    if timeline_entity_id:
        # Get timeline
        timeline_events = events_service.get_entity_timeline(
            timeline_entity_type, timeline_entity_id
        )

        if timeline_events:
            st.success(
                f"✅ Trovati {len(timeline_events)} eventi per {timeline_entity_type} {timeline_entity_id}"
            )

            # Display timeline
            for event in timeline_events:
                with st.container(border=True):
                    col_time, col_type, col_desc = st.columns([2, 2, 6])

                    with col_time:
                        st.write(f"🕐 **{event['timestamp'].strftime('%d/%m/%Y %H:%M')}**")

                    with col_type:
                        st.write(f"📋 {event['event_type']}")

                    with col_desc:
                        st.write(event["description"])

                    # Show metadata if available
                    if event["metadata"]:
                        with st.expander("📄 Dettagli", expanded=False):
                            st.json(event["metadata"])
        else:
            st.info(f"📭 Nessun evento trovato per {timeline_entity_type} {timeline_entity_id}")
    else:
        st.info("💡 Seleziona un tipo entità e inserisci un ID per vedere la timeline")

# Footer info
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
    📋 <strong>Event System:</strong> Audit trail completo per compliance e debugging •
    🔍 <strong>Ricerca:</strong> Filtra per tipo, entità e periodo •
    📊 <strong>Analytics:</strong> Statistiche attività e timeline entità
    </div>
    """,
    unsafe_allow_html=True,
)
