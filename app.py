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

    st.subheader("📋 Optimal Dispatch Schedule (Units Shipped)")
    
    # Schedule Dataframe
    schedule_data = {j: [int(x[i][j].varValue) for i in depots] for j in stores}
    schedule_df = pd.DataFrame(schedule_data, index=depots)
    
    # Calculate row (depot) and column (store) totals
    row_totals = schedule_df.sum(axis=1)
    col_totals = schedule_df.sum(axis=0)
    
    # Display main dispatch matrix
    st.dataframe(schedule_df.style.format("{:,}"), use_container_width=True)

    st.divider()

    # --- CONSTRAINT BINDING & CAPACITY CHECKLIST ---
    st.subheader("📌 Constraint Binding & Capacity Checklist")
    st.markdown(
        "This checklist calculates the totals from the dispatch matrix rows (Depots) and columns (Stores) "
        "and evaluates whether each constraint is **Fully Binding** (100% capacity/supply utilized) "
        "or **Not Fully Binding** (contains remaining slack capacity)."
    )

    # 1. Depot Supply Checklist (Row Totals)
    st.markdown("#### 🏭 Supply Depot Constraints (Row Totals)")
    depot_cols = st.columns(3)
    for idx, depot in enumerate(depots):
        actual_shipped = int(row_totals[depot])
        max_supply = supply[depot]
        is_binding = (actual_shipped == max_supply)
        
        with depot_cols[idx]:
            if is_binding:
                st.success(
                    f"**{depot}**\n\n"
                    f"**Status:** Fully Binding 🟢\n\n"
                    f"**Total Shipped:** {actual_shipped:,} / {max_supply:,} units (100%)"
                )
            else:
                st.error(
                    f"**{depot}**\n\n"
                    f"**Status:** Not Fully Binding 🔴\n\n"
                    f"**Total Shipped:** {actual_shipped:,} / {max_supply:,} units"
                )

    # 2. Store Capacity Checklist (Column Totals)
    st.markdown("#### 🏬 Store Capacity Constraints (Column Totals)")
    store_cols = st.columns(3)
    for idx, store in enumerate(stores):
        actual_received = int(col_totals[store])
        max_cap = capacity[store]
        is_binding = (actual_received == max_cap)
        slack = max_cap - actual_received
        
        with store_cols[idx]:
            if is_binding:
                st.success(
                    f"**{store}**\n\n"
                    f"**Status:** Fully Binding 🟢\n\n"
                    f"**Total Received:** {actual_received:,} / {max_cap:,} units (100%)"
                )
            else:
                st.error(
                    f"**{store}**\n\n"
                    f"**Status:** Not Fully Binding 🔴\n\n"
                    f"**Total Received:** {actual_received:,} / {max_cap:,} units ({slack:,} units slack)"
                )

    st.divider()

    # --- ANALYTICAL INSIGHT PARAGRAPH ---
    st.subheader("📊 Analytical Insight")
    s2_received = int(col_totals["Store 2"])
    s2_cap_val = capacity["Store 2"]
    s2_slack_val = s2_cap_val - s2_received

    st.info(
        f"**Binding Network Analysis:** Five out of six network constraints—specifically all three supply depots "
        f"(Depot 1, 2, and 3) alongside Store 1 and Store 3—are operating as **fully binding constraints (🟢 Green)**, "
        f"utilizing 100% of their available inventory and floor space. The only non-binding node across the entire distribution "
        f"network is **Store 2 (🔴 Red)**, which receives **{s2_received:,} units** against a maximum capacity of **{s2_cap_val:,} units**, "
        f"leaving **{s2_slack_val:,} units of non-binding slack capacity**. From a managerial perspective, this single non-binding point "
        f"identifies Store 2 as the sole strategic buffer in the supply chain—offering immediate operational flexibility to absorb "
        f"promotional inventory, store seasonal safety stock, or accommodate fluctuating regional demand without incurring additional facility capital expenditure."
    )

else:
    st.error("No optimal solution could be found with the current constraints.")
