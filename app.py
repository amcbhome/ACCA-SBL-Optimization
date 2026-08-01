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
routes = [(i, j) for i in depots for j in stores]
x = pulp.LpVariable.dicts("Route", (depots, stores), lowBound=0, cat="Integer")

# Objective Function
model += pulp.lpSum([x[i][j] * distances[i][j] * freight_rate for i in depots for j in stores]), "Total_Transportation_Cost"

# Constraints
# 1. Supply Constraints (Equality: All available inventory dispatched)
supply_constraints = {}
for i in depots:
    c = pulp.lpSum([x[i][j] for j in stores]) == supply[i]
    model += c, f"Supply_Constraint_{i}"
    supply_constraints[i] = c

# 2. Capacity Constraints (Inequality: Delivered units <= Capacity)
capacity_constraints = {}
for j in stores:
    c = pulp.lpSum([x[i][j] for i in depots]) <= capacity[j]
    model += c, f"Capacity_Constraint_{j}"
    capacity_constraints[j] = c

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
    schedule_df["Total Dispatched"] = schedule_df.sum(axis=1)
    
    st.dataframe(schedule_df.style.format("{:,}"), use_container_width=True)

    st.divider()

    # --- CONSTRAINT BINDING CHECKLIST ---
    st.subheader("📌 Constraint Binding & Capacity Checklist")
    st.markdown("This checklist analyzes each operational constraint to indicate whether it is **Binding** (operating at 100% full capacity) or **Non-Binding** (has remaining slack capacity).")

    checklist_items = []

    # Check Supply Constraints
    for i in depots:
        dispatched = sum(int(x[i][j].varValue) for j in stores)
        max_supply = supply[i]
        slack = max_supply - dispatched
        is_binding = abs(slack) < 1e-5
        
        checklist_items.append({
            "Constraint Category": "Depot Dispatch / Supply",
            "Entity": i,
            "Target / Limit": f"{max_supply:,} units",
            "Actual Value": f"{dispatched:,} units",
            "Slack / Unused": f"{int(slack):,} units",
            "Status": "🔴 Binding (100% Dispatched)" if is_binding else f"🟢 Non-Binding ({int(slack)} unused)"
        })

    # Check Store Capacity Constraints
    for j in stores:
        received = sum(int(x[i][j].varValue) for i in depots)
        max_cap = capacity[j]
        slack = max_cap - received
        is_binding = abs(slack) < 1e-5

        checklist_items.append({
            "Constraint Category": "Store Storage Capacity",
            "Entity": j,
            "Target / Limit": f"{max_cap:,} units",
            "Actual Value": f"{received:,} units",
            "Slack / Unused": f"{int(slack):,} units",
            "Status": "🔴 Binding (At Max Capacity)" if is_binding else f"🟢 Non-Binding ({int(slack)} units slack)"
        })

    checklist_df = pd.DataFrame(checklist_items)
    
    # Display Checklist Table
    st.table(checklist_df)

    # Key Takeaway Banner
    s2_slack = capacity["Store 2"] - sum(int(x[i]["Store 2"].varValue) for i in depots)
    st.info(f"💡 **Strategic Insight:** Store 2 currently operates with **{int(s2_slack)} units of non-binding slack capacity**, offering an ideal operational buffer for promotional stock holding or seasonal demand spikes.")

else:
    st.error("No optimal solution could be found with the current constraints.")
