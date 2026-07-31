import streamlit as st
import pandas as pd
import pulp

# Page Configuration
st.set_page_config(
    page_title="ACCA SBL Transportation Optimizer",
    page_icon="🚚",
    layout="wide"
)

# Top Bar Header with Portfolio & CV Link
st.title("🚚 Prescriptive Supply Chain Transportation Optimizer")
st.markdown("""
**ACCA Technical Framework Alignment (PM / APM / SBL)**  
*This app updates the traditional spreadsheet solution (Excel Solver) to Python.*  
Developed by **Alastair McBride** | [View Project Repository & CV on GitHub](https://github.com/amcbhome/ACCA-SBL-Transportation)
""")

st.divider()

# --- SIDEBAR: INPUT CONTROL PANEL ---
st.sidebar.header("⚙️ Network Parameters")

# Depots & Stores matching spreadsheet
depots = ["D1", "D2", "D3"]
stores = ["Store 1", "Store 2", "Store 3"]

# Freight Rate Parameter (£5 / TV / mile)
st.sidebar.subheader("1. Freight Rate Parameter")
rate_per_mile = st.sidebar.number_input(
    "Cost per TV per mile (£)",
    min_value=0.0,
    value=5.00,
    step=0.50,
    help="Delivery cost per TV per mile shipped"
)

# Depot Supply / Availability Inputs (D1=2500, D2=3100, D3=1250)
st.sidebar.subheader("2. Depot Supply (TVs Available)")
supply = {
    "D1": st.sidebar.number_input("D1 Supply", min_value=0, value=2500, step=100),
    "D2": st.sidebar.number_input("D2 Supply", min_value=0, value=3100, step=100),
    "D3": st.sidebar.number_input("D3 Supply", min_value=0, value=1250, step=100)
}

# Store Maximum Capacity Inputs (Store 1=2000, Store 2=3000, Store 3=2000)
st.sidebar.subheader("3. Store Max Capacity")
store_capacity = {
    "Store 1": st.sidebar.number_input("Store 1 Capacity", min_value=0, value=2000, step=100),
    "Store 2": st.sidebar.number_input("Store 2 Capacity", min_value=0, value=3000, step=100),
    "Store 3": st.sidebar.number_input("Store 3 Capacity", min_value=0, value=2000, step=100)
}

# Total Network Sanity Check
total_supply = sum(supply.values())
total_capacity = sum(store_capacity.values())

# --- MAIN CONTENT: ROUTE DISTANCE MATRIX ---
st.subheader("📏 Distances between Depots and Stores (Miles)")
st.caption(f"Freight cost per route is calculated as: **Distance (Miles) × £{rate_per_mile:.2f}/TV/Mile**")

# Exact Distance Matrix from Excel (C8:E10)
default_distances = {
    "D1": {"Store 1": 22.0, "Store 2": 33.0, "Store 3": 40.0},
    "D2": {"Store 1": 27.0, "Store 2": 30.0, "Store 3": 22.0},
    "D3": {"Store 1": 36.0, "Store 2": 20.0, "Store 3": 25.0},
}

# Interactive Distance Input Grid in Columns
distances = {d: {} for d in depots}

for d in depots:
    st.markdown(f"**{d}**")
    cols = st.columns(len(stores))
    for idx, s in enumerate(stores):
        with cols[idx]:
            distances[d][s] = st.number_input(
                label=f"➔ {s} (Miles)",
                min_value=0.0,
                value=float(default_distances[d][s]),
                step=1.0,
                key=f"dist_{d}_{s}"
            )

# Calculate Unit Cost (£/TV) = Distance * Rate
costs = {
    d: {s: distances[d][s] * rate_per_mile for s in stores}
    for d in depots
}

# --- PULP OPTIMIZATION ENGINE ---
model = pulp.LpProblem("TV_Transportation_Minimization", pulp.LpMinimize)

# Decision Variables: TVs Shipped from Depots to Stores
routes = [(i, j) for i in depots for j in stores]
x = pulp.LpVariable.dicts("Ship_TVs", (depots, stores), lowBound=0, cat="Continuous")

# Objective Function: Minimize total delivery cost (£)
model += pulp.lpSum([x[i][j] * costs[i][j] for (i, j) in routes]), "Total_Delivery_Cost"

