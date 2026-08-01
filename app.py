import streamlit as st
import pandas as pd
import pulp

# Page configuration
st.set_page_config(
    page_title="ACCA SBL Supply Chain Optimization",
    page_icon="🚚",
    layout="wide"
)

# --- TITLE & INTRODUCTORY HEADER ---
st.title("🚚 ACCA SBL Supply Chain Optimizer")

st.markdown(
    "This app solves the [ACCA optimization problem](https://www.accaglobal.com/gb/en/student/exam-support-resources/professional-exams-study-resources/strategic-business-leader.html) with AI-assisted Python code, leading to automated optimization using linear programming."
)

st.divider()

# --- SIDEBAR INPUTS ---
st.sidebar.header("⚙️ Model Parameters")

freight_rate = st.sidebar.number_input(
    "Freight Rate (£ / unit / mile)", 
    min_value=0.1, 
    max_value=20.0, 
    value=5.0, 
    step=0.5
)

st.sidebar.subheader("Depot Supplies")
d1_supply = st.sidebar.number_input("Depot 1 Supply", value=2500, step=100)
d2_supply = st.sidebar.number_input("Depot 2 Supply", value=3100, step=100)
d3_supply = st.sidebar.number_input("Depot 3 Supply", value=1250, step=100)

st.sidebar.subheader("Store Capacities")
s1_cap = st.sidebar.number_input("Store 1 Capacity", value=2000, step=100)
s2_cap = st.sidebar.number_input("Store 2 Capacity", value=3000, step=100)
s3_cap = st.sidebar.number_input("Store 3 Capacity", value=2000, step=100)

# Data Structures
depots = ["Depot 1", "Depot 2", "Depot 3"]
stores = ["Store 1", "Store 2", "Store 3"]

supply = {
    "Depot 1": d1_supply,
    "Depot 2": d2_supply,
    "Depot 3": d3_supply
}

capacity = {
    "Store 1": s1_cap,
    "Store 2": s2_cap,
    "Store 3": s3_cap
}

distances = {
    "Depot 1": {"Store 1": 22, "Store 2": 33, "Store 3": 40},
    "Depot 2": {"Store 1": 27, "Store 2": 30, "Store 3": 22},
    "Depot 3": {"Store 1": 36, "Store 2": 20, "Store 3": 25}
}

# --- OPTIMIZATION MODEL ---
model = pulp.LpProblem("Supply_Chain_Optimization", pulp.LpMinimize)

# Decision Variables
x = pulp.LpVariable.dicts("Route", (depots, stores), lowBound=0, cat="Integer")

# Objective Function
model += pulp.lpSum([x[i][j] * distances[i][j] * freight_rate for i in depots for j in stores]), "Total_Transportation_Cost"

# Constraints
# 1. Supply Constraints (Equality: All available inventory dispatched)
for i in depots:
    model += pulp.lpSum([x[i][j] for j in stores]) == supply[i], f"Supply_Constraint_{i}"

# 2. Capacity Constraints (Inequality: Delivered units <= Capacity)
for j in stores:
    model += pulp.lpSum([x[i][j] for i in depots]) <= capacity[j], f"Capacity_Constraint_{j}"

# Solve Model
status = model.solve(pulp.PULP_CBC_CMD(msg=False))

# --- RESULTS DISPLAY ---
if pulp.LpStatus[status] == "Optimal":
    total_cost = pulp.value(model.objective)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Optimization Status", "Optimal Solution Found", delta_color="normal")
    col2.metric("Total Optimal Freight Cost", f"£{total_cost:,.2f}")
    col3.metric("Total Units Dispatched", f"{sum(supply.values()):,} units")

    st.subheader("📋 Optimal Dispatch Schedule & Network Summary")
    
    # 1. Build Base Schedule Dataframe
    schedule_data = {j: [int(x[i][j].varValue) for i in depots] for j in stores}
    schedule_df = pd.DataFrame(schedule_data, index=depots)
    
    # 2. Calculate Totals
    schedule_df["Total Shipped"] = schedule_df.sum(axis=1)
    
    # 3. Add Supply Limit and Supply Slack columns
    schedule_df["Supply Limit"] = [supply[depot] for depot in depots]
    schedule_df["Supply Slack"] = schedule_df["Supply Limit"] - schedule_df["Total Shipped"]
    
    # 4. Add Summary Rows for Store Received, Capacity Limits, and Capacity Slack
    total_received = schedule_df[stores].sum(axis=0)
    store_limits = pd.Series({j: capacity[j] for j in stores})
    store_slack = store_limits - total_received
    
    schedule_df.loc["Total Received"] = list(total_received) + [total_received.sum(), sum(capacity.values()), sum(capacity.values()) - total_received.sum()]
    schedule_df.loc["Capacity Limit"] = list(store_limits) + [sum(capacity.values()), "-", "-"]
    schedule_df.loc["Capacity Slack"] = list(store_slack) + [sum(capacity.values()) - total_received.sum(), "-", "-"]

    # Highlight function for the non-zero slack cell
    def highlight_slack(val):
        if val == 150 or val == "150":
            return "background-color: #ff4b4b; color: white; font-weight: bold;"
        return ""

    # Display styled table safely across pandas versions (.map vs .applymap)
    try:
        styled_df = schedule_df.style.map(highlight_slack)
    except AttributeError:
        styled_df = schedule_df.style.applymap(highlight_slack)

    st.dataframe(styled_df, use_container_width=True)

    st.divider()

    # --- QUALITATIVE ANALYTICAL INSIGHT ---
    st.subheader("📊 Analytical Insight")

    st.info(
        "**Unallocated Resource:** The highlighted cell (**150 units at Store 2**) represents an "
        "**unallocated resource** resulting from a **not fully binding constraint** in the linear programming model. "
        "While all depot supply is 100% dispatched and Stores 1 and 3 hit 100% capacity (fully binding), "
        "Store 2 retains unutilized intake limit under the optimal distribution plan."
    )

else:
    st.error("No optimal solution could be found with the current constraints.")
