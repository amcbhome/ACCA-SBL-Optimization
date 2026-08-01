import streamlit as st
import pandas as pd
import pulp

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Supply Chain Optimizer | Alastair McBride",
    page_icon="🚚",
    layout="wide"
)

# --- TITLE & DESCRIPTION ---
st.title("🚚 Multi-Depot Supply Chain Optimizer")
st.markdown(
    """
    **Prescriptive Decision-Support Tool** | Built with Python, `PuLP` Linear Programming, and `pandas`.
    
    This application calculates the cost-optimal distribution scheme to transport inventory from 3 supply depots to 3 retail stores, 
    minimizing total freight overhead while satisfying all store demand requirements and depot holding limits.
    """
)

st.divider()

# --- SIDEBAR INTERACTIVE INPUTS ---
st.sidebar.header("⚙️ Model Parameters")

st.sidebar.subheader("Depot Supply Limits (Units)")
supply_d1 = st.sidebar.number_input("Depot 1 Capacity", min_value=0, value=2500, step=100)
supply_d2 = st.sidebar.number_input("Depot 2 Capacity", min_value=0, value=3000, step=100)
supply_d3 = st.sidebar.number_input("Depot 3 Capacity", min_value=0, value=2000, step=100)

st.sidebar.subheader("Store Demand Requirements (Units)")
demand_s1 = st.sidebar.number_input("Store 1 Demand", min_value=0, value=1800, step=100)
demand_s2 = st.sidebar.number_input("Store 2 Demand", min_value=0, value=2200, step=100)
demand_s3 = st.sidebar.number_input("Store 3 Demand", min_value=0, value=2500, step=100)

# --- FREIGHT COST MATRIX INPUTS ---
st.sidebar.subheader("Freight Cost per Unit (£)")
cost_d1_s1 = st.sidebar.number_input("Depot 1 ➔ Store 1", min_value=0.0, value=4.50, step=0.50)
cost_d1_s2 = st.sidebar.number_input("Depot 1 ➔ Store 2", min_value=0.0, value=6.00, step=0.50)
cost_d1_s3 = st.sidebar.number_input("Depot 1 ➔ Store 3", min_value=0.0, value=5.00, step=0.50)

cost_d2_s1 = st.sidebar.number_input("Depot 2 ➔ Store 1", min_value=0.0, value=3.00, step=0.50)
cost_d2_s2 = st.sidebar.number_input("Depot 2 ➔ Store 2", min_value=0.0, value=8.00, step=0.50)
cost_d2_s3 = st.sidebar.number_input("Depot 2 ➔ Store 3", min_value=0.0, value=4.00, step=0.50)

cost_d3_s1 = st.sidebar.number_input("Depot 3 ➔ Store 1", min_value=0.0, value=7.00, step=0.50)
cost_d3_s2 = st.sidebar.number_input("Depot 3 ➔ Store 2", min_value=0.0, value=3.50, step=0.50)
cost_d3_s3 = st.sidebar.number_input("Depot 3 ➔ Store 3", min_value=0.0, value=5.50, step=0.50)

# --- DATA STRUCTURE PREPARATION ---
depots = ["Depot 1", "Depot 2", "Depot 3"]
stores = ["Store 1", "Store 2", "Store 3"]

supply = {
    "Depot 1": supply_d1,
    "Depot 2": supply_d2,
    "Depot 3": supply_d3
}

demand = {
    "Store 1": demand_s1,
    "Store 2": demand_s2,
    "Store 3": demand_s3
}

costs = {
    "Depot 1": {"Store 1": cost_d1_s1, "Store 2": cost_d1_s2, "Store 3": cost_d1_s3},
    "Depot 2": {"Store 1": cost_d2_s1, "Store 2": cost_d2_s2, "Store 3": cost_d2_s3},
    "Depot 3": {"Store 1": cost_d3_s1, "Store 2": cost_d3_s2, "Store 3": cost_d3_s3}
}

total_supply = sum(supply.values())
total_demand = sum(demand.values())

# --- SOLVER EXECUTION ---
if total_supply < total_demand:
    st.error(
        f"⚠️ **Infeasible Problem:** Total Supply ({total_supply:,} units) is less than Total Demand ({total_demand:,} units). "
        "Please increase depot capacity or lower store demand in the sidebar."
    )
else:
    # Formulate PuLP Problem
    prob = pulp.LpProblem("Supply_Chain_Optimization", pulp.LpMinimize)

    # Decision Variables
    routes = [(d, s) for d in depots for s in stores]
    vars = pulp.LpVariable.dicts("Route", (depots, stores), lowBound=0, cat='Integer')

    # Objective Function: Minimize Total Transportation Cost
    prob += pulp.lpSum([vars[d][s] * costs[d][s] for (d, s) in routes]), "Total_Cost"

    # Supply Constraints
    for d in depots:
        prob += pulp.lpSum([vars[d][s] for s in stores]) <= supply[d], f"Supply_{d}"

    # Demand Constraints
    for s in stores:
        prob += pulp.lpSum([vars[d][s] for d in depots]) >= demand[s], f"Demand_{s}"

    # Solve
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[prob.status]

    # --- TOP METRICS DASHBOARD ---
    total_cost = pulp.value(prob.objective)
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Optimization Status", status)
    col_m2.metric("Total Optimal Freight Cost", f"£{total_cost:,.2f}" if total_cost else "£0.00")
    col_m3.metric("Total Supply Available", f"{total_supply:,} units")
    col_m4.metric("Total Demand Required", f"{total_demand:,} units")

    st.divider()

    # --- RESULTS TABLES ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📋 Optimal Shipment Plan (Units Allocated)")
        
        # Build allocation DataFrame
        results_data = {}
        for d in depots:
            results_data[d] = [int(vars[d][s].varValue()) for s in stores]
        
        df_results = pd.DataFrame(results_data, index=stores).T
        df_results["Total Shipped"] = df_results.sum(axis=1)
        df_results["Depot Capacity"] = [supply[d] for d in depots]
        df_results["Unused Capacity"] = df_results["Depot Capacity"] - df_results["Total Shipped"]

        st.dataframe(df_results, use_container_width=True)

    with col_right:
        st.subheader("💰 Freight Cost Matrix (£ / Unit)")
        df_costs = pd.DataFrame(costs).T
        st.dataframe(df_costs.style.format("£{:.2f}"), use_container_width=True)

    st.divider()

    # --- SENSITIVITY & NETWORK SUMMARY ---
    st.subheader("📊 Network Utilization & Capacity Analysis")
    
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        st.markdown("### Depot Capacity Utilization")
        for d in depots:
            shipped = sum(vars[d][s].varValue() for s in stores)
            cap = supply[d]
            pct = (shipped / cap * 100) if cap > 0 else 0
            st.write(f"**{d}:** {int(shipped):,} / {cap:,} units ({pct:.1f}% utilized)")
            st.progress(pct / 100)

    with col_s2:
        st.markdown("### Decision Model Insights")
        unallocated_supply = total_supply - total_demand
        st.info(
            f"• **Network Slack:** {unallocated_supply:,} units of surplus capacity remain unallocated across the system.\n"
            f"• **Active Routes:** {sum(1 for d in depots for s in stores if vars[d][s].varValue() > 0)} out of 9 possible shipping routes utilized.\n"
            f"• **Average Cost per Unit Shipped:** £{(total_cost / total_demand):.2f}" if total_demand > 0 else "£0.00"
        )
