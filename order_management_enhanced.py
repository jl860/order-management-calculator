import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import io

# Page configuration
st.set_page_config(
    page_title="Order Management AI - Business Case",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better formatting
st.markdown("""
    <style>
    .case-indicator {
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .best-case {
        background-color: #d4edda;
        color: #155724;
        border: 2px solid #28a745;
    }
    .base-case {
        background-color: #d1ecf1;
        color: #0c5460;
        border: 2px solid #17a2b8;
    }
    .worst-case {
        background-color: #fff3cd;
        color: #856404;
        border: 2px solid #ffc107;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #007bff;
    }
    .section-header {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
        margin-top: 30px;
        margin-bottom: 20px;
    }
    .insight-box {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #17a2b8;
        margin: 15px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Currency exchange rates (as of typical rates, update as needed)
CURRENCY_RATES = {
    'USD': 1.0,
    'EUR': 0.92  # 1 USD = 0.92 EUR (approximate)
}

# Define case multipliers
CASE_SCENARIOS = {
    'Best Case': {
        'dso_improvement': 1.3,
        'error_reduction': 1.2,
        'leakage_reduction': 1.25,
        'automation_rate': 1.2,
        'cycle_time_improvement': 1.25,
        'cost_multiplier': 0.9,
        'description': 'Optimistic scenario with maximum adoption and impact'
    },
    'Base Case': {
        'dso_improvement': 1.0,
        'error_reduction': 1.0,
        'leakage_reduction': 1.0,
        'automation_rate': 1.0,
        'cycle_time_improvement': 1.0,
        'cost_multiplier': 1.0,
        'description': 'Realistic scenario based on industry benchmarks'
    },
    'Worst Case': {
        'dso_improvement': 0.7,
        'error_reduction': 0.75,
        'leakage_reduction': 0.7,
        'automation_rate': 0.8,
        'cycle_time_improvement': 0.75,
        'cost_multiplier': 1.15,
        'description': 'Conservative scenario with implementation challenges'
    }
}

def format_number(value, decimals=0, prefix='', suffix=''):
    """Format numbers with commas and optional prefix/suffix"""
    if decimals == 0:
        formatted = f"{value:,.0f}"
    else:
        formatted = f"{value:,.{decimals}f}"
    return f"{prefix}{formatted}{suffix}"

def convert_currency(amount, from_currency, to_currency):
    """Convert amount from one currency to another"""
    usd_amount = amount / CURRENCY_RATES[from_currency]
    return usd_amount * CURRENCY_RATES[to_currency]

def calculate_benefits(inputs, case_multipliers, currency='USD'):
    """Calculate all financial benefits based on inputs and case scenario"""
    
    # Extract inputs
    annual_orders = inputs['annual_orders']
    avg_order_value = inputs['avg_order_value']
    current_dso = inputs['current_dso']
    current_error_rate = inputs['current_error_rate']
    current_leakage = inputs['current_leakage']
    cost_per_order = inputs['cost_per_order']
    minutes_per_manual = inputs['minutes_per_manual']
    hourly_cost = inputs['hourly_cost']
    current_cycle_days = inputs['current_cycle_days']
    gross_margin = inputs['gross_margin']
    wacc = inputs['wacc']
    
    annual_revenue = annual_orders * avg_order_value
    
    # Apply case multipliers to improvements
    target_dso = current_dso - (10 * case_multipliers['dso_improvement'])
    target_error_rate = current_error_rate - ((current_error_rate - 8) * case_multipliers['error_reduction'])
    target_leakage = current_leakage - ((current_leakage - 3) * case_multipliers['leakage_reduction'])
    target_cycle_days = current_cycle_days - (2.2 * case_multipliers['cycle_time_improvement'])
    
    # Automation rate based on case
    base_automation_improvement = 23  # percentage points
    automation_improvement = base_automation_improvement * case_multipliers['automation_rate']
    
    # Benefit 1: Working Capital Improvement
    current_ar = (current_dso / 365) * annual_revenue
    target_ar = (target_dso / 365) * annual_revenue
    cash_freed = current_ar - target_ar
    working_capital_benefit = cash_freed * (wacc / 100)
    
    # Benefit 2: Error Reduction
    current_errors = annual_orders * (current_error_rate / 100)
    target_errors = annual_orders * (target_error_rate / 100)
    errors_eliminated = current_errors - target_errors
    error_reduction_benefit = errors_eliminated * cost_per_order
    
    # Benefit 3: Revenue Leakage Prevention
    current_leakage_amount = annual_revenue * (current_leakage / 100)
    target_leakage_amount = annual_revenue * (target_leakage / 100)
    leakage_prevented = current_leakage_amount - target_leakage_amount
    leakage_benefit = leakage_prevented * (gross_margin / 100)
    
    # Benefit 4: Labor Cost Reduction
    manual_orders_eliminated = annual_orders * (automation_improvement / 100)
    hours_saved = (manual_orders_eliminated * minutes_per_manual) / 60
    labor_benefit = hours_saved * hourly_cost
    
    # Benefit 5: Cycle Time / Capacity Increase
    cycle_time_reduction_pct = (current_cycle_days - target_cycle_days) / current_cycle_days
    potential_additional_orders = annual_orders * cycle_time_reduction_pct * 0.3  # 30% capacity capture
    capacity_benefit = potential_additional_orders * avg_order_value * (gross_margin / 100)
    
    total_annual_benefit = (working_capital_benefit + error_reduction_benefit + 
                           leakage_benefit + labor_benefit + capacity_benefit)
    
    # Convert to selected currency
    if currency != 'USD':
        working_capital_benefit = convert_currency(working_capital_benefit, 'USD', currency)
        error_reduction_benefit = convert_currency(error_reduction_benefit, 'USD', currency)
        leakage_benefit = convert_currency(leakage_benefit, 'USD', currency)
        labor_benefit = convert_currency(labor_benefit, 'USD', currency)
        capacity_benefit = convert_currency(capacity_benefit, 'USD', currency)
        total_annual_benefit = convert_currency(total_annual_benefit, 'USD', currency)
        cash_freed = convert_currency(cash_freed, 'USD', currency)
    
    return {
        'working_capital': working_capital_benefit,
        'error_reduction': error_reduction_benefit,
        'leakage_prevention': leakage_benefit,
        'labor_savings': labor_benefit,
        'capacity_increase': capacity_benefit,
        'total_annual': total_annual_benefit,
        'cash_freed': cash_freed,
        'target_dso': target_dso,
        'target_error_rate': target_error_rate,
        'target_leakage': target_leakage,
        'target_cycle_days': target_cycle_days,
        'automation_improvement': automation_improvement
    }

def calculate_investment(inputs, case_multipliers, currency='USD'):
    """Calculate total investment costs"""
    
    platform_cost = inputs['platform_annual_cost'] * case_multipliers['cost_multiplier']
    implementation_cost = inputs['implementation_cost'] * case_multipliers['cost_multiplier']
    change_mgmt = inputs['change_management'] * case_multipliers['cost_multiplier']
    
    year1_cost = platform_cost + implementation_cost + change_mgmt
    recurring_cost = platform_cost
    
    if currency != 'USD':
        year1_cost = convert_currency(year1_cost, 'USD', currency)
        recurring_cost = convert_currency(recurring_cost, 'USD', currency)
    
    return {
        'year1': year1_cost,
        'recurring': recurring_cost
    }

def calculate_roi_metrics(benefits, costs, currency='USD'):
    """Calculate ROI, payback, and NPV"""
    
    annual_benefit = benefits['total_annual']
    year1_cost = costs['year1']
    recurring_cost = costs['recurring']
    
    # Simple payback period (months)
    if annual_benefit > 0:
        payback_months = (year1_cost / annual_benefit) * 12
    else:
        payback_months = float('inf')
    
    # 3-year NPV (simplified, 8% discount rate)
    discount_rate = 0.08
    year1_net = annual_benefit - year1_cost
    year2_net = annual_benefit - recurring_cost
    year3_net = annual_benefit - recurring_cost
    
    npv = (year1_net / (1 + discount_rate)**1 + 
           year2_net / (1 + discount_rate)**2 + 
           year3_net / (1 + discount_rate)**3)
    
    # ROI (Year 1)
    if year1_cost > 0:
        roi = ((annual_benefit - year1_cost) / year1_cost) * 100
    else:
        roi = 0
    
    # 3-Year ROI
    total_investment = year1_cost + recurring_cost * 2
    total_benefits = annual_benefit * 3
    roi_3year = ((total_benefits - total_investment) / total_investment) * 100
    
    return {
        'payback_months': payback_months,
        'npv': npv,
        'roi_year1': roi,
        'roi_3year': roi_3year
    }

def perform_sensitivity_analysis(inputs, base_case_results, currency='USD'):
    """Perform sensitivity analysis on key variables"""
    
    variables = {
        'DSO Improvement': ('current_dso', [5, 7.5, 10, 12.5, 15]),
        'Error Reduction': ('current_error_rate', [4, 6, 8, 10, 12]),
        'Leakage Prevention': ('current_leakage', [2, 3, 5, 6, 7]),
        'Automation Rate': ('minutes_per_manual', [20, 24, 28, 32, 36]),
        'Platform Cost': ('platform_annual_cost', [-20, -10, 0, 10, 20])  # percentage change
    }
    
    sensitivity_results = []
    base_roi = base_case_results['roi_3year']
    
    for var_name, (param_key, test_values) in variables.items():
        impacts = []
        
        for test_value in test_values:
            test_inputs = inputs.copy()
            
            if param_key == 'platform_annual_cost':
                # Handle percentage changes
                test_inputs[param_key] = inputs[param_key] * (1 + test_value / 100)
                label = f"{test_value:+.0f}%"
            else:
                test_inputs[param_key] = test_value
                label = f"{test_value}"
            
            # Recalculate with modified input
            test_benefits = calculate_benefits(test_inputs, CASE_SCENARIOS['Base Case'], currency)
            test_costs = calculate_investment(test_inputs, CASE_SCENARIOS['Base Case'], currency)
            test_metrics = calculate_roi_metrics(test_benefits, test_costs, currency)
            
            roi_change = test_metrics['roi_3year'] - base_roi
            
            impacts.append({
                'variable': var_name,
                'value': label,
                'roi': test_metrics['roi_3year'],
                'roi_change': roi_change
            })
        
        sensitivity_results.extend(impacts)
    
    return pd.DataFrame(sensitivity_results)

# Initialize session state for currency
if 'currency' not in st.session_state:
    st.session_state.currency = 'USD'

# Sidebar - Business Inputs
with st.sidebar:
    st.title("📊 Business Inputs")
    
    # Currency selector at the top of sidebar
    st.markdown("### 💱 Currency Selection")
    currency = st.selectbox(
        "Select Currency",
        options=['USD', 'EUR'],
        index=0 if st.session_state.currency == 'USD' else 1,
        key='currency_selector'
    )
    st.session_state.currency = currency
    currency_symbol = '$' if currency == 'USD' else '€'
    
    st.markdown("---")
    
    st.markdown("### 📈 Current State Metrics")
    
    annual_orders = st.number_input(
        "Annual Order Volume",
        min_value=1000,
        max_value=10000000,
        value=50000,
        step=1000,
        format="%d",
        help="Total number of orders processed annually"
    )
    
    avg_order_value = st.number_input(
        f"Average Order Value ({currency_symbol})",
        min_value=100,
        max_value=1000000,
        value=2500,
        step=100,
        format="%d"
    )
    
    current_dso = st.slider(
        "Current DSO (Days)",
        min_value=20,
        max_value=90,
        value=45,
        help="Days Sales Outstanding - how long it takes to collect payment"
    )
    
    current_error_rate = st.slider(
        "Current Error Rate (%)",
        min_value=5.0,
        max_value=50.0,
        value=25.0,
        step=1.0,
        help="Percentage of orders with errors requiring rework"
    )
    
    current_leakage = st.slider(
        "Current Revenue Leakage (%)",
        min_value=2.0,
        max_value=20.0,
        value=8.0,
        step=0.5,
        help="Revenue lost due to pricing errors, missed charges, etc."
    )
    
    cost_per_order = st.number_input(
        f"Cost per Order ({currency_symbol})",
        min_value=10,
        max_value=500,
        value=85,
        step=5,
        format="%d"
    )
    
    minutes_per_manual = st.slider(
        "Minutes per Manual Touch",
        min_value=10,
        max_value=60,
        value=28,
        help="Average time spent on manual order processing"
    )
    
    hourly_cost = st.number_input(
        f"Fully-Loaded Hourly Cost ({currency_symbol})",
        min_value=25,
        max_value=200,
        value=75,
        step=5,
        format="%d",
        help="Includes salary, benefits, overhead"
    )
    
    current_cycle_days = st.slider(
        "Current Order-to-Cash Cycle (Days)",
        min_value=2.0,
        max_value=15.0,
        value=5.2,
        step=0.1
    )
    
    gross_margin = st.slider(
        "Gross Margin (%)",
        min_value=5.0,
        max_value=50.0,
        value=15.0,
        step=1.0
    )
    
    wacc = st.slider(
        "Cost of Capital / WACC (%)",
        min_value=4.0,
        max_value=15.0,
        value=8.0,
        step=0.5,
        help="Weighted Average Cost of Capital"
    )
    
    st.markdown("---")
    st.markdown("### 💰 Investment Costs")
    
    platform_annual_cost = st.number_input(
        f"Platform Annual Cost ({currency_symbol})",
        min_value=50000,
        max_value=5000000,
        value=250000,
        step=25000,
        format="%d"
    )
    
    implementation_cost = st.number_input(
        f"Implementation Cost ({currency_symbol})",
        min_value=25000,
        max_value=2000000,
        value=150000,
        step=25000,
        format="%d"
    )
    
    change_management = st.number_input(
        f"Change Management ({currency_symbol})",
        min_value=10000,
        max_value=500000,
        value=50000,
        step=10000,
        format="%d"
    )

# Compile inputs
inputs = {
    'annual_orders': annual_orders,
    'avg_order_value': avg_order_value,
    'current_dso': current_dso,
    'current_error_rate': current_error_rate,
    'current_leakage': current_leakage,
    'cost_per_order': cost_per_order,
    'minutes_per_manual': minutes_per_manual,
    'hourly_cost': hourly_cost,
    'current_cycle_days': current_cycle_days,
    'gross_margin': gross_margin,
    'wacc': wacc,
    'platform_annual_cost': platform_annual_cost,
    'implementation_cost': implementation_cost,
    'change_management': change_management
}

# Main content
st.title("🎯 Order Management AI - Financial Business Case")

# Case selector
st.markdown("### 📊 Scenario Selection")
selected_case = st.radio(
    "Select Analysis Scenario",
    options=['Best Case', 'Base Case', 'Worst Case'],
    index=1,  # Default to Base Case
    horizontal=True,
    help="Choose between optimistic, realistic, or conservative scenarios"
)

# Display case indicator with color
case_class = selected_case.lower().replace(' ', '-')
st.markdown(f"""
    <div class="case-indicator {case_class}">
        {selected_case}: {CASE_SCENARIOS[selected_case]['description']}
    </div>
""", unsafe_allow_html=True)

# Calculate results for selected case
case_multipliers = CASE_SCENARIOS[selected_case]
benefits = calculate_benefits(inputs, case_multipliers, currency)
costs = calculate_investment(inputs, case_multipliers, currency)
roi_metrics = calculate_roi_metrics(benefits, costs, currency)

# Calculate all three cases for comparison
all_cases_results = {}
for case_name in ['Best Case', 'Base Case', 'Worst Case']:
    case_mult = CASE_SCENARIOS[case_name]
    case_benefits = calculate_benefits(inputs, case_mult, currency)
    case_costs = calculate_investment(inputs, case_mult, currency)
    case_metrics = calculate_roi_metrics(case_benefits, case_costs, currency)
    all_cases_results[case_name] = {
        'benefits': case_benefits,
        'costs': case_costs,
        'metrics': case_metrics
    }

# Key Financial Metrics
st.markdown("## 💎 Key Financial Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Annual Benefit",
        format_number(benefits['total_annual'], prefix=currency_symbol),
        delta=None
    )

with col2:
    st.metric(
        "3-Year NPV",
        format_number(roi_metrics['npv'], prefix=currency_symbol),
        delta=None
    )

with col3:
    st.metric(
        "Payback Period",
        f"{roi_metrics['payback_months']:.1f} months",
        delta=None
    )

with col4:
    st.metric(
        "3-Year ROI",
        f"{roi_metrics['roi_3year']:.1f}%",
        delta=None
    )

# Benefit Breakdown
st.markdown("## 📊 Annual Benefit Breakdown")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="insight-box">
        <strong>💰 Working Capital</strong><br>
        Cash freed from DSO reduction
        </div>
    """, unsafe_allow_html=True)
    st.metric("", format_number(benefits['working_capital'], prefix=currency_symbol))

with col2:
    st.markdown("""
        <div class="insight-box">
        <strong>❌ Error Reduction</strong><br>
        Eliminated rework costs
        </div>
    """, unsafe_allow_html=True)
    st.metric("", format_number(benefits['error_reduction'], prefix=currency_symbol))

with col3:
    st.markdown("""
        <div class="insight-box">
        <strong>🔒 Leakage Prevention</strong><br>
        Revenue protected
        </div>
    """, unsafe_allow_html=True)
    st.metric("", format_number(benefits['leakage_prevention'], prefix=currency_symbol))

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="insight-box">
        <strong>⚙️ Labor Savings</strong><br>
        Automation efficiency gains
        </div>
    """, unsafe_allow_html=True)
    st.metric("", format_number(benefits['labor_savings'], prefix=currency_symbol))

with col2:
    st.markdown("""
        <div class="insight-box">
        <strong>🚀 Capacity Increase</strong><br>
        Revenue from faster cycles
        </div>
    """, unsafe_allow_html=True)
    st.metric("", format_number(benefits['capacity_increase'], prefix=currency_symbol))

with col3:
    st.markdown("""
        <div class="insight-box">
        <strong>💵 Year 1 Investment</strong><br>
        Total implementation cost
        </div>
    """, unsafe_allow_html=True)
    st.metric("", format_number(costs['year1'], prefix=currency_symbol))

# Financial Analysis Section
st.markdown('<h2 class="section-header">📈 Financial Analysis</h2>', unsafe_allow_html=True)

st.markdown("""
<div class="insight-box">
<strong>Understanding the Financial Analysis</strong><br>
This section provides detailed visualizations of your financial returns across multiple dimensions.
Each chart is designed to answer specific executive questions about value creation, timing, and risk.
</div>
""", unsafe_allow_html=True)

# Benefit Waterfall Chart
st.markdown("### 💧 Value Creation Waterfall")
st.markdown("""
**What this shows:** The waterfall chart breaks down how each operational improvement contributes to your total annual benefit.
This visualization helps identify which value drivers are most significant and where to focus implementation efforts.
""")

waterfall_data = {
    'Category': ['Working Capital', 'Error Reduction', 'Leakage Prevention', 
                'Labor Savings', 'Capacity Increase', 'Total'],
    'Amount': [benefits['working_capital'], benefits['error_reduction'], 
               benefits['leakage_prevention'], benefits['labor_savings'],
               benefits['capacity_increase'], benefits['total_annual']],
    'Type': ['relative', 'relative', 'relative', 'relative', 'relative', 'total']
}

fig_waterfall = go.Figure(go.Waterfall(
    x=waterfall_data['Category'],
    y=waterfall_data['Amount'],
    measure=waterfall_data['Type'],
    text=[format_number(v, prefix=currency_symbol) for v in waterfall_data['Amount']],
    textposition="outside",
    connector={"line": {"color": "rgb(63, 63, 63)"}},
    increasing={"marker": {"color": "#28a745"}},
    totals={"marker": {"color": "#007bff"}}
))

fig_waterfall.update_layout(
    title=f"Annual Benefit Breakdown - {selected_case}",
    showlegend=False,
    height=500,
    yaxis_title=f"Benefit Amount ({currency_symbol})"
)

st.plotly_chart(fig_waterfall, use_container_width=True)

# Three-year projection
st.markdown("### 📅 3-Year Financial Projection")
st.markdown("""
**What this shows:** This projection illustrates cumulative financial impact over three years, showing when the investment
breaks even and how benefits compound over time. The shaded area represents your net cumulative benefit.
""")

years = ['Year 1', 'Year 2', 'Year 3']
annual_benefits = [benefits['total_annual']] * 3
annual_costs = [costs['year1'], costs['recurring'], costs['recurring']]
net_benefits = [b - c for b, c in zip(annual_benefits, annual_costs)]
cumulative_net = [sum(net_benefits[:i+1]) for i in range(3)]

fig_projection = go.Figure()

fig_projection.add_trace(go.Bar(
    name='Annual Benefit',
    x=years,
    y=annual_benefits,
    marker_color='#28a745',
    text=[format_number(v, prefix=currency_symbol) for v in annual_benefits],
    textposition='outside'
))

fig_projection.add_trace(go.Bar(
    name='Annual Cost',
    x=years,
    y=[-c for c in annual_costs],
    marker_color='#dc3545',
    text=[format_number(v, prefix=currency_symbol) for v in annual_costs],
    textposition='outside'
))

fig_projection.add_trace(go.Scatter(
    name='Cumulative Net Benefit',
    x=years,
    y=cumulative_net,
    mode='lines+markers+text',
    line=dict(color='#007bff', width=3),
    marker=dict(size=10),
    text=[format_number(v, prefix=currency_symbol) for v in cumulative_net],
    textposition='top center',
    fill='tozeroy',
    fillcolor='rgba(0, 123, 255, 0.1)'
))

fig_projection.update_layout(
    title=f"3-Year Financial Projection - {selected_case}",
    barmode='relative',
    height=500,
    yaxis_title=f"Amount ({currency_symbol})",
    hovermode='x unified',
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig_projection, use_container_width=True)

# Scenario Comparison Chart
st.markdown("### 🎲 Scenario Comparison Analysis")
st.markdown("""
**What this shows:** Compare financial outcomes across Best, Base, and Worst case scenarios. This helps quantify
the range of potential outcomes and supports risk-adjusted decision making. The bars show total 3-year benefits minus costs.
""")

scenario_names = list(all_cases_results.keys())
scenario_benefits = [all_cases_results[case]['benefits']['total_annual'] * 3 for case in scenario_names]
scenario_costs = [all_cases_results[case]['costs']['year1'] + all_cases_results[case]['costs']['recurring'] * 2 
                  for case in scenario_names]
scenario_net = [b - c for b, c in zip(scenario_benefits, scenario_costs)]
scenario_roi = [all_cases_results[case]['metrics']['roi_3year'] for case in scenario_names]

fig_scenarios = go.Figure()

fig_scenarios.add_trace(go.Bar(
    name='3-Year Net Benefit',
    x=scenario_names,
    y=scenario_net,
    marker_color=['#28a745', '#17a2b8', '#ffc107'],
    text=[format_number(v, prefix=currency_symbol) for v in scenario_net],
    textposition='outside',
    yaxis='y'
))

fig_scenarios.add_trace(go.Scatter(
    name='3-Year ROI',
    x=scenario_names,
    y=scenario_roi,
    mode='lines+markers+text',
    line=dict(color='#dc3545', width=3),
    marker=dict(size=12),
    text=[f"{v:.1f}%" for v in scenario_roi],
    textposition='top center',
    yaxis='y2'
))

fig_scenarios.update_layout(
    title="Financial Outcomes Across Scenarios",
    height=500,
    yaxis=dict(title=f"3-Year Net Benefit ({currency_symbol})"),
    yaxis2=dict(title="3-Year ROI (%)", overlaying='y', side='right'),
    hovermode='x unified',
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig_scenarios, use_container_width=True)

# Sensitivity Analysis
st.markdown("### 🎯 Sensitivity Analysis")
st.markdown("""
**What this shows:** This tornado chart ranks variables by their impact on ROI. The longest bars represent the most
sensitive assumptions—these are the variables that require the most careful validation and monitoring during implementation.
The chart helps prioritize due diligence efforts and identify potential risks.
""")

# Calculate sensitivity for base case
sensitivity_df = perform_sensitivity_analysis(inputs, all_cases_results['Base Case']['metrics'], currency)

# Create tornado chart - show impact range for each variable
tornado_data = []
for var in sensitivity_df['variable'].unique():
    var_data = sensitivity_df[sensitivity_df['variable'] == var]
    max_impact = var_data['roi_change'].max()
    min_impact = var_data['roi_change'].min()
    range_impact = max_impact - min_impact
    tornado_data.append({
        'variable': var,
        'min_impact': min_impact,
        'max_impact': max_impact,
        'range': range_impact
    })

tornado_df = pd.DataFrame(tornado_data).sort_values('range', ascending=True)

fig_tornado = go.Figure()

fig_tornado.add_trace(go.Bar(
    name='Negative Impact',
    y=tornado_df['variable'],
    x=tornado_df['min_impact'],
    orientation='h',
    marker_color='#dc3545',
    text=[f"{v:.1f}%" for v in tornado_df['min_impact']],
    textposition='outside'
))

fig_tornado.add_trace(go.Bar(
    name='Positive Impact',
    y=tornado_df['variable'],
    x=tornado_df['max_impact'],
    orientation='h',
    marker_color='#28a745',
    text=[f"{v:+.1f}%" for v in tornado_df['max_impact']],
    textposition='outside'
))

fig_tornado.update_layout(
    title="ROI Sensitivity to Key Variables (Base Case)",
    barmode='overlay',
    height=400,
    xaxis_title="Impact on 3-Year ROI (percentage points)",
    yaxis_title="Variable",
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig_tornado, use_container_width=True)

# Financial Analysis Tables
st.markdown('<h3 class="section-header">📋 Detailed Financial Tables</h3>', unsafe_allow_html=True)

st.markdown("""
**What these tables show:** Comprehensive financial details supporting the visualizations above. 
These tables provide the specific numbers executives need for budget approvals and board presentations.
""")

# Three scenario comparison table
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 💰 Benefits by Scenario")
    benefits_comparison = pd.DataFrame({
        'Benefit Category': ['Working Capital', 'Error Reduction', 'Leakage Prevention', 
                            'Labor Savings', 'Capacity Increase', 'Total Annual'],
        'Best Case': [
            format_number(all_cases_results['Best Case']['benefits']['working_capital'], prefix=currency_symbol),
            format_number(all_cases_results['Best Case']['benefits']['error_reduction'], prefix=currency_symbol),
            format_number(all_cases_results['Best Case']['benefits']['leakage_prevention'], prefix=currency_symbol),
            format_number(all_cases_results['Best Case']['benefits']['labor_savings'], prefix=currency_symbol),
            format_number(all_cases_results['Best Case']['benefits']['capacity_increase'], prefix=currency_symbol),
            format_number(all_cases_results['Best Case']['benefits']['total_annual'], prefix=currency_symbol)
        ],
        'Base Case': [
            format_number(all_cases_results['Base Case']['benefits']['working_capital'], prefix=currency_symbol),
            format_number(all_cases_results['Base Case']['benefits']['error_reduction'], prefix=currency_symbol),
            format_number(all_cases_results['Base Case']['benefits']['leakage_prevention'], prefix=currency_symbol),
            format_number(all_cases_results['Base Case']['benefits']['labor_savings'], prefix=currency_symbol),
            format_number(all_cases_results['Base Case']['benefits']['capacity_increase'], prefix=currency_symbol),
            format_number(all_cases_results['Base Case']['benefits']['total_annual'], prefix=currency_symbol)
        ],
        'Worst Case': [
            format_number(all_cases_results['Worst Case']['benefits']['working_capital'], prefix=currency_symbol),
            format_number(all_cases_results['Worst Case']['benefits']['error_reduction'], prefix=currency_symbol),
            format_number(all_cases_results['Worst Case']['benefits']['leakage_prevention'], prefix=currency_symbol),
            format_number(all_cases_results['Worst Case']['benefits']['labor_savings'], prefix=currency_symbol),
            format_number(all_cases_results['Worst Case']['benefits']['capacity_increase'], prefix=currency_symbol),
            format_number(all_cases_results['Worst Case']['benefits']['total_annual'], prefix=currency_symbol)
        ]
    })
    st.dataframe(benefits_comparison, use_container_width=True, hide_index=True)

with col2:
    st.markdown("#### 📊 ROI Metrics by Scenario")
    roi_comparison = pd.DataFrame({
        'Metric': ['3-Year NPV', 'Payback (months)', 'Year 1 ROI', '3-Year ROI'],
        'Best Case': [
            format_number(all_cases_results['Best Case']['metrics']['npv'], prefix=currency_symbol),
            f"{all_cases_results['Best Case']['metrics']['payback_months']:.1f}",
            f"{all_cases_results['Best Case']['metrics']['roi_year1']:.1f}%",
            f"{all_cases_results['Best Case']['metrics']['roi_3year']:.1f}%"
        ],
        'Base Case': [
            format_number(all_cases_results['Base Case']['metrics']['npv'], prefix=currency_symbol),
            f"{all_cases_results['Base Case']['metrics']['payback_months']:.1f}",
            f"{all_cases_results['Base Case']['metrics']['roi_year1']:.1f}%",
            f"{all_cases_results['Base Case']['metrics']['roi_3year']:.1f}%"
        ],
        'Worst Case': [
            format_number(all_cases_results['Worst Case']['metrics']['npv'], prefix=currency_symbol),
            f"{all_cases_results['Worst Case']['metrics']['payback_months']:.1f}",
            f"{all_cases_results['Worst Case']['metrics']['roi_year1']:.1f}%",
            f"{all_cases_results['Worst Case']['metrics']['roi_3year']:.1f}%"
        ]
    })
    st.dataframe(roi_comparison, use_container_width=True, hide_index=True)

# Investment breakdown
st.markdown("#### 💵 Investment Breakdown")
investment_detail = pd.DataFrame({
    'Cost Category': ['Platform (Annual)', 'Implementation (One-time)', 'Change Management (One-time)', 
                     'Year 1 Total', 'Years 2-3 (Annual)'],
    selected_case: [
        format_number(inputs['platform_annual_cost'] * case_multipliers['cost_multiplier'], prefix=currency_symbol),
        format_number(inputs['implementation_cost'] * case_multipliers['cost_multiplier'], prefix=currency_symbol),
        format_number(inputs['change_management'] * case_multipliers['cost_multiplier'], prefix=currency_symbol),
        format_number(costs['year1'], prefix=currency_symbol),
        format_number(costs['recurring'], prefix=currency_symbol)
    ]
})
st.dataframe(investment_detail, use_container_width=True, hide_index=True)

# Operational improvements table
st.markdown("#### 🎯 Operational Improvements")
improvements = pd.DataFrame({
    'Metric': ['DSO (Days)', 'Error Rate (%)', 'Revenue Leakage (%)', 
              'Order-to-Cash Cycle (Days)', 'Automation Rate Improvement (%)'],
    'Current State': [
        f"{inputs['current_dso']:.0f}",
        f"{inputs['current_error_rate']:.1f}%",
        f"{inputs['current_leakage']:.1f}%",
        f"{inputs['current_cycle_days']:.1f}",
        "—"
    ],
    f'Target State ({selected_case})': [
        f"{benefits['target_dso']:.0f}",
        f"{benefits['target_error_rate']:.1f}%",
        f"{benefits['target_leakage']:.1f}%",
        f"{benefits['target_cycle_days']:.1f}",
        f"+{benefits['automation_improvement']:.0f}%"
    ],
    'Improvement': [
        f"{inputs['current_dso'] - benefits['target_dso']:.0f} days",
        f"{inputs['current_error_rate'] - benefits['target_error_rate']:.1f}%",
        f"{inputs['current_leakage'] - benefits['target_leakage']:.1f}%",
        f"{inputs['current_cycle_days'] - benefits['target_cycle_days']:.1f} days",
        f"+{benefits['automation_improvement']:.0f}%"
    ]
})
st.dataframe(improvements, use_container_width=True, hide_index=True)

# Export functionality
st.markdown("## 📥 Export & Documentation")

col1, col2 = st.columns(2)

with col1:
    # Prepare CSV export with all scenarios
    export_data = []
    for case_name in ['Best Case', 'Base Case', 'Worst Case']:
        case_data = all_cases_results[case_name]
        export_data.append({
            'Scenario': case_name,
            'Total Annual Benefit': case_data['benefits']['total_annual'],
            'Working Capital': case_data['benefits']['working_capital'],
            'Error Reduction': case_data['benefits']['error_reduction'],
            'Leakage Prevention': case_data['benefits']['leakage_prevention'],
            'Labor Savings': case_data['benefits']['labor_savings'],
            'Capacity Increase': case_data['benefits']['capacity_increase'],
            'Year 1 Investment': case_data['costs']['year1'],
            'Recurring Cost': case_data['costs']['recurring'],
            '3-Year NPV': case_data['metrics']['npv'],
            'Payback Months': case_data['metrics']['payback_months'],
            '3-Year ROI': case_data['metrics']['roi_3year'],
            'Currency': currency
        })
    
    export_df = pd.DataFrame(export_data)
    csv = export_df.to_csv(index=False)
    
    st.download_button(
        label="📊 Download Full Analysis (CSV)",
        data=csv,
        file_name=f"order_management_business_case_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

with col2:
    # Executive summary
    exec_summary = f"""
ORDER MANAGEMENT AI - EXECUTIVE SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Currency: {currency}
Selected Scenario: {selected_case}

KEY FINANCIAL METRICS
Total Annual Benefit: {format_number(benefits['total_annual'], prefix=currency_symbol)}
3-Year NPV: {format_number(roi_metrics['npv'], prefix=currency_symbol)}
Payback Period: {roi_metrics['payback_months']:.1f} months
3-Year ROI: {roi_metrics['roi_3year']:.1f}%

BENEFIT BREAKDOWN
Working Capital: {format_number(benefits['working_capital'], prefix=currency_symbol)}
Error Reduction: {format_number(benefits['error_reduction'], prefix=currency_symbol)}
Leakage Prevention: {format_number(benefits['leakage_prevention'], prefix=currency_symbol)}
Labor Savings: {format_number(benefits['labor_savings'], prefix=currency_symbol)}
Capacity Increase: {format_number(benefits['capacity_increase'], prefix=currency_symbol)}

INVESTMENT REQUIRED
Year 1: {format_number(costs['year1'], prefix=currency_symbol)}
Recurring (Years 2-3): {format_number(costs['recurring'], prefix=currency_symbol)}

OPERATIONAL IMPROVEMENTS
DSO: {inputs['current_dso']:.0f} → {benefits['target_dso']:.0f} days
Error Rate: {inputs['current_error_rate']:.1f}% → {benefits['target_error_rate']:.1f}%
Revenue Leakage: {inputs['current_leakage']:.1f}% → {benefits['target_leakage']:.1f}%
Order Cycle: {inputs['current_cycle_days']:.1f} → {benefits['target_cycle_days']:.1f} days
Automation Increase: +{benefits['automation_improvement']:.0f}%

SCENARIO COMPARISON
Best Case 3-Year ROI: {all_cases_results['Best Case']['metrics']['roi_3year']:.1f}%
Base Case 3-Year ROI: {all_cases_results['Base Case']['metrics']['roi_3year']:.1f}%
Worst Case 3-Year ROI: {all_cases_results['Worst Case']['metrics']['roi_3year']:.1f}%
"""
    
    st.download_button(
        label="📄 Download Executive Summary",
        data=exec_summary,
        file_name=f"executive_summary_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6c757d; font-size: 0.9em;'>
<strong>Order Management AI Business Case</strong> | 
Powered by Uniphore Business AI Cloud | 
Built for CFO-grade financial analysis
</div>
""", unsafe_allow_html=True)
