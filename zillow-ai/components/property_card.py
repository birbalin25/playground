"""Property card grid rendering."""

import streamlit as st


def _status_class(status: str) -> str:
    """Map listing status to CSS class."""
    s = status.lower().replace(" ", "-")
    return f"status-{s}"


def render_property_card(prop: dict, zestimate: float | None = None):
    """Render a single property card as HTML."""
    price = prop.get("price", 0)
    beds = prop.get("beds", 0)
    baths = prop.get("baths", 0)
    sqft = prop.get("sqft", 0)
    address = prop.get("address", "")
    city = prop.get("city", "")
    state = prop.get("state", "")
    zip_code = prop.get("zip_code", "")
    prop_type = prop.get("property_type", "")
    status = prop.get("listing_status", "For Sale")
    image_url = prop.get("image_url", "https://picsum.photos/640/400")
    features = prop.get("features", [])
    neighborhood = prop.get("neighborhood", "")

    zestimate_html = ""
    if zestimate is not None:
        diff = zestimate - price
        diff_pct = (diff / price * 100) if price > 0 else 0
        arrow = "+" if diff > 0 else ""
        zestimate_html = (
            f'<span class="zestimate-badge">'
            f'Zestimate: ${zestimate:,.0f} ({arrow}{diff_pct:.1f}%)</span>'
        )

    if isinstance(features, list):
        features_html = "".join(f'<span class="feature-tag">{f}</span>' for f in features[:4])
    else:
        features_html = ""

    st.markdown(
        f"""
        <div class="property-card">
            <img src="{image_url}" alt="Property" onerror="this.src='https://picsum.photos/640/400'">
            <div class="card-body">
                <span class="status-badge {_status_class(status)}">{status}</span>
                <p class="price">${price:,.0f} {zestimate_html}</p>
                <p class="details">
                    <strong>{beds}</strong> bd | <strong>{baths}</strong> ba | <strong>{sqft:,}</strong> sqft
                    — {prop_type}
                </p>
                <p class="address">{address}, {neighborhood}, {city}, {state} {zip_code}</p>
                <div>{features_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_property_grid(properties: list[dict], zestimates: list[float | None] | None = None, cols: int = 3):
    """Render a grid of property cards."""
    if not properties:
        st.info("No properties found. Try a different search.")
        return

    zestimates = zestimates or [None] * len(properties)

    for i in range(0, len(properties), cols):
        row = st.columns(cols)
        for j, col in enumerate(row):
            idx = i + j
            if idx < len(properties):
                with col:
                    render_property_card(properties[idx], zestimates[idx])
