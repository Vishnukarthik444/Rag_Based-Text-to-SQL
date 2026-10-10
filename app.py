import streamlit as st

from src.agent import RetailSqlAgent
from src.ui import apply_page_style, render_database_sidebar, render_example_buttons
from src.visualization import choose_chart


st.set_page_config(
    page_title="Agentic RAG SQL Retail Analytics",
    layout="wide",
)


apply_page_style()


@st.cache_resource(show_spinner="Starting RAG SQL agent...")
def get_agent():
    return RetailSqlAgent()


if "history" not in st.session_state:
    st.session_state.history = []


render_database_sidebar()


st.title("Agentic RAG-Based Natural Language to SQL")
st.caption("Natural language -> RAG schema retrieval -> Mistral SQL -> validation -> PostgreSQL -> chart and explanation")

selected_example = render_example_buttons()
if selected_example:
    st.session_state.pending_question = selected_example

for item in st.session_state.history:
    with st.chat_message("user"):
        st.write(item["question"])
    with st.chat_message("assistant"):
        st.write(item["explanation"])

question = st.chat_input("Ask a retail analytics question")
if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        try:
            agent = get_agent()
            with st.spinner("Retrieving schema, generating SQL, validating, and executing..."):
                result = agent.answer(question)

            st.write(result["explanation"])
            result_tab, chart_tab, sql_tab, explanation_tab = st.tabs(
                ["Results", "Chart", "SQL", "Explanation"]
            )

            with result_tab:
                st.dataframe(result["dataframe"], use_container_width=True, hide_index=True)

            with chart_tab:
                chart = choose_chart(result["dataframe"])
                if chart is None:
                    st.info("No chart was generated because the result does not contain a suitable numeric field.")
                else:
                    st.plotly_chart(chart, use_container_width=True)

            with sql_tab:
                st.code(result["sql"], language="sql")
                st.caption(f"SQL source: {result['source']}")
                with st.expander("Retrieved schema and examples"):
                    for doc in result["retrieved_docs"]:
                        st.markdown(f"**{doc.title}**")
                        st.write(doc.content.strip())

            with explanation_tab:
                st.write(result["explanation"])
                st.markdown("**Agent steps**")
                for attempt in result["attempts"]:
                    st.write(attempt)

            st.session_state.history.append(
                {
                    "question": question,
                    "sql": result["sql"],
                    "explanation": result["explanation"],
                }
            )
        except Exception as exc:
            st.error("The agent could not complete the query.")
            st.code(str(exc), language=None)
