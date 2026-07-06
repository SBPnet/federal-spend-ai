"""Pydantic models and bilingual column mappings for open government CSVs."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

# CanadaBuys award notice: bilingual header -> canonical field
AWARD_COLUMN_MAP: dict[str, str] = {
    "title-titre-eng": "title_eng",
    "title-titre-fra": "title_fra",
    "referenceNumber-numeroReference": "reference_number",
    "amendmentNumber-numeroModification": "amendment_number",
    "solicitationNumber-numeroSollicitation": "solicitation_number",
    "contractNumber-numeroContrat": "contract_number",
    "publicationDate-datePublication": "publication_date",
    "contractAwardDate-dateAttributionContrat": "contract_award_date",
    "amendmentDate-dateModification": "amendment_date",
    "contractStartDate-contratDateDebut": "contract_start_date",
    "contractEndDate-dateFinContrat": "contract_end_date",
    "contractAmount-montantContrat": "contract_amount",
    "totalContractValue-valeurTotaleContrat": "total_contract_value",
    "contractCurrency-contratMonnaie": "contract_currency",
    "awardStatus-attributionStatut-eng": "award_status",
    "awardStatus-attributionStatut-fra": "award_status_fra",
    "unspsc": "unspsc",
    "unspscDescription-eng": "unspsc_description_eng",
    "unspscDescription-fra": "unspsc_description_fra",
    "procurementCategory-categorieApprovisionnement": "procurement_category",
    "procurementMethod-methodeApprovisionnement-eng": "procurement_method",
    "procurementMethod-methodeApprovisionnement-fra": "procurement_method_fra",
    "supplierLegalName-nomLegalFournisseur-eng": "vendor",
    "supplierLegalName-nomLegalFournisseur-fra": "vendor_fra",
    "contractingEntityName-nomEntitContractante-eng": "department",
    "contractingEntityName-nomEntitContractante-fra": "department_fra",
    "awardDescription-descriptionAttribution-eng": "description_eng",
    "awardDescription-descriptionAttribution-fra": "description_fra",
}

# Known CKAN package IDs for official datasets
DATASET_PACKAGES: dict[str, str] = {
    "awards": "a1acb126-9ce8-40a9-b889-5da2b1dd20cb",
    "contract_history": "4fe645a1-ffcd-40c1-9385-2c771be956a4",
    "proactive": "d8f85d91-7dec-4fd1-8055-483b77225d8b",
}

# Fallback direct URLs when CKAN discovery fails
FALLBACK_CSV_URLS: dict[str, list[str]] = {
    "awards": [
        "https://canadabuys.canada.ca/opendata/pub/awardNoticeComplete-avisAttributionComplet.csv",
    ],
    "contract_history": [
        "https://canadabuys.canada.ca/opendata/pub/contractHistoryComplete-historiqueContratsComplet.csv",
    ],
}


class AwardRecord(BaseModel):
    """Normalized award / contract row."""

    reference_number: str
    title_eng: str | None = None
    title_fra: str | None = None
    contract_number: str | None = None
    solicitation_number: str | None = None
    vendor: str | None = None
    department: str | None = None
    contract_amount: float | None = None
    total_contract_value: float | None = None
    contract_currency: str | None = None
    publication_date: date | None = None
    contract_award_date: date | None = None
    contract_start_date: date | None = None
    contract_end_date: date | None = None
    award_status: str | None = None
    unspsc: str | None = None
    unspsc_description_eng: str | None = None
    procurement_category: str | None = None
    procurement_method: str | None = None
    description_eng: str | None = None
    source_dataset: str = "awards"
    source_url: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


AWARDS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS awards (
    reference_number VARCHAR PRIMARY KEY,
    title_eng VARCHAR,
    title_fra VARCHAR,
    contract_number VARCHAR,
    solicitation_number VARCHAR,
    vendor VARCHAR,
    department VARCHAR,
    contract_amount DOUBLE,
    total_contract_value DOUBLE,
    contract_currency VARCHAR,
    publication_date DATE,
    contract_award_date DATE,
    contract_start_date DATE,
    contract_end_date DATE,
    award_status VARCHAR,
    unspsc VARCHAR,
    unspsc_description_eng VARCHAR,
    procurement_category VARCHAR,
    procurement_method VARCHAR,
    description_eng VARCHAR,
    source_dataset VARCHAR,
    source_url VARCHAR,
    ingested_at TIMESTAMP DEFAULT now()
);
"""

INGEST_RUNS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS ingest_runs (
    id BIGINT PRIMARY KEY,
    dataset VARCHAR NOT NULL,
    source_url VARCHAR NOT NULL,
    checksum VARCHAR,
    row_count INTEGER,
    status VARCHAR NOT NULL,
    message VARCHAR,
    started_at TIMESTAMP DEFAULT now(),
    finished_at TIMESTAMP
);
"""
