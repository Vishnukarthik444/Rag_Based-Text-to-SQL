from dataclasses import dataclass

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from .config import EMBEDDING_MODEL


@dataclass(frozen=True)
class SchemaDoc:
    title: str
    content: str


SCHEMA_DOCS = [
    SchemaDoc(
        "sales fact table",
        """
        Table sales contains one row per order line. Columns: order_id primary key,
        order_date joins calendar.date, product_id joins products.product_id,
        store_id joins stores.store_id, customer_id joins customers.customer_id,
        quantity, unit_price, discount, revenue, cost, profit.
        Use sales for revenue, profit, order count, quantity sold, discounts and trends.
        """,
    ),
    SchemaDoc(
        "customers dimension",
        """
        Table customers contains customer attributes. Columns: customer_id primary key,
        age, gender, loyalty_member, join_date. Join with sales on customer_id.
        Use for top customers, loyalty analysis, age groups and gender breakdown.
        """,
    ),
    SchemaDoc(
        "products dimension",
        """
        Table products contains product details. Columns: product_id primary key,
        product_name, brand, category, cocoa_percent, weight_g. Join with sales on product_id.
        Use LEFT JOIN products when preserving all sales rows because sales has P0000
        and P0201 missing in products. Use for category, brand, product and cocoa analysis.
        """,
    ),
    SchemaDoc(
        "stores dimension",
        """
        Table stores contains store details. Columns: store_id primary key, store_name,
        city, country, store_type. Join with sales on store_id.
        Use for city, country, online, mall, airport and retail store analysis.
        """,
    ),
    SchemaDoc(
        "calendar dimension",
        """
        Table calendar contains date attributes. Columns: date primary key, year, month,
        day, week, day_of_week. Join sales.order_date to calendar.date.
        Use for monthly, yearly, weekly and day-of-week sales trends.
        """,
    ),
    SchemaDoc(
        "example top customers by revenue",
        """
        SELECT s.customer_id, c.age, c.gender, c.loyalty_member,
               SUM(s.revenue) AS total_revenue
        FROM sales s
        JOIN customers c ON s.customer_id = c.customer_id
        GROUP BY s.customer_id, c.age, c.gender, c.loyalty_member
        ORDER BY total_revenue DESC
        LIMIT 5;
        """,
    ),
    SchemaDoc(
        "example product category revenue",
        """
        SELECT COALESCE(p.category, 'Unknown') AS category,
               SUM(s.revenue) AS total_revenue,
               SUM(s.profit) AS total_profit
        FROM sales s
        LEFT JOIN products p ON s.product_id = p.product_id
        GROUP BY COALESCE(p.category, 'Unknown')
        ORDER BY total_revenue DESC;
        """,
    ),
    SchemaDoc(
        "example monthly revenue trend",
        """
        SELECT c.year, c.month, SUM(s.revenue) AS total_revenue
        FROM sales s
        JOIN calendar c ON s.order_date = c.date
        GROUP BY c.year, c.month
        ORDER BY c.year, c.month;
        """,
    ),
    SchemaDoc(
        "example store country performance",
        """
        SELECT st.country, st.store_type,
               SUM(s.revenue) AS total_revenue,
               SUM(s.profit) AS total_profit
        FROM sales s
        JOIN stores st ON s.store_id = st.store_id
        GROUP BY st.country, st.store_type
        ORDER BY total_revenue DESC;
        """,
    ),
]


class SchemaRetriever:
    def __init__(self, docs: list[SchemaDoc] | None = None) -> None:
        self.docs = docs or SCHEMA_DOCS
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.texts = [f"{doc.title}\n{doc.content.strip()}" for doc in self.docs]
        embeddings = self.model.encode(self.texts, normalize_embeddings=True)
        self.embeddings = np.asarray(embeddings, dtype="float32")
        self.index = faiss.IndexFlatIP(self.embeddings.shape[1])
        self.index.add(self.embeddings)

    def retrieve(self, question: str, top_k: int = 4) -> list[SchemaDoc]:
        query = self.model.encode([question], normalize_embeddings=True)
        query = np.asarray(query, dtype="float32")
        _, indexes = self.index.search(query, top_k)
        return [self.docs[index] for index in indexes[0] if index >= 0]
