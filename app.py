"""Run with: python -m streamlit run app.py"""

import csv
from dataclasses import asdict, replace
from io import StringIO
import json

import plotly.graph_objects as go
import streamlit as st

from model import Inputs, weight_stack, cycling, cumulative_balance

st.set_page_config(page_title="Gym Energy Lab", page_icon="⚡", layout="wide")
st.markdown("""<style>
.block-container {max-width:1400px; padding-top:2rem; padding-bottom:3rem;}
h1,h2,h3 {letter-spacing:-.035em;}
[data-testid="stSidebar"] {border-right:1px solid #e4eaf0;}
[data-testid="stMetric"] {background:white;border:1px solid #e1e8ee;border-radius:14px;padding:18px;}
[data-testid="stMetricLabel"] {color:#4f6475;}
[data-testid="stMetricValue"] {font-size:1.85rem;letter-spacing:-.04em;}
.hero {background:#122b36;color:#fff;border-radius:20px;padding:32px 36px;margin-bottom:24px;}
.hero h1 {font-size:2.7rem;color:#fff;margin:8px 0;line-height:1.12;}
.hero p {color:#c9d9df;max-width:760px;font-size:1.05rem;margin:12px 0 0;}
.eyebrow {color:#b8f279;font-weight:700;letter-spacing:.15em;font-size:.8rem;}
.flow {display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:10px 0 20px;}
.flow div {padding:16px;border:1px solid #dce5ec;border-radius:12px;background:#fff;}
.flow b {display:block;font-size:1rem;color:#153f4b;margin-bottom:6px;}
.flow span {color:#536779;font-size:.9rem;}
.footnote {font-size:.85rem;color:#5f7282;border-top:1px solid #dfe6ed;padding-top:18px;margin-top:24px;}
@media(max-width:700px) {.hero {padding:24px;} .hero h1 {font-size:2rem;} .flow {grid-template-columns:1fr 1fr;}}
</style>""", unsafe_allow_html=True)

DEFAULTS = {
    "mass": 30, "travel": 0.4, "reps": 12, "sets": 50, "lift": 2.0,
    "lower": 2.0, "pause": 1.0, "capture": 50, "efficiency": 60,
    "usable": 100, "machines": 1, "days": 300, "availability": 100,
    "opening": 12.0, "active_aux": 0.2, "standby": 0.01,
    "always_on": False, "currency": "USD", "tariff": 0.2, "retrofit": 250.0,
    "shared": 0.0, "maintenance": 10.0, "life": 10, "discount": 5.0,
    "bike_power": 100, "bike_minutes": 30, "bike_sessions": 4,
    "bike_efficiency": 60, "device_w": 5.0,
}


def reset():
    st.session_state.update(DEFAULTS)


for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)

with st.sidebar:
    st.markdown("### ⚡ Gym Energy Lab")
    st.caption("JUNIOR ACADEMY · FEASIBILITY MODEL")
    st.button("Reset example", on_click=reset, width="stretch")
    st.markdown("### Build your scenario")
    st.caption("All starting values are illustrative assumptions, not measurements or equipment quotes.")
    with st.expander("Exercise & movement", expanded=True):
        st.slider("Moving stack mass (kg)", 0, 200, key="mass", step=5)
        st.slider("Vertical stack travel (m)", 0.0, 1.5, key="travel", step=0.05,
                  help="Measure the weight stack's vertical rise, not handle travel.")
        st.slider("Repetitions per set", 1, 40, key="reps")
        st.number_input("Sets per machine per day", 0, 1000, key="sets", step=5)
        a, b = st.columns(2)
        a.number_input("Lift (s/rep)", 0.1, 20.0, key="lift", step=0.1)
        b.number_input("Lower (s/rep)", 0.1, 20.0, key="lower", step=0.1)
        st.number_input("Pause (s/rep)", 0.0, 60.0, key="pause", step=0.5,
                        help="Pause within a repetition. Between-set rest is not modelled; leave time for it in the daily schedule.")
    with st.expander("Energy recovery", expanded=True):
        st.slider("Mechanical capture (%)", 0, 100, key="capture",
                  help="Share of descending gravitational energy diverted to the harvesting mechanism. Higher capture changes the lowering resistance.")
        st.slider("Combined conversion efficiency (%)", 0, 100, key="efficiency",
                  help="Transmission × generator × electronics × storage/inverter efficiencies, where applicable. Do not apply those losses again.")
        st.slider("Electricity used locally (%)", 0, 100, key="usable",
                  help="Accounts for discarded energy or full storage. Unused generation earns no export income.")
    with st.expander("Gym & operating schedule"):
        st.number_input("Number of machines", 1, 500, key="machines")
        st.number_input("Operating days per year", 0, 365, key="days")
        st.number_input("Opening hours per day", 1.0, 24.0, key="opening", step=0.5)
        st.slider("Equipment availability (%)", 0, 100, key="availability",
                  help="Reduces exercise and generation, but electronics may remain on during downtime.")
    with st.expander("Controller & monitoring consumption"):
        st.number_input("Active consumption per machine (W)", 0.0, 100.0, key="active_aux", step=0.1, format="%.2f")
        st.number_input("Standby consumption per machine (W)", 0.0, 100.0, key="standby", step=0.01, format="%.2f")
        st.checkbox("Powered 24/7, including closed days", key="always_on")
        st.caption("Otherwise powered only during gym opening hours. Active power replaces standby power while exercising.")
    with st.expander("Costs & lifetime"):
        st.selectbox("Currency label", ["USD", "KGS", "EUR", "GBP"], key="currency",
                     help="Labels only; no exchange-rate conversion. Enter every price in the selected currency.")
        st.number_input("Electricity price / kWh", 0.0, 1000.0, key="tariff", step=0.01, format="%.3f")
        st.number_input("Installed retrofit cost / machine", 0.0, 1000000.0, key="retrofit", step=10.0)
        st.number_input("Shared installation cost", 0.0, 1000000.0, key="shared", step=10.0)
        st.number_input("Annual upkeep / machine", 0.0, 100000.0, key="maintenance", step=1.0,
                        help="Include maintenance and an annual allowance for component replacements.")
        st.slider("System lifetime (years)", 1, 30, key="life")
        st.number_input("Discount rate (%)", 0.0, 30.0, key="discount", step=0.5)

