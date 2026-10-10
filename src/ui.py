import streamlit as st

from .data_loader import get_engine, table_columns, table_counts


PAGE_CSS = """
<style>
.block-container { padding-top: 1.2rem; max-width: 1280px; }
h1, h2, h3 { letter-spacing: 0; }
[data-testid="stMetricValue"] { font-size: 1.35rem; }
</style>
"""


EXAMPLE_QUESTIONS = [
    "Show top 5 customers by revenue",
    "Revenue and profit by product category",
    "Monthly revenue trend",
    "Revenue by country and store type",
    "What is the total profit margin?",
]


@st.cache_data(show_spinner=False)
def get_sidebar_metadata():
    engine = get_engine()
    return table_counts(engine), table_columns(engine)


def apply_page_style() -> None:
    st.markdown(PAGE_CSS, unsafe_allow_html=True)


def render_database_sidebar() -> None:
    with st.sidebar:
        st.title("Database")
        st.caption("PostgreSQL retail analytics schema")
        try:
            counts, columns = get_sidebar_metadata()
            for table, table_columns_list in columns.items():
                with st.expander(
                    f"{table} ({counts.get(table, 0):,})",
                    expanded=table == "sales",
                ):
                    for column in table_columns_list:
                        st.code(column, language=None)
        except Exception as exc:
            st.error("PostgreSQL is not connected or the tables are not loaded.")
            st.code(str(exc), language=None)
            st.info("Set DATABASE_URL, create the database, then run: python -m scripts.load_postgres")


def render_example_buttons() -> str | None:
    selected = None
    example_cols = st.columns(len(EXAMPLE_QUESTIONS))
    for col, example in zip(example_cols, EXAMPLE_QUESTIONS):
        if col.button(example, use_container_width=True):
            selected = example
    return selected
