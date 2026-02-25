"""Pydeck map visualization of property search results."""

import streamlit as st
import pydeck as pdk
import pandas as pd


def render_map(properties: list[dict]):
    """Render a scatter plot map of properties using pydeck."""
    if not properties:
        return

    df = pd.DataFrame(properties)

    # Ensure numeric lat/lon
    df["latitude"] = pd.to_numeric(df.get("latitude", pd.Series(dtype=float)), errors="coerce")
    df["longitude"] = pd.to_numeric(df.get("longitude", pd.Series(dtype=float)), errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])

    if df.empty:
        st.warning("No location data available for map.")
        return

    df["price"] = pd.to_numeric(df.get("price", pd.Series(dtype=float)), errors="coerce").fillna(0)
    df["price_label"] = df["price"].apply(lambda x: f"${x:,.0f}")
    df["tooltip"] = (
        df.get("address", "").astype(str) + ", " + df.get("city", "").astype(str)
        + "\n" + df["price_label"]
        + "\n" + df.get("beds", "").astype(str) + " bd / "
        + df.get("baths", "").astype(str) + " ba / "
        + df.get("sqft", "").astype(str) + " sqft"
    )

    # Color by price tier
    price_median = df["price"].median()
    df["color_r"] = df["price"].apply(lambda p: min(255, int(200 * p / price_median)) if price_median > 0 else 100)
    df["color_g"] = df["price"].apply(lambda p: max(50, 200 - int(150 * p / price_median)) if price_median > 0 else 100)
    df["color_b"] = 100

    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_fill_color=["color_r", "color_g", "color_b", 200],
        get_radius=300,
        pickable=True,
        auto_highlight=True,
    )

    view = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=10,
        pitch=0,
    )

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        tooltip={"text": "{tooltip}"},
        map_style="mapbox://styles/mapbox/light-v10",
    )

    st.pydeck_chart(deck)
