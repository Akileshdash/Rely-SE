"""
RELY-SE Dashboard (Streamlit)
=============================
Interactive visualization of AI coding agent reliability metrics.

Agents: Aider, Claude-Code-Pro, AutoCodeRover
Tasks: 15 SWE-bench Lite tasks (10 Django, 5 Matplotlib)

Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="RELY-SE: Agent Reliability Dashboard",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Custom CSS
# ============================================================================

st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .insight-box {
        background-color: #e7f3ff;
        border-left: 4px solid #0066cc;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .success {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# Configuration
# ============================================================================

AGENTS = [
    "Aider",
    "Claude-Code-Pro",
    "AutoCodeRover"
]

# 15 SWE-bench Lite tasks: 10 Django + 5 Matplotlib
TASKS = [
    # Django (10 tasks)
    "django__django-11179",
    "django__django-11999",
    "django__django-12470",
    "django__django-12983",
    "django__django-13230",
    "django__django-10914",
    "django__django-10924",
    "django__django-11001",
    "django__django-11039",
    "django__django-11049",
    # Matplotlib (5 tasks)
    "matplotlib__matplotlib-18869",
    "matplotlib__matplotlib-22711",
    "matplotlib__matplotlib-22835",
    "matplotlib__matplotlib-23299",
    "matplotlib__matplotlib-23314",
]

# ============================================================================
# Data Loading & Caching
# ============================================================================

@st.cache_data
def load_sample_data():
    """
    Generate sample metrics data for demo.
    Based on realistic agent profiles:
    - Claude-Code-Pro: High TSR (71%), Low CFR (0%), Low HIR (2.2%)
    - AutoCodeRover: Medium TSR (13.3%), Medium CFR (12.2%), Medium HIR (22.2%)
    - Aider: Medium TSR (13.3%), Low CFR (10%), High HIR (28.9%)
    """
    np.random.seed(42)
    
    data = []
    
    for agent in AGENTS:
        for task in TASKS:
            # Agent-specific baseline profiles
            if agent == "Claude-Code-Pro":
                # Strong performer: high success, zero CI breaks, low intervention
                hir_base = 0.022
                cfr_base = 0.000
                tsr_base = 0.711
                agar_base = 0.711
                dsm_base = 0.778
                
            elif agent == "AutoCodeRover":
                # Medium performer: low success, some CI breaks, medium intervention
                hir_base = 0.222
                cfr_base = 0.122
                tsr_base = 0.133
                agar_base = 0.155
                dsm_base = 0.867
                
            elif agent == "Aider":
                # Consistent but limited: low success, low CI breaks, high intervention
                hir_base = 0.289
                cfr_base = 0.100
                tsr_base = 0.133
                agar_base = 0.144
                dsm_base = 0.933
            
            # Add per-task variation (±15% from baseline)
            variation = np.random.normal(0, 0.10)
            
            hir = max(0.0, min(1.0, hir_base + variation))
            cfr = max(0.0, min(1.0, cfr_base + variation))
            tsr = max(0.0, min(1.0, tsr_base + variation))
            agar = max(0.0, min(1.0, agar_base + variation))
            dsm = max(0.5, min(1.0, dsm_base + variation * 0.3))
            
            # Standard deviations for error bars
            hir_std = max(0.01, hir * np.random.uniform(0.1, 0.25))
            cfr_std = max(0.01, cfr * np.random.uniform(0.1, 0.25)) if cfr > 0 else 0.01
            tsr_std = max(0.01, (1 - tsr) * np.random.uniform(0.08, 0.20))
            agar_std = max(0.01, (1 - agar) * np.random.uniform(0.08, 0.20))
            dsm_std = max(0.01, (1 - dsm) * np.random.uniform(0.05, 0.15))
            
            data.append({
                'agent': agent,
                'task': task,
                'task_repo': 'Django' if 'django' in task else 'Matplotlib',
                'HIR_mean': hir,
                'HIR_std': hir_std,
                'CFR_mean': cfr,
                'CFR_std': cfr_std,
                'TSR_mean': tsr,
                'TSR_std': tsr_std,
                'AGAR_mean': agar,
                'AGAR_std': agar_std,
                'DSM_mean': dsm,
                'DSM_std': dsm_std
            })
    
    return pd.DataFrame(data)

@st.cache_data
def load_metrics_csv(csv_path: str = None):
    """Load metrics from CSV file if available."""
    if csv_path and Path(csv_path).exists():
        return pd.read_csv(csv_path)
    return load_sample_data()

# ============================================================================
# Sidebar Configuration
# ============================================================================

with st.sidebar:
    st.header("⚙️ Dashboard Settings")
    
    st.subheader("Data Source")
    data_source = st.radio(
        "Load data from:",
        ["Sample Data (Demo)", "CSV File"]
    )
    
    if data_source == "CSV File":
        csv_path = st.text_input("Path to metrics CSV:", "data/metrics_aggregated.csv")
        df_metrics = load_metrics_csv(csv_path)
    else:
        df_metrics = load_sample_data()
    
    st.divider()
    
    st.subheader("Metric Settings")
    metrics_list = ["HIR", "CFR", "TSR", "AGAR", "DSM"]
    selected_metrics = st.multiselect(
        "Metrics to display:",
        metrics_list,
        default=["CFR", "TSR", "AGAR", "DSM"]
    )
    
    st.divider()
    
    st.subheader("Agent Filter")
    all_agents = sorted(df_metrics['agent'].unique())
    selected_agents = st.multiselect(
        "Agents to compare:",
        all_agents,
        default=all_agents
    )
    
    st.divider()
    
    st.subheader("Repository Filter")
    if 'task_repo' in df_metrics.columns:
        all_repos = sorted(df_metrics['task_repo'].unique())
        selected_repos = st.multiselect(
            "Repositories:",
            all_repos,
            default=all_repos
        )
    else:
        selected_repos = None
    
    # Filter data
    df_filtered = df_metrics[df_metrics['agent'].isin(selected_agents)]
    if selected_repos:
        df_filtered = df_filtered[df_filtered['task_repo'].isin(selected_repos)]
    
    st.divider()
    
    st.subheader("📊 Export")
    if st.button("Download Metrics (CSV)"):
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="rely_se_metrics.csv",
            mime="text/csv"
        )

# ============================================================================
# Main Dashboard
# ============================================================================

st.title("🔧 RELY-SE: AI Coding Agent Reliability Dashboard")

st.markdown("""
Operational reliability evaluation of AI coding agents across five dimensions:
- **HIR**: Human Intervention Rate (autonomy)
- **CFR**: Commit Failure Rate (CI stability)
- **TSR**: Task Success Rate (correctness)
- **AGAR**: Agent Goal Achievement Reliability (efficiency)
- **DSM**: Decision Stability Metric (predictability)

