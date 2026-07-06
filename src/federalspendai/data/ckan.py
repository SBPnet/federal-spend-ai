"""CKAN Action API client for open.canada.ca."""

from __future__ import annotations

from typing import Any

import httpx

from federalspendai.config import Settings, get_settings


class CKANClient:
  """Thin wrapper around the Canada Open Data CKAN API."""

  def __init__(self, settings: Settings | None = None) -> None:
    self.settings = settings or get_settings()
    self.base_url = self.settings.ckan_base_url.rstrip("/")

  def _get(self, action: str, **params: Any) -> dict[str, Any]:
    url = f"{self.base_url}/{action}"
    with httpx.Client(timeout=self.settings.request_timeout) as client:
      response = client.get(url, params=params)
      response.raise_for_status()
      payload = response.json()
    if not payload.get("success"):
      raise RuntimeError(f"CKAN {action} failed: {payload}")
    return payload["result"]

  def package_show(self, package_id: str) -> dict[str, Any]:
    return self._get("package_show", id=package_id)

  def list_csv_resources(self, package_id: str) -> list[dict[str, Any]]:
    package = self.package_show(package_id)
    resources: list[dict[str, Any]] = []
    for resource in package.get("resources", []):
      fmt = (resource.get("format") or "").upper()
      url = resource.get("url") or ""
      if fmt == "CSV" and url:
        resources.append(resource)
    return resources
