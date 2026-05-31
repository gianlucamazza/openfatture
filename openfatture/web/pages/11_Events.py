"""Events & Audit Trail page.

View system events and audit trails.
"""

import pandas as pd
import streamlit as st

from openfatture.web.services.events_service import StreamlitEventsService
from openfatture.web.utils.i18n import get_translator

t = get_translator()

st.set_page_config(page_title=t("page-events-page-title"), page_icon="📋", layout="wide")

# Title
st.title(t("page-events-title"))
st.markdown(f"### {t('page-events-subtitle')}")

# Initialize service
events_service = StreamlitEventsService()

# Get statistics
stats = events_service.get_event_statistics()

# Summary cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        t("page-events-total-events"),
        f"{stats['total_events']:,}",
        t("page-events-last-days", days=stats["period_days"]),
    )

with col2:
    st.metric(t("page-events-daily-events"), f"{stats['avg_daily_events']:.1f}")

with col3:
    st.metric(t("page-events-event-types"), len(stats["event_types"]))

with col4:
    st.metric(t("page-events-tracked-entities"), len(stats["entity_types"]))

# Sidebar filters
st.sidebar.subheader(t("page-events-filters-title"))

# Date range
days_options = [1, 7, 30, 90]
selected_days = st.sidebar.selectbox(
    t("page-events-period-label"),
    days_options,
    index=1,  # Default to 7 days
    help=t("page-events-period-help"),
)

# Event type filter
available_event_types = events_service.get_available_event_types()
event_type_filter: list[str] | None = None
if available_event_types:
    event_type_filter_raw = st.sidebar.multiselect(
        t("page-events-event-type-label"),
        [t("page-events-all-label")] + available_event_types,
        default=[t("page-events-all-label")],
        help=t("page-events-event-type-help"),
    )
    if t("page-events-all-label") not in event_type_filter_raw:
        event_type_filter = event_type_filter_raw

# Entity type filter
available_entity_types = events_service.get_available_entity_types()
entity_type_filter: list[str] | None = None
if available_entity_types:
    entity_type_filter_raw = st.sidebar.multiselect(
        t("page-events-entity-type-label"),
        [t("page-events-all-label")] + available_entity_types,
        default=[t("page-events-all-label")],
        help=t("page-events-entity-type-help"),
    )
    if t("page-events-all-label") not in entity_type_filter_raw:
        entity_type_filter = entity_type_filter_raw

# Search
search_term = st.sidebar.text_input(
    t("page-events-search-label"),
    placeholder=t("page-events-search-placeholder"),
    help=t("page-events-search-help"),
)

# Tabs for different views
tab_recent, tab_filtered, tab_stats, tab_timeline = st.tabs(
    [
        t("page-events-tab-recent"),
        t("page-events-tab-filtered"),
        t("page-events-tab-stats"),
        t("page-events-tab-timeline"),
    ]
)

with tab_recent:
    st.subheader(t("page-events-recent-title"))

    # Get recent events
    recent_events = events_service.get_recent_events(limit=50)

    if recent_events:
        # Display as table
        events_df = pd.DataFrame(
            [
                {
                    t("page-events-timestamp-col"): event["timestamp"].strftime("%d/%m/%Y %H:%M"),
                    t("page-events-event-type-col"): event["event_type"],
                    t("page-events-entity-col"): (
                        f"{event['entity_type']} {event['entity_id']}"
                        if event["entity_id"]
                        else event["entity_type"] or t("page-events-system-label")
                    ),
                    t("page-events-description-col"): event["description"],
                    t("page-events-user-col"): event["user_id"] or t("page-events-system-label"),
                }
                for event in recent_events
            ]
        )

        st.dataframe(
            events_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                t("page-events-timestamp-col"): st.column_config.DatetimeColumn(
                    t("page-events-timestamp-col"), width="medium"
                ),
                t("page-events-event-type-col"): st.column_config.TextColumn(
                    t("page-events-event-type-col"), width="medium"
                ),
                t("page-events-entity-col"): st.column_config.TextColumn(
                    t("page-events-entity-col"), width="medium"
                ),
                t("page-events-description-col"): st.column_config.TextColumn(
                    t("page-events-description-col"), width="large"
                ),
                t("page-events-user-col"): st.column_config.TextColumn(
                    t("page-events-user-col"), width="small"
                ),
            },
        )

        # Show details for selected event
        if st.button(t("page-events-show-details-btn"), help=t("page-events-show-details-help")):
            for i, event in enumerate(recent_events[:5]):  # Show first 5
                with st.expander(
                    t("page-events-event-detail-title", num=i + 1, desc=event["description"]),
                    expanded=False,
                ):
                    st.json(event)

    else:
        st.info(t("page-events-no-events-found"))