# Supply Constraints (Equalities per Excel Row 15-17): All available depot stock must be dispatched
for i in depots:
    model += (pulp.lpSum([x[i][j] for j in stores]) == supply[i], f"Depot_Supply_{i}")

# Store Capacity Constraints (Inequalities per Excel Row 18-20): Received <= Store Capacity
for j in stores:
    model += (pulp.lpSum([x[i][j] for i in depots]) <= store_capacity[j], f"Store_Capacity_{j}")

# Solve Model using CBC Simplex LP engine
model.solve(pulp.PULP_CBC_CMD(msg=False))
status = pulp.LpStatus[model.status]

# --- RESULTS DASHBOARD ---
st.divider()

if status != "Optimal":
    st.error("⚠️ **Infeasible Optimization State**: Constraints cannot be satisfied with current parameters.")
else:
    total_cost = pulp.value(model.objective)

    # Calculate aggregate metrics
    total_shipped = sum(x[i][j].varValue for i in depots for j in stores)
    total_distance_tv_miles = sum(x[i][j].varValue * distances[i][j] for i in depots for j in stores)

    # Key Performance Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Optimization Status", status)
    col2.metric("Total Cost (£)", f"£{total_cost:,.2f}")
    col3.metric("Total TV/Miles", f"{total_distance_tv_miles:,.0f}")
    col4.metric("Total TVs Shipped", f"{total_shipped:,.0f}")

    # Extract Matrix Results
    results_data = []
    for i in depots:
        row = {}
        for j in stores:
            val = x[i][j].varValue
            row[j] = int(round(val)) if val > 0 else 0
        results_data.append(row)

    # Create DataFrame and explicitly format as integers to remove decimal places
    results_df = pd.DataFrame(results_data, index=depots).astype(int)

    # Output Visualizations & Tables
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.subheader("📋 Optimal Dispatch Schedule (TVs)")
        st.dataframe(results_df.style.highlight_between(left=1, color="#d1e7dd"), use_container_width=True)

    with right_col:
        st.subheader("🔍 Store Capacity & Unallocated Space (Slack)")
        st.caption("Slack measures unused storage capacity at retail destinations.")

        # Calculate Slack per Store
        slack_data = []
        for j in stores:
            received = int(round(sum(x[i][j].varValue for i in depots)))
            cap = store_capacity[j]
            slack_val = cap - received
            status_text = "Fully Utilized (Binding)" if slack_val == 0 else f"Unallocated Space ({slack_val:,.0f} units)"
            
            slack_data.append({
                "Store": j,
                "Max Capacity": cap,
                "TVs Received": received,
                "Unallocated Storage Slack": slack_val,
                "Constraint Status": status_text
            })

        slack_df = pd.DataFrame(slack_data)
        st.dataframe(slack_df, use_container_width=True, hide_index=True)

        store2_slack = store_capacity["Store 2"] - sum(x[i]["Store 2"].varValue for i in depots)
        if store2_slack > 0:
            st.info(f"💡 **Store 2 Storage Note:** Store 2 has **{store2_slack:,.0f} units of unallocated storage space** remaining. Operational leadership can utilize this buffer for stock replenishment or secondary product displays without exceeding store limits.")

# --- STRATEGIC DISCUSSION ---
st.divider()
st.subheader("💡 Strategic Benefits: Transitioning from Excel Solver to Python (`PuLP`)")

st.markdown("""
While classic accounting curricula (ACCA PM/APM/SBL) teach linear programming using manual matrix steps or Excel's Solver plugin, migrating these models to Python provides distinct commercial advantages:

1. **Analytical Slack Identification:** Python's `PuLP` engine automatically flags non-binding constraints. Identifying the **150-unit storage slack at Store 2** allows commercial decision-makers to evaluate whether to hold buffer space or increase sales allocations without paying extra fixed holding overhead.
2. **Overcoming Constraint & Cell Limits:** Standard Excel Solver restricts models to 200 decision variables without expensive third-party add-ins. Python handles thousands of supply nodes, routes, and SKU constraints seamlessly.
3. **Auditability & Reduced Cell Error:** Formula errors in hidden spreadsheet cells can obscure misallocations. Python isolates logic, parameters, and constraints into clear, version-controlled code on GitHub.
4. **Automated Pipeline Integration:** Instead of manual spreadsheet copy-pasting, Python scripts pull live inventory levels and store demand forecasts straight from SQL databases or ERP systems.
""")
