"""System Health Dashboard - Best Practices 2025.

Provides real-time health monitoring and diagnostics.
"""

import streamlit as st

from openfatture.web.utils.health import quick_health_check, render_health_dashboard
from openfatture.web.utils.i18n import get_translator
from openfatture.web.utils.logging_config import get_usage_metrics, track_page_visit

t = get_translator()

# Page configuration
st.set_page_config(
    page_title=t("page-health-page-title"),
    page_icon="🏥",
    layout="wide",
)

# Track page visit
track_page_visit("health")

# Render health dashboard
render_health_dashboard()

# Additional diagnostics
st.markdown("---")
st.markdown(f"## {t('page-health-usage-metrics-title')}")

metrics = get_usage_metrics()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(t("page-health-total-visits"), metrics["total_page_visits"])

with col2:
    st.metric(t("page-health-unique-pages"), metrics["unique_pages_visited"])

with col3:
    st.metric(t("page-health-session-start"), metrics["session_start"].split("T")[0])

# Cache statistics (Best Practice 2025: monitor cache health)
st.markdown("---")
st.markdown(f"## {t('page-health-cache-stats-title')}")

from openfatture.web.utils.cache import cleanup_expired_caches, get_cache_stats

# Cleanup expired caches first
expired_count = cleanup_expired_caches()
if expired_count > 0:
    st.info(t("page-health-cleaned-caches", count=expired_count))

cache_stats = get_cache_stats()

col_c1, col_c2, col_c3 = st.columns(3)

with col_c1:
    st.metric(t("page-health-total-cache-entries"), cache_stats["total_entries"])

with col_c2:
    st.metric(t("page-health-cached-functions"), len(cache_stats["functions"]))

with col_c3:
    if st.button(t("page-health-clear-all-caches-btn")):
        from openfatture.web.utils.cache import invalidate_all_caches

        invalidate_all_caches()
        st.success(t("page-health-all-caches-cleared"))
        st.rerun()

# Function-level cache breakdown
if cache_stats["functions"]:
    st.markdown(f"### {t('page-health-cache-breakdown-title')}")

    import pandas as pd

    df_cache = pd.DataFrame(
        [{"Function": func, "Entries": count} for func, count in cache_stats["functions"].items()]
    )
    df_cache = df_cache.sort_values("Entries", ascending=False)

    st.dataframe(df_cache, use_container_width=True, hide_index=True)

    # Selective cache clearing
    st.markdown(f"### {t('page-health-selective-cache-title')}")

    col_cat1, col_cat2, col_cat3 = st.columns(3)

    with col_cat1:
        if st.button(t("page-health-clear-invoice-caches")):
            from openfatture.web.utils.cache import invalidate_cache_by_category

            cleared = invalidate_cache_by_category("invoices")
            st.success(
                t(
                    "page-health-cleared-count",
                    count=cleared,
                    category=t("page-health-invoice-category"),
                )
            )
            st.rerun()

    with col_cat2:
        if st.button(t("page-health-clear-client-caches")):
            from openfatture.web.utils.cache import invalidate_cache_by_category

            cleared = invalidate_cache_by_category("clients")
            st.success(
                t(
                    "page-health-cleared-count",
                    count=cleared,
                    category=t("page-health-client-category"),
                )
            )
            st.rerun()

    with col_cat3:
        if st.button(t("page-health-clear-payment-caches")):
            from openfatture.web.utils.cache import invalidate_cache_by_category

            cleared = invalidate_cache_by_category("payments")
            st.success(
                t(
                    "page-health-cleared-count",
                    count=cleared,
                    category=t("page-health-payment-category"),
                )
            )
            st.rerun()

# Page visit breakdown
if metrics["page_visits"]:
    st.markdown(f"### {t('page-health-visit-breakdown-title')}")

    import pandas as pd

    df = pd.DataFrame(
        [{"Page": page, "Visits": count} for page, count in metrics["page_visits"].items()]
    )
    df = df.sort_values("Visits", ascending=False)

    st.dataframe(df, use_container_width=True, hide_index=True)

# API health endpoint info
st.markdown("---")
st.markdown(f"## {t('page-health-api-endpoint-title')}")

st.markdown(t("page-health-api-endpoint-desc"))

# Show sample health check output
if st.button(t("page-health-show-sample-json-btn")):
    health = quick_health_check()

    st.json(health)

st.markdown("---")
st.info(t("page-health-best-practice-info"))
