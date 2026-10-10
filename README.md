# RAG-Based Text-to-SQL System

A Streamlit app that converts natural-language retail analytics questions into PostgreSQL queries using RAG-based schema retrieval and a Hugging Face LLM.

## Tech Stack

- Python
- Streamlit
- PostgreSQL
- Hugging Face `mistralai/Mistral-7B-Instruct-v0.3` 
- `all-MiniLM-L6-v2` embeddings
- FAISS vector search

## Features

- Natural language to SQL
- RAG-based schema retrieval
- SQL safety validation
- PostgreSQL query execution
- Result table
- Automatic chart generation
- Query explanation
- Self-correction retry for failed SQL
- Local fallback SQL templates when the Hugging Face call is unavailable

## Architecture

```text
Streamlit UI
    -> Agent Controller
        -> FAISS Schema Retriever
        -> Hugging Face Mistral LLM
        -> SQL Safety Validator
        -> PostgreSQL Executor
        -> Chart and Explanation Generator
```

## Project Flow

```text
1. User enters a natural-language query
2. Relevant schema and SQL examples are retrieved using FAISS
3. Mistral generates a PostgreSQL SELECT query
4. SQL validator blocks unsafe or invalid operations
5. Query runs on PostgreSQL
6. Results are returned as a dataframe
7. Chart and explanation are generated
8. UI displays results, chart, SQL, and explanation
```

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a `.env` file:

```env
HF_API_TOKEN=your_huggingface_token_here
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.3
DATABASE_URL=postgresql+psycopg2://postgres:your_password@localhost:5432/retail_db
```

Create a PostgreSQL database named `retail_db`, then load the dataset:

```powershell
python -m scripts.load_postgres
```

## Run

```powershell
python -m streamlit run app.py
```

Open the local Streamlit URL shown in the terminal.

## Project Structure

```text
app.py                 Streamlit UI
src/agent.py           RAG SQL agent orchestration
src/llm.py             Hugging Face call, SQL prompts and fallback SQL
src/schema_rag.py      Schema docs and FAISS retrieval
src/sql_guard.py       SQL safety validation
src/data_loader.py     PostgreSQL setup and CSV loading
src/visualization.py   Charts and result explanation
src/ui.py              Shared Streamlit UI helpers
scripts/load_postgres.py Dataset loading command
```

## Output

For each user query, the app returns:

- Generated SQL query
- Result table
- Chart
- Explanation
