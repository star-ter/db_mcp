import os

from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from starlette.responses import JSONResponse

load_dotenv()

verifier = StaticTokenVerifier(
    tokens={
        os.getenv("TOKEN"): {
            "client_id": "openAI",
            "scopes": [],
        }
    }
)

mcp = FastMCP("db-mcp", auth=verifier, stateless_http=True)


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
    if not sql:
        return {"error": "sql 필드가 필요합니다."}
    try:
        with psycopg.connect(_get_dsn(), row_factory=dict_row) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
                cur.execute(sql)
                if cur.description:
                    rows = cur.fetchall()
                    if len(rows) > 100:
                        return {"error": "결과 행 수가 100개를 초과했습니다."}
                    return {"rows": rows, "rowcount": cur.rowcount}
                return {"rows": [], "rowcount": cur.rowcount}
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool
def get_area_points(div: str, name: str) -> dict:
    """지정된 지역의 x, y 좌표를 반환합니다."""
    try:
        with psycopg.connect(_get_dsn(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                if div == "gu":
                    cur.execute(
                        """
                        SELECT
                        ST_Y(ST_Transform(ST_SetSRID(ST_MakePoint(x, y), 5179), 4326)) AS lat,
                        ST_X(ST_Transform(ST_SetSRID(ST_MakePoint(x, y), 5179), 4326)) AS lng
                        FROM admin_area_gu
                        WHERE REPLACE(adm_nm, ' ', '') ILIKE '%%' || REPLACE(%s, ' ', '') || '%%'
                        ORDER BY length(adm_nm) ASC
                        LIMIT 1
                        """,
                        (name,),
                    )
                elif div == "dong":
                    cur.execute(
                        """
                        SELECT
                        ST_Y(ST_Transform(ST_SetSRID(ST_MakePoint(x, y), 5179), 4326)) AS lat,
                        ST_X(ST_Transform(ST_SetSRID(ST_MakePoint(x, y), 5179), 4326)) AS lng
                        FROM admin_area_dong
                        WHERE REPLACE(adm_nm, ' ', '') ILIKE '%%' || REPLACE(%s, ' ', '') || '%%'
                        ORDER BY length(adm_nm) ASC
                        LIMIT 1
                        """,
                        (name,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT
                        ST_Y(ST_Transform(ST_SetSRID(ST_MakePoint("XCNTS_VALUE", "YDNTS_VALUE"), 5181), 4326)) AS lat,
                        ST_X(ST_Transform(ST_SetSRID(ST_MakePoint("XCNTS_VALUE", "YDNTS_VALUE"), 5181), 4326)) AS lng
                        FROM area_commercial
                        WHERE REPLACE("TRDAR_CD_NM", ' ', '') ILIKE '%%' || REPLACE(%s, ' ', '') || '%%'
                        ORDER BY (CASE WHEN "TRDAR_CD_NM" LIKE '%번%' THEN 1 ELSE 0 END) ASC, length("TRDAR_CD_NM") ASC
                        LIMIT 1
                        """,
                        (name,),
                    )
                rows = cur.fetchone()
                return rows
    except Exception as exc:
        return {"error": str(exc)}


app = mcp.http_app()
