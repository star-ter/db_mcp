# db-mcp

PostgreSQL SQL문을 실행하는 MCP 서버입니다.

## 설정

`.env`로 DSN을 지정하세요.

```bash
POSTGRES_DSN=postgresql://user:password@host:5432/dbname
TOKEN=your_mcp_token
```

## 실행

```bash
uv sync
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## MCP Tool

- `execute_sql(sql: str)` : 읽기 전용 SQL(SELECT/WITH, 단일 문장)만 실행합니다.