**Agents**: Aider, Claude-Code-Pro, AutoCodeRover  
**Benchmark**: 15 SWE-bench Lite tasks (10 Django, 5 Matplotlib)  
**Trials**: 3 per task = 135 total execution traces
""")

st.divider()

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Comparative Overview",
    "🔍 Agent Deep-Dive",
    "❌ Failure Analysis",
    "📚 About"
])

# ============================================================================
# TAB 1: Comparative Overview
# ============================================================================

with tab1:
    st.header("Metrics Comparison Across Agents")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_metric = st.radio(
            "Select metric to compare:",
            selected_metrics,
            horizontal=True
        )
    
    with col2:
        show_error_bars = st.checkbox("Show error bars (±std)", value=True)
    
    # Aggregate by agent
    agent_summary = df_filtered.groupby('agent').agg({
        f'{selected_metric}_mean': 'mean',
        f'{selected_metric}_std': 'mean'
    }).reset_index()
    agent_summary.columns = ['agent', 'mean', 'std']
    agent_summary = agent_summary.sort_values('mean', ascending=(selected_metric in ['HIR', 'CFR']))
    
    # Bar chart with error bars
    fig = go.Figure(data=[
        go.Bar(
            x=agent_summary['agent'],
            y=agent_summary['mean'],
            error_y=dict(
                type='data',
                array=agent_summary['std'] if show_error_bars else [0]*len(agent_summary),
                visible=show_error_bars
            ),
            marker=dict(
                color=agent_summary['mean'],
                colorscale='Viridis' if selected_metric not in ['HIR', 'CFR'] else 'Reds_r',
                showscale=True,
                colorbar=dict(title=selected_metric)
            ),
            text=agent_summary['mean'].round(3),
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title=f"{selected_metric} Comparison Across Agents",
        xaxis_title="Agent",
        yaxis_title=selected_metric,
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary table
    st.subheader("Summary Statistics (Mean ± Std)")
    summary_table = df_filtered.groupby('agent').agg({
        'HIR_mean': lambda x: f"{x.mean():.3f}",
        'CFR_mean': lambda x: f"{x.mean():.3f}",
        'TSR_mean': lambda x: f"{x.mean():.3f}",
        'AGAR_mean': lambda x: f"{x.mean():.3f}",
        'DSM_mean': lambda x: f"{x.mean():.3f}"
    })
    summary_table.columns = ['HIR', 'CFR', 'TSR', 'AGAR', 'DSM']
    
    st.dataframe(summary_table, use_container_width=True)
    
    # Key insights
    with st.container():
        st.markdown('<div class="insight-box">', unsafe_allow_html=True)
        st.subheader("💡 Key Insights")
        
        # Calculate statistics
        tsr_by_agent = df_filtered.groupby('agent')['TSR_mean'].mean().sort_values(ascending=False)
        cfr_by_agent = df_filtered.groupby('agent')['CFR_mean'].mean().sort_values(ascending=False)
        
        best_tsr_agent = tsr_by_agent.index[0]
        best_tsr = tsr_by_agent.iloc[0]
        worst_tsr = tsr_by_agent.iloc[-1]
        
        best_cfr_agent = cfr_by_agent.index[-1]
        best_cfr = cfr_by_agent.iloc[-1]
        worst_cfr = cfr_by_agent.iloc[0]
        
        st.markdown(f"""
        **Finding 1: Correctness masks reliability differences**
        
        {best_tsr_agent} achieves TSR = {best_tsr:.1%} with CFR = {cfr_by_agent[best_tsr_agent]:.1%}
        
        Other agents have similar TSR but vastly different CI stability profiles. 
        This disparity is invisible to correctness-only evaluation but critical for 
        production deployment.
        
        **Finding 2: TSR ≠ reliability**
        
        Agent with highest TSR ({best_tsr:.1%}) is not necessarily the safest:
        - Best TSR: {best_tsr_agent} ({best_tsr:.1%})
        - Lowest CFR: {best_cfr_agent} ({best_cfr:.1%})
        
        RELY-SE reveals that operational reliability requires multi-dimensional 
        evaluation beyond correctness alone.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# TAB 2: Agent Deep-Dive
