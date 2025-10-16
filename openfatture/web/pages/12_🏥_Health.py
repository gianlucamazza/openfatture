"""System Health Dashboard - Best Practices 2025.

Provides real-time health monitoring and diagnostics.
"""

import streamlit as st

from openfatture.web.utils.health import quick_health_check, render_health_dashboard
from openfatture.web.utils.logging_config import get_usage_metrics, track_page_visit

# Page configuration
st.set_page_config(
    page_title="System Health - OpenFatture",
    page_icon="🏥",
    layout="wide",
)

# Track page visit
track_page_visit("health")

# Render health dashboard
render_health_dashboard()

# Additional diagnostics
st.markdown("---")
st.markdown("## 📊 Usage Metrics")

metrics = get_usage_metrics()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Page Visits", metrics["total_page_visits"])

with col2:
    st.metric("Unique Pages", metrics["unique_pages_visited"])

with col3:
    st.metric("Session Start", metrics["session_start"].split("T")[0])

# Cache statistics (Best Practice 2025: monitor cache health)
st.markdown("---")
st.markdown("## 💾 Cache Statistics")

from openfatture.web.utils.cache import cleanup_expired_caches, get_cache_stats

# Cleanup expired caches first
expired_count = cleanup_expired_caches()
if expired_count > 0:
    st.info(f"🧹 Cleaned up {expired_count} expired cache entries")

cache_stats = get_cache_stats()

col_c1, col_c2, col_c3 = st.columns(3)

with col_c1:
    st.metric("Total Cache Entries", cache_stats["total_entries"])

with col_c2:
    st.metric("Cached Functions", len(cache_stats["functions"]))

with col_c3:
    if st.button("🗑️ Clear All Caches"):
        from openfatture.web.utils.cache import invalidate_all_caches

        invalidate_all_caches()
        st.success("✅ All caches cleared!")
        st.rerun()

# Function-level cache breakdown
if cache_stats["functions"]:
    st.markdown("### Cache Breakdown by Function")

    import pandas as pd

    df_cache = pd.DataFrame(
        [{"Function": func, "Entries": count} for func, count in cache_stats["functions"].items()]
    )
    df_cache = df_cache.sort_values("Entries", ascending=False)

    st.dataframe(df_cache, use_container_width=True, hide_index=True)

    # Selective cache clearing
    st.markdown("### Selective Cache Management")

    col_cat1, col_cat2, col_cat3 = st.columns(3)

    with col_cat1:
        if st.button("🧾 Clear Invoice Caches"):
            from openfatture.web.utils.cache import invalidate_cache_by_category

            cleared = invalidate_cache_by_category("invoices")
            st.success(f"✅ Cleared {cleared} invoice caches")
            st.rerun()

    with col_cat2:
        if st.button("👥 Clear Client Caches"):
            from openfatture.web.utils.cache import invalidate_cache_by_category

            cleared = invalidate_cache_by_category("clients")
            st.success(f"✅ Cleared {cleared} client caches")
            st.rerun()

    with col_cat3:
        if st.button("💰 Clear Payment Caches"):
            from openfatture.web.utils.cache import invalidate_cache_by_category

            cleared = invalidate_cache_by_category("payments")
            st.success(f"✅ Cleared {cleared} payment caches")
            st.rerun()

# Page visit breakdown
if metrics["page_visits"]:
    st.markdown("### Page Visit Breakdown")

    import pandas as pd

    df = pd.DataFrame(
        [{"Page": page, "Visits": count} for page, count in metrics["page_visits"].items()]
    )
    df = df.sort_values("Visits", ascending=False)

    st.dataframe(df, use_container_width=True, hide_index=True)

# API health endpoint info
st.markdown("---")
st.markdown("## 🔌 API Health Endpoint")

st.markdown(
    """
    For external monitoring, use the `quick_health_check()` function:

    ```python
    from openfatture.web.utils.health import quick_health_check

    health = quick_health_check()
    # Returns: {"status": "healthy|degraded|unhealthy", "checks": [...]}
    ```

    This can be exposed via an API endpoint for monitoring tools like:
    - Prometheus
    - Datadog
    - New Relic
    - Custom monitoring dashboards
    """
)

# Show sample health check output
if st.button("🔍 Show Sample Health Check JSON"):
    health = quick_health_check()

    st.json(health)

st.markdown("---")
st.info(
    """
    **💡 Best Practice:** Monitor this dashboard regularly to catch issues early.
    Set up alerts for "unhealthy" or "degraded" statuses in production.
    """
)