s = st.session_state
p = Inputs(mass_kg=s.mass, travel_m=s.travel, reps_per_set=s.reps, sets_per_day=s.sets,
           lifting_s=s.lift, lowering_s=s.lower, pause_s=s.pause, capture=s.capture / 100,
           efficiency=s.efficiency / 100, usable_fraction=s.usable / 100,
           machines=s.machines, days_per_year=s.days, availability=s.availability / 100,
           opening_hours=s.opening, active_aux_w=s.active_aux, standby_w=s.standby,
           always_on=s.always_on, tariff=s.tariff, retrofit_per_machine=s.retrofit,
           shared_cost=s.shared, maintenance_per_machine=s.maintenance,
           lifetime_years=s.life, discount_rate=s.discount / 100)

st.markdown("""<div class="hero"><div class="eyebrow">HUMAN POWER · MEASURABLE IMPACT</div>
<h1>What could your workout power?</h1>
<p>Explore the energy hidden in a descending weight stack. Test the physics,
scale it to a gym, and find out whether the retrofit pays for itself.</p></div>""", unsafe_allow_html=True)
st.caption("VERSION 01 · LOWERING-ONLY RECOVERY · SIMULATED RESULTS")

try:
    result = weight_stack(p)
except ValueError as exc:
    st.error(str(exc))
    st.info("Adjust the inputs in the sidebar to calculate a valid scenario.")
    st.stop()


def money(value):
    return f"{s.currency} {value:,.2f}"


def style_chart(fig, height=330, ytitle=None):
    fig.update_layout(height=height, margin=dict(l=12, r=12, t=25, b=20),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Arial, sans-serif", size=14, color="#42576a"),
                      hoverlabel=dict(bgcolor="white"),
                      legend=dict(orientation="h", y=1.15),
                      yaxis_title=ytitle)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#e4eaf0", zerolinecolor="#9eb0bc")
    return fig


if result.payback_years is None:
    payback_label = "No payback"
elif result.payback_years > p.lifetime_years:
    payback_label = "Beyond lifetime"
else:
    payback_label = f"{result.payback_years:.1f} years"

cols = st.columns(4)
cols[0].metric("Electricity per set", f"{result.gross_wh_per_session:.3f} Wh", help="Gross electricity from one machine before auxiliary consumption and unused output.")
cols[1].metric("Annual net energy · fleet", f"{result.net_kwh_year:,.2f} kWh", help="Locally used generation minus controller and monitoring consumption.")
cols[2].metric("Annual net savings · fleet", money(result.savings_year), help="Electricity value less annual upkeep. Installation costs are accounted for in payback.")
cols[3].metric("Simple payback", payback_label, help="Installed cost divided by positive annual net savings. Ignores discounting.")

if result.net_kwh_year < 0:
    st.warning("This scenario consumes more electricity than it recovers. Reduce auxiliary draw or increase useful generation.")