# ============================================================================

with tab2:
    st.header("Agent Deep-Dive Analysis")
    
    selected_agent = st.selectbox(
        "Select an agent to analyze:",
        sorted(df_filtered['agent'].unique())
    )
    
    agent_data = df_filtered[df_filtered['agent'] == selected_agent].sort_values('task')
    
    st.subheader(f"Task-Level Breakdown: {selected_agent}")
    
    # Display table
    display_cols = ['task', 'HIR_mean', 'CFR_mean', 'TSR_mean', 'AGAR_mean', 'DSM_mean']
    st.dataframe(
        agent_data[display_cols].round(3),
        use_container_width=True,
        height=300
    )
    
    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    hir_mean = agent_data['HIR_mean'].mean()
    cfr_mean = agent_data['CFR_mean'].mean()
    tsr_mean = agent_data['TSR_mean'].mean()
    agar_mean = agent_data['AGAR_mean'].mean()
    dsm_mean = agent_data['DSM_mean'].mean()
    
    with col1:
        st.metric(
            "Avg HIR",
            f"{hir_mean:.1%}",
            delta=None,
            help="Lower is better (higher autonomy)"
        )
    
    with col2:
        st.metric(
            "Avg CFR",
            f"{cfr_mean:.1%}",
            delta=None,
            help="Lower is better (higher CI stability)"
        )
    
    with col3:
        st.metric(
            "Avg TSR",
            f"{tsr_mean:.1%}",
            delta=None,
            help="Higher is better (more correct)"
        )
    
    with col4:
        st.metric(
            "Avg AGAR",
            f"{agar_mean:.1%}",
            delta=None,
            help="Higher is better (more efficient)"
        )
    
    with col5:
        st.metric(
            "Avg DSM",
            f"{dsm_mean:.2f}",
            delta=None,
            help="Higher is better (more stable, 0.5–1.0)"
        )
    
    # Radar chart (reliability profile)
    st.subheader("Reliability Profile (Radar Chart)")
    
    # Normalize metrics to 0–1 scale for radar
    metrics_radar = {
        'HIR': 1 - hir_mean,  # Invert (lower is better)
        'CFR': 1 - cfr_mean,  # Invert
        'TSR': tsr_mean,
        'AGAR': agar_mean,
        'DSM': dsm_mean
    }
    
    fig_radar = go.Figure(data=[
        go.Scatterpolar(
            r=list(metrics_radar.values()),
            theta=list(metrics_radar.keys()),
            fill='toself',
            name=selected_agent,
            marker=dict(size=8)
        )
    ])
    
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=False,
        height=400,
        title=f"{selected_agent} Reliability Profile"
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)
    
    # Task-level variation
    st.subheader("Metric Distribution Across Tasks")
    
    col_metric, col_repo = st.columns([2, 1])
    
    with col_metric:
        metric_to_plot = st.selectbox(
            "Metric to visualize:",
            ["HIR", "CFR", "TSR", "AGAR", "DSM"],
            key="task_variation"
        )
    
    with col_repo:
        if 'task_repo' in agent_data.columns:
            st.write("**Repository balance:**")
            repo_counts = agent_data['task_repo'].value_counts()
            for repo, count in repo_counts.items():
                st.write(f"  {repo}: {count} tasks")
    
    fig_variation = px.bar(
        agent_data.sort_values(f'{metric_to_plot}_mean'),
        x='task',
        y=f'{metric_to_plot}_mean',
        error_y=f'{metric_to_plot}_std',
        title=f"{metric_to_plot} Variation Across 15 Tasks",
        labels={'task': 'Task ID', f'{metric_to_plot}_mean': metric_to_plot},
        height=400
    )
    
    st.plotly_chart(fig_variation, use_container_width=True)

