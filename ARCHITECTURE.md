# Architecture

## Stack

- Backend: Python
- LLM: Hugging Face `mistralai/Mistral-7B-Instruct-v0.3`
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- Vector DB: FAISS
- Database: PostgreSQL
- UI: Streamlit

The project intentionally uses a direct implementation. This keeps the RAG flow explicit, reduces dependency issues, and makes the app easier to run and explain.

## Tables

- `sales`: central fact table for revenue, profit, cost, orders and quantity
- `customers`: customer age, gender, loyalty and join date
- `products`: product name, brand, category, cocoa percent and weight
- `stores`: store name, city, country and store type
- `calendar`: date attributes for time-series analysis

## Workflow

```text
1. User enters a natural-language query
2. RAG retrieves schema and example SQL from FAISS
3. Mistral converts the query into PostgreSQL SQL
4. SQL validation blocks unsafe commands and unknown tables
5. SQL executes on PostgreSQL
6. Results are returned as a table
7. The app generates an automatic chart
8. The app generates a short explanation
9. If SQL execution fails, the agent asks Mistral to correct the SQL and retries once

If the Hugging Face call is unavailable, the LLM layer falls back to safe local SQL templates for common retail analytics questions.
```

## Output

- SQL query
- Result table
- Chart
- Explanation