elif result.savings_year <= 0:
    st.info("Electricity savings do not exceed annual upkeep at these settings.")
elif result.payback_years > p.lifetime_years:
    st.info(f"The retrofit saves money each year, but its {result.payback_years:,.1f}-year simple payback exceeds the selected {p.lifetime_years}-year lifetime.")
else:
    st.success("Under these assumptions, electricity savings recover the installed cost within the selected lifetime. Check the discounted result in Costs & payback.")

overview, economics, comparison, science = st.tabs(["Energy overview", "Costs & payback", "Compare equipment", "Physics & assumptions"])

with overview:
    st.markdown("### Follow the energy")
    st.markdown(f"""<div class="flow">
    <div><b>Weight descends</b><span>{p.mass_kg:g} kg × {p.travel_m:g} m vertical travel</span></div>
    <div><b>Mechanical capture</b><span>{p.capture:.0%} of gravitational energy</span></div>
    <div><b>Electrical conversion</b><span>{p.efficiency:.0%} combined efficiency</span></div>
    <div><b>Useful electricity</b><span>{p.usable_fraction:.0%} used locally, then subtract auxiliaries</span></div>
    </div>""", unsafe_allow_html=True)
    left, right = st.columns([1.65, 1], gap="large")
    with left:
        st.markdown("#### Annual energy balance")
        losses = result.source_kwh_year - result.gross_kwh_year
        unused = result.gross_kwh_year - result.usable_kwh_year
        fig = go.Figure(go.Waterfall(
            x=["Available<br>on descent", "Uncaptured &<br>conversion losses", "Unused<br>electricity", "Auxiliary<br>consumption", "Net<br>electricity"],
            measure=["absolute", "relative", "relative", "relative", "total"],
            y=[result.source_kwh_year, -losses, -unused, -result.auxiliary_kwh_year, 0],
            connector=dict(line=dict(color="#acbec9")),
            decreasing=dict(marker=dict(color="#d5a267")),
            increasing=dict(marker=dict(color="#8babc0")),
            totals=dict(marker=dict(color="#087f70")),
            hovertemplate="%{x}: %{y:.3f} kWh<extra></extra>"))
        st.plotly_chart(style_chart(fig, ytitle="kWh / year · entire fleet"), width="stretch")
        st.caption("Uncaptured energy includes energy still absorbed by the user and machine; it is not all an electrical conversion loss.")
    with right:
        st.markdown("#### Put it in perspective")
        st.number_input("Example device power (W)", 0.1, 5000.0, key="device_w", step=1.0)
        runtime = max(0, result.net_kwh_year) * 1000 / s.device_w
        st.metric("Equivalent runtime from a year's net energy", f"{runtime:,.1f} hours")
        st.caption("An energy equivalence, not a guarantee of continuous operation. Storage and output-power limits are not simulated.")
        st.markdown(f"**{result.generating_power_w:.1f} W** average electrical power during one descent.")
        st.markdown(f"**{result.active_hours_per_day:.2f} h/day** of exercise per machine before availability adjustment.")
        st.caption("Daily usage is based on sets; changing movement speed changes power and active electronics consumption, not ideal energy per repetition.")
    st.markdown("### How much does usage matter?")
    maximum_sets = int(p.opening_hours * 3600 / (p.reps_per_set * (p.lifting_s + p.lowering_s + p.pause_s)))
    upper = min(max(100, p.sets_per_day * 2), maximum_sets)
    counts = sorted(set([0, p.sets_per_day, upper] + [round(upper * i / 30) for i in range(31)]))
    net_values = [weight_stack(replace(p, sets_per_day=n)).net_kwh_year for n in counts]
    fig = go.Figure(go.Scatter(x=counts, y=net_values, mode="lines", line=dict(color="#087f70", width=3),
                             hovertemplate="%{x} sets/day<br>%{y:.3f} kWh/year<extra></extra>"))
    fig.add_trace(go.Scatter(x=[p.sets_per_day], y=[result.net_kwh_year], mode="markers", marker=dict(size=11, color="#122b36"), showlegend=False))
    fig.update_layout(showlegend=False, xaxis_title="Sets per machine per day")
    fig.add_hline(y=0, line_dash="dot", line_color="#a0adb7")
    st.plotly_chart(style_chart(fig, height=270, ytitle="Net kWh / year · fleet"), width="stretch")

