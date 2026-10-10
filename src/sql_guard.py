import re


ALLOWED_TABLES = {"sales", "customers", "products", "stores", "calendar"}
BLOCKED_WORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "truncate",
    "replace",
    "attach",
    "detach",
    "pragma",
    "vacuum",
    "grant",
    "revoke",
}


def normalize_sql(sql: str) -> str:
    return re.sub(r"\s+", " ", sql.strip()).rstrip(";") + ";"


def validate_sql(sql: str) -> str:
    cleaned = normalize_sql(sql)
    lowered = cleaned.lower()

    if "--" in lowered or "/*" in lowered:
        raise ValueError("SQL comments are not allowed.")

    if not lowered.startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    if ";" in cleaned[:-1]:
        raise ValueError("Only one SQL statement is allowed.")

    tokens = set(re.findall(r"\b[a-z_]+\b", lowered))
    blocked = tokens.intersection(BLOCKED_WORDS)
    if blocked:
        raise ValueError(f"Unsafe SQL keyword blocked: {', '.join(sorted(blocked))}")

    mentioned_tables = set(
        match.group(1)
        for match in re.finditer(r"\b(?:from|join)\s+([a-z_][a-z0-9_]*)", lowered)
    )
    unknown_tables = mentioned_tables - ALLOWED_TABLES
    if unknown_tables:
        raise ValueError(f"Unknown table: {', '.join(sorted(unknown_tables))}")

    return cleaned
