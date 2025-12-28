# db-mcp

PostgreSQL SQL문을 실행하는 MCP 서버입니다.

## 설정

`.env`로 DSN을 지정하세요.

```bash
POSTGRES_DSN=postgresql://user:password@host:5432/dbname
# 또는
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

## 실행

```bash
uv sync
uv run python main.py
```

## MCP Tool

- `execute_sql(sql: str)` : 읽기 전용 SQL(SELECT/WITH, 단일 문장)만 실행합니다.
