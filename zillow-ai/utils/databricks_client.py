"""Shared Databricks SDK initialization."""

import os
from functools import lru_cache
from databricks.sdk import WorkspaceClient


@lru_cache(maxsize=1)
def get_workspace_client() -> WorkspaceClient:
    """Return a cached Databricks WorkspaceClient.

    When running as a Databricks App, authentication is automatic.
    For local development, set DATABRICKS_HOST and DATABRICKS_TOKEN env vars.
    """
    return WorkspaceClient()


def get_databricks_host() -> str:
    """Return the Databricks workspace host URL."""
    client = get_workspace_client()
    return client.config.host


def get_token() -> str:
    """Return the current auth token (for OpenAI-compatible client)."""
    client = get_workspace_client()
    header = client.config.authenticate()
    return header.get("Authorization", "").replace("Bearer ", "")
