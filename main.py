import os

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("db-mcp")

load_dotenv()


def _get_dsn() -> str:
    dsn = os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("POSTGRES_DSN 또는 DATABASE_URL 환경변수가 필요합니다.")
    return dsn


@mcp.tool()
def execute_sql(sql: str) -> dict:
    """PostgreSQL SQL문을 실행하고 결과를 반환합니다."""
    try:
        with psycopg.connect(_get_dsn(), row_factory=dict_row) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
                cur.execute(sql)
                if cur.description:
                    rows = cur.fetchall()
                    return {"rows": rows, "rowcount": cur.rowcount}
                return {"rows": [], "rowcount": cur.rowcount}
    except Exception as exc:
        return {"error": str(exc)}


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