with economics:
    st.markdown("### Does the retrofit earn its cost back?")
    st.caption(f"All amounts are in {s.currency}. Prices are user assumptions; changing the currency label does not convert them.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total installed cost", money(result.installed_cost))
    c2.metric("Lifetime cash balance", money(result.lifetime_balance))
    c3.metric("Net present value", money(result.net_present_value), help="Annual net savings discounted at the selected rate, minus installed cost.")
    rows = cumulative_balance(p, result)
    fig = go.Figure(go.Scatter(x=[r["Year"] for r in rows], y=[r["Cash balance"] for r in rows],
                             mode="lines+markers", line=dict(color="#087f70", width=3),
                             hovertemplate="Year %{x}<br>Balance %{y:.2f}<extra></extra>"))
    fig.add_hline(y=0, line_dash="dot", line_color="#9caeba")
    fig.update_layout(xaxis_title="Years since installation", xaxis=dict(dtick=max(1, p.lifetime_years // 10)))
    st.plotly_chart(style_chart(fig, ytitle=f"Cumulative cash balance ({s.currency})"), width="stretch")
    a, b = st.columns(2, gap="large")
    with a:
        st.markdown("#### Annual balance")
        st.table([
            {"Item": "Value of net electricity", f"{s.currency} / year": round(result.electricity_value_year, 2)},
            {"Item": "Upkeep and replacement allowance", f"{s.currency} / year": -round(result.maintenance_year, 2)},
            {"Item": "Net savings", f"{s.currency} / year": round(result.savings_year, 2)},
        ])
    with b:
        st.markdown("#### Your retrofit budget target")
        if result.savings_year > 0:
            st.metric("Maximum total installed cost to break even", money(result.break_even_budget))
            st.caption(f"Present value of {p.lifetime_years} years of net savings at a {p.discount_rate:.1%} discount rate, including the current upkeep assumption.")
        else:
            st.warning("No nonnegative installation budget breaks even while annual net savings are negative or zero (except a zero-cost, zero-savings case).")
        st.caption("Constant annual use and prices; no grants, export revenue, taxes, resale value, or separate major replacement schedule. Membership or educational benefits are not counted as electricity income.")

with comparison:
    st.markdown("### Weight stack or exercise bike?")
    st.write("Compare intermittent lowering recovery with continuous pedal input. These are two alternative fleets, not combined generation.")
    a, b, c, d = st.columns(4)
    a.number_input("Pedal mechanical power (W)", 0, 1000, key="bike_power", step=10,
                   help="Power delivered mechanically to the bike, not metabolic calories or measured electrical output.")
    b.number_input("Minutes per cycling session", 1, 240, key="bike_minutes", step=5)
    c.number_input("Sessions per bike per day", 0, 100, key="bike_sessions")
    d.slider("Bike conversion efficiency (%)", 0, 100, key="bike_efficiency")
    st.caption("Both options use the sidebar's machine count, operating days, availability, usable fraction, auxiliary draw and cost assumptions. Equal retrofit costs are a comparison assumption, not a supplier quote.")
    try:
        bike = cycling(p, s.bike_power, s.bike_minutes, s.bike_sessions, s.bike_efficiency / 100)
        fig = go.Figure()
        for name, color, values in [
            ("Gross generation", "#9cb5c5", [result.gross_kwh_year, bike.gross_kwh_year]),
            ("Net electricity", "#087f70", [result.net_kwh_year, bike.net_kwh_year]),
        ]:
            fig.add_trace(go.Bar(name=name, x=["Weight stack", "Exercise bike"], y=values, marker_color=color,
                                 hovertemplate="%{x}<br>%{y:.3f} kWh/year<extra>%{fullData.name}</extra>"))
        st.plotly_chart(style_chart(fig, ytitle="kWh / year · entire fleet"), width="stretch")
        st.table([
            {"Metric": "Gross electricity per set / cycling session (Wh)", "Weight stack": round(result.gross_wh_per_session, 3), "Exercise bike": round(bike.gross_wh_per_session, 3)},
            {"Metric": "Exercise hours per machine per day", "Weight stack": round(result.active_hours_per_day, 2), "Exercise bike": round(bike.active_hours_per_day, 2)},
            {"Metric": f"Annual net savings ({s.currency})", "Weight stack": round(result.savings_year, 2), "Exercise bike": round(bike.savings_year, 2)},
        ])
        st.caption("A set and a cycling session have different durations. Use the exercise-hours row when interpreting the comparison. Neither option includes the person's food-energy footprint.")
    except ValueError as exc:
        bike = None
        st.warning(f"Cycling scenario: {exc}")

with science:
    st.markdown("### A transparent first model")
    st.write("The stack starts and ends each descent at rest. We recover only a selected fraction of its released gravitational potential energy.")
    st.latex(r"E_{\mathrm{set,Wh}}=\frac{mgh\,n\,\alpha\,\eta}{3600}")
    st.write("m = moving mass (kg); g = 9.81 m/s²; h = vertical stack travel (m); n = repetitions; α = capture fraction; η = combined conversion efficiency.")
    st.latex(r"E_{\mathrm{net,year}}=u E_{\mathrm{gross,year}}-E_{\mathrm{aux,year}}")
    st.latex(r"E_{\mathrm{aux,kWh}}=\frac{M[P_{\mathrm{active}}H_{\mathrm{active}}+P_{\mathrm{standby}}(H_{\mathrm{powered}}-H_{\mathrm{active}})]}{1000}")
    st.write("M = machine count. Annual active hours include availability. Powered hours are opening hours × operating days, or 8,760 for always-on electronics. Auxiliary energy is subtracted once, after conversion and local-use losses.")
    st.latex(r"\mathrm{NPV}=-C_0+\sum_{y=1}^{L}\frac{S_{\mathrm{annual}}}{(1+r)^y}")
    st.markdown("#### What this model assumes")
    st.markdown("""
- **Generation changes the workout.** A descending generator provides braking and reduces the user's eccentric loading. A 100% capture setting is a theoretical boundary, not a recommended exercise design.
- **No double-counting.** Lifting energy is not harvested in this version; pulley ratios do not multiply energy.
- **Constant efficiency.** Low-speed cut-in, torque limits, acceleration, friction curves and generator saturation are not resolved. Capture and efficiency are assumed effective averages.
- **Identical representative machines.** Usage is averaged; availability scales activity and output. Between-set rest and queues are not explicitly scheduled.
- **A common electrical boundary.** Include any storage/inverter losses in combined efficiency. Auxiliary draw is total added electrical consumption at that boundary.
- **Local use only.** Net energy offsets purchases at a flat tariff; negative net energy increases purchases. Unused electricity has zero export value.
- **Concept study.** The simulator does not validate a mechanical attachment, electrical installation, or preservation of exercise biomechanics.
- **Environmental claims are not yet calculated.** Materials, food-related effects, manufacturing and end-of-life impacts need separate evidence. No AI service or live telemetry is required by the simulator.
""")
    st.markdown("#### Evidence and data to collect")
    st.markdown("""
1. Measure actual moving mass, stack travel, repetition timing and daily utilization at one gym.
2. Obtain generator efficiency and cut-in curves, plus measured controller active and standby consumption.
3. Obtain installed retrofit quotes, replacement estimates and the gym's electricity tariff.
4. Compare measured electrical energy with this model when a prototype becomes available.

**Engineering reference:** [Maxon: motors as generators](https://support.maxongroup.com/hc/en-us/articles/360004496254-maxon-Motors-as-Generators) explains speed, torque and efficiency dependencies.

**Commercial context:** [SportsArt ECO-POWR](https://www.gosportsart.com/eco-powr/) demonstrates generating cardio equipment. Manufacturer figures are not used as measured performance for this retrofit.
""")
    st.info("Every editable starting value is an illustrative assumption. No field currently represents a verified measurement from your gym.")

st.divider()
st.markdown("#### Take this scenario to your team")
payload = {"model_version": "1.0", "currency": s.currency, "inputs": asdict(p),
           "weight_stack_results": asdict(result),
           "cycling_inputs": {"mechanical_w": s.bike_power, "minutes_per_session": s.bike_minutes,
                              "sessions_per_day": s.bike_sessions, "efficiency": s.bike_efficiency / 100},
           "cycling_results": asdict(bike) if bike else None,
           "assumption_status": "Illustrative inputs; no prototype validation"}
buffer = StringIO()
writer = csv.writer(buffer)
writer.writerow(["section", "name", "value"])
writer.writerow(["metadata", "currency", s.currency])
writer.writerow(["metadata", "model_version", "1.0"])
writer.writerow(["metadata", "assumption_status", payload["assumption_status"]])
for section in ("inputs", "weight_stack_results", "cycling_inputs", "cycling_results"):
    for name, value in (payload[section] or {}).items():
        writer.writerow([section, name, "not_applicable" if value is None else value])
a, b, _ = st.columns([1, 1, 2])
a.download_button("Download scenario JSON", json.dumps(payload, indent=2, allow_nan=False), "gym-energy-scenario.json", "application/json", width="stretch")
b.download_button("Download results CSV", buffer.getvalue(), "gym-energy-results.csv", "text/csv", width="stretch")
st.markdown('<div class="footnote">Gym Energy Lab · Junior Academy · A model to test an idea, with assumptions you can inspect.</div>', unsafe_allow_html=True)
