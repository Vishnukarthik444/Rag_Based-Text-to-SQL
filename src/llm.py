import re

from huggingface_hub import InferenceClient

from .config import HF_API_TOKEN, HF_MODEL


def build_prompt(question: str, context: str) -> str:
    return f"""<s>[INST]
You are an expert PostgreSQL text-to-SQL agent for retail analytics.

Rules:
- Generate exactly one safe SELECT query.
- Use only these tables: sales, customers, products, stores, calendar.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, PRAGMA, ATTACH, DETACH.
- Prefer explicit JOINs.
- Use LEFT JOIN products when product details are needed, because two sales product IDs are missing in products.
- Add LIMIT 500 when the query returns detail rows.
- Return only SQL, no markdown.

Retrieved schema context:
{context}

User question: {question}
[/INST]"""


def build_correction_prompt(question: str, context: str, sql: str, error: str) -> str:
    return f"""<s>[INST]
You are a PostgreSQL SQL repair agent.

Fix the failed SQL query.

Rules:
- Return exactly one safe SELECT query.
- Use only these tables: sales, customers, products, stores, calendar.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE.
- Return only SQL, no markdown.

Retrieved schema context:
{context}

Original user question: {question}

Failed SQL:
{sql}

Database error:
{error}
[/INST]"""


def extract_sql(text: str) -> str:
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", text, flags=re.I | re.S)
    if fenced:
        text = fenced.group(1)
    select_pos = text.lower().find("select")
    if select_pos >= 0:
        text = text[select_pos:]
    return text.strip().rstrip(";") + ";"


def _call_huggingface(prompt: str) -> str | None:
    if not HF_API_TOKEN:
        return None

    # The chat completions API applies the model's own [INST] template,
    # so the manual tags are removed before sending.
    clean_prompt = prompt.replace("<s>[INST]", "").replace("[/INST]", "").strip()

    client = InferenceClient(api_key=HF_API_TOKEN, timeout=60)
    response = client.chat.completions.create(
        model=HF_MODEL,
        messages=[{"role": "user", "content": clean_prompt}],
        max_tokens=350,
        temperature=0.1,
    )
    generated = response.choices[0].message.content or ""
    return extract_sql(generated)


def call_mistral(question: str, context: str) -> str | None:
    return _call_huggingface(build_prompt(question, context))


def correct_sql(question: str, context: str, sql: str, error: str) -> str | None:
    return _call_huggingface(build_correction_prompt(question, context, sql, error))


def fallback_sql(question: str) -> str:
    q = question.lower()
    wants_bottom = any(word in q for word in ["bottom", "lowest", "least", "worst"])
    wants_top = any(word in q for word in ["top", "highest", "most", "best"])
    sort_direction = "ASC" if wants_bottom else "DESC"
    limit_match = re.search(r"\b(?:top|bottom|limit)\s+(\d+)\b", q)
    limit = min(int(limit_match.group(1)), 500) if limit_match else 10

    if "customer" in q and ("revenue" in q or "sales" in q or wants_top or wants_bottom):
        return f"""
        SELECT s.customer_id, c.age, c.gender, c.loyalty_member,
               ROUND(SUM(s.revenue), 2) AS total_revenue
        FROM sales s
        JOIN customers c ON s.customer_id = c.customer_id
        GROUP BY s.customer_id, c.age, c.gender, c.loyalty_member
        ORDER BY total_revenue {sort_direction}
        LIMIT {limit};
        """

    if "product" in q and ("revenue" in q or "sales" in q) and "category" not in q:
        return f"""
        SELECT COALESCE(p.product_name, 'Unknown') AS product_name,
               ROUND(SUM(s.revenue), 2) AS total_revenue,
               ROUND(SUM(s.profit), 2) AS total_profit
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.product_id
        GROUP BY COALESCE(p.product_name, 'Unknown')
        ORDER BY total_revenue {sort_direction}
        LIMIT 10;
        """

    if "category" in q:
        return f"""
        SELECT COALESCE(p.category, 'Unknown') AS category,
               ROUND(SUM(s.revenue), 2) AS total_revenue,
               ROUND(SUM(s.profit), 2) AS total_profit
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.product_id
        GROUP BY COALESCE(p.category, 'Unknown')
        ORDER BY total_revenue {sort_direction};
        """

    if "brand" in q:
        return f"""
        SELECT COALESCE(p.brand, 'Unknown') AS brand,
               ROUND(SUM(s.revenue), 2) AS total_revenue,
               ROUND(SUM(s.profit), 2) AS total_profit
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.product_id
        GROUP BY COALESCE(p.brand, 'Unknown')
        ORDER BY total_revenue {sort_direction};
        """

    if "month" in q or "trend" in q:
        return """
        SELECT c.year, c.month, ROUND(SUM(s.revenue), 2) AS total_revenue
        FROM sales s
        JOIN calendar c ON s.order_date = c.date
        GROUP BY c.year, c.month
        ORDER BY c.year, c.month;
        """

    if "country" in q or "store" in q or "city" in q:
        return """
        SELECT st.country, st.store_type,
               ROUND(SUM(s.revenue), 2) AS total_revenue,
               ROUND(SUM(s.profit), 2) AS total_profit
        FROM sales s
        JOIN stores st ON s.store_id = st.store_id
        GROUP BY st.country, st.store_type
        ORDER BY total_revenue DESC;
        """

    if "profit" in q:
        return """
        SELECT ROUND(SUM(revenue), 2) AS total_revenue,
               ROUND(SUM(cost), 2) AS total_cost,
               ROUND(SUM(profit), 2) AS total_profit,
               ROUND(SUM(profit) * 100.0 / NULLIF(SUM(revenue), 0), 2) AS profit_margin_percent
        FROM sales;
        """

    return """
    SELECT COUNT(*) AS total_orders,
           ROUND(SUM(revenue), 2) AS total_revenue,
           ROUND(SUM(profit), 2) AS total_profit,
           SUM(quantity) AS total_quantity
    FROM sales;
    """


def generate_sql(question: str, context: str) -> tuple[str, str]:
    try:
        sql = call_mistral(question, context)
        if sql:
            return sql, f"{HF_MODEL} via Hugging Face"
    except Exception as exc:
        return fallback_sql(question), f"Fallback template because Hugging Face call failed: {exc}"

    return fallback_sql(question), "Local fallback template; set HF_API_TOKEN to use the LLM"