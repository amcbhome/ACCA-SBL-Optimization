import streamlit as st

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Alastair McBride | Portfolio & Interactive CV",
    page_icon="💼",
    layout="wide"
)

# --- HEADER SECTION ---
st.title("Alastair McBride")
st.subheader("Decision-Support & Prescriptive Analytics Specialist")

st.markdown(
    """
    *Bridging the gap between accounting logic, operational research, and modern software tools.*
    
    📍 **Location:** Scotland, UK  
    🔗 **GitHub:** [github.com/amcbhome](https://github.com/amcbhome)  
    ✉️ **Contact:** [Your Email Here]
    """
)

st.divider()

# --- FEATURED PROJECT BANNER ---
st.info(
    "👉 **Explore Live Demo:** Select **'1 🚚 Optimizer'** from the sidebar to launch an interactive "
    "Linear Programming supply chain transportation model built with Python and `PuLP`."
)

# --- CORE COMPETENCIES ---
st.header("⚡ Core Competencies")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### **Analytical Capabilities**")
    st.markdown("- Prescriptive Analytics")
    st.markdown("- Operations Research")
    st.markdown("- Linear Programming (`PuLP`)")
    st.markdown("- Cost Minimization Models")

with col2:
    st.markdown("### **Technical Stack**")
    st.markdown("- **Languages:** Python, SQL")
    st.markdown("- **Frameworks:** Streamlit, Pandas")
    st.markdown("- **Platforms:** Apache Superset")
    st.markdown("- **Tools:** Git, GitHub")

with col3:
    st.markdown("### **Domain Expertise**")
    st.markdown("- Accounting & Financial Logic")
    st.markdown("- Supply Chain & Logistics")
    st.markdown("- FMCG Data Collection")
    st.markdown("- Decision Support Systems")

st.divider()

# --- EXPERIENCE & PROJECTS ---
st.header("🛠️ Technical Projects & Experience")

st.markdown("### **Prescriptive Supply Chain Optimization Application**")
st.caption("Python | PuLP | Streamlit | Open-Source")
st.markdown(
    """
    * **Architected and deployed** an interactive web application that formulates and solves 9-route linear programming transportation problems to optimize multi-depot inventory distribution.
    * **Engineered dynamic decision-support metrics** recalculating total freight overhead in real time based on user-adjusted supply limits, store capacities, and freight rates.
    * **Implemented automated network summary reporting** using custom conditional styling in `pandas` to visually highlight operational slack and unallocated store holding capacity.
    """
)

st.markdown("---")

st.markdown("### **Data Collection & Operations**")
st.caption("Retail Asset Solutions | Casual Contract")
st.markdown(
    """
    * Conducted inventory and stock data collection across retail environments to support operational audit accuracy.
    * Utilized systematic quantitative workflows to ensure high data fidelity across high-volume SKU environments.
    """
)

st.divider()

# --- EDUCATION & QUALIFICATIONS ---
st.header("🎓 Education & Credentials")

col_edu1, col_edu2 = st.columns(2)

with col_edu1:
    st.markdown("### **BAcc (Hons) Accountancy**")
    st.markdown("**University of the West of Scotland** | 2021 – 2025")
    st.markdown("- **Top Academic Performance:** Grade A in Management Accounting (MA) & Financial Management (FM).")
    st.markdown("- Core focus on cost accounting, financial decision-making, and quantitative business management.")

with col_edu2:
    st.markdown("### **Professional Qualifications & Exemptions**")
    st.markdown("- **ACCA Exemptions:** Qualified for Fundamental papers F1 through F9.")
    st.markdown("- **PDA Bookkeeping:** Personal Development Award.")

st.divider()

# --- FOOTER ---
st.caption("© 2026 Alastair McBride. Portfolio application hosted on Streamlit Community Cloud.")
