"""
Enterprise Security Dashboard — Cyber Defense Control Center
Panels: Threat Score | Auto-Mitigation | Privacy Budget History |
        Model Integrity | MIA Monitoring | Compliance Mode | Anomaly Feed
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import random
from datetime import datetime, timedelta

from privacy_guardian_ai.sandbox.audit_logger import AuditLogger
from privacy_guardian_ai.defender.threat_engine import ThreatScoreEngine
from privacy_guardian_ai.defender.auto_mitigator import AutoMitigator
from privacy_guardian_ai.defender.model_integrity import ModelIntegrityVerifier
from privacy_guardian_ai.anomaly_detection.detector import AnomalyDetector
from privacy_guardian_ai.compliance.mode_manager import ComplianceModeManager

# ── constants / mock data ──────────────────────────────────────────────────────
EPSILON      = 3.84
NOISE_MULT   = 1.1
ATK_ACCURACY = 0.522   # as float
BLOCKED_CNT  = 13

EXFIL_IPS = [
    {"ip": "192.32.0.105",  "bar": 80, "time": "15:52", "note": "Current ε = 9.88"},
    {"ip": "172.16.4.52",   "bar": 60, "time": "15:49", "note": "Attempt lot decided"},
    {"ip": "10.100.28.115", "bar": 90, "time": "15:41", "note": "Model weight (false)"},
    {"ip": "156.34.221.34", "bar": 50, "time": "15:31", "note": "Attempted lab export"},
    {"ip": "221.43.76.172", "bar": 75, "time": "15:30", "note": "Sandbox file copy"},
]
MIA_ROWS = [
    {"ip": "192.168.0.105", "risk": "HIGH",   "col": "#ef4444", "data": "Attempted data download"},
    {"ip": "172.16.4.52",   "risk": "MEDIUM", "col": "#eab308", "data": "API dataset request"},
    {"ip": "10.100.28.115", "risk": "HIGH",   "col": "#ef4444", "data": "Model weight download"},
    {"ip": "156.34.221.34", "risk": "MEDIUM", "col": "#eab308", "data": "Attempted lab export"},
    {"ip": "221.43.76.172", "risk": "HIGH",   "col": "#ef4444", "data": "Sandbox file copy"},
]
ALERT_ROWS = [
    {"time": "Today 15:32", "agent": "High Fidelton Agnt",        "type": "⚠️ Threshold Breach",  "detail": "Current ε = 3.8"},
    {"time": "Today 15:49", "agent": "Data Exfiltration",         "type": "🔴 Exfil Detected",    "detail": "Download blocked"},
    {"time": "Today 15:41", "agent": "Admin Access Spike",        "type": "🟡 Anomaly",            "detail": "15 min profile view"},
    {"time": "Today 15:30", "agent": "Connection Anomaly",        "type": "⚠️ Reconnection",      "detail": "50 unfinished"},
]

def load_css(f):
    if os.path.exists(f):
        with open(f) as fh:
            st.markdown(f'<style>{fh.read()}</style>', unsafe_allow_html=True)

def _sparkline(vals, color="#22c55e"):
    fig = go.Figure(go.Scatter(
        x=list(range(len(vals))), y=vals, mode="lines",
        line=dict(color=color, width=1.5),
        fill="tozeroy", fillcolor=f"rgba({','.join(str(int(color.lstrip('#')[i:i+2],16)) for i in (0,2,4))},0.08)"
    ))
    fig.update_layout(height=80, margin=dict(l=0,r=0,t=0,b=0),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False)
    return fig

def _donut(val, total, color="#22c55e", label=""):
    fig = go.Figure(go.Pie(
        values=[val, max(total-val,0)], labels=[label,""],
        hole=0.72, marker_colors=[color,"rgba(255,255,255,0.05)"], textinfo="none"
    ))
    fig.add_annotation(text=f"<b>{val}</b>", x=0.5, y=0.5, showarrow=False,
                       font=dict(size=20, color="#f8fafc", family="Orbitron"))
    fig.update_layout(height=120, margin=dict(l=0,r=0,t=0,b=0),
                      paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
    return fig

# ══════════════════════════════════════════════════════════════════════════════
def show_security_dashboard():
    load_css(os.path.join("dashboard","style.css"))

    st.markdown("""
    <style>
    body,.stApp{background:#0B0F1A !important;}
    .sec-p{background:rgba(6,15,30,0.9);border:1px solid rgba(34,197,94,0.2);
            border-radius:10px;padding:14px;margin-bottom:10px;}
    .sec-lbl{font-size:0.6rem;color:#64748b;letter-spacing:1.5px;text-transform:uppercase;}
    .sec-val{font-family:Orbitron,sans-serif;font-size:1.3rem;font-weight:bold;color:#f8fafc;}
    .badge-safe{background:rgba(34,197,94,0.15);border:1px solid #22c55e;color:#22c55e;
                border-radius:6px;padding:3px 10px;font-size:0.7rem;font-weight:bold;
                animation:pulse-g 2s infinite;}
    .badge-elev{background:rgba(234,179,8,0.15);border:1px solid #eab308;color:#eab308;
                border-radius:6px;padding:3px 10px;font-size:0.7rem;font-weight:bold;
                animation:pulse-y 2s infinite;}
    .badge-crit{background:rgba(239,68,68,0.15);border:1px solid #ef4444;color:#ef4444;
                border-radius:6px;padding:3px 10px;font-size:0.7rem;font-weight:bold;
                animation:pulse-r 1s infinite;}
    @keyframes pulse-g{0%,100%{box-shadow:0 0 0 0 rgba(34,197,94,0.4)}
                        50%{box-shadow:0 0 8px 4px rgba(34,197,94,0.2)}}
    @keyframes pulse-y{0%,100%{box-shadow:0 0 0 0 rgba(234,179,8,0.4)}
                        50%{box-shadow:0 0 8px 4px rgba(234,179,8,0.2)}}
    @keyframes pulse-r{0%,100%{box-shadow:0 0 0 0 rgba(239,68,68,0.5)}
                        50%{box-shadow:0 0 10px 6px rgba(239,68,68,0.25)}}
    .mit-on{background:rgba(239,68,68,0.12);border:1px solid #ef4444;border-radius:8px;
            padding:10px;color:#ef4444;font-weight:bold;animation:pulse-r 1s infinite;}
    .mit-off{background:rgba(34,197,94,0.07);border:1px solid rgba(34,197,94,0.3);
             border-radius:8px;padding:10px;color:#22c55e;}
    .hash-box{font-family:monospace;font-size:0.62rem;color:#38bdf8;
              background:rgba(56,189,248,0.07);border:1px solid rgba(56,189,248,0.2);
              border-radius:4px;padding:4px 8px;word-break:break-all;}
    .anom-row{display:flex;gap:8px;align-items:center;padding:5px 0;
              border-bottom:1px solid rgba(255,255,255,0.05);font-size:0.72rem;}
    .ip-row{display:flex;align-items:center;gap:8px;padding:5px 0;
            border-bottom:1px solid rgba(255,255,255,0.05);font-size:0.72rem;}
    .alert-row{display:flex;gap:8px;padding:5px 0;font-size:0.7rem;
               border-bottom:1px solid rgba(255,255,255,0.05);}
    div[data-testid="stPlotlyChart"]{padding:0!important;}
    </style>
    """, unsafe_allow_html=True)

    # ── instantiate engines ────────────────────────────────────────────────────
    logger    = AuditLogger()
    anomaly_d = AnomalyDetector()
    threat_e  = ThreatScoreEngine()
    auto_mit  = AutoMitigator(noise_multiplier=NOISE_MULT)
    integrity = ModelIntegrityVerifier()
    comp_mgr  = ComplianceModeManager()

    admin_cnt     = logger.get_inspection_count(hours=1)
    anomalies     = anomaly_d.detect()
    sus_logins    = anomaly_d.get_suspicious_login_count(24)
    eps_history   = logger.get_epsilon_history(30)
    eps_growth    = abs(eps_history[-1]["epsilon"] - eps_history[-2]["epsilon"]) if len(eps_history)>=2 else 0.1
    threat_result = threat_e.compute(ATK_ACCURACY, admin_cnt, eps_growth, sus_logins)
    mit_result    = auto_mit.evaluate(ATK_ACCURACY, EPSILON, admin_cnt)
    integrity_v   = integrity.verify()

    # initial hash store if chain empty
    if not integrity.get_chain():
        h = integrity.get_current_hash()
        integrity.store_hash(30, h, "model_file")

    # ── compliance mode (need to do before header so we have mode) ─────────────
    current_mode = comp_mgr.get_mode()
    mode_colors  = {"STANDARD": "#38bdf8", "STRICT": "#eab308", "AUDIT": "#ef4444"}
    mode_col     = mode_colors.get(current_mode, "#38bdf8")

    # ── TOP HEADER ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:8px 0;border-bottom:1px solid rgba(34,197,94,0.3);margin-bottom:14px;">
        <div style="display:flex;align-items:center;gap:8px;">
            <span style="font-size:1.3rem;">🛡️</span>
            <span style="font-family:Orbitron;color:#22c55e;font-size:0.9rem;">Privacy Guardian</span>
        </div>
        <div style="font-family:Orbitron;font-size:1.2rem;font-weight:bold;letter-spacing:3px;">
            Welcome Security Admin
        </div>
        <div style="display:flex;gap:10px;align-items:center;">
            <span style="border:1px solid {mode_col};color:{mode_col};border-radius:4px;
                         padding:2px 8px;font-size:0.65rem;font-weight:bold;">{current_mode}</span>
            <span style="color:#94a3b8;font-size:0.8rem;">👤 Security Admin</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ══ ROW 1 — Threat Score | Attack Rate | Exfil Donut | Log Accuracy ═══════
    c1, c2, c3, c4 = st.columns([1.1, 1.3, 1.2, 1.1])

    with c1:
        badge_cls = {"SAFE":"badge-safe","ELEVATED":"badge-elev","CRITICAL":"badge-crit"}[threat_result["label"]]
        score_bar = int(threat_result["score"])
        st.markdown(f"""
        <div class="sec-p">
            <div class="sec-lbl">Threat Severity Engine</div>
            <div style="display:flex;align-items:baseline;gap:10px;margin:8px 0;">
                <div class="sec-val" style="font-size:2rem;color:{threat_result['color']};">
                    {threat_result['score']:.0f}
                </div>
                <div style="font-size:0.65rem;color:#64748b;">/100</div>
            </div>
            <span class="{badge_cls}">{threat_result['label']}</span>
            <div style="height:4px;background:rgba(255,255,255,0.07);border-radius:2px;margin:10px 0;">
                <div style="width:{score_bar}%;height:4px;background:{threat_result['color']};
                             border-radius:2px;transition:width 0.5s;"></div>
            </div>
            <div style="font-size:0.6rem;color:#64748b;margin-top:6px;">
                ATK:{threat_result['components']['attack_accuracy']:.1f} |
                ADM:{threat_result['components']['admin_freq']:.1f} |
                EPS:{threat_result['components']['eps_growth']:.1f} |
                SUS:{threat_result['components']['suspicious_logins']:.1f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        random.seed(42)
        spark_y = [random.uniform(3000,3800) + random.uniform(-200,500)*(i/40) for i in range(40)]
        st.markdown('<div class="sec-p">', unsafe_allow_html=True)
        st.markdown('<div class="sec-lbl">Recent Attack Rate ↑↑</div>', unsafe_allow_html=True)
        st.plotly_chart(_sparkline(spark_y), use_container_width=True, config={"displayModeBar":False})
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;font-size:0.72rem;">
            <div>
                <div class="sec-lbl">Latest Accuracy</div>
                <div style="color:#22c55e;font-weight:bold;">↗ {ATK_ACCURACY*100:.1f}%</div>
            </div>
            <div style="width:28px;height:8px;background:#ef4444;border-radius:2px;
                        align-self:flex-end;margin-bottom:4px;"></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c3:
        mia_color = "#22c55e" if ATK_ACCURACY < 0.55 else "#eab308" if ATK_ACCURACY < 0.65 else "#ef4444"
        mia_label = "SAFE" if ATK_ACCURACY < 0.55 else "ELEVATED" if ATK_ACCURACY < 0.65 else "HIGH RISK"
        st.markdown('<div class="sec-p">', unsafe_allow_html=True)
        st.markdown('<div class="sec-lbl">Attempted Exfiltrations</div>', unsafe_allow_html=True)
        d1, d2 = st.columns([1,1])
        with d1:
            st.plotly_chart(_donut(BLOCKED_CNT,17,"#22c55e","BLOCKED"),
                            use_container_width=True, config={"displayModeBar":False})
        with d2:
            st.markdown(f"""
            <div style="padding-top:20px;">
                <div class="sec-lbl">BLOCKED</div>
                <div style="font-family:Orbitron;color:#22c55e;font-size:1rem;font-weight:bold;">+52%</div>
                <div style="margin-top:8px;">
                    <span style="font-size:0.6rem;color:{mia_color};font-weight:bold;">{mia_label}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="sec-p">
            <div class="sec-lbl">Current Log Accuracy ···</div>
            <table style="width:100%;font-size:0.72rem;border-collapse:collapse;margin-top:8px;">
                <tr><td style="color:#94a3b8;padding:4px 0;">EPSILON</td>
                    <td style="color:#38bdf8;font-weight:bold;text-align:right;">{EPSILON}</td>
                    <td style="color:#22c55e;text-align:right;">1.0</td></tr>
                <tr><td style="color:#94a3b8;padding:4px 0;">NOISE MULT</td>
                    <td style="color:#38bdf8;font-weight:bold;text-align:right;">{auto_mit.noise_multiplier}</td>
                    <td style="color:#22c55e;text-align:right;">{ATK_ACCURACY*100:.1f}%</td></tr>
                <tr><td style="color:#94a3b8;padding:4px 0;">ATTACK ACC.</td>
                    <td colspan="2" style="color:#ef4444;font-weight:bold;text-align:right;">{ATK_ACCURACY*100:.1f}%</td></tr>
            </table>
            <div style="height:3px;background:linear-gradient(90deg,#22c55e,#38bdf8,#ef4444);
                        border-radius:2px;margin-top:10px;"></div>
        </div>
        """, unsafe_allow_html=True)

    # ══ ROW 2 — Auto-Mitigation | Model Integrity ════════════════════════════
    am_col, mi_col = st.columns(2)

    with am_col:
        if mit_result["status"] == "ACTIVATED":
            st.markdown(f"""
            <div class="mit-on">
                <div style="font-size:0.8rem;margin-bottom:6px;">⚡ AUTO-MITIGATION ACTIVATED</div>
                <div style="font-size:0.7rem;font-weight:normal;color:#fca5a5;">
                    {'<br>'.join(mit_result['triggers'])}
                </div>
                <div style="margin-top:8px;font-size:0.7rem;color:#f8fafc;">
                    Actions: {'  |  '.join(mit_result['actions'])}
                </div>
                <div style="margin-top:8px;font-size:0.65rem;">
                    Noise: <b>{mit_result['noise_multiplier']}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="mit-off">
                <div style="font-size:0.8rem;">✅ AUTO-MITIGATION: STANDBY</div>
                <div style="font-size:0.7rem;color:#94a3b8;margin-top:4px;">
                    All thresholds within acceptable range. System nominal.
                </div>
            </div>
            """, unsafe_allow_html=True)

    with mi_col:
        integrity_color = "#22c55e" if integrity_v["valid"] else "#ef4444"
        integrity_icon  = "✅" if integrity_v["valid"] else "🚨"
        chain = integrity.get_chain(3)
        latest_hash = chain[-1].get("model_hash","")[:20]+"..." if chain else "N/A"
        chain_pills = "".join(
            '<div style="font-size:0.6rem;color:#38bdf8;background:rgba(56,189,248,0.07);'
            'border-radius:3px;padding:2px 6px;">Round '
            + str(e.get("round","?")) + " ✓</div>"
            for e in chain
        )
        st.markdown(f"""
        <div class="sec-p" style="border-left:3px solid {integrity_color};">
            <div class="sec-lbl">Model Integrity Verification</div>
            <div style="margin:8px 0;display:flex;align-items:center;gap:10px;">
                <span style="font-size:1.4rem;">{integrity_icon}</span>
                <div>
                    <div style="font-weight:bold;color:{integrity_color};font-size:0.8rem;">
                        {integrity_v['detail']}
                    </div>
                    <div style="font-size:0.62rem;color:#64748b;margin-top:2px;">
                        Round {integrity_v.get('round','—')} | SHA256 Verified
                    </div>
                </div>
            </div>
            <div class="hash-box">{latest_hash}</div>
            <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;">
                {chain_pills}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══ ROW 3 — Privacy Budget History | Anomaly Feed ════════════════════════
    pb_col, af_col = st.columns([1.6, 1])

    with pb_col:
        st.markdown('<div class="sec-p">', unsafe_allow_html=True)
        st.markdown("### 📊 Privacy Budget History")
        if eps_history:
            eps_df = pd.DataFrame(eps_history)
            fig_eps = go.Figure()
            fig_eps.add_trace(go.Scatter(
                x=list(range(len(eps_df))), y=eps_df["epsilon"],
                mode="lines+markers", name="Epsilon",
                line=dict(color="#38bdf8", width=2),
                fill="tozeroy", fillcolor="rgba(56,189,248,0.07)",
                marker=dict(size=4)
            ))
            if "noise_multiplier" in eps_df.columns:
                fig_eps.add_trace(go.Scatter(
                    x=list(range(len(eps_df))), y=eps_df["noise_multiplier"],
                    mode="lines", name="Noise ×",
                    line=dict(color="#22c55e", width=1.5, dash="dot"),
                    yaxis="y2"
                ))
            fig_eps.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8", height=200,
                legend=dict(orientation="h", y=1.15, font=dict(size=10)),
                xaxis=dict(showgrid=False, title="Round"),
                yaxis=dict(showgrid=False, title="ε"),
                yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Noise"),
                margin=dict(l=0,r=0,t=10,b=0)
            )
            st.plotly_chart(fig_eps, use_container_width=True, config={"displayModeBar":False})
            # summary row
            latest_eps = eps_df["epsilon"].iloc[-1] if len(eps_df) else EPSILON
            st.markdown(f"""
            <div style="display:flex;gap:20px;font-size:0.72rem;margin-top:4px;">
                <div><div class="sec-lbl">Current ε</div>
                     <div style="color:#38bdf8;font-weight:bold;">{latest_eps:.3f}</div></div>
                <div><div class="sec-lbl">Noise Mult</div>
                     <div style="color:#22c55e;font-weight:bold;">{NOISE_MULT}</div></div>
                <div><div class="sec-lbl">Rounds</div>
                     <div style="color:#f8fafc;font-weight:bold;">{len(eps_df)}</div></div>
                <div><div class="sec-lbl">Growth Rate</div>
                     <div style="color:{'#ef4444' if eps_growth>0.5 else '#22c55e'};font-weight:bold;">
                         {eps_growth:.4f}/round</div></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No epsilon history recorded yet. Run federated training first.")
        st.markdown('</div>', unsafe_allow_html=True)

    with af_col:
        st.markdown('<div class="sec-p">', unsafe_allow_html=True)
        st.markdown("### ⚡ Anomaly Feed")
        if anomalies:
            for a in anomalies:
                sev_col = "#ef4444" if a["severity"] == "CRITICAL" else "#eab308"
                st.markdown(f"""
                <div class="anom-row">
                    <span style="color:{sev_col};font-size:1rem;">{'🔴' if a['severity']=='CRITICAL' else '🟡'}</span>
                    <div style="flex:1;">
                        <div style="color:#f8fafc;font-size:0.72rem;font-weight:bold;">{a['type']}</div>
                        <div style="color:#94a3b8;font-size:0.62rem;">{a['detail']}</div>
                    </div>
                    <span style="border:1px solid {sev_col};color:{sev_col};border-radius:3px;
                                 padding:1px 5px;font-size:0.55rem;">{a['severity']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            # show recent audit events as live feed
            recent = list(reversed(logger.get_all_logs()))[:5]
            for l in recent:
                try:
                    t = datetime.fromisoformat(l["timestamp"]).strftime("%H:%M")
                except Exception:
                    t = "--:--"
                st.markdown(f"""
                <div class="anom-row">
                    <span style="color:#22c55e;">✅</span>
                    <div style="flex:1;">
                        <div style="color:#94a3b8;font-size:0.68rem;">{l.get('action_type','')}</div>
                        <div style="color:#64748b;font-size:0.6rem;">{t}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            if not recent:
                st.markdown('<div style="color:#64748b;font-size:0.75rem;padding:10px;">No anomalies detected. System nominal.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══ ROW 4 — MIA Detector table | Exfil Log ═══════════════════════════════
    mia_col, ex_col = st.columns([1.2, 1])

    with mia_col:
        mia_col_cls = "#22c55e" if ATK_ACCURACY<0.55 else "#eab308" if ATK_ACCURACY<0.65 else "#ef4444"
        st.markdown(f"""
        <div class="sec-p">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <div style="font-family:Orbitron;font-size:0.85rem;color:#f8fafc;">
                    Membership Inference Detector
                </div>
                <span style="border:1px solid {mia_col_cls};color:{mia_col_cls};border-radius:4px;
                             padding:2px 8px;font-size:0.62rem;font-weight:bold;">{mia_label}</span>
            </div>
            <div style="display:flex;gap:16px;align-items:center;margin-bottom:12px;">
                <div style="width:56px;height:56px;border:3px solid {mia_col_cls};border-radius:50%;
                            display:flex;flex-direction:column;align-items:center;justify-content:center;">
                    <div style="font-family:Orbitron;font-size:0.9rem;color:#f8fafc;font-weight:bold;">
                        {ATK_ACCURACY*100:.0f}%</div>
                    <div style="font-size:0.45rem;color:#64748b;">ATK ACC</div>
                </div>
                <div style="flex:1;">
                    <div style="font-size:0.65rem;color:#94a3b8;">Risk Classification</div>
                    <div style="font-size:0.72rem;color:{mia_col_cls};font-weight:bold;">{mia_label}</div>
                    <div style="font-size:0.6rem;color:#64748b;">Threshold: &lt;55% Safe · 55–65% Elevated · &gt;65% Critical</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        # IP table
        st.markdown("""
        <div style="display:grid;grid-template-columns:120px 70px 1fr 60px;gap:6px;
                    font-size:0.58rem;color:#64748b;padding:4px 0;
                    border-bottom:1px solid rgba(255,255,255,0.08);">
            <div>IP Address</div><div>Risk</div><div>Data Accessed</div><div>Status</div>
        </div>""", unsafe_allow_html=True)
        for r in MIA_ROWS:
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:120px 70px 1fr 60px;gap:6px;
                        font-size:0.68rem;padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
                <div style="font-family:monospace;color:#94a3b8;">{r['ip']}</div>
                <div><span style="color:{r['col']};font-weight:bold;">{r['risk']}</span></div>
                <div style="color:#64748b;">— {r['data']}</div>
                <div><span style="background:rgba(239,68,68,0.12);border:1px solid #ef4444;
                                  color:#ef4444;border-radius:3px;padding:1px 5px;
                                  font-size:0.55rem;">MGRT</span></div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ex_col:
        st.markdown("""
        <div class="sec-p">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <div style="font-family:Orbitron;font-size:0.82rem;color:#f8fafc;">
                    Exfiltration Attempts Log</div>
                <div style="font-size:0.62rem;color:#22c55e;">● Auto-Mitigation ON</div>
            </div>
        """, unsafe_allow_html=True)
        for ex in EXFIL_IPS:
            bar_col = "#ef4444" if ex["bar"]>70 else "#eab308" if ex["bar"]>50 else "#22c55e"
            st.markdown(f"""
            <div class="ip-row">
                <span style="color:#ef4444;">⚠</span>
                <span style="font-family:monospace;color:#94a3b8;min-width:95px;">{ex['ip']}</span>
                <div style="flex:1;height:5px;background:rgba(255,255,255,0.06);border-radius:3px;">
                    <div style="width:{ex['bar']}%;height:5px;background:{bar_col};border-radius:3px;"></div>
                </div>
                <span style="color:#64748b;font-size:0.62rem;min-width:65px;">Today {ex['time']}</span>
            </div>
            """, unsafe_allow_html=True)
        if st.button("▶▶ Run Full Vulnerability Scan", use_container_width=True, key="vuln_scan"):
            logger.log_event("security","security_officer","VULNERABILITY_SCAN","Full scan triggered")
            st.toast("🔍 Vulnerability scan initiated and logged.")
        # Alerts
        st.markdown('<div style="margin-top:10px;font-family:Orbitron;font-size:0.75rem;color:#f8fafc;">Alerts &amp; Active Threats</div>', unsafe_allow_html=True)
        for a in ALERT_ROWS:
            st.markdown(f"""
            <div class="alert-row">
                <span style="color:#64748b;min-width:80px;">{a['time']}</span>
                <span style="color:#eab308;">{a['type']}</span>
                <span style="color:#64748b;font-size:0.62rem;">{a['detail']}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══ ROW 5 — Compliance Mode Switcher ══════════════════════════════════════
    st.markdown('<div class="sec-p" style="margin-top:6px;">', unsafe_allow_html=True)
    st.markdown("### 🔐 Compliance Mode Control")
    cm_c1, cm_c2, cm_c3 = st.columns([2, 1.5, 1.5])

    with cm_c1:
        all_modes = comp_mgr.all_modes()
        mode_choice = st.radio(
            "Active Privacy Mode",
            options=list(all_modes.keys()),
            index=list(all_modes.keys()).index(current_mode),
            horizontal=True,
            key="compliance_mode_radio"
        )
        if mode_choice != current_mode:
            comp_mgr.set_mode(mode_choice)
            st.rerun()

        cfg = all_modes[current_mode]
        st.markdown(f"""
        <div style="margin-top:8px;font-size:0.72rem;color:#94a3b8;">{cfg['description']}</div>
        <div style="display:flex;gap:12px;margin-top:8px;font-size:0.68rem;">
            <div><span class="sec-lbl">Noise Min</span>
                 <div style="color:#38bdf8;">{cfg['noise_multiplier_min']}</div></div>
            <div><span class="sec-lbl">Noise Max</span>
                 <div style="color:#38bdf8;">{cfg['noise_multiplier_max']}</div></div>
            <div><span class="sec-lbl">Admin Restricted</span>
                 <div style="color:{'#ef4444' if cfg['admin_access_restricted'] else '#22c55e'};">
                     {'YES' if cfg['admin_access_restricted'] else 'NO'}</div></div>
            <div><span class="sec-lbl">Log All Access</span>
                 <div style="color:{'#22c55e' if cfg['log_all_access'] else '#64748b'};">
                     {'YES' if cfg['log_all_access'] else 'NO'}</div></div>
        </div>
        """, unsafe_allow_html=True)

    with cm_c2:
        st.markdown("""<div class="sec-lbl" style="margin-bottom:6px;">Quick Actions</div>""", unsafe_allow_html=True)
        if st.button("🔄 Rotate DP Keys", use_container_width=True, key="rot_keys"):
            logger.log_event("security","security_officer","DP_KEY_ROTATION","Keys rotated")
            st.success("DP Keys Rotated & Logged.")
        if st.button("📈 Escalate Noise ε", use_container_width=True, key="esc_noise"):
            logger.log_event("security","security_officer","NOISE_ESCALATION","Noise manually escalated")
            st.warning("Noise escalated. Privacy budget consuming faster.")
        if st.button("🚀 Optimize Privacy", use_container_width=True, key="opt_priv"):
            logger.log_event("security","security_officer","PRIVACY_OPTIMIZATION","Global privacy tightened")
            st.success("Global privacy guardrails tightened!")

    with cm_c3:
        st.markdown("""<div class="sec-lbl" style="margin-bottom:6px;">Reports</div>""", unsafe_allow_html=True)
        if st.button("📋 Privacy Report", use_container_width=True, key="priv_rep"):
            st.toast("Generating privacy compliance report…")
        if st.button("📂 Alert History", use_container_width=True, key="alert_hist"):
            st.toast("Loading full alert history…")
        if st.button("⚙️ Control Panel", use_container_width=True, key="ctrl_panel"):
            st.toast("Control panel locked by security policy.")

    st.markdown('</div>', unsafe_allow_html=True)

    # ══ Audit Trail Expander ══════════════════════════════════════════════════
    with st.expander("📜 System Audit Trail (Immutable Records)", expanded=False):
        all_logs = logger.get_all_logs()
        if all_logs:
            st.dataframe(pd.DataFrame(all_logs), use_container_width=True)
        else:
            st.info("No audit logs recorded yet.")

    # ══ Bottom Bar ════════════════════════════════════════════════════════════
    st.markdown('<div style="margin-top:14px;display:flex;gap:10px;">', unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("📋 PRIVACY REPORT", use_container_width=True, key="b_rep"):
            st.toast("Generating report…")
    with b2:
        if st.button("📂 ALERT HISTORY ›", use_container_width=True, key="b_hist"):
            st.toast("Loading alert history…")
    with b3:
        if st.button("⚙️ CONTROL PANEL", use_container_width=True, key="b_ctrl"):
            st.toast("Locked by security policy.")
    with b4:
        if st.button("🚪 SIGN OUT", use_container_width=True, type="primary", key="sec_signout"):
            st.session_state['authenticated'] = False
            st.session_state['user'] = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
