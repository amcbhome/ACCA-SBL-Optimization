import streamlit as st
import pandas as pd
import pulp

# Page configuration
st.set_page_config(
    page_title="ACCA SBL Supply Chain Optimization",
    page_icon="🚚",
    layout="wide"
)

# --- TITLE & INTRODUCTORY PARAGRAPH ---
st.title("🚚 Prescriptive Supply Chain Transportation Optimizer")

st.markdown(
    """
    ### Overview
    This application solves the **ACCA SBL Big Data Freight & Distribution Problem** by calculating the cost-optimal transportation schedule across multi-depot and retail store networks. 
    
    * **Problem Context:** Modernizing legacy accounting case study spreadsheet frameworks into dynamic, scalable analytics.
    * **Methodology:** Developed using **GenAI-assisted Python coding** (`PuLP` linear programming engine & `pandas` data processing) and deployed as an automated Business Intelligence dashboard via **Streamlit**.
    """
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

    # Display full matrix with embedded capacity/supply limits
    st.dataframe(schedule_df, use_container_width=True)

    st.divider()

    # --- CONSTRAINT BINDING & CAPACITY CHECKLIST ---
    st.subheader("📌 Constraint Binding & Capacity Checklist")

    grid_cols = st.columns(3)

    # Depot Cards
    for idx, depot in enumerate(depots):
        shipped = schedule_df.loc[depot, "Total Shipped"]
        limit = supply[depot]
        is_binding = (shipped == limit)
        
        with grid_cols[idx]:
            if is_binding:
                st.success(f"**{depot} (Supply)**\n\n🟢 **Fully Binding**\n\nShipped: {shipped:,} / {limit:,} units")
            else:
                st.error(f"**{depot} (Supply)**\n\n🔴 **Not Fully Binding**\n\nShipped: {shipped:,} / {limit:,} units")

    # Store Cards
    for idx, store in enumerate(stores):
        received = schedule_df.loc["Total Received", store]
        limit = capacity[store]
        is_binding = (received == limit)
        slack = limit - received
        
        with grid_cols[idx]:
            if is_binding:
                st.success(f"**{store} (Capacity)**\n\n🟢 **Fully Binding**\n\nReceived: {received:,} / {limit:,} units")
            else:
                st.error(f"**{store} (Capacity)**\n\n🔴 **Not Fully Binding**\n\nReceived: {received:,} / {limit:,} units ({slack:,} slack)")

    st.divider()

    # --- FOCUSED ANALYTICAL INSIGHT (RED CELL ONLY) ---
    st.subheader("📊 Analytical Insight: Unused Network Capacity")
    
    s2_received = schedule_df.loc["Total Received", "Store 2"]
    s2_cap_val = capacity["Store 2"]
    s2_slack_val = s2_cap_val - s2_received

    st.info(
        f"Across the entire transportation network, **Store 2** is the sole **not fully binding** constraint (🔴 Red). "
        f"While all three depots dispatch 100% of their supply and Stores 1 and 3 hit 100% of their maximum intake, "
        f"Store 2 receives **{s2_received:,} units against its {s2_cap_val:,}-unit limit**.\n\n"
        f"This leaves **{s2_slack_val:,} units of unallocated slack space**. Strategically, this red cell identifies "
        f"Store 2 as the network's only operational safety valve—providing built-in flexibility to absorb unexpected demand "
        f"spikes or hold promotional inventory without requiring extra warehouse investment."
    )

else:
    st.error("No optimal solution could be found with the current constraints.")
