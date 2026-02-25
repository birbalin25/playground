"""Vector Search retrieval + Foundation Model API generation."""

from databricks.vector_search.client import VectorSearchClient
from openai import OpenAI
from config import VS_ENDPOINT_NAME, VS_INDEX_NAME, LLM_MODEL
from utils.databricks_client import get_databricks_host, get_token

SEARCH_COLUMNS = [
    "id", "address", "city", "state", "price", "beds", "baths", "sqft",
    "property_type", "neighborhood", "description", "features",
    "school_rating", "walk_score", "image_url", "listing_status",
    "latitude", "longitude", "year_built", "price_per_sqft",
    "lot_size", "hoa_fee", "parking", "days_on_market", "zip_code",
]


def search_properties(query: str, num_results: int = 12, filters: dict | None = None) -> list[dict]:
    """Run a Vector Search similarity query and return matching properties."""
    vsc = VectorSearchClient()
    index = vsc.get_index(endpoint_name=VS_ENDPOINT_NAME, index_name=VS_INDEX_NAME)

    filter_string = None
    if filters:
        parts = []
        for key, value in filters.items():
            if value is not None and value != "All":
                if isinstance(value, str):
                    parts.append(f"{key} = '{value}'")
                elif isinstance(value, (list, tuple)) and len(value) == 2:
                    parts.append(f"{key} >= {value[0]} AND {key} <= {value[1]}")
        if parts:
            filter_string = " AND ".join(parts)

    results = index.similarity_search(
        query_text=query,
        columns=SEARCH_COLUMNS,
        num_results=num_results,
        filters_json=filter_string,
    )

    rows = results.get("result", {}).get("data_array", [])
    columns = [col["name"] for col in results.get("manifest", {}).get("columns", [])]

    properties = []
    for row in rows:
        prop = dict(zip(columns, row))
        if isinstance(prop.get("features"), str):
            prop["features"] = [f.strip() for f in prop["features"].strip("[]").replace("'", "").split(",")]
        properties.append(prop)

    return properties


def _build_context(properties: list[dict]) -> str:
    """Format retrieved properties into context for the LLM."""
    if not properties:
        return "No properties found matching the search criteria."

    lines = []
    for i, p in enumerate(properties[:6], 1):
        lines.append(
            f"{i}. {p.get('address', 'N/A')}, {p.get('city', '')}, {p.get('state', '')} — "
            f"${p.get('price', 0):,.0f} | {p.get('beds', 0)} bed / {p.get('baths', 0)} bath | "
            f"{p.get('sqft', 0):,} sqft | {p.get('property_type', '')} | "
            f"School: {p.get('school_rating', 'N/A')}/10 | Walk: {p.get('walk_score', 'N/A')}\n"
            f"   {p.get('description', '')}"
        )
    return "\n\n".join(lines)


def chat_with_rag(
    user_message: str,
    chat_history: list[dict],
    search_results: list[dict] | None = None,
) -> str:
    """Generate a response using Foundation Model API with optional RAG context."""
    host = get_databricks_host()
    token = get_token()

    client = OpenAI(
        api_key=token,
        base_url=f"{host}/serving-endpoints",
    )

    system_prompt = (
        "You are a knowledgeable and friendly AI real estate assistant for Zillow. "
        "Help users find homes, understand neighborhoods, and make informed decisions. "
        "Use the provided property listings as context when available. "
        "Be concise but helpful. Format prices with commas. "
        "If you don't have specific data, say so honestly."
    )

    if search_results:
        context = _build_context(search_results)
        system_prompt += f"\n\nHere are relevant property listings:\n{context}"

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history[-10:])  # keep last 10 messages
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
    )

    return response.choices[0].message.content


def stream_chat_with_rag(
    user_message: str,
    chat_history: list[dict],
    search_results: list[dict] | None = None,
):
    """Stream a response using Foundation Model API with optional RAG context."""
    host = get_databricks_host()
    token = get_token()

    client = OpenAI(
        api_key=token,
        base_url=f"{host}/serving-endpoints",
    )

    system_prompt = (
        "You are a knowledgeable and friendly AI real estate assistant for Zillow. "
        "Help users find homes, understand neighborhoods, and make informed decisions. "
        "Use the provided property listings as context when available. "
        "Be concise but helpful. Format prices with commas. "
        "If you don't have specific data, say so honestly."
    )

    if search_results:
        context = _build_context(search_results)
        system_prompt += f"\n\nHere are relevant property listings:\n{context}"

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history[-10:])
    messages.append({"role": "user", "content": user_message})

    stream = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
