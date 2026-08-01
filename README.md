# 🚚 ACCA SBL Supply Chain Optimizer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)

An interactive web application demonstrating prescriptive analytics and operations research techniques. Built using Python, `PuLP`, and Streamlit, this tool solves multi-depot linear programming transportation matrices modeled after strategic business management scenarios.

---

## 📌 Business Case & Overview

Logistics management requires allocating limited inventories across distribution networks to minimize freight overhead while honoring physical constraints.

* **Objective:** Minimize total transportation cost across a 9-route distribution network.
* **Depot Supply:** 6,850 total units across 3 regional depots.
* **Store Capacities:** 7,000 total receiving capacity across 3 retail outlets.
* **Prescriptive Model:** Formulated via Linear Programming (LP) and solved using Branch-and-Bound algorithms (`PuLP` COIN-OR CBC solver).
* **Key Business Insight:** The application dynamically calculates capacity utilization and identifies non-binding constraints (e.g., 150 units of unallocated slack capacity at Store 2).

---

## 🛠️ Tech Stack & Analytical Methods

* **Languages & Frameworks:** Python, Streamlit
* **Optimization & Modeling:** `PuLP` (Linear Programming)
* **Data Wrangling & Visualization:** `pandas`
* **Core Concepts:** Prescriptive Analytics, Operations Research, Linear Programming, Cost Minimization, Sensitivity Analysis.

---

## 🚀 Quick Start (Local Setup)

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/amcbhome/delivery-LP.git](https://github.com/amcbhome/delivery-LP.git)
   cd delivery-LP
