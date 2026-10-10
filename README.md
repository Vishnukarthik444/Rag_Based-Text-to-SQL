RAG-Based Text-to-SQL System

An LLM-powered application that converts natural-language questions into SQL queries using Retrieval-Augmented Generation (RAG), allowing users to interact with relational databases without writing SQL manually.

🚀 Features

* Natural Language to SQL: Convert plain-English questions into SQL queries.
* RAG Pipeline: Retrieve relevant database schemas and example queries.
* Vector Search: Find relevant context using FAISS.
* LLM Integration: Generate SQL using Mistral-7B-Instruct.
* Query Execution: Execute SQL against PostgreSQL.
* Results & Visualization: Present query results in tables and charts, where supported.

🛠️ Tech Stack

* Language: Python
* LLM: Mistral-7B-Instruct
* Embeddings: all-MiniLM-L6-v2
* Vector Search: FAISS
* Database: PostgreSQL
* Concepts: RAG, Embeddings, Text-to-SQL

🔄 Project Workflow

                 USER QUESTION
                       |
                       v
             Question Processing
                       |
                       v
           Schema and Context Retrieval
                       |
                       v
              Vector Search / RAG
                       |
                       v
              LLM-Based SQL Generation
                       |
                       v
                SQL Validation
                       |
                       v
                Query Execution
                       |
                       v
              Results and Explanation
                       |
                       v
              Table / Chart Output

Workflow Explanation

1. User Input

The user enters a question in natural language, such as:

What are the total sales for each product category?

2. Context Retrieval

The system retrieves relevant database schema details and, where available, example SQL queries that can help the model understand the database structure.

3. Context Augmentation

The retrieved information is incorporated into the model’s prompt to ground SQL generation in the available database context.

4. SQL Generation

The LLM generates an SQL query based on the user’s question and the retrieved context.

5. Validation and Execution

The generated query can be checked for validity and safety before being executed against the configured database.

6. Result Presentation

The application presents the query results in a structured format and can provide a natural-language explanation or visualization when those features are available.