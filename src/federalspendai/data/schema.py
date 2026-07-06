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
    "public_accounts": "ac597ff8-ee13-48c3-b315-42e528090af2",
}

# Fallback direct URLs when CKAN discovery fails
FALLBACK_CSV_URLS: dict[str, list[str]] = {
    "awards": [
        "https://canadabuys.canada.ca/opendata/pub/awardNoticeComplete-avisAttributionComplet.csv",
    ],
    "contract_history": [
        "https://canadabuys.canada.ca/opendata/pub/contractHistoryComplete-historiqueContratsComplet.csv",
    ],
    "public_accounts": [
        "https://donnees-data.tpsgc-pwgsc.gc.ca/ba1/idsps-dipss/idsps-dipss-2024.csv",
    ],
}

PUBLIC_ACCOUNTS_COLUMN_MAP: dict[str, str] = {
    "Fscl-yr_Ex-fin": "fiscal_year",
    "Dept-name_Nom-min_eng": "department",
    "Dept-name_Nom-min_fra": "department_fra",
    "Rpt-obj_Art-rppt_eng": "service_class",
    "Rpt-obj_Art-rppt_fra": "service_class_fra",
    "Proj-desc_eng": "payee",
    "Proj-desc_fra": "payee_fra",
    "Xpnd-current-yr_Dep-ex-courant": "expenditure_current_year",
    "Aggregate-payments_Versements-totalisant": "aggregate_payment",
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

PUBLIC_ACCOUNTS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS public_accounts (
    id VARCHAR PRIMARY KEY,
    fiscal_year VARCHAR,
    department VARCHAR,
    service_class VARCHAR,
    payee VARCHAR,
    amount DOUBLE,
    source_url VARCHAR,
    ingested_at TIMESTAMP DEFAULT now()
);
"""

EMBEDDINGS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS contract_embeddings (
    reference_number VARCHAR PRIMARY KEY,
    model VARCHAR NOT NULL,
    embedding DOUBLE[],
    text_hash VARCHAR,
    updated_at TIMESTAMP DEFAULT now()
);
"""

VENDOR_LINKS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS vendor_payee_links (
    vendor VARCHAR,
    payee VARCHAR,
    link_confidence DOUBLE,
    method VARCHAR,
    updated_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (vendor, payee)
);
"""

SPENDING_ANOMALIES_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS spending_anomalies (
    anomaly_id VARCHAR PRIMARY KEY,
    anomaly_type VARCHAR NOT NULL,
    department VARCHAR,
    vendor VARCHAR,
    month VARCHAR NOT NULL,
    observed_amount DOUBLE,
    baseline_mean DOUBLE,
    z_score DOUBLE,
    contract_count INTEGER,
    sample_contracts VARCHAR,
    evidence_fingerprint VARCHAR NOT NULL,
    anomaly_status VARCHAR DEFAULT 'open',
    investigation_status VARCHAR DEFAULT 'pending',
    investigation_fingerprint VARCHAR,
    investigation_report VARCHAR,
    first_seen_at TIMESTAMP DEFAULT now(),
    last_seen_at TIMESTAMP DEFAULT now(),
    last_updated_at TIMESTAMP DEFAULT now(),
    last_investigated_at TIMESTAMP
);
"""
