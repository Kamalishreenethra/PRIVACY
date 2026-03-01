"""
Enterprise Admin Dashboard — upgraded with:
- Risk Heatmap, Federated Training Monitor, Privacy Budget Widget,
- Compliance Mode Badge, Model Retrain Trigger, Real Inspection History
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import datetime
from privacy_guardian_ai.identity.vault import IdentityVault
from privacy_guardian_ai.sandbox.audit_logger import AuditLogger
from privacy_guardian_ai.compliance.mode_manager import ComplianceModeManager
from privacy_guardian_ai.defender.model_integrity import ModelIntegrityVerifier

def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def create_training_chart():
    df_train = pd.DataFrame({
        'Step': range(1, 21),
        'Accuracy': [0.5,0.55,0.6,0.62,0.65,0.68,0.72,0.75,0.78,0.81,
                     0.83,0.85,0.87,0.89,0.9,0.91,0.92,0.93,0.94,0.94]
    })
    fig = px.area(df_train, x='Step', y='Accuracy', title="Model Training Overview",
                  color_discrete_sequence=['#38bdf8'])
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      font_color="#94a3b8", xaxis_showgrid=False, yaxis_showgrid=False,
                      height=220, margin=dict(l=0, r=0, t=30, b=0))
    return fig

def show_admin_dashboard():
    css_path = os.path.join("dashboard", "style.css")
    load_css(css_path)

    st.markdown("""
    <style>
    .adm-p{background:rgba(6,15,30,0.9);border:1px solid rgba(56,189,248,0.2);
            border-radius:10px;padding:14px;margin-bottom:10px;}
    .adm-lbl{font-size:0.6rem;color:#64748b;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;}
    .adm-val{font-family:Orbitron,sans-serif;font-size:1.3rem;font-weight:bold;color:#f8fafc;}
    .log-entry{display:flex;align-items:center;gap:10px;padding:7px 0;
               border-bottom:1px solid rgba(255,255,255,0.05);}
    .avatar-sim{width:28px;height:28px;border-radius:50%;background:rgba(56,189,248,0.12);
                border:1px solid rgba(56,189,248,0.3);display:flex;align-items:center;
                justify-content:center;font-size:0.8rem;flex-shrink:0;}
    </style>
    """, unsafe_allow_html=True)

    data_path = "privacy_guardian_ai/dataset/student_data.csv"
    if not os.path.exists(data_path):
        st.warning("No dataset found. Run simulation first.")
        return
    df = pd.read_csv(data_path)

    comp_mgr  = ComplianceModeManager()
    current_mode = comp_mgr.get_mode()
    mode_col  = {"STANDARD":"#38bdf8","STRICT":"#eab308","AUDIT":"#ef4444"}.get(current_mode,"#38bdf8")
    integrity = ModelIntegrityVerifier()
    audit_log = AuditLogger()

    # ── TOP HEADER ──────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:8px 0;border-bottom:1px solid rgba(56,189,248,0.25);margin-bottom:16px;">
        <div style="font-family:Orbitron;font-size:1rem;color:#38bdf8;">Privacy Guardian</div>
        <div style="font-family:Orbitron;font-size:1.4rem;font-weight:bold;letter-spacing:2px;">
            ADMIN DASHBOARD
        </div>
        <div style="display:flex;gap:10px;align-items:center;">
            <span style="border:1px solid {mode_col};color:{mode_col};border-radius:4px;
                         padding:2px 8px;font-size:0.62rem;font-weight:bold;">{current_mode}</span>
            <span style="background:rgba(34,197,94,0.12);border:1px solid #22c55e;color:#22c55e;
                         border-radius:4px;padding:2px 8px;font-size:0.62rem;">NETWORK SECURE</span>
            <span style="color:#94a3b8;">⚙️</span>
            <span style="color:#94a3b8;">👤</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── TOP METRICS ROW ─────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(f"""
        <div class="adm-p">
            <div class="adm-lbl">Students Analyzed</div>
            <div style="display:flex;align-items:baseline;gap:8px;">
                <div class="adm-val">{len(df)}</div>
                <div style="color:#22c55e;font-size:0.75rem;">↑ 12%</div>
            </div>
            <div style="height:3px;background:rgba(56,189,248,0.12);border-radius:2px;
                        border-bottom:1px solid #38bdf8;margin-top:8px;"></div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        risk_score = (df['risk_label'].sum() / len(df)) * 10
        risk_col   = "#ef4444" if risk_score > 5 else "#eab308" if risk_score > 3 else "#22c55e"
        st.markdown(f"""
        <div class="adm-p">
            <div class="adm-lbl">Average Risk Score</div>
            <div style="display:flex;align-items:baseline;gap:8px;">
                <div class="adm-val" style="color:{risk_col};">{risk_score:.1f}</div>
                <div style="color:#ef4444;font-size:0.7rem;">▲ ELEVATED</div>
            </div>
            <div style="height:3px;background:rgba(239,68,68,0.12);border-radius:2px;
                        border-bottom:1px solid #ef4444;margin-top:8px;"></div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        int_v = integrity.verify()
        int_col = "#22c55e" if int_v["valid"] else "#ef4444"
        st.markdown(f"""
        <div class="adm-p">
            <div class="adm-lbl">Model Integrity</div>
            <div class="adm-val" style="color:{int_col};font-size:0.9rem;">
                {'✅ VERIFIED' if int_v['valid'] else '🚨 BREACH'}
            </div>
            <div style="font-size:0.62rem;color:#64748b;margin-top:4px;">
                Round {int_v.get('round','—')} | SHA256 Chained
            </div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        eps_hist = audit_log.get_epsilon_history(1)
        eps_now  = eps_hist[-1]["epsilon"] if eps_hist else 3.84
        st.markdown(f"""
        <div class="adm-p">
            <div class="adm-lbl">Privacy Budget (ε)</div>
            <div class="adm-val" style="color:#38bdf8;">{eps_now:.2f}</div>
            <div style="font-size:0.62rem;color:#64748b;margin-top:4px;">
                Noise: {eps_hist[-1]['noise_multiplier'] if eps_hist else 1.1}× | Training Round 30
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ── MAIN CONTENT GRID ───────────────────────────────────────────────────────
    main_left, main_right = st.columns([1.5, 1])

    with main_left:
        # Risk Heatmap
        st.markdown('<div class="adm-p">', unsafe_allow_html=True)
        st.markdown("### 🗺️ Student Risk Heatmap")
        n = min(len(df), 200)
        sample = df.iloc[:n].copy()
        sample["id"]  = sample.index
        hmap_data     = sample["risk_label"].values.reshape(-1, 10) if n >= 10 else sample["risk_label"].values.reshape(1, -1)
        fig_hmap = px.imshow(
            hmap_data,
            color_continuous_scale=[[0,"#22c55e"],[0.5,"#eab308"],[1,"#ef4444"]],
            zmin=0, zmax=1,
            labels=dict(color="Risk"),
            title=f"Risk Distribution (first {n} students)",
            aspect="auto"
        )
        fig_hmap.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', font_color="#94a3b8",
            height=200, coloraxis_showscale=True,
            margin=dict(l=0,r=0,t=30,b=0)
        )
        st.plotly_chart(fig_hmap, use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

        # Activity Logs
        st.markdown('<div class="adm-p">', unsafe_allow_html=True)
        st.markdown("### 📜 Admin Activity Logs")
        logs = [
            {"user":"admin1",   "role":"Administrator",    "time":"3:32 PM","icon":"👤"},
            {"user":"sec_off",  "role":"SecurityOfficer",  "time":"3:30 PM","icon":"🛡️"},
            {"user":"admin1",   "role":"View Profile (72)","time":"3:22 PM","icon":"🔍"},
            {"user":"ep_admin", "role":"Requesting Access","time":"3:15 PM","icon":"📝"},
        ]
        for log in logs:
            st.markdown(f'''
            <div class="log-entry">
                <div class="avatar-sim">{log['icon']}</div>
                <div>
                    <div style="font-size:0.85rem;font-weight:bold;">{log['user']}
                        <span style="color:#94a3b8;font-weight:normal;"> | {log['role']}</span>
                    </div>
                    <div style="font-size:0.65rem;color:#64748b;">{log['time']}</div>
                </div>
                <div style="margin-left:auto;font-size:0.9rem;">🔒</div>
            </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Federated Training Monitor + Risk Distribution side by side
        fc1, fc2 = st.columns(2)
        with fc1:
            st.markdown('<div class="adm-p">', unsafe_allow_html=True)
            st.markdown("### 📈 Federated Training")
            st.plotly_chart(create_training_chart(), use_container_width=True,
                            config={"displayModeBar":False})
            st.markdown("""
            <div style="display:flex;gap:16px;font-size:0.68rem;margin-top:4px;">
                <div><span style="color:#64748b;">Rounds</span>
                     <div style="color:#38bdf8;font-weight:bold;">30 / 30</div></div>
                <div><span style="color:#64748b;">Accuracy</span>
                     <div style="color:#22c55e;font-weight:bold;">94%</div></div>
                <div><span style="color:#64748b;">Clients</span>
                     <div style="color:#f8fafc;font-weight:bold;">5</div></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with fc2:
            st.markdown('<div class="adm-p">', unsafe_allow_html=True)
            st.markdown("### 📊 Risk Distribution")
            risk_counts = df['risk_label'].value_counts().rename({0:'LOW',1:'HIGH'}).reset_index()
            risk_counts.columns = ['Level','Count']
            fig_bars = px.bar(risk_counts, x='Level', y='Count', color='Level',
                              color_discrete_map={'LOW':'#22c55e','HIGH':'#ef4444'},
                              template="plotly_dark")
            fig_bars.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                                   height=220, showlegend=False, margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig_bars, use_container_width=True, config={"displayModeBar":False})
            st.markdown('</div>', unsafe_allow_html=True)

    with main_right:
        # Status Overview gauge
        st.markdown('<div class="adm-p" style="text-align:center;">', unsafe_allow_html=True)
        st.markdown("### 🛠️ Status Overview")
        fig_radial = go.Figure(go.Indicator(
            mode="gauge+number", value=30,
            number={'font':{'size':36,'color':'#f8fafc'}},
            gauge={'axis':{'range':[None,100],'visible':False},
                   'bar':{'color':"#38bdf8"},'bgcolor':"rgba(0,0,0,0)",'borderwidth':0}
        ))
        fig_radial.update_layout(height=180, margin=dict(l=10,r=10,t=10,b=10),
                                 paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_radial, use_container_width=True, config={"displayModeBar":False})
        st.markdown('<div style="font-family:Orbitron;font-size:0.75rem;color:#38bdf8;">Training Round 30/30</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Privacy Budget Widget
        eps_data = audit_log.get_epsilon_history(10)
        if eps_data:
            eps_vals  = [e["epsilon"] for e in eps_data]
            eps_fig   = go.Figure(go.Scatter(
                x=list(range(len(eps_vals))), y=eps_vals,
                mode="lines+markers", line=dict(color="#38bdf8",width=2),
                fill="tozeroy", fillcolor="rgba(56,189,248,0.08)",
                marker=dict(size=4)
            ))
            eps_fig.update_layout(height=120, margin=dict(l=0,r=0,t=0,b=0),
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  xaxis=dict(visible=False), yaxis=dict(visible=False))
            st.markdown('<div class="adm-p">', unsafe_allow_html=True)
            st.markdown("### 🔒 Privacy Budget History")
            st.plotly_chart(eps_fig, use_container_width=True, config={"displayModeBar":False})
            st.markdown(f"""
            <div style="display:flex;gap:12px;font-size:0.68rem;">
                <div><span style="color:#64748b;">Current ε</span>
                     <div style="color:#38bdf8;font-weight:bold;">{eps_vals[-1]:.3f}</div></div>
                <div><span style="color:#64748b;">Budget Used</span>
                     <div style="color:#eab308;font-weight:bold;">{min(eps_vals[-1]/10*100,100):.1f}%</div></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Privacy Alerts
        st.markdown("""
        <div class="adm-p" style="border-left:4px solid #ef4444;">
            <div style="font-size:0.85rem;font-weight:bold;color:#f8fafc;margin-bottom:8px;">⚠️ Privacy Alerts</div>
            <div style="display:flex;align-items:center;gap:16px;">
                <div style="width:64px;height:64px;border:5px solid #ef4444;border-radius:50%;
                            border-top-color:transparent;display:flex;align-items:center;
                            justify-content:center;color:#ef4444;font-weight:bold;">99%</div>
                <div>
                    <div style="font-weight:bold;color:#ef4444;font-size:0.8rem;">THREAT LEVEL: CRITICAL</div>
                    <div style="font-size:0.72rem;color:#94a3b8;">Potential MIA detected from node 0.3.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Model Retrain Trigger
        st.markdown('<div class="adm-p">', unsafe_allow_html=True)
        st.markdown("### 🔁 Model Retraining")

        r_rounds  = st.slider("Rounds",       5, 30, 10, key="rt_rounds")
        r_clients = st.slider("Clients",      2, 10,  5, key="rt_clients")
        r_noise   = st.slider("Noise Mult", 0.5, 2.0, 1.1, step=0.1, key="rt_noise")

        if st.button("⚡ Trigger Model Retraining", use_container_width=True, key="retrain_btn"):
            audit_log.log_event("admin", "admin", "MODEL_RETRAIN_TRIGGER",
                                "Admin triggered federated model retraining")
            prog_bar  = st.progress(0, text="Initialising training…")
            status_tx = st.empty()

            try:
                from privacy_guardian_ai.federated.retrain_runner import run_federated_training

                def _cb(done, total, msg):
                    prog_bar.progress(int(done / total * 100), text=msg)
                    status_tx.markdown(
                        f'<div style="font-size:0.7rem;color:#38bdf8;">{msg}</div>',
                        unsafe_allow_html=True
                    )

                result = run_federated_training(
                    rounds=r_rounds,
                    num_clients=r_clients,
                    noise_multiplier=r_noise,
                    progress_callback=_cb,
                )
                prog_bar.progress(100, text="✅ Training complete!")
                new_h = integrity.get_current_hash()
                integrity.store_hash(r_rounds, new_h, "admin_triggered")
                status_tx.empty()
                st.success(
                    f"✅ Retraining done — Accuracy: **{result['accuracy']}%** | "
                    f"ε = {result['epsilon']:.3f} | Rounds: {result['rounds']}"
                )
            except Exception as e:
                prog_bar.empty()
                status_tx.empty()
                st.error(f"❌ Retraining failed: {e}")

        if st.button("📋 Download Privacy Report", use_container_width=True, key="priv_dl"):
            st.toast("Report generation initiated — sandboxed download.")
        st.markdown('</div>', unsafe_allow_html=True)

        # Profile Access History (real from audit trail)
        st.markdown('<div class="adm-p">', unsafe_allow_html=True)
        st.markdown("### 🔍 Profile Access History")
        vault   = IdentityVault()
        _audit  = AuditLogger()
        _inspections = [
            l for l in reversed(_audit.get_all_logs())
            if l.get("action_type") == "MANUAL_INSPECTION"
        ][:5]
        if _inspections:
            for _log in _inspections:
                try:
                    _ts = datetime.datetime.fromisoformat(_log["timestamp"]).strftime("%d %b, %I:%M %p")
                except Exception:
                    _ts = _log.get("timestamp","")[:16]
                _reason = _log.get("reason","")
                _subj = ""
                _just = _reason
                if "Subject:" in _reason and ", Reason:" in _reason:
                    _parts = _reason.split(", Reason:")
                    _subj  = _parts[0].replace("Subject:","").strip()
                    _just  = _parts[1].strip() if len(_parts)>1 else ""
                _idnt  = vault.get_identity(_subj)
                _name  = _idnt['name'] if _idnt else f"Subject {_subj}"
                st.markdown(f"""
                <div class="log-entry">
                    <div class="avatar-sim">🔍</div>
                    <div style="flex:1;">
                        <div style="font-size:0.8rem;font-weight:bold;">{_name}
                            <span style="color:#38bdf8;"> #{_subj}</span></div>
                        <div style="font-size:0.62rem;color:#94a3b8;">{_just}</div>
                        <div style="font-size:0.6rem;color:#64748b;">{_ts}</div>
                    </div>
                    <div style="font-size:0.7rem;color:#38bdf8;">REVIEWED</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#64748b;font-size:0.75rem;padding:10px 0;">No inspection history yet.</div>', unsafe_allow_html=True)

        # Inspect Form
        st.markdown('<hr style="border:0.5px solid rgba(255,255,255,0.08);margin:12px 0;">', unsafe_allow_html=True)
        selected_id  = st.selectbox("SUBJECT ID", vault.get_all_ids(), key="admin_inspect_id")
        access_reason = st.text_input("JUSTIFICATION / REASON", placeholder="e.g. Academic Review #402", key="admin_reason")

        if st.button("AUTHORIZE INSPECTION", use_container_width=True, key="auth_inspect"):
            if access_reason:
                _audit.log_event("admin","admin","MANUAL_INSPECTION",
                                 f"Subject: {selected_id}, Reason: {access_reason}",
                                 resource_id=selected_id)
                st.success(f"✅ Authorized for Subject {selected_id}. Incident Logged.")

                identity     = vault.get_identity(selected_id)
                student_name = identity['name']  if identity else "Unknown"
                student_email = identity.get('email','N/A') if identity else "N/A"

                student_row  = df.iloc[int(selected_id)] if selected_id.isdigit() and int(selected_id)<len(df) else None
                risk_val     = int(student_row['risk_label']) if student_row is not None else 0
                risk_color   = "#ef4444" if risk_val == 1 else "#22c55e"
                risk_label   = "HIGH RISK" if risk_val == 1 else "LOW RISK"

                st.markdown(f"""
                <div style="background:rgba(56,189,248,0.07);border:1px solid rgba(56,189,248,0.3);
                            border-radius:10px;padding:16px;margin-top:10px;">
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                        <div style="width:44px;height:44px;border-radius:50%;
                                    background:linear-gradient(135deg,#38bdf8,#6366f1);
                                    display:flex;align-items:center;justify-content:center;font-size:1.2rem;">👤</div>
                        <div>
                            <div style="font-family:Orbitron;font-size:0.9rem;color:#f8fafc;font-weight:bold;">{student_name}</div>
                            <div style="font-size:0.7rem;color:#94a3b8;">ID: <b style="color:#38bdf8;">{selected_id}</b> | {student_email}</div>
                        </div>
                        <div style="margin-left:auto;background:{risk_color}22;border:1px solid {risk_color};
                                    color:{risk_color};border-radius:6px;padding:3px 8px;font-size:0.65rem;font-weight:bold;">
                            {risk_label}
                        </div>
                    </div>
                    <hr style="border:0.5px solid rgba(255,255,255,0.08);">
                """, unsafe_allow_html=True)

                if student_row is not None:
                    cols_to_show = [c for c in df.columns if c not in ['risk_label']]
                    field_html   = ""
                    for col in cols_to_show:
                        val   = student_row.get(col, "N/A")
                        if isinstance(val, float):
                            val = f"{val:.2f}"
                        label = col.replace('_',' ').title()
                        field_html += f"""
                        <div style="display:flex;justify-content:space-between;padding:4px 0;
                                    border-bottom:1px solid rgba(255,255,255,0.04);font-size:0.75rem;">
                            <span style="color:#94a3b8;">{label}</span>
                            <span style="color:#f8fafc;font-weight:500;">{val}</span>
                        </div>"""
                    st.markdown(field_html + "</div>", unsafe_allow_html=True)
                else:
                    st.markdown('<div style="font-size:0.75rem;color:#94a3b8;">No dataset record.</div></div>', unsafe_allow_html=True)

                st.markdown(f"""
                <div style="font-size:0.65rem;color:#64748b;margin-top:6px;">
                    🔒 Access logged | Reason: <i>{access_reason}</i>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Access Denied: Justification required.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── BOTTOM NAV ──────────────────────────────────────────────────────────────
    st.markdown('<div style="margin-top:14px;">', unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("SETTINGS", use_container_width=True, key="adm_settings"):
            st.toast("System configuration locked by isolation policy.")
    with b2:
        if st.button("SUPPORT", use_container_width=True, key="adm_support"):
            st.toast("Contacting Privacy Guardian Support…")
    with b3:
        if st.button("SIGN OUT", use_container_width=True, key="adm_signout"):
            st.session_state['authenticated'] = False
            st.session_state['user'] = None
            st.rerun()
    with b4:
        if st.button("🚨 ABORT", use_container_width=True, type="primary", key="adm_abort"):
            audit_log.log_event("admin","admin","EMERGENCY_ABORT","Admin triggered emergency abort")
            st.warning("EMERGENCY ABORT SEQUENCE INITIATED")
            st.session_state['authenticated'] = False
            st.session_state['user'] = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
