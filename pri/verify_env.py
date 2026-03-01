try:
    import streamlit as st
except ImportError:
    print("Error: streamlit not installed")

try:
    import plotly
except ImportError:
    print("Error: plotly not installed")

try:
    import torch
except ImportError:
    print("Error: torch not installed")

try:
    import opacus
except ImportError:
    print("Error: opacus not installed")

try:
    from privacy_guardian_ai.dashboards.student import show_student_dashboard
    print("Imports success: privacy_guardian_ai.dashboards.student")
except Exception as e:
    print(f"Error importing privacy_guardian_ai components: {e}")
