"""DuckDB query layer for federal spending data."""

from __future__ import annotations

from datetime import date
from typing import Any

import duckdb

from federalspendai.config import Settings, get_settings
from federalspendai.data.schema import (
    AWARDS_TABLE_DDL,
    EMBEDDINGS_TABLE_DDL,
    INGEST_RUNS_TABLE_DDL,
    PUBLIC_ACCOUNTS_TABLE_DDL,
    VENDOR_LINKS_TABLE_DDL,
)


class DataStore:
  """Local analytical store backed by DuckDB."""

  def __init__(self, settings: Settings | None = None) -> None:
    self.settings = settings or get_settings()
    self.db_path = self.settings.database_path
    self.db_path.parent.mkdir(parents=True, exist_ok=True)

  def connect(self) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(self.db_path))
    conn.execute(AWARDS_TABLE_DDL)
    conn.execute(INGEST_RUNS_TABLE_DDL)
    conn.execute(PUBLIC_ACCOUNTS_TABLE_DDL)
    conn.execute(EMBEDDINGS_TABLE_DDL)
    conn.execute(VENDOR_LINKS_TABLE_DDL)
    return conn

  def init_schema(self) -> None:
    with self.connect() as conn:
      conn.execute(AWARDS_TABLE_DDL)

  def table_counts(self) -> dict[str, int]:
    with self.connect() as conn:
      awards = conn.execute("SELECT COUNT(*) FROM awards").fetchone()[0]
      runs = conn.execute("SELECT COUNT(*) FROM ingest_runs").fetchone()[0]
      public_accounts = conn.execute("SELECT COUNT(*) FROM public_accounts").fetchone()[0]
      embeddings = conn.execute("SELECT COUNT(*) FROM contract_embeddings").fetchone()[0]
    return {
      "awards": int(awards),
      "ingest_runs": int(runs),
      "public_accounts": int(public_accounts),
      "contract_embeddings": int(embeddings),
    }

  def last_ingest(self, dataset: str | None = None) -> dict[str, Any] | None:
    query = """
      SELECT dataset, source_url, checksum, row_count, status, finished_at
      FROM ingest_runs
    """
    params: list[Any] = []
    if dataset:
      query += " WHERE dataset = ?"
      params.append(dataset)
    query += " ORDER BY finished_at DESC NULLS LAST, id DESC LIMIT 1"
    with self.connect() as conn:
      row = conn.execute(query, params).fetchone()
    if not row:
      return None
    return {
      "dataset": row[0],
      "source_url": row[1],
      "checksum": row[2],
      "row_count": row[3],
      "status": row[4],
      "finished_at": row[5].isoformat() if row[5] else None,
    }

  def upsert_awards(self, rows: list[dict[str, Any]]) -> int:
    if not rows:
      return 0
    columns = [
      "reference_number",
      "title_eng",
      "title_fra",
      "contract_number",
      "solicitation_number",
      "vendor",
      "department",
      "contract_amount",
      "total_contract_value",
      "contract_currency",
      "publication_date",
      "contract_award_date",
      "contract_start_date",
      "contract_end_date",
      "award_status",
      "unspsc",
      "unspsc_description_eng",
      "procurement_category",
      "procurement_method",
      "description_eng",
      "source_dataset",
      "source_url",
    ]
    values = [tuple(row.get(col) for col in columns) for row in rows]
    placeholders = ", ".join(["?"] * len(columns))
    col_list = ", ".join(columns)
    sql = f"""
      INSERT INTO awards ({col_list}, ingested_at)
      VALUES ({placeholders}, now())
      ON CONFLICT (reference_number) DO UPDATE SET
        title_eng = excluded.title_eng,
        title_fra = excluded.title_fra,
        contract_number = excluded.contract_number,
        solicitation_number = excluded.solicitation_number,
        vendor = excluded.vendor,
        department = excluded.department,
        contract_amount = excluded.contract_amount,
        total_contract_value = excluded.total_contract_value,
        contract_currency = excluded.contract_currency,
        publication_date = excluded.publication_date,
        contract_award_date = excluded.contract_award_date,
        contract_start_date = excluded.contract_start_date,
        contract_end_date = excluded.contract_end_date,
        award_status = excluded.award_status,
        unspsc = excluded.unspsc,
        unspsc_description_eng = excluded.unspsc_description_eng,
        procurement_category = excluded.procurement_category,
        procurement_method = excluded.procurement_method,
        description_eng = excluded.description_eng,
        source_dataset = excluded.source_dataset,
        source_url = excluded.source_url,
        ingested_at = now()
    """
    with self.connect() as conn:
      conn.executemany(sql, values)
    return len(rows)

  def record_ingest_run(
    self,
    dataset: str,
    source_url: str,
    checksum: str | None,
    row_count: int,
    status: str,
    message: str | None = None,
  ) -> None:
    with self.connect() as conn:
      next_id = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM ingest_runs").fetchone()[0]
      conn.execute(
        """
        INSERT INTO ingest_runs (id, dataset, source_url, checksum, row_count, status, message, finished_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, now())
        """,
        [next_id, dataset, source_url, checksum, row_count, status, message],
      )

  def search_contracts(
    self,
    *,
    vendor: str | None = None,
    department: str | None = None,
    keyword: str | None = None,
    status: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    award_date_from: date | None = None,
    award_date_to: date | None = None,
    limit: int = 50,
    offset: int = 0,
  ) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if vendor:
      clauses.append("LOWER(vendor) LIKE ?")
      params.append(f"%{vendor.lower()}%")
    if department:
      clauses.append("LOWER(department) LIKE ?")
      params.append(f"%{department.lower()}%")
    if keyword:
      clauses.append(
        "(LOWER(title_eng) LIKE ? OR LOWER(description_eng) LIKE ? OR LOWER(vendor) LIKE ?)"
      )
      kw = f"%{keyword.lower()}%"
      params.extend([kw, kw, kw])
    if status:
      clauses.append("LOWER(award_status) = ?")
      params.append(status.lower())
    if min_amount is not None:
      clauses.append("COALESCE(contract_amount, 0) >= ?")
      params.append(min_amount)
    if max_amount is not None:
      clauses.append("COALESCE(contract_amount, 0) <= ?")
      params.append(max_amount)
    if award_date_from:
      clauses.append("contract_award_date >= ?")
      params.append(award_date_from)
    if award_date_to:
      clauses.append("contract_award_date <= ?")
      params.append(award_date_to)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
      SELECT *
      FROM awards
      {where}
      ORDER BY contract_amount DESC NULLS LAST, contract_award_date DESC NULLS LAST
      LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    with self.connect() as conn:
      result = conn.execute(sql, params)
      columns = [desc[0] for desc in result.description]
      return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]

  def contract_details(self, reference_number: str | None = None, contract_number: str | None = None) -> dict[str, Any] | None:
    if reference_number:
      sql = "SELECT * FROM awards WHERE reference_number = ?"
      param: Any = reference_number
    elif contract_number:
      sql = "SELECT * FROM awards WHERE contract_number = ?"
      param = contract_number
    else:
      return None
    with self.connect() as conn:
      result = conn.execute(sql, [param])
      row = result.fetchone()
      if not row:
        return None
      columns = [desc[0] for desc in result.description]
      return dict(zip(columns, row, strict=True))

  def contract_count(self, group_by: str = "department") -> list[dict[str, Any]]:
    allowed = {"department", "award_status", "procurement_category", "vendor"}
    if group_by not in allowed:
      group_by = "department"
    sql = f"""
      SELECT {group_by} AS group_key, COUNT(*) AS count,
             SUM(COALESCE(contract_amount, 0)) AS total_amount
      FROM awards
      WHERE {group_by} IS NOT NULL AND TRIM({group_by}) != ''
      GROUP BY 1
      ORDER BY total_amount DESC
      LIMIT 100
    """
    with self.connect() as conn:
      rows = conn.execute(sql).fetchall()
    return [
      {"group_key": row[0], "count": row[1], "total_amount": row[2]}
      for row in rows
    ]

  def top_vendors(
    self,
    *,
    department: str | None = None,
    min_amount: float | None = None,
    limit: int = 20,
  ) -> list[dict[str, Any]]:
    clauses = ["vendor IS NOT NULL", "TRIM(vendor) != ''"]
    params: list[Any] = []
    if department:
      clauses.append("LOWER(department) LIKE ?")
      params.append(f"%{department.lower()}%")
    if min_amount is not None:
      clauses.append("COALESCE(contract_amount, 0) >= ?")
      params.append(min_amount)
    where = " AND ".join(clauses)
    sql = f"""
      SELECT vendor,
             COUNT(*) AS contract_count,
             SUM(COALESCE(contract_amount, 0)) AS total_amount
      FROM awards
      WHERE {where}
      GROUP BY vendor
      ORDER BY total_amount DESC
      LIMIT ?
    """
    params.append(limit)
    with self.connect() as conn:
      rows = conn.execute(sql, params).fetchall()
    return [
      {"vendor": row[0], "contract_count": row[1], "total_amount": row[2]}
      for row in rows
    ]

  def spending_by_department(self, limit: int = 50) -> list[dict[str, Any]]:
    sql = """
      SELECT department,
             COUNT(*) AS contract_count,
             SUM(COALESCE(contract_amount, 0)) AS total_amount
      FROM awards
      WHERE department IS NOT NULL AND TRIM(department) != ''
      GROUP BY department
      ORDER BY total_amount DESC
      LIMIT ?
    """
    with self.connect() as conn:
      rows = conn.execute(sql, [limit]).fetchall()
    return [
      {"department": row[0], "contract_count": row[1], "total_amount": row[2]}
      for row in rows
    ]

  def spending_by_category(self, limit: int = 50) -> list[dict[str, Any]]:
    sql = """
      SELECT COALESCE(unspsc_description_eng, procurement_category, unspsc) AS category,
             COUNT(*) AS contract_count,
             SUM(COALESCE(contract_amount, 0)) AS total_amount
      FROM awards
      GROUP BY 1
      HAVING category IS NOT NULL AND TRIM(category) != ''
      ORDER BY total_amount DESC
      LIMIT ?
    """
    with self.connect() as conn:
      rows = conn.execute(sql, [limit]).fetchall()
    return [
      {"category": row[0], "contract_count": row[1], "total_amount": row[2]}
      for row in rows
    ]

  def list_departments(self, limit: int = 100) -> list[dict[str, Any]]:
    sql = """
      SELECT department, COUNT(*) AS contract_count
      FROM awards
      WHERE department IS NOT NULL AND TRIM(department) != ''
      GROUP BY department
      ORDER BY contract_count DESC
      LIMIT ?
    """
    with self.connect() as conn:
      rows = conn.execute(sql, [limit]).fetchall()
    return [{"department": row[0], "contract_count": row[1]} for row in rows]

  def upsert_public_accounts(self, rows: list[dict[str, Any]]) -> int:
    if not rows:
      return 0
    columns = ["id", "fiscal_year", "department", "service_class", "payee", "amount", "source_url"]
    values = [tuple(row.get(col) for col in columns) for row in rows]
    placeholders = ", ".join(["?"] * len(columns))
    col_list = ", ".join(columns)
    sql = f"""
      INSERT INTO public_accounts ({col_list}, ingested_at)
      VALUES ({placeholders}, now())
      ON CONFLICT (id) DO UPDATE SET
        fiscal_year = excluded.fiscal_year,
        department = excluded.department,
        service_class = excluded.service_class,
        payee = excluded.payee,
        amount = excluded.amount,
        source_url = excluded.source_url,
        ingested_at = now()
    """
    with self.connect() as conn:
      conn.executemany(sql, values)
    return len(rows)

  def search_public_accounts(
    self,
    *,
    payee: str | None = None,
    department: str | None = None,
    fiscal_year: str | None = None,
    min_amount: float | None = None,
    limit: int = 50,
    offset: int = 0,
  ) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if payee:
      clauses.append("LOWER(payee) LIKE ?")
      params.append(f"%{payee.lower()}%")
    if department:
      clauses.append("LOWER(department) LIKE ?")
      params.append(f"%{department.lower()}%")
    if fiscal_year:
      clauses.append("fiscal_year = ?")
      params.append(fiscal_year)
    if min_amount is not None:
      clauses.append("amount >= ?")
      params.append(min_amount)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
      SELECT * FROM public_accounts {where}
      ORDER BY amount DESC NULLS LAST
      LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    with self.connect() as conn:
      result = conn.execute(sql, params)
      columns = [desc[0] for desc in result.description]
      return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]

  def list_awards_for_embedding(self, limit: int | None = None) -> list[dict[str, Any]]:
    sql = """
      SELECT reference_number, title_eng, description_eng, vendor, department, contract_amount
      FROM awards
      WHERE title_eng IS NOT NULL OR description_eng IS NOT NULL
      ORDER BY contract_amount DESC NULLS LAST
    """
    params: list[Any] = []
    if limit is not None:
      sql += " LIMIT ?"
      params.append(limit)
    with self.connect() as conn:
      result = conn.execute(sql, params)
      columns = [desc[0] for desc in result.description]
      return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]

  def upsert_embedding(
    self,
    reference_number: str,
    model: str,
    embedding: list[float],
    text_hash: str,
  ) -> None:
    with self.connect() as conn:
      conn.execute(
        """
        INSERT INTO contract_embeddings (reference_number, model, embedding, text_hash, updated_at)
        VALUES (?, ?, ?, ?, now())
        ON CONFLICT (reference_number) DO UPDATE SET
          model = excluded.model,
          embedding = excluded.embedding,
          text_hash = excluded.text_hash,
          updated_at = now()
        """,
        [reference_number, model, embedding, text_hash],
      )

  def get_embeddings(self, model: str | None = None) -> list[dict[str, Any]]:
    sql = "SELECT reference_number, model, embedding, text_hash FROM contract_embeddings"
    params: list[Any] = []
    if model:
      sql += " WHERE model = ?"
      params.append(model)
    with self.connect() as conn:
      result = conn.execute(sql, params)
      columns = [desc[0] for desc in result.description]
      return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]

  def get_embedding_text_hashes(self, model: str) -> dict[str, str]:
    with self.connect() as conn:
      rows = conn.execute(
        "SELECT reference_number, text_hash FROM contract_embeddings WHERE model = ?",
        [model],
      ).fetchall()
    return {row[0]: row[1] for row in rows if row[1]}

  def upsert_vendor_link(self, vendor: str, payee: str, confidence: float, method: str) -> None:
    with self.connect() as conn:
      conn.execute(
        """
        INSERT INTO vendor_payee_links (vendor, payee, link_confidence, method, updated_at)
        VALUES (?, ?, ?, ?, now())
        ON CONFLICT (vendor, payee) DO UPDATE SET
          link_confidence = excluded.link_confidence,
          method = excluded.method,
          updated_at = now()
        """,
        [vendor, payee, confidence, method],
      )

  def get_vendor_links(self, vendor: str | None = None) -> list[dict[str, Any]]:
    if vendor:
      sql = "SELECT * FROM vendor_payee_links WHERE LOWER(vendor) LIKE ? ORDER BY link_confidence DESC"
      params: list[Any] = [f"%{vendor.lower()}%"]
    else:
      sql = "SELECT * FROM vendor_payee_links ORDER BY link_confidence DESC"
      params = []
    with self.connect() as conn:
      result = conn.execute(sql, params)
      columns = [desc[0] for desc in result.description]
      return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]

  def monthly_department_spend(self) -> list[dict[str, Any]]:
    sql = """
      SELECT department,
             strftime(contract_award_date, '%Y-%m') AS month,
             SUM(COALESCE(contract_amount, 0)) AS total_amount,
             COUNT(*) AS contract_count
      FROM awards
      WHERE contract_award_date IS NOT NULL AND department IS NOT NULL
      GROUP BY 1, 2
      ORDER BY 1, 2
    """
    with self.connect() as conn:
      result = conn.execute(sql)
      columns = [desc[0] for desc in result.description]
      return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]

  def vendor_monthly_spend(self, vendor: str | None = None) -> list[dict[str, Any]]:
    clauses = ["contract_award_date IS NOT NULL", "vendor IS NOT NULL"]
    params: list[Any] = []
    if vendor:
      clauses.append("LOWER(vendor) LIKE ?")
      params.append(f"%{vendor.lower()}%")
    where = " AND ".join(clauses)
    sql = f"""
      SELECT vendor,
             strftime(contract_award_date, '%Y-%m') AS month,
             SUM(COALESCE(contract_amount, 0)) AS total_amount,
             COUNT(*) AS contract_count
      FROM awards
      WHERE {where}
      GROUP BY 1, 2
      ORDER BY total_amount DESC
    """
    with self.connect() as conn:
      result = conn.execute(sql, params)
      columns = [desc[0] for desc in result.description]
      return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]
