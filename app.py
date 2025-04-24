import streamlit as st
import psycopg2
import pandas as pd

# 🎯 PostgreSQL connection details (Render)
DB_HOST = "dpg-d059t0p5pdvs73etvfq0-a.virginia-postgres.render.com"
DB_NAME = "dmql_project"
DB_USER = "dmql_project_user"
DB_PASS = "RDrsV0Oms363s3RuGJPGLN3y4sFZKCaI"
DB_PORT = 5432

# 🧠 Cache DB connection
@st.cache_resource
def connect():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )

# 🌐 Page config
st.set_page_config(page_title="🏥 Hospital Database Explorer", layout="wide")


st.title("🏥 Hospital Database Explorer")
st.caption("Connected to Render PostgreSQL")

# 🔌 Connect to DB
conn = connect()

# 📂 Get list of tables
try:
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = [row[0] for row in cur.fetchall()]
    cur.close()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

# 🧭 Tabs for navigation
tab1, tab2 = st.tabs(["📋 Table Viewer", "🧠 Custom SQL Query"])

# 📋 Table Viewer tab
with tab1:
    st.subheader("🗃️ Browse Tables")
    selected_table = st.selectbox("Choose a table to preview:", tables)

    if selected_table:
        try:
            df = pd.read_sql_query(f'SELECT * FROM "{selected_table}" LIMIT 100', conn)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to load table: {e}")

# 🧠 Custom SQL Query tab
with tab2:
    st.subheader("💬 Write a SQL SELECT query")
    default_query = f'SELECT * FROM "{tables[0]}" LIMIT 10' if tables else ""
    user_query = st.text_area("Write your SQL query below:", default_query, height=150)

    # Track query result in session state to preserve it across interactions
    if "query_df" not in st.session_state:
        st.session_state.query_df = pd.DataFrame()

    if st.button("▶️ Run Query"):
        lowered = user_query.strip().lower()
        if "select" not in lowered:
            st.error("❌ Only SELECT queries are allowed.")
        else:
            try:
                st.session_state.query_df = pd.read_sql_query(user_query, conn)
                st.success("✅ Query executed successfully!")
            except Exception as e:
                st.session_state.query_df = pd.DataFrame()
                st.error(f"⚠️ Query failed: {e}")

    # Show results if they exist
    if not st.session_state.query_df.empty:
        st.dataframe(st.session_state.query_df, use_container_width=True)

        # 💾 Download CSV
        csv = st.session_state.query_df.to_csv(index=False).encode("utf-8")
        st.download_button("💾 Download Results as CSV", csv, "query_results.csv", "text/csv")

        # 📊 Visualization
        st.markdown("---")
        st.subheader("📈 Visualize Query Results")

        numeric_cols = st.session_state.query_df.select_dtypes(include=["number"]).columns.tolist()
        all_cols = st.session_state.query_df.columns.tolist()

        if numeric_cols:
            x_axis = st.selectbox("🧭 Select X-axis", options=all_cols, index=0, key="x_axis")
            y_axis = st.selectbox("📊 Select Y-axis (numeric only)", options=numeric_cols, index=0, key="y_axis")
            chart_type = st.radio("📈 Chart Type", ["Bar Chart", "Line Chart"], horizontal=True, key="chart_type")

            if chart_type == "Bar Chart":
                st.bar_chart(st.session_state.query_df.set_index(x_axis)[y_axis])
            elif chart_type == "Line Chart":
                st.line_chart(st.session_state.query_df.set_index(x_axis)[y_axis])
        else:
            st.info("No numeric columns available for visualization.")
