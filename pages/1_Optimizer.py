import streamlit as st
import pandas as pd
import pulp

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Supply Chain Optimizer | Alastair McBride",
    page_icon="💼",
    layout="wide"
)

# --- TITLE & DESCRIPTION ---
st.title("Multi-Depot Supply Chain Optimizer (PuLP LP)")
st.markdown(
    """
    **Prescriptive Decision-Support Tool** | Built with Python, `PuLP` Linear Programming, and `pandas`.
    
    This application calculates the cost-optimal distribution scheme to transport TVs from 3 supply depots to 3 retail stores using **`PuLP`**, 
    minimizing total freight cost at a rate of **£5.00 per mile per TV**, subject to depot supply constraints and store capacity limits.
    """
)

st.divider()

# --- CONSTANTS & FIXED ROUTE DISTANCES (MILES) ---
RATE_PER_MILE_PER_UNIT = 5.00

# Distance Matrix from Excel model
distances = {
    "D1": {"Store 1": 22.0, "Store 2": 33.0, "Store 3": 40.0},
    "D2": {"Store 1": 27.0, "Store 2": 30.0, "Store 3": 22.0},
    "D3": {"Store 1": 36.0, "Store 2": 20.0, "Store 3": 25.0}
}

# --- SIDEBAR INTERACTIVE INPUTS ---
st.sidebar.header("Model Parameters")

st.sidebar.subheader("Depot Supply (TVs Available)")
supply_d1 = st.sidebar.number_input("D1 Supply", min_value=0, value=2500, step=100)
supply_d2 = st.sidebar.number_input("D2 Supply", min_value=0, value=3100, step=100)
supply_d3 = st.sidebar.number_input("D3 Supply", min_value=0, value=1250, step=100)

st.sidebar.subheader("Store Capacities")
cap_s1 = st.sidebar.number_input("Store 1 Capacity", min_value=0, value=2000, step=100)
cap_s2 = st.sidebar.number_input("Store 2 Capacity", min_value=0, value=3000, step=100)
cap_s3 = st.sidebar.number_input("Store 3 Capacity", min_value=0, value=2000, step=100)

# --- DATA STRUCTURE PREPARATION ---
depots = ["D1", "D2", "D3"]
stores = ["Store 1", "Store 2", "Store 3"]

supply = {
    "D1": supply_d1,
    "D2": supply_d2,
    "D3": supply_d3
}

store_capacity = {
    "Store 1": cap_s1,
    "Store 2": cap_s2,
    "Store 3": cap_s3
}

# Calculate freight cost per TV (£5/mi)
unit_costs = {
    d: {s: distances[d][s] * RATE_PER_MILE_PER_UNIT for s in stores}
    for d in depots
}

total_supply = sum(supply.values())
total_store_capacity = sum(store_capacity.values())

# --- PULP MODEL FORMULATION ---
# Create LP problem instance
prob = pulp.LpProblem("TV_Distribution_Optimization", pulp.LpMaximize)

# Decision Variables: Number of TVs shipped on route (d, s)
routes = [(d, s) for d in depots for s in stores]
vars = pulp.LpVariable.dicts("Shipment", (depots, stores), lowBound=0, cat='Integer')

# Objective Function: Maximize total throughput value while minimizing transportation cost
# (1000 - cost) ensures maximum units are moved at minimum freight cost
UNIT_VALUE = 1000.0
prob += pulp.lpSum([vars[d][s] * (UNIT_VALUE - unit_costs[d][s]) for (d, s) in routes]), "Total_Net_Objective"

# Supply Constraints: Total shipped from depot <= Depot Supply
for d in depots:
    prob += pulp.lpSum([vars[d][s] for s in stores]) <= supply[d], f"Supply_Constraint_{d}"

# Capacity Constraints: Total received at store <= Store Capacity
for s in stores:
    prob += pulp.lpSum([vars[d][s] for d in depots]) <= store_capacity[s], f"Capacity_Constraint_{s}"

# Solve model using PuLP CBC Solver
prob.solve(pulp.PULP_CBC_CMD(msg=False))
status = pulp.LpStatus[prob.status]

# --- CALCULATE OPTIMAL TOTAL FREIGHT COST ---
total_freight_cost = sum(
    (pulp.value(vars[d][s]) or 0) * unit_costs[d][s]
    for d in depots for s in stores
)

total_tvs_shipped = sum(
    (pulp.value(vars[d][s]) or 0)
    for d in depots for s in stores
)

# --- TOP METRICS DASHBOARD ---
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("PuLP Solver Status", status)
col_m2.metric("Total Optimal Freight Cost", f"£{total_freight_cost:,.2f}")
col_m3.metric("Total Supply Available", f"{total_supply:,} TVs")
col_m4.metric("Total Store Capacity", f"{total_store_capacity:,} TVs")

st.divider()

# --- RESULTS TABLES ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Optimal Shipment Plan (TVs Allocated)")
    
    results_data = {}
    for d in depots:
        results_data[d] = [int(pulp.value(vars[d][s]) or 0) for s in stores]
    
    df_results = pd.DataFrame(results_data, index=stores).T
    df_results["TVs Shipped"] = df_results.sum(axis=1)
    df_results["Depot Supply"] = [supply[d] for d in depots]
    df_results["Unused Supply"] = df_results["Depot Supply"] - df_results["TVs Shipped"]

    st.dataframe(df_results, use_container_width=True)

with col_right:
    st.subheader("Freight Cost Matrix (£ / TV)")
    
    cost_data = {}
    for d in depots:
        cost_data[d] = [unit_costs[d][s] for s in stores]
        
    df_costs = pd.DataFrame(cost_data, index=stores).T
    st.caption("Derived Freight Cost (Miles × £5.00/TV):")
    st.dataframe(df_costs.style.format("£{:.2f}"), use_container_width=True)

st.divider()

# --- SENSITIVITY & NETWORK SUMMARY ---
st.subheader("Network Utilization & Capacity Analysis")

col_s1, col_s2 = st.columns(2)

with col_s1:
    st.markdown("### Depot Capacity Utilization")
    for d in depots:
        shipped = sum(pulp.value(vars[d][s]) or 0 for s in stores)
        cap = supply[d]
        pct = (shipped / cap * 100) if cap > 0 else 0
        st.write(f"**{d}:** {int(shipped):,} / {cap:,} TVs ({pct:.1f}% utilized)")
        st.progress(pct / 100)

with col_s2:
    st.markdown("### Decision Model Insights")
    active_routes = sum(1 for d in depots for s in stores if (pulp.value(vars[d][s]) or 0) > 0)
    avg_cost = (total_freight_cost / total_tvs_shipped) if total_tvs_shipped > 0 else 0.0
    
    st.info(
        f"• **Delivery Rate:** Fixed at £5.00 per mile per TV.\n"
        f"• **Total Delivered:** {int(total_tvs_shipped):,} TVs shipped out of {total_supply:,} available.\n"
        f"• **Active Shipping Routes:** {active_routes} out of 9 possible routes utilized.\n"
        f"• **Average Delivery Cost per TV:** £{avg_cost:.2f}"
    )
