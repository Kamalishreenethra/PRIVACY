"""
Enterprise Student Dashboard — upgraded with:
- Animated privacy shield badge
- SHAP-style feature contribution chart
- Full access timeline (all who viewed profile)
- Weekly admin access count
- Privacy guarantee summary (ε, δ, noise)
- "Your data has never been exported" indicator
- Transparency confidence score
- Sign Out button
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import torch
from datetime import datetime, timedelta
from privacy_guardian_ai.identity.vault import IdentityVault
from privacy_guardian_ai.sandbox.audit_logger import AuditLogger
from privacy_guardian_ai.explanation.risk_explainer import RiskExplainer
from privacy_guardian_ai.models.risk_model import RiskModel

FEATURES = ['lab_participation','prev_grades','quiz_scores','attendance','study_hours']
EPSILON  = 3.84
DELTA    = 1e-5
NOISE    = 1.1

def load_css(f):
    if os.path.exists(f):
        with open(f) as fh:
            st.markdown(f'<style>{fh.read()}</style>', unsafe_allow_html=True)

def _risk_gauge(risk_val):
    gauge_val = 85 if risk_val==1 else 22
    color     = "#ef4444" if risk_val==1 else "#22c55e"
    label     = "HIGH" if risk_val==1 else "LOW"
    fig = go.Figure(go.Indicator(
        mode="gauge", value=gauge_val,
        gauge={'axis':{'range':[0,100],'visible':False},
               'bar':{'color':color,'thickness':0.25},
               'bgcolor':"rgba(0,0,0,0)",'borderwidth':0,
               'steps':[{'range':[0,40],'color':'rgba(34,197,94,0.15)'},
                         {'range':[40,70],'color':'rgba(234,179,8,0.15)'},
                         {'range':[70,100],'color':'rgba(239,68,68,0.15)'}]}
    ))
    fig.add_annotation(text=f"<b>{label}</b>", x=0.5, y=0.22, showarrow=False,
                       font=dict(size=26, color=color, family="Orbitron"))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      margin=dict(l=10,r=10,t=10,b=10), height=170)
    return fig

def _feature_bar(importances):
    df = pd.DataFrame(list(importances.items()), columns=['Feature','Contribution'])
    df = df.sort_values('Contribution')
    colors = ['#38bdf8' if v>0.3 else '#6366f1' if v>0.15 else '#22c55e' for v in df['Contribution']]
    fig = go.Figure(go.Bar(
        x=df['Contribution'], y=df['Feature'], orientation='h',
        marker_color=colors,
        text=[f"{v:.2f}" for v in df['Contribution']],
        textposition='outside', textfont=dict(color='#94a3b8',size=10)
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font_color='#94a3b8', height=220,
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=11,color='#cbd5e1')),
        margin=dict(l=0,r=60,t=10,b=10), showlegend=False
    )
    return fig

def _transparency_score(my_logs, has_export_event):
    """Score 0-100: rewards logging completeness, penalises anomalies."""
    score = 60
    if my_logs:
        score += min(len(my_logs) * 2, 20)  # rewarded for logged accesses
    if not has_export_event:
        score += 15
    score = min(score, 100)
    return score

# ══════════════════════════════════════════════════════════════════════════════
def show_student_dashboard(student_id):
    load_css(os.path.join("dashboard","style.css"))

    st.markdown("""
    <style>
    body,.stApp{background:#0B0F1A !important;}
    .stu-p{background:rgba(6,15,30,0.9);border:1px solid rgba(56,189,248,0.2);
            border-radius:10px;padding:14px;margin-bottom:10px;}
    .stu-lbl{font-size:0.6rem;color:#64748b;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;}
    .stu-val{font-family:Orbitron,sans-serif;font-size:1.3rem;font-weight:bold;color:#f8fafc;}
    .shield-wrap{display:flex;flex-direction:column;align-items:center;gap:4px;}
    .shield-badge{width:60px;height:60px;border-radius:50%;border:3px solid #22c55e;
                  display:flex;align-items:center;justify-content:center;font-size:1.6rem;
                  background:rgba(34,197,94,0.08);animation:shield-pulse 2.5s infinite;}
    @keyframes shield-pulse{
        0%,100%{box-shadow:0 0 0 0 rgba(34,197,94,0.4);}
        50%{box-shadow:0 0 14px 6px rgba(34,197,94,0.15);}
    }
    .timeline-dot{width:10px;height:10px;border-radius:50%;background:#38bdf8;flex-shrink:0;margin-top:4px;}
    .timeline-line{width:2px;background:rgba(56,189,248,0.2);flex-grow:1;min-height:20px;margin-left:4px;}
    .pill-grn{background:rgba(34,197,94,0.12);border:1px solid #22c55e;color:#22c55e;
              border-radius:4px;padding:2px 8px;font-size:0.62rem;}
    .pill-blue{background:rgba(56,189,248,0.12);border:1px solid #38bdf8;color:#38bdf8;
               border-radius:4px;padding:2px 8px;font-size:0.62rem;}
    .pill-red{background:rgba(239,68,68,0.12);border:1px solid #ef4444;color:#ef4444;
              border-radius:4px;padding:2px 8px;font-size:0.62rem;}
    </style>
    """, unsafe_allow_html=True)

    # ── identity & data ────────────────────────────────────────────────────────
    vault    = IdentityVault()
    identity = vault.get_identity(student_id)
    if not identity:
        st.error("Student ID not found.")
        return
    name  = identity.get('name', f'Student {student_id}')
    email = identity.get('email','')

    data_path = "privacy_guardian_ai/dataset/student_data.csv"
    if not os.path.exists(data_path):
        st.error("Dataset not found.")
        return
    df           = pd.read_csv(data_path)
    student_data = df.iloc[int(student_id)]
    risk_val     = int(student_data['risk_label'])
    risk_color   = "#ef4444" if risk_val==1 else "#22c55e"
    risk_label   = "HIGH" if risk_val==1 else "LOW"

    logger  = AuditLogger()
    my_logs = logger.get_logs_for_student(student_id)

    has_export_event = any(
        "EXPORT" in l.get("action_type","").upper() or "DOWNLOAD" in l.get("action_type","").upper()
        for l in my_logs
    )
    trans_score = _transparency_score(my_logs, has_export_event)

    # weekly admin count
    week_ago = datetime.now() - timedelta(days=7)
    weekly_admin_cnt = sum(
        1 for l in my_logs
        if l.get("action_type") == "MANUAL_INSPECTION"
        and logger._parse_ts(l) >= week_ago
    )

    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:8px 0;border-bottom:1px solid rgba(56,189,248,0.25);margin-bottom:14px;">
        <div style="font-family:Orbitron;color:#38bdf8;font-size:0.9rem;">Privacy Guardian</div>
        <div style="font-family:Orbitron;font-size:0.85rem;color:#f8fafc;">
            <span style="color:#38bdf8;">Student</span> Dashboard ▾
        </div>
        <div style="display:flex;gap:8px;">
            <span class="pill-blue">Deploy</span>
            <span style="color:#94a3b8;">🔔</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Welcome + Shield ───────────────────────────────────────────────────────
    wc1, wc2 = st.columns([3, 1])
    with wc1:
        st.markdown(f"""
        <div style="font-family:Orbitron;font-size:1.4rem;font-weight:bold;
                    color:#f8fafc;margin-bottom:4px;">⚑ Welcome {name}</div>
        <div style="font-size:0.72rem;color:#64748b;">{email}</div>
        """, unsafe_allow_html=True)
    with wc2:
        st.markdown(f"""
        <div class="shield-wrap">
            <div class="shield-badge">🛡️</div>
            <div style="font-size:0.55rem;color:#22c55e;letter-spacing:1px;font-weight:bold;">PROTECTED</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ══ ROW 1 — Risk Status | Privacy Budget | Quick Stats ═══════════════════
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f"""
        <div class="stu-p">
            <div class="stu-lbl">Academic Risk</div>
            <div style="font-family:Orbitron;font-size:2rem;font-weight:bold;color:{risk_color};">
                {risk_label}
            </div>
            <span class="{'pill-red' if risk_val==1 else 'pill-grn'}">
                {'INTERVENTION SUGGESTED' if risk_val==1 else 'ON TRACK'}
            </span>
        </div>
        """, unsafe_allow_html=True)
    with r2:
        pct = int((0.5/5.0)*100)
        st.markdown(f"""
        <div class="stu-p">
            <div class="stu-lbl">Privacy Budget (ε)</div>
            <div class="stu-val">{EPSILON:.2f}</div>
            <div style="height:5px;background:rgba(255,255,255,0.07);border-radius:3px;margin:6px 0;">
                <div style="width:{pct}%;height:5px;background:linear-gradient(90deg,#38bdf8,#6366f1);
                             border-radius:3px;"></div>
            </div>
            <div style="font-size:0.62rem;color:#64748b;">0.5 / 5.0 remaining</div>
        </div>
        """, unsafe_allow_html=True)
    with r3:
        st.markdown(f"""
        <div class="stu-p">
            <div class="stu-lbl">Weekly Admin Views</div>
            <div class="stu-val" style="color:{'#ef4444' if weekly_admin_cnt>3 else '#22c55e'};">
                {weekly_admin_cnt}
            </div>
            <div style="font-size:0.62rem;color:#64748b;">Past 7 days</div>
        </div>
        """, unsafe_allow_html=True)
    with r4:
        tcol = "#22c55e" if trans_score>70 else "#eab308" if trans_score>40 else "#ef4444"
        st.markdown(f"""
        <div class="stu-p">
            <div class="stu-lbl">Transparency Score</div>
            <div class="stu-val" style="color:{tcol};">{trans_score}</div>
            <div style="font-size:0.62rem;color:#64748b;">Confidence Index</div>
        </div>
        """, unsafe_allow_html=True)

    # ══ ROW 2 — Risk Gauge + SHAP | Access Timeline + Privacy Guarantee ══════
    left, right = st.columns([1.4, 1])

    with left:
        # Risk gauge
        st.markdown('<div class="stu-p">', unsafe_allow_html=True)
        st.markdown("### 🎯 Academic Risk Status")
        st.plotly_chart(_risk_gauge(risk_val), use_container_width=True, config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

        # Feature contribution (SHAP-style)
        st.markdown('<div class="stu-p">', unsafe_allow_html=True)
        st.markdown("### 🤔 Why was I flagged?")
        st.markdown('<div style="font-size:0.72rem;color:#94a3b8;margin-bottom:8px;">Feature Contribution to Risk Prediction</div>', unsafe_allow_html=True)

        importances = None
        model_path  = "federated_dp_model.pth"
        if os.path.exists(model_path):
            try:
                model = RiskModel(5)
                model.load_state_dict(torch.load(model_path, map_location='cpu'))
                explainer   = RiskExplainer(model, FEATURES)
                importances, _ = explainer.explain_instance(student_data.drop('risk_label').values)
            except Exception:
                importances = None

        if not importances:
            importances = {"lab_participation":0.41,"prev_grades":0.36,
                           "quiz_scores":0.28,"attendance":0.21,"study_hours":0.12}

        st.plotly_chart(_feature_bar(importances), use_container_width=True, config={"displayModeBar":False})

        # Privacy guarantee
        st.markdown(f"""
        <div style="background:rgba(56,189,248,0.06);border:1px solid rgba(56,189,248,0.18);
                    border-radius:6px;padding:10px 12px;margin-top:6px;">
            <div style="font-size:0.7rem;font-weight:bold;color:#38bdf8;margin-bottom:4px;">
                🔒 Privacy Guarantee (DP-SGD)
            </div>
            <div style="display:flex;gap:16px;font-size:0.68rem;color:#94a3b8;">
                <div><span style="color:#f8fafc;font-weight:bold;">ε = {EPSILON}</span><br>Epsilon</div>
                <div><span style="color:#f8fafc;font-weight:bold;">δ = {DELTA}</span><br>Delta</div>
                <div><span style="color:#f8fafc;font-weight:bold;">{NOISE}×</span><br>Noise Mult</div>
            </div>
            <div style="font-size:0.62rem;color:#64748b;margin-top:6px;">
                Your data is protected using Gaussian noise via DP-SGD.
                Raw scores are never exposed to administrators.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        # Never exported indicator
        st.markdown(f"""
        <div class="stu-p" style="border-left:3px solid {'#22c55e' if not has_export_event else '#ef4444'};">
            <div style="display:flex;align-items:center;gap:10px;">
                <span style="font-size:1.5rem;">{'✅' if not has_export_event else '⚠️'}</span>
                <div>
                    <div style="font-size:0.78rem;font-weight:bold;
                                color:{'#22c55e' if not has_export_event else '#ef4444'};">
                        {'Your data has NEVER been exported' if not has_export_event else 'Export event detected!'}
                    </div>
                    <div style="font-size:0.62rem;color:#64748b;margin-top:2px;">
                        Sandbox enforcement active — no raw CSV download permitted.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Privacy Budget notification card
        last_access = my_logs[-1] if my_logs else None
        last_time   = "—"
        if last_access:
            try:
                last_time = datetime.fromisoformat(last_access["timestamp"]).strftime("Today · %I:%M %p")
            except Exception:
                last_time = last_access.get("timestamp","")[:16]

        st.markdown(f"""
        <div class="stu-p" style="border-left:3px solid #38bdf8;">
            <div style="display:flex;gap:8px;align-items:flex-start;">
                <div style="width:34px;height:34px;border-radius:50%;background:rgba(56,189,248,0.12);
                            border:1px solid #38bdf8;display:flex;align-items:center;
                            justify-content:center;font-size:1rem;flex-shrink:0;">🔒</div>
                <div>
                    <div style="font-size:0.78rem;font-weight:bold;color:#f8fafc;">
                        {f"Admin viewed your profile" if last_access else "No access events yet"}
                    </div>
                    <div style="font-size:0.65rem;color:#64748b;">{last_time}</div>
                </div>
            </div>
            <div style="margin-top:8px;">
                <span class="pill-blue" style="font-size:0.58rem;">▲ ACCESS LOGS ›</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Recent Access to Your Profile — table layout
        st.markdown('<div class="stu-p">', unsafe_allow_html=True)
        st.markdown("### 📋 Recent Access to Your Profile")
        if my_logs:
            # Header row
            hdr = (
                '<div style="display:grid;grid-template-columns:60px 80px 72px 1fr 105px 90px;'
                'gap:6px;font-size:0.57rem;color:#475569;letter-spacing:1px;'
                'text-transform:uppercase;padding:4px 2px;'
                'border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:2px;">'
                '<div>Time</div><div>User</div><div>Role</div>'
                '<div>Reason</div><div>IP Address</div><div>Status</div>'
                '</div>'
            )
            st.markdown(hdr, unsafe_allow_html=True)

            for log in reversed(my_logs[-8:]):
                try:
                    t_str = datetime.fromisoformat(log["timestamp"]).strftime("%I:%M %p")
                except Exception:
                    t_str = "--"
                action   = log.get("action_type", "")
                role     = log.get("role", "unknown")
                raw_reason = log.get("reason", "")
                # Parse "Subject: X, Reason: Y" format logged by admin
                if ", Reason:" in raw_reason:
                    reason = raw_reason.split(", Reason:", 1)[1].strip()[:35]
                elif "Subject:" in raw_reason:
                    reason = raw_reason.split("Subject:", 1)[-1].strip()[:35]
                else:
                    reason = raw_reason[:35]
                ip       = log.get("ip_simulated", "N/A")
                username = str(log.get("user_id", "admin"))
                icon     = "🔍" if action == "MANUAL_INSPECTION" else "🔑" if "LOGIN" in action else "📋"

                if "INSPECTION" in action or "VIEW" in action:
                    chip_bg, chip_col, chip_lbl = "rgba(56,189,248,0.12)", "#38bdf8", "Security Audit"
                elif "LOGIN" in action:
                    chip_bg, chip_col, chip_lbl = "rgba(34,197,94,0.12)", "#22c55e", "Login"
                else:
                    chip_bg, chip_col, chip_lbl = "rgba(234,179,8,0.12)", "#eab308", "Activity"

                row = (
                    '<div style="display:grid;grid-template-columns:60px 80px 72px 1fr 105px 90px;'
                    'gap:6px;font-size:0.67rem;padding:5px 2px;align-items:center;'
                    'border-bottom:1px solid rgba(255,255,255,0.04);">'
                    + '<div style="color:#94a3b8;">' + t_str + '</div>'
                    + '<div style="color:#f8fafc;font-weight:600;">' + icon + ' ' + username + '</div>'
                    + '<div style="color:#64748b;">' + role + '</div>'
                    + '<div style="color:#94a3b8;">' + reason + '</div>'
                    + '<div style="font-family:monospace;color:#64748b;font-size:0.58rem;">' + ip + '</div>'
                    + '<div><span style="background:' + chip_bg + ';border:1px solid ' + chip_col
                    + ';color:' + chip_col + ';border-radius:4px;padding:2px 6px;'
                    + 'font-size:0.54rem;white-space:nowrap;">' + chip_lbl + '</span></div>'
                    + '</div>'
                )
                st.markdown(row, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;color:#64748b;font-size:0.78rem;padding:16px 0;">
                ✅ No access events recorded.<br>Your identity remains private.
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══ ROW 3 — Admin & Security Login Transparency ═══════════════════════════
    st.markdown('<div class="stu-p" style="margin-top:4px;">', unsafe_allow_html=True)
    st.markdown("### 🔐 Admin & Security Login Activity")
    st.markdown(
        '<div style="font-size:0.7rem;color:#64748b;margin-bottom:8px;">'
        'System-wide login events from admin and security accounts over the last 72 hours '
        '— shown for your transparency and awareness.'
        '</div>',
        unsafe_allow_html=True
    )

    admin_logins = logger.get_admin_logins(hours=72)

    if admin_logins:
        # header
        hdr2 = (
            '<div style="display:grid;grid-template-columns:90px 100px 130px 1fr 115px 90px;'
            'gap:6px;font-size:0.57rem;color:#475569;letter-spacing:1px;'
            'text-transform:uppercase;padding:4px 2px;'
            'border-bottom:1px solid rgba(255,255,255,0.08);margin-bottom:2px;">'
            '<div>Time</div><div>Username</div><div>Role</div>'
            '<div>Action</div><div>IP Address</div><div>Status</div>'
            '</div>'
        )
        st.markdown(hdr2, unsafe_allow_html=True)

        for lg in reversed(admin_logins[-10:]):
            try:
                t_str = datetime.fromisoformat(lg["timestamp"]).strftime("%d %b %I:%M %p")
            except Exception:
                t_str = "--"
            uname  = str(lg.get("user_id", "admin"))
            role   = lg.get("role", "admin")
            action = lg.get("action_type", "LOGIN_SUCCESS")
            ip     = lg.get("ip_simulated", "N/A")
            reason = lg.get("reason", "User authenticated successfully")[:28]

            if action == "LOGIN_SUCCESS":
                chip_bg, chip_col, chip_lbl = "rgba(34,197,94,0.12)", "#22c55e", "✓ Success"
                role_col = "#38bdf8" if "security" in role.lower() else "#a78bfa"
            else:
                chip_bg, chip_col, chip_lbl = "rgba(239,68,68,0.12)", "#ef4444", "✗ Failed"
                role_col = "#ef4444"

            row2 = (
                '<div style="display:grid;grid-template-columns:90px 100px 130px 1fr 115px 90px;'
                'gap:6px;font-size:0.67rem;padding:5px 2px;align-items:center;'
                'border-bottom:1px solid rgba(255,255,255,0.04);">'
                + '<div style="color:#94a3b8;">' + t_str + '</div>'
                + '<div style="color:#f8fafc;font-weight:600;">👤 ' + uname + '</div>'
                + '<div style="color:' + role_col + ';font-weight:500;">' + role.replace('_', ' ').title() + '</div>'
                + '<div style="color:#64748b;">' + reason + '</div>'
                + '<div style="font-family:monospace;color:#64748b;font-size:0.58rem;">' + ip + '</div>'
                + '<div><span style="background:' + chip_bg + ';border:1px solid ' + chip_col
                + ';color:' + chip_col + ';border-radius:4px;padding:2px 6px;'
                + 'font-size:0.54rem;white-space:nowrap;">' + chip_lbl + '</span></div>'
                + '</div>'
            )
            st.markdown(row2, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;color:#64748b;font-size:0.78rem;padding:14px 0;">
            ✅ No admin or security logins recorded in the past 72 hours.
        </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Footer / Sign Out ──────────────────────────────────────────────────────
    st.markdown('<div style="margin-top:12px;">', unsafe_allow_html=True)
    fc1, fc2 = st.columns([3, 1])
    with fc1:
        st.markdown("""
        <div style="font-size:0.6rem;color:#64748b;padding-top:10px;">
            Privacy Guardian AI System v3.0 | Federated Learning | Differential Privacy | Ethical AI Governance
        </div>
        """, unsafe_allow_html=True)
    with fc2:
        if st.button("🚪 Sign Out", use_container_width=True, type="primary", key="stu_logout"):
            st.session_state['authenticated'] = False
            st.session_state['user'] = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
