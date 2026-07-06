"""Dataset ingestion orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl

from federalspendai.config import Settings, get_settings
from federalspendai.data.ckan import CKANClient
from federalspendai.data.download import download_file, file_checksum
from federalspendai.data.normalize import awards_frame_to_records
from federalspendai.data.parsers.public_accounts import public_accounts_frame_to_records
from federalspendai.data.schema import DATASET_PACKAGES, FALLBACK_CSV_URLS
from federalspendai.data.store import DataStore

AWARD_DATASETS = {"awards", "contract_history", "proactive"}
PUBLIC_ACCOUNTS_DATASETS = {"public_accounts"}


def resolve_csv_urls(dataset: str, settings: Settings | None = None) -> list[str]:
    """Resolve CSV download URLs via CKAN, with static fallbacks."""
    settings = settings or get_settings()
    package_id = DATASET_PACKAGES.get(dataset)
    if not package_id:
        raise ValueError(f"Unknown dataset: {dataset}")

    try:
        client = CKANClient(settings)
        resources = client.list_csv_resources(package_id)
        urls = [resource["url"] for resource in resources if resource.get("url")]
        if urls:
            return urls
    except Exception:
        pass

    return FALLBACK_CSV_URLS.get(dataset, [])


def _read_csv(path: Path) -> pl.DataFrame:
    return pl.read_csv(
        path,
        infer_schema_length=1000,
        ignore_errors=True,
        truncate_ragged_lines=True,
    )


def ingest_csv_path(
    path: Path,
    dataset: str,
    source_url: str,
    store: DataStore | None = None,
) -> int:
    """Load a local CSV file into DuckDB."""
    store = store or DataStore()
    store.init_schema()
    df = _read_csv(path)

    if dataset in PUBLIC_ACCOUNTS_DATASETS:
        prepared = public_accounts_frame_to_records(df, source_url=source_url)
        count = store.upsert_public_accounts(prepared.to_dicts())
    elif dataset in AWARD_DATASETS:
        prepared = awards_frame_to_records(df, source_dataset=dataset, source_url=source_url)
        count = store.upsert_awards(prepared.to_dicts())
    else:
        raise ValueError(f"Unsupported dataset for ingest: {dataset}")

    checksum = file_checksum(path)
    store.record_ingest_run(dataset, source_url, checksum, count, "success")
    return count


def ingest_dataset(
    dataset: str,
    *,
    settings: Settings | None = None,
    dry_run: bool = False,
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Download and ingest one dataset, or load from a fixture path."""
    settings = settings or get_settings()
    store = DataStore(settings)
    store.init_schema()

    if fixture_path is not None:
        if dry_run:
            return {
                "dataset": dataset,
                "dry_run": True,
                "fixture_path": str(fixture_path),
                "message": "Would ingest fixture file",
            }
        count = ingest_csv_path(fixture_path, dataset, f"fixture://{fixture_path}", store)
        return {"dataset": dataset, "rows": count, "source": str(fixture_path)}

    urls = resolve_csv_urls(dataset, settings)
    if not urls:
        raise RuntimeError(f"No CSV URLs found for dataset '{dataset}'")

    preferred = urls[0]
    for url in urls:
        if dataset == "awards" and ("Complete" in url or "Complet" in url):
            preferred = url
            break
        if dataset == "public_accounts" and "idsps-dipss" in url and url.endswith(".csv"):
            preferred = url
            break

    if dry_run:
        return {
            "dataset": dataset,
            "dry_run": True,
            "source_url": preferred,
            "available_urls": urls[:5],
            "message": "Would download and ingest CSV",
        }

    cache_dir = settings.cache_dir / dataset
    cache_dir.mkdir(parents=True, exist_ok=True)
    filename = preferred.split("/")[-1] or f"{dataset}.csv"
    dest = cache_dir / filename

    checksum = download_file(preferred, dest, settings)
    count = ingest_csv_path(dest, dataset, preferred, store)
    return {
        "dataset": dataset,
        "rows": count,
        "source_url": preferred,
        "checksum": checksum,
        "cache_path": str(dest),
    }


def ingest_all(
    datasets: list[str] | None = None,
    *,
    settings: Settings | None = None,
    dry_run: bool = False,
    fixture_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Ingest multiple datasets."""
    datasets = datasets or ["awards"]
    results: list[dict[str, Any]] = []
    for dataset in datasets:
        fixture_path = None
        if fixture_dir is not None:
            candidate = fixture_dir / f"{dataset}.csv"
            if candidate.exists():
                fixture_path = candidate
        results.append(
            ingest_dataset(
                dataset,
                settings=settings,
                dry_run=dry_run,
                fixture_path=fixture_path,
            )
        )
    return results
