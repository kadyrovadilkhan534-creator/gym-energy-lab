# Gym Energy Lab

A local Streamlit feasibility simulator for recovering energy from a descending
gym weight stack, with a continuous-cycling comparison. All defaults are
illustrative assumptions, not equipment measurements or quotes.

## Run locally

Python 3.11 or newer is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate` instead.
Open the Local URL printed by Streamlit, normally http://localhost:8501.

## Features

- Editable exercise, recovery, rest-time, utilization, auxiliary-power and cost assumptions.
- Conservative, expected and optimistic cases that vary uncertain recovery inputs.
- Energy balance, usage sensitivity, device-runtime equivalence and cash-flow charts.
- Negative net energy and uneconomic cases remain visible.
- Exercise-bike comparison with explicit shared cost and operating assumptions.
- JSON/CSV downloads containing inputs and results; no external account required.
- Separate pure-Python physics model for review by the science team.

## Model boundary

For one set, `E_Wh = mass * 9.81 * vertical_travel * reps * capture * efficiency / 3600`.
Only descending gravitational energy is harvested. Mechanical capture and
conversion efficiency are separate. Generator braking changes lowering effort.
Travel is the weight stack's vertical movement, not necessarily handle travel.

Scale by sets/day, operating days, availability and machine count. Subtract active/standby auxiliary consumption once.
Efficiency includes any transmission, conversion, storage and inverter losses.
Active electronics power replaces standby power during exercise; powered hours
cover gym opening hours or all 8,760 hours/year. Negative net output is permitted.

Electricity value is net kWh times a user-entered tariff. Annual savings subtract
maintenance. Electricity prices and maintenance grow at the selected annual
inflation rate; NPV discounts these nominal cash flows at the selected nominal
discount rate. Simple payback uses the first-year savings. Major replacement
schedules, grants, export income and resale value are not modelled. Currency
selection only labels values; it never converts prices. USD, KGS, EUR, GBP and
INR are available.

The annual energy waterfall separates energy not captured mechanically from
captured energy lost as heat during generator/electrical conversion. The model
counts all generated electricity as used locally and subtracts auxiliary power;
storage constraints and export are outside the current boundary.

## Manim animation

GitHub Actions renders and commits the video when the model or scene changes.
The app embeds `media/stack_energy.mp4` in the Physics tab when present. The
scene generator reads the model defaults and calculation directly:

```bash
python -m pip install manim
manim -qm gym_energy_animation.py StackEnergy
```

Copy the rendered `StackEnergy.mp4` to `media/stack_energy.mp4` to include it in
the deployment. Manim is optional and is not installed by the Streamlit app.

Cycling uses mechanical pedal power times duration times its own efficiency.
The stack capture fraction does not apply to cycling. The two fleets share the
same costs, schedule and auxiliary settings for a controlled comparison, not as
a claim that their actual retrofit prices or hardware are identical.

No cut-in speed, generator torque limits, detailed biomechanics, battery state,
carbon footprint or food-energy impacts are resolved. No AI or telemetry service
is needed. Treat outputs as a concept study until validated experimentally.

## Validate

```bash
python -m unittest discover -s tests -v
```

Physics tests use only the Python standard library. UI tests additionally use
Streamlit's built-in AppTest and the packages in `requirements.txt`.

## Share later

Upload `app.py`, `model.py`, `requirements.txt`, `.streamlit/config.toml`, README
and tests to a GitHub repository. Do not upload `.venv` or secrets. Connect the
repository to Streamlit Community Cloud, choose `app.py` as the entrypoint and
deploy. A public repository exposes the source; the deployment provides the
interactive app. GitHub Pages does not run a conventional Streamlit server.

- https://docs.streamlit.io/deploy/streamlit-community-cloud
- https://support.maxongroup.com/hc/en-us/articles/360004496254-maxon-Motors-as-Generators
- https://www.gosportsart.com/eco-powr/

Break-even electricity price is the first-year tariff at which lifetime NPV equals zero, including installation and upkeep. First-year prices are entered directly; inflation starts in year two. Rest occupies the machine but uses standby electronics power.