with tab_filtered:
    st.subheader(t("page-events-filtered-title"))

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
        st.success(t("page-events-found-count", count=len(filtered_events)))

        # Display filtered results
        filtered_df = pd.DataFrame(
            [
                {
                    t("page-events-timestamp-col"): event["timestamp"].strftime("%d/%m/%Y %H:%M"),
                    t("page-events-event-type-col"): event["event_type"],
                    t("page-events-entity-col"): (
                        f"{event['entity_type']} {event['entity_id']}"
                        if event["entity_id"]
                        else event["entity_type"] or t("page-events-system-label")
                    ),
                    t("page-events-description-col"): event["description"],
                }
                for event in filtered_events
            ]
        )

        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        # Export option
        if st.button(t("page-events-export-csv-btn"), help=t("page-events-export-csv-help")):
            csv_data = filtered_df.to_csv(index=False)
            st.download_button(
                label=t("page-events-download-csv"),
                data=csv_data,
                file_name=f"events_filtered_{selected_days}days.csv",
                mime="text/csv",
                use_container_width=True,
            )

    else:
        st.info(t("page-events-no-filtered-events"))

with tab_stats:
    st.subheader(t("page-events-stats-title"))

    # Event types breakdown
    if stats["event_types"]:
        st.markdown(f"### {t('page-events-by-type-title')}")

        event_types_df = pd.DataFrame(
            [
                {t("page-events-event-type-col"): event_type, t("page-events-count-col"): count}
                for event_type, count in stats["event_types"].items()
            ]
        ).sort_values(t("page-events-count-col"), ascending=False)

        st.dataframe(event_types_df, use_container_width=True, hide_index=True)

        # Simple bar chart
        st.bar_chart(
            event_types_df.set_index(t("page-events-event-type-col"))[t("page-events-count-col")],
            use_container_width=True,
            height=300,
        )

    # Entity types breakdown
    if stats["entity_types"]:
        st.markdown(f"### {t('page-events-by-entity-title')}")

        entity_types_df = pd.DataFrame(
            [
                {t("page-events-entity-type-col"): entity_type, t("page-events-count-col"): count}
                for entity_type, count in stats["entity_types"].items()
            ]
        ).sort_values(t("page-events-count-col"), ascending=False)

        st.dataframe(entity_types_df, use_container_width=True, hide_index=True)

    # Daily activity
    if stats["daily_activity"]:
        st.markdown(f"### {t('page-events-daily-activity-title')}")

        daily_df = pd.DataFrame(stats["daily_activity"])
        daily_df["date"] = pd.to_datetime(daily_df["date"])
        daily_df = daily_df.sort_values("date")

        st.line_chart(daily_df.set_index("date")["count"], use_container_width=True, height=250)

with tab_timeline:
    st.subheader(t("page-events-timeline-title"))

    # Entity selection
    col1, col2 = st.columns(2)

    with col1:
        timeline_entity_type = st.selectbox(
            t("page-events-entity-type-label"),
            ["fattura", "cliente", "payment"] + (available_entity_types or []),
            help=t("page-events-timeline-entity-help"),
        )

    with col2:
        timeline_entity_id = st.text_input(
            t("page-events-entity-id-label"),
            placeholder=t("page-events-entity-id-placeholder"),
            help=t("page-events-entity-id-help"),
        )

    if timeline_entity_id:
        # Get timeline
        timeline_events = events_service.get_entity_timeline(
            timeline_entity_type, timeline_entity_id
        )

        if timeline_events:
            st.success(
                t(
                    "page-events-timeline-found",
                    count=len(timeline_events),
                    entity_type=timeline_entity_type,
                    entity_id=timeline_entity_id,
                )
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
                        with st.expander(t("page-events-details-label"), expanded=False):
                            st.json(event["metadata"])
        else:
            st.info(
                t(
                    "page-events-no-timeline-events",
                    entity_type=timeline_entity_type,
                    entity_id=timeline_entity_id,
                )
            )
    else:
        st.info(t("page-events-timeline-instruction"))

# Footer info
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #666; font-size: 0.9em;'>
    {t("page-events-footer-info")}
    </div>
    """,
    unsafe_allow_html=True,
)
