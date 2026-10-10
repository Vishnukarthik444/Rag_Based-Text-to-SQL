import pandas as pd
from sqlalchemy import text

from .config import MAX_ROWS
from .data_loader import ensure_database, get_engine
from .llm import correct_sql, generate_sql
from .schema_rag import SchemaRetriever
from .sql_guard import validate_sql
from .visualization import explain_result


class RetailSqlAgent:
    def __init__(self) -> None:
        ensure_database()
        self.retriever = SchemaRetriever()

    def _execute(self, sql: str) -> pd.DataFrame:
        engine = get_engine()
        with engine.connect() as conn:
            return pd.read_sql_query(text(sql), conn)

    def answer(self, question: str) -> dict:
        docs = self.retriever.retrieve(question)
        context = "\n\n".join(f"{doc.title}:\n{doc.content.strip()}" for doc in docs)
        sql, source = generate_sql(question, context)
        attempts = []

        try:
            safe_sql = validate_sql(sql)
            df = self._execute(safe_sql)
            attempts.append("Initial SQL validated and executed successfully.")
        except Exception as exc:
            attempts.append(f"Initial SQL failed: {exc}")
            corrected_sql = correct_sql(question, context, sql, str(exc))
            if not corrected_sql:
                raise
            safe_sql = validate_sql(corrected_sql)
            df = self._execute(safe_sql)
            source = f"{source} + self-correction"
            attempts.append("Corrected SQL validated and executed successfully.")

        if len(df) > MAX_ROWS:
            df = df.head(MAX_ROWS)
            attempts.append(f"Displayed first {MAX_ROWS} rows.")

        return {
            "question": question,
            "retrieved_docs": docs,
            "sql": safe_sql,
            "source": source,
            "dataframe": df,
            "explanation": explain_result(question, df, source),
            "attempts": attempts,
        }
