import streamlit as st
import os
import sys
import importlib

# Add project root to sys.path (FORCE LOCAL)
sys.path.insert(0, os.getcwd())

# Force reload for development edits
import privacy_guardian_ai.sandbox.audit_logger as _audit_mod
import privacy_guardian_ai.dashboards.student as student_mod
import privacy_guardian_ai.dashboards.admin as admin_mod
import privacy_guardian_ai.dashboards.security as security_mod

importlib.reload(_audit_mod)
importlib.reload(student_mod)
importlib.reload(admin_mod)
importlib.reload(security_mod)

from privacy_guardian_ai.identity.rbac import Roles
from privacy_guardian_ai.identity.auth import AuthSystem
from privacy_guardian_ai.sandbox.audit_logger import AuditLogger

st.set_page_config(page_title="Privacy Guardian AI Enterprise", layout="wide", initial_sidebar_state="collapsed")

def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("dashboard/style.css")

# --- Session State Initialization ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'dark'

# --- Theme Injection ---
theme_class = "light-theme" if st.session_state['theme'] == 'light' else ""
st.markdown(f'<div class="{theme_class}">', unsafe_allow_html=True)

auth_system = AuthSystem()
audit_logger = AuditLogger()

def login_page():
    st.title("🛡️ Privacy Guardian Login")
    st.markdown("### Ethical AI Governance Platform")
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                username = st.text_input("Username / student_id")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    user_data = auth_system.authenticate(username, password)
                    if user_data:
                        st.session_state['authenticated'] = True
                        st.session_state['user'] = user_data
                        audit_logger.log_event(username, user_data['role'], "LOGIN_SUCCESS", "User authenticated successfully")
                        st.rerun()
                    else:
                        audit_logger.log_event(username, "UNKNOWN", "LOGIN_FAILED", "Invalid credentials attempt")
                        st.error("Invalid username or password")

def logout():
    user = st.session_state['user']
    if user:
        audit_logger.log_event(user['username'], user['role'], "LOGOUT", "User logged out")
    st.session_state['authenticated'] = False
    st.session_state['user'] = None
    st.rerun()

# --- Main Application Logic ---
if not st.session_state['authenticated']:
    login_page()
else:
    user = st.session_state['user']
    
    # --- Sidebar (Conditional) ---
    if user['role'] not in [Roles.ADMIN, Roles.SECURITY_OFFICER]:
        with st.sidebar:
            st.title("🛡️ Privacy Guardian")
            st.image("https://img.icons8.com/isometric/100/shield.png", width=80)
            st.divider()
            
            st.header(f"👤 {user['display_name']}")
            st.info(f"Role: **{user['role'].upper()}**")
            
            if st.button("🚪 Logout"):
                logout()
                
            st.divider()
            st.info("System Status: **ACTIVE**")
            st.info("Isolation: **ENFORCED**")

    # --- Routing ---
    if user['role'] == Roles.STUDENT:
        student_mod.show_student_dashboard(user['username'])
    elif user['role'] == Roles.ADMIN:
        admin_mod.show_admin_dashboard()
    elif user['role'] == Roles.SECURITY_OFFICER:
        security_mod.show_security_dashboard()

# --- Footer (Conditional) ---
if 'user' in st.session_state and st.session_state['user'] and st.session_state['user']['role'] not in [Roles.ADMIN, Roles.SECURITY_OFFICER]:
    st.divider()
    st.caption("Privacy Guardian AI System v3.0 | Federated Learning | Differential Privacy | Full Authentication | Ethical AI Governance")
elif not st.session_state.get('authenticated'):
     st.divider()
     st.caption("Privacy Guardian AI System v3.0 | Federated Learning | Differential Privacy | Full Authentication | Ethical AI Governance")
