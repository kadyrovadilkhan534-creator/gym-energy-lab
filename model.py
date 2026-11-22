"""Energy and economics, independent of Streamlit. SI units unless specified.

The weight model recovers gravitational energy only on descent. It does not
claim unchanged exercise loading or count lifting energy a second time.
"""

from dataclasses import dataclass, asdict
import math

G = 9.81


@dataclass(frozen=True)
class Inputs:
    mass_kg: float = 30
    travel_m: float = 0.4
    reps_per_set: int = 12
    sets_per_day: int = 50
    lifting_s: float = 2
    lowering_s: float = 2
    pause_s: float = 1
    rest_between_sets_s: float = 60
    capture: float = 0.5
    efficiency: float = 0.6
    machines: int = 1
    days_per_year: int = 300
    availability: float = 1
    opening_hours: float = 12
    active_aux_w: float = 0.2
    standby_w: float = 0.01
    always_on: bool = False
    tariff: float = 0.2
    retrofit_per_machine: float = 250
    shared_cost: float = 0
    maintenance_per_machine: float = 10
    lifetime_years: int = 10
    discount_rate: float = 0.05
    inflation_rate: float = 0.02

    def validate(self):
        for name, value in asdict(self).items():
            if isinstance(value, (int, float)) and (not math.isfinite(value) or value < 0):
                raise ValueError(f"{name} must be finite and nonnegative.")
        for name in ("capture", "efficiency", "availability"):
            if getattr(self, name) > 1:
                raise ValueError(f"{name} must be between 0 and 1.")
        for name in ("reps_per_set", "sets_per_day", "machines", "days_per_year", "lifetime_years"):
            if int(getattr(self, name)) != getattr(self, name):
                raise ValueError(f"{name} must be a whole number.")
        if self.machines < 1 or self.lifetime_years < 1 or self.lowering_s <= 0:
            raise ValueError("Machines, lifetime and lowering time must be positive.")
        if self.days_per_year > 365 or not 0 < self.opening_hours <= 24:
            raise ValueError("Use at most 365 operating days and 0–24 opening hours (excluding zero).")
        if self.discount_rate > 1 or self.inflation_rate > 1:
            raise ValueError("Discount and inflation rates must be between 0 and 100%.")


@dataclass(frozen=True)
class Result:
    source_wh_per_session: float
    gross_wh_per_session: float
    mechanical_loss_wh_per_session: float
    generator_heat_loss_wh_per_session: float
    generating_power_w: float
    active_hours_per_day: float
    scheduled_hours_per_day: float
    source_kwh_year: float
    gross_kwh_year: float
    generated_kwh_year: float
    auxiliary_kwh_year: float
    net_kwh_year: float
    electricity_value_year: float
    maintenance_year: float
    savings_year: float
    installed_cost: float
    payback_years: float | None
    lifetime_balance: float
    net_present_value: float
    break_even_budget: float
    break_even_tariff: float | None


def _finish(p: Inputs, source_wh: float, captured_wh: float, gross_wh: float, sessions_day: float,
            active_hours_day: float, generating_power_w: float, scheduled_hours_day: float | None = None) -> Result:
    scheduled_hours_day = active_hours_day if scheduled_hours_day is None else scheduled_hours_day
    if scheduled_hours_day > p.opening_hours + 1e-9:
        raise ValueError(
            f"This schedule needs {scheduled_hours_day:.1f} scheduled hours (exercise + rest) per machine per day, "
            f"but the gym is open for {p.opening_hours:g}. Reduce usage or repetition time."
        )
    scale = sessions_day * p.days_per_year * p.availability * p.machines / 1000
    source = source_wh * scale
    gross = gross_wh * scale
    active_hours_year = active_hours_day * p.days_per_year * p.availability
    powered_hours_year = 8760 if p.always_on else p.opening_hours * p.days_per_year
    auxiliary = p.machines * (
        p.active_aux_w * active_hours_year
        + p.standby_w * max(0, powered_hours_year - active_hours_year)
    ) / 1000
    net = gross - auxiliary
    electricity_value = net * p.tariff
    maintenance = p.maintenance_per_machine * p.machines
    savings = electricity_value - maintenance
    cost = p.retrofit_per_machine * p.machines + p.shared_cost
    payback = cost / savings if savings > 0 else None
    cashflows = [((gross * p.tariff - auxiliary * p.tariff - maintenance)
                  * (1 + p.inflation_rate) ** (y - 1)) for y in range(1, p.lifetime_years + 1)]
    discounted_savings = sum(cf / (1 + p.discount_rate) ** y
                             for y, cf in enumerate(cashflows, start=1))
    factor = sum((1 + p.inflation_rate) ** (y - 1) / (1 + p.discount_rate) ** y
                 for y in range(1, p.lifetime_years + 1))
    breakeven_tariff = ((cost / factor + maintenance) / net if net > 0 else None)
    return Result(source_wh, gross_wh, source_wh - captured_wh,
                  captured_wh - gross_wh, generating_power_w, active_hours_day, scheduled_hours_day,
                  source, gross, gross, auxiliary, net, electricity_value,
                  maintenance, savings, cost, payback,
                  sum(cashflows) - cost, discounted_savings - cost,
                  max(0, discounted_savings), breakeven_tariff)


def weight_stack(p: Inputs) -> Result:
    p.validate()
    source = p.mass_kg * G * p.travel_m * p.reps_per_set / 3600
    gross = source * p.capture * p.efficiency
    captured = source * p.capture
    scheduled_hours = ((p.lifting_s + p.lowering_s + p.pause_s) * p.reps_per_set * p.sets_per_day
                    + p.rest_between_sets_s * max(0, p.sets_per_day - 1)) / 3600
    power = p.mass_kg * G * p.travel_m * p.capture * p.efficiency / p.lowering_s
    active_hours = (p.lifting_s + p.lowering_s + p.pause_s) * p.reps_per_set * p.sets_per_day / 3600
    return _finish(p, source, captured, gross, p.sets_per_day, active_hours, power, scheduled_hours)


def cycling(p: Inputs, mechanical_w: float = 100, minutes_per_session: float = 30,
            sessions_per_day: int = 4, efficiency: float = 0.6) -> Result:
    """Mechanical pedal power, not metabolic power or generated electrical power.

    Shares fleet, operating schedule, auxiliary draw and financial
    assumptions with the stack. Capture fraction does not apply to the bike.
    """
    p.validate()
    values = (mechanical_w, minutes_per_session, sessions_per_day, efficiency)
    if any(not math.isfinite(v) or v < 0 for v in values) or efficiency > 1:
        raise ValueError("Cycling inputs must be finite and nonnegative; efficiency is at most 1.")
    source = mechanical_w * minutes_per_session / 60
    return _finish(p, source, source, source * efficiency, sessions_per_day,
                   minutes_per_session * sessions_per_day / 60,
                   mechanical_w * efficiency)


def cumulative_balance(p: Inputs, result: Result) -> list[dict]:
    rows = [{"Year": 0, "Cash balance": -result.installed_cost}]
    balance = -result.installed_cost
    annual = result.gross_kwh_year * p.tariff - result.auxiliary_kwh_year * p.tariff - result.maintenance_year
    for y in range(1, p.lifetime_years + 1):
        balance += annual * (1 + p.inflation_rate) ** (y - 1)
        rows.append({"Year": y, "Cash balance": balance})
    return rows
