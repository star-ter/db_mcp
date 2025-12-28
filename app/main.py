import os

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from starlette.responses import JSONResponse

load_dotenv()

verifier = StaticTokenVerifier(tokens={os.getenv("TOKEN"): {
    "client_id": "openAI",
    "scopes": [],
}})

mcp = FastMCP("db-mcp", auth=verifier)


def _get_dsn() -> str:
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        raise RuntimeError("POSTGRES_DSN 환경변수가 필요합니다.")
    return dsn


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "mcp-server"})


@mcp.tool
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


app = mcp.http_app()