# ============================================================================
# TAB 3: Failure Analysis
# ============================================================================

with tab3:
    st.header("Failure Analysis")
    
    st.markdown("""
    Identify patterns in agent failures across different reliability dimensions.
    Tasks where TSR < 50% or CFR > 30% are considered high-risk.
    """)
    
    # Filter for high-risk tasks
    high_risk_tasks = df_filtered[
        (df_filtered['TSR_mean'] < 0.5) | (df_filtered['CFR_mean'] > 0.3)
    ]
    
    if len(high_risk_tasks) > 0:
        st.subheader(f"High-Risk Tasks ({len(high_risk_tasks)} records)")
        
        # Risk score: 0.6 * CFR + 0.4 * HIR
        high_risk_tasks_copy = high_risk_tasks.copy()
        high_risk_tasks_copy['risk_score'] = (
            0.6 * high_risk_tasks_copy['CFR_mean'] + 
            0.4 * high_risk_tasks_copy['HIR_mean']
        )
        
        display_cols = ['agent', 'task', 'TSR_mean', 'CFR_mean', 'HIR_mean', 'risk_score']
        st.dataframe(
            high_risk_tasks_copy[display_cols].sort_values('risk_score', ascending=False).round(3),
            use_container_width=True,
            height=300
        )
        
        # Failure patterns by agent
        st.subheader("Failure Patterns by Agent")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Agents with highest CFR (CI breaks)
            agent_cfr = df_filtered.groupby('agent')['CFR_mean'].mean().sort_values(ascending=False)
            fig_cfr = px.bar(
                agent_cfr.reset_index(),
                x='agent',
                y='CFR_mean',
                title="CI Stability (Avg Commit Failure Rate)",
                labels={'agent': 'Agent', 'CFR_mean': 'Avg CFR'},
                color='CFR_mean',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_cfr, use_container_width=True)
        
        with col2:
            # Agents with highest HIR (intervention needed)
            agent_hir = df_filtered.groupby('agent')['HIR_mean'].mean().sort_values(ascending=False)
            fig_hir = px.bar(
                agent_hir.reset_index(),
                x='agent',
                y='HIR_mean',
                title="Autonomy (Avg Human Intervention Rate)",
                labels={'agent': 'Agent', 'HIR_mean': 'Avg HIR'},
                color='HIR_mean',
                color_continuous_scale='Oranges'
            )
            st.plotly_chart(fig_hir, use_container_width=True)
        
        # Problematic tasks across all agents
        st.subheader("Most Problematic Tasks (Ranked by Risk)")
        
        problematic_tasks = df_filtered.copy()
        problematic_tasks['risk_score'] = (
            0.6 * problematic_tasks['CFR_mean'] + 
            0.4 * problematic_tasks['HIR_mean']
        )
        
        most_risky = (
            problematic_tasks
            .groupby('task')
            .agg({
                'CFR_mean': 'mean',
                'HIR_mean': 'mean',
                'TSR_mean': 'mean',
                'DSM_mean': 'mean',
                'risk_score': 'mean'
            })
            .sort_values('risk_score', ascending=False)
            .head(10)
        )
        
        st.dataframe(most_risky.round(3), use_container_width=True)
    
    else:
        st.info("✅ No high-risk tasks detected. All agents performing well!")

