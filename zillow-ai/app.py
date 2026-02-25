"""Zillow Re-imagined with AI — Databricks App (Streamlit)."""

import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(
    page_title="Zillow AI — Powered by Databricks",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load custom CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from components.search_bar import render_search_bar
from components.property_card import render_property_grid
from components.sidebar_filters import render_sidebar_filters
from components.chat import render_chat
from components.map_view import render_map
from utils.rag import search_properties
from utils.price_predictor import predict_prices_batch
from utils.data_access import (
    get_market_summary,
    get_price_distribution,
    get_property_type_breakdown,
    get_neighborhood_stats,
    get_total_stats,
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Zillow_logo.svg/200px-Zillow_logo.svg.png", width=150)
st.sidebar.markdown("**Re-imagined with AI**")
st.sidebar.markdown("---")
filters = render_sidebar_filters()
st.sidebar.markdown("---")
st.sidebar.caption("Powered by Databricks | Unity Catalog | Vector Search | MLflow | Foundation Models")

# ── Session State ────────────────────────────────────────────────────────────
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "zestimates" not in st.session_state:
    st.session_state.zestimates = []

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_search, tab_chat, tab_insights = st.tabs(["Search", "AI Assistant", "Market Insights"])

# ── Tab 1: Search ────────────────────────────────────────────────────────────
with tab_search:
    query = render_search_bar()

    if query:
        st.session_state.last_query = query
        with st.spinner("Searching with AI..."):
            results = search_properties(query, num_results=12, filters=filters if filters else None)
            st.session_state.search_results = results

            # Get Zestimate predictions
            if results:
                zestimates = predict_prices_batch(results)
                st.session_state.zestimates = zestimates

    results = st.session_state.search_results
    zestimates = st.session_state.zestimates

    if results:
        st.markdown(f"### {len(results)} results for *\"{st.session_state.last_query}\"*")

        # Map view
        with st.expander("Map View", expanded=True):
            render_map(results)

        # Property grid
        render_property_grid(results, zestimates)
    else:
        # Show some example queries
        st.markdown("#### Try searching for:")
        examples = [
            "Modern condos in Seattle with rooftop views",
            "Family homes near top schools in Austin under $600k",
            "Walkable neighborhoods in Chicago with 3+ bedrooms",
            "Luxury homes in San Francisco with smart home features",
        ]
        cols = st.columns(2)
        for i, example in enumerate(examples):
            with cols[i % 2]:
                st.markdown(f"- *{example}*")

# ── Tab 2: AI Assistant ─────────────────────────────────────────────────────
with tab_chat:
    render_chat()

# ── Tab 3: Market Insights ──────────────────────────────────────────────────
with tab_insights:
    st.markdown("### Market Insights")
    st.caption("Real-time analytics from Unity Catalog Delta tables")

    try:
        # Top-level metrics
        stats = get_total_stats()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Listings", f"{stats['total_listings']:,}")
        m2.metric("Avg Price", f"${stats['avg_price']:,}")
        m3.metric("Markets", stats["num_cities"])
        m4.metric("Avg Days on Market", stats["avg_dom"])

        st.markdown("---")

        # Market summary table
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### Average Price by City")
            summary = get_market_summary()
            if not summary.empty:
                summary["avg_price"] = pd.to_numeric(summary["avg_price"], errors="coerce")
                summary["listing_count"] = pd.to_numeric(summary["listing_count"], errors="coerce")
                fig = px.bar(
                    summary.sort_values("avg_price", ascending=True),
                    x="avg_price", y="city",
                    orientation="h",
                    color="avg_price",
                    color_continuous_scale="Blues",
                    labels={"avg_price": "Average Price ($)", "city": "City"},
                )
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.markdown("#### Property Type Breakdown")
            pt = get_property_type_breakdown()
            if not pt.empty:
                pt["count"] = pd.to_numeric(pt["count"], errors="coerce")
                fig2 = px.pie(
                    pt, values="count", names="property_type",
                    color_discrete_sequence=px.colors.sequential.Blues_r,
                )
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)

        # City deep-dive
        st.markdown("---")
        st.markdown("#### Neighborhood Deep Dive")
        selected_city = st.selectbox("Select a city", [
            "Austin", "Boston", "Chicago", "Denver", "Miami",
            "Nashville", "New York", "Portland", "San Francisco", "Seattle",
        ])

        if selected_city:
            nb = get_neighborhood_stats(selected_city)
            if not nb.empty:
                nb["avg_price"] = pd.to_numeric(nb["avg_price"], errors="coerce")
                nb["avg_school_rating"] = pd.to_numeric(nb["avg_school_rating"], errors="coerce")
                nb["avg_walk_score"] = pd.to_numeric(nb["avg_walk_score"], errors="coerce")

                c1, c2 = st.columns(2)
                with c1:
                    fig3 = px.bar(
                        nb, x="neighborhood", y="avg_price",
                        color="avg_school_rating",
                        color_continuous_scale="Greens",
                        labels={"avg_price": "Avg Price ($)", "neighborhood": "Neighborhood"},
                        title=f"Neighborhoods in {selected_city}",
                    )
                    fig3.update_layout(height=350)
                    st.plotly_chart(fig3, use_container_width=True)
                with c2:
                    fig4 = px.scatter(
                        nb, x="avg_walk_score", y="avg_price",
                        size="listings", text="neighborhood",
                        labels={"avg_walk_score": "Walk Score", "avg_price": "Avg Price ($)"},
                        title="Walk Score vs Price",
                    )
                    fig4.update_traces(textposition="top center")
                    fig4.update_layout(height=350)
                    st.plotly_chart(fig4, use_container_width=True)

                st.dataframe(nb, use_container_width=True)

    except Exception as e:
        st.error(f"Could not load market data. Make sure the notebooks have been run. Error: {e}")
