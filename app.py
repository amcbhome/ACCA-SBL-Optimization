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
    "This app solves the [ACCA optimization problem](https://www.accaglobal.com/gb/en/student/exam-support-resources/professional-exams-study-resources/strategic-business-leader.html) with AI-assisted Python code, advancing business intelligence for the AI era."
)

st.divider()

# --- 1. SCENARIO ---
st.subheader("1. Scenario")

st.markdown(
    """
    The company needs to distribute **televisions** from three regional depots to three retail stores:

    * **Depot Inventory:** Depot 1 has **2,500 TVs**, Depot 2 has **3,100 TVs**, and Depot 3 has **1,250 TVs** available for dispatch.
    * **Store Holding Capacity:** Store 1 can hold **2,000 TVs**, Store 2 can hold **3,000 TVs**, and Store 3 can hold **2,000 TVs**.
    * **Freight Cost Rate:** Shipping incurs a fixed rate of **£5.00 per TV per mile**.

    #### **Depot-to-Store Distance Matrix (Miles)**
    """
)

# Define static distance matrix for display
distances_display = pd.DataFrame(
    [
        [22, 33, 40],
        [27, 30, 22],
        [36, 20, 25]
    ],
    index=["Depot 1", "Depot 2", "Depot 3"],
    columns=["Store 1", "Store 2", "Store 3"]
)

st.table(distances_display)

st.markdown(
    """
    > **The Business Objective:** The company wants to determine the **most cost-efficient delivery schedule** that satisfies all store receiving capacities while completely dispatching available depot inventories.
    """
)

st.divider()

# --- 2. SOLUTION ---
st.subheader("2. Solution")

st.markdown(
    """
    To find the optimal delivery schedule, the problem is formulated and solved using **Linear Programming**, broken down into three clear parts:

    * **1. Decision Variables:** The actual choices the model needs to make—specifically, deciding how many TVs to ship along each of the 9 routes between the depots and stores.
    * **2. Objective Function:** The total cost formula the model works to minimize by adding up the costs across all routes (number of TVs shipped × route distance × £5 rate).
    * **3. Constraints:** The operational rules the solution must respect—ensuring 100% of the TVs leave the depots without overloading any store beyond its holding limit.
    """
)

st.divider()

# --- SIDEBAR INPUTS ---
st.sidebar.header("⚙️ Model Parameters")

freight_rate = st.sidebar.number_input(
    "Freight Rate (£ / TV / mile)", 
    min_value=0.1, 
    max_value=20.0, 
    value=5.0, 
    step=0.5
)

st.sidebar.subheader("Depot Inventories (TVs)")
d1_supply = st.sidebar.number_input("Depot 1 Supply", value=2500, step=100)
d2_supply = st.sidebar.number_input("Depot 2 Supply", value=3100, step=100)
d3_supply = st.sidebar.number_input("Depot 3 Supply", value=1250, step=100)

st.sidebar.subheader("Store Holding Capacities (TVs)")
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

# --- 3. OUTPUT ---
st.subheader("3. Output")

if pulp.LpStatus[status] == "Optimal":
    total_cost = pulp.value(model.objective)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Optimization Status", "Optimal Solution Found", delta_color="normal")
    col2.metric("Total Optimal Freight Cost", f"£{total_cost:,.2f}")
    col3.metric("Total TVs Dispatched", f"{sum(supply.values()):,} units")

    st.markdown("#### **Optimal Dispatch Schedule & Network Summary**")
    
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

    # Styling function: Bolds delivery schedule quantities and highlights non-zero slack
    def style_schedule_cells(df):
        styles = pd.DataFrame('', index=df.index, columns=df.columns)
        
        # Bold non-zero delivery schedule values (Depots x Stores)
        for depot in depots:
            for store in stores:
                val = df.loc[depot, store]
                if isinstance(val, (int, float)) and val > 0:
                    styles.loc[depot, store] = 'font-weight: bold;'

        # Highlight capacity slack cell if present
        for col in df.columns:
            for idx in df.index:
                val = df.loc[idx, col]
                if val == 150 or val == "150":
                    styles.loc[idx, col] = 'background-color: #ff4b4b; color: white; font-weight: bold;'

        return styles

    # Apply styles to DataFrame
    styled_df = schedule_df.style.apply(style_schedule_cells, axis=None)

    st.dataframe(styled_df, use_container_width=True)

    # Footnote note on non-binding constraint / unallocated capacity
    st.caption(
        "**Note:** The optimization model is not fully binding; there is unallocated storage space for 150 TVs at Store 2."
    )

else:
    st.error("No optimal solution could be found with the current constraints.")