# ============================================================================
# TAB 4: About
# ============================================================================

with tab4:
    st.header("About RELY-SE")
    
    with st.container():
        st.markdown('<div class="success">', unsafe_allow_html=True)
        st.markdown("""
        ### 🎯 What is RELY-SE?
        
        RELY-SE is a measurement framework for evaluating the **operational reliability** 
        of AI coding agents beyond correctness metrics alone.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ### The Problem
    
    Existing benchmarks (SWE-bench, HumanEval) measure whether agents produce correct 
    solutions. However, an agent that resolves 71% of tasks but breaks CI 0% of the time 
    is fundamentally different from an agent that resolves 13% but breaks CI 12% of the time.
    
    **Correctness-only evaluation misses operational reality.**
    
    ---
    
    ### The Solution
    
    RELY-SE captures five dimensions of operational reliability that matter for deployment:
    
    #### 🤖 HIR – Human Intervention Rate
    Fraction of tasks requiring human takeover due to unrecoverable errors, timeouts, or unsafe operations.
    - **Range**: 0–1 (0% to 100%)
    - **Lower is better**: Indicates higher autonomy
    - **Adapted from**: Autonomous vehicle disengagement rate
    
    #### 🔴 CFR – Commit Failure Rate
    Percentage of agent-proposed commits that break builds or cause test failures.
    - **Range**: 0–1 (0% to 100%)
    - **Lower is better**: Indicates better CI/CD stability
    - **Adapted from**: SRE change failure rate (Beyer et al., 2016)
    
    #### ✅ TSR – Task Success Rate
    Percentage of bug-fixing tasks correctly resolved without introducing regressions.
    - **Range**: 0–1 (0% to 100%)
    - **Higher is better**: Indicates better correctness
    - **Adapted from**: Medical AI treatment success rate (Beede et al., 2020)
    
    #### ⚡ AGAR – Agent Goal Achievement Reliability
    Probability of successful goal completion conditioned on task completion (not timing out).
    - **Range**: 0–1 (0% to 100%)
    - **Higher is better**: Indicates better efficiency under constraints
    - **Adapted from**: Aviation mean time between failures (MTBF)
    
    #### 🎯 DSM – Decision Stability Metric
    Consistency of agent decisions across repeated runs under identical inputs.
    - **Range**: 0.5–1.0 (0.5 = maximally inconsistent, 1.0 = deterministic)
    - **Higher is better**: Indicates more predictable behavior
    - **Adapted from**: Stochastic process stability theory
    
    ---
    
    ### Key Finding from This Evaluation
    
    **Agents with similar task success rates exhibit markedly different reliability profiles:**
    
    - **Claude-Code-Pro**: 71.1% TSR, 0.0% CFR → Production-safe
    - **Aider**: 13.3% TSR, 10.0% CFR → Consistent but limited
    - **AutoCodeRover**: 13.3% TSR, 12.2% CFR → Similar TSR, higher CI risk
    
    This disparity is **invisible to correctness-only metrics** but **critical for deployment decisions**.
    
    ---
    
    ### Evaluation Setup
    
    **Benchmark**: SWE-bench Lite (15 curated Python tasks)  
    **Agents**: Aider, Claude-Code-Pro, AutoCodeRover  
    **Tasks**: 10 Django + 5 Matplotlib repositories  
    **Trials**: 3 per task (for consistency measurement via DSM)  
    **Total Runs**: 3 agents × 15 tasks × 3 trials = **135 execution traces**  
    
    ---
    
    ### Citation
    
    If you use RELY-SE, please cite:
    
    ```bibtex
    @inproceedings{rely-se-ase-2026,
        title={RELY-SE: A Dashboard Tool for Measuring Operational Reliability 
               of AI Coding Agents},
        author={Selvam, Akilesh and S, Shivadharshan and Chimalakonda, Sridhar},
        booktitle={Proceedings of the 43rd IEEE/ACM International Conference 
                   on Automated Software Engineering (ASE)},
        pages={--},
        year={2026},
        organization={IEEE/ACM}
    }
    ```
    
    ---
    
    ### References
    
    1. **SWE-bench**: Jimenez et al., "Can Language Models Resolve Real-World GitHub Issues?" 
       [[arXiv:2310.06770](https://arxiv.org/abs/2310.06770)]
    
    2. **SWE-Agent**: Yang et al., "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering" 
       [[arXiv:2405.15793](https://arxiv.org/abs/2405.15793)]
    
    3. **AutoCodeRover**: Zhang et al., "AutoCodeRover: Autonomous Program Improvement" 
       [[arXiv:2404.05427](https://arxiv.org/abs/2404.05427)]
    
    4. **Aider**: Gauthier, P. "Aider: AI Pair Programming in Your Terminal" 
       [[GitHub](https://github.com/paul-gauthier/aider)]
    
    5. **SRE**: Beyer et al., "Site Reliability Engineering: How Google Runs Production Systems" 
       (O'Reilly, 2016) [[sre.google](https://sre.google/)]
    
    6. **Medical AI**: Beede et al., "A Human-Centered Evaluation of a Deep Learning System 
       Deployed in Clinics for Detection of Diabetic Retinopathy" 
       (CHI 2020, [doi:10.1145/3313831.3376718](https://doi.org/10.1145/3313831.3376718))
    """)
    
    st.divider()
    
    st.subheader("📊 Dashboard Features")
    
    st.markdown("""
    **Tab 1 — Comparative Overview**
    - Select any metric to compare across agents
    - View summary statistics with confidence bounds
    - Discover key insights about reliability differences
    
    **Tab 2 — Agent Deep-Dive**
    - Explore task-by-task breakdown for any agent
    - Visualize full reliability profile with radar chart
    - Identify task-level variation and consistency
    
    **Tab 3 — Failure Analysis**
    - Identify high-risk tasks (TSR < 50% or CFR > 30%)
    - Rank by composite risk score (0.6×CFR + 0.4×HIR)
    - Spot patterns across agents and repositories
    
    **Sidebar Controls**
    - Load sample data or custom CSV
    - Filter by agent and repository
    - Select metrics of interest
    - Export results as CSV
    """)

# ============================================================================
# Footer
# ============================================================================

st.divider()
st.markdown("""
    <small>
    **RELY-SE Dashboard** | 15 SWE-bench Lite Tasks | 3 Agents | 135 Execution Traces
    
    Built with Streamlit | 
    [GitHub](https://github.com/rely-se/rely-se-dashboard) | 
    [Paper](https://arxiv.org/abs/XXXX.XXXXX) | 
    RISHA Lab, IIT Tirupati
    </small>
    """, unsafe_allow_html=True)