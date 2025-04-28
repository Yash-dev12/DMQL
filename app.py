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
tab1, tab2, tab3 = st.tabs(["📋 Table Viewer", "🧠 Custom SQL Query", "➕ Insert / 🗑️ Delete Rows"])

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
# ➕ Insert / 🗑️ Delete Rows tab
with tab3:
    st.subheader("🔒 Admin Panel (Insert/Delete)")

    # Set your admin password
    ADMIN_PASSWORD = "admin123"  # 🛑 Change to your secret password

    password = st.text_input("Enter Admin Password", type="password")

    if password == ADMIN_PASSWORD:
        st.success("🔓 Access Granted!")

        action = st.radio("Choose Action", ["Insert", "Delete"], horizontal=True)

        if action == "Insert":
            table_to_insert = st.selectbox("Select table to insert into:", tables, key="insert_table")
            if table_to_insert:
                cur = conn.cursor()
                cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_to_insert}'")
                columns = [row[0] for row in cur.fetchall()]
                cur.close()

                st.write("Fill in the values for new row:")
                values = {}
                for col in columns:
                    values[col] = st.text_input(f"Enter {col}")

                if st.button("➕ Insert Row"):
                    try:
                        cols = ', '.join(f'"{col}"' for col in columns)
                        vals = ', '.join(f"'{v}'" for v in values.values())
                        insert_query = f'INSERT INTO "{table_to_insert}" ({cols}) VALUES ({vals})'
                        cur = conn.cursor()
                        cur.execute(insert_query)
                        conn.commit()
                        cur.close()
                        st.success("✅ Row inserted successfully!")
                    except Exception as e:
                        conn.rollback()  # 🛡️ Important: reset after failure
                        st.error(f"⚠️ Insert failed: {e}")

        elif action == "Delete":
            table_to_delete = st.selectbox("Select table to delete from:", tables, key="delete_table")
            delete_condition = st.text_input("Enter DELETE condition (e.g., patient_id=5):")

            if st.button("🗑️ Delete Row(s)"):
                if delete_condition.strip() == "":
                    st.error("❌ Please provide a valid delete condition!")
                else:
                    try:
                        delete_query = f'DELETE FROM "{table_to_delete}" WHERE {delete_condition}'
                        cur = conn.cursor()
                        cur.execute(delete_query)
                        conn.commit()
                        cur.close()
                        st.success("✅ Row(s) deleted successfully!")
                    except Exception as e:
                        conn.rollback()  # 🛡️ Important: reset after failure
                        st.error(f"⚠️ Delete failed: {e}")
    elif password:
        st.error("❌ Incorrect Password!")
