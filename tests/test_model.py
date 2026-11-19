from dataclasses import replace
import math
import unittest

from model import Inputs, weight_stack, cycling


class PhysicsTests(unittest.TestCase):
    def test_reference_example(self):
        r = weight_stack(replace(Inputs(), active_aux_w=0, standby_w=0))
        self.assertAlmostEqual(r.gross_wh_per_session, 0.11772)
        self.assertAlmostEqual(r.gross_kwh_year, 1.7658)
        self.assertAlmostEqual(r.electricity_value_year, 0.35316)

    def test_conservation_at_perfect_capture(self):
        r = weight_stack(replace(Inputs(), capture=1, efficiency=1))
        self.assertAlmostEqual(r.gross_wh_per_session, 0.3924)
        self.assertAlmostEqual(r.gross_kwh_year, r.source_kwh_year)

    def test_speed_changes_power_not_energy(self):
        slow = weight_stack(Inputs())
        fast = weight_stack(replace(Inputs(), lowering_s=1))
        self.assertEqual(slow.gross_kwh_year, fast.gross_kwh_year)
        self.assertAlmostEqual(fast.generating_power_w, 2 * slow.generating_power_w)

    def test_always_on_one_watt_can_be_net_consumer(self):
        r = weight_stack(replace(Inputs(), active_aux_w=1, standby_w=1, always_on=True))
        self.assertAlmostEqual(r.auxiliary_kwh_year, 8.76)
        self.assertLess(r.net_kwh_year, 0)
        self.assertIsNone(r.payback_years)

    def test_zero_usage_keeps_standby_cost(self):
        r = weight_stack(replace(Inputs(), sets_per_day=0, standby_w=1))
        self.assertEqual(r.gross_kwh_year, 0)
        self.assertAlmostEqual(r.net_kwh_year, -3.6)

    def test_zero_availability_keeps_standby(self):
        r = weight_stack(replace(Inputs(), availability=0, standby_w=1))
        self.assertEqual(r.gross_kwh_year, 0)
        self.assertAlmostEqual(r.auxiliary_kwh_year, 3.6)

    def test_no_usable_output(self):
        r = weight_stack(replace(Inputs(), usable_fraction=0))
        self.assertAlmostEqual(r.net_kwh_year, -r.auxiliary_kwh_year)

    def test_costs_and_discounting(self):
        p = replace(Inputs(), retrofit_per_machine=1, shared_cost=2,
                    maintenance_per_machine=0, active_aux_w=0, standby_w=0,
                    machines=2, lifetime_years=10, discount_rate=0)
        r = weight_stack(p)
        self.assertEqual(r.installed_cost, 4)
        self.assertAlmostEqual(r.payback_years, 4 / (0.35316 * 2))
        self.assertAlmostEqual(r.net_present_value, r.lifetime_balance)
        self.assertAlmostEqual(r.break_even_budget, 10 * r.savings_year)

    def test_schedule_rejected(self):
        with self.assertRaises(ValueError):
            weight_stack(replace(Inputs(), sets_per_day=1000))

    def test_invalid_inputs(self):
        for changes in ({"mass_kg": -1}, {"efficiency": 1.1}, {"lowering_s": 0},
                        {"mass_kg": math.nan}, {"machines": 0}, {"days_per_year": 366}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                weight_stack(replace(Inputs(), **changes))

    def test_bike_reference_and_independent_capture(self):
        p = replace(Inputs(), capture=0, active_aux_w=0, standby_w=0)
        r = cycling(p, 100, 30, 4, 0.6)
        self.assertEqual(r.gross_wh_per_session, 30)
        self.assertEqual(r.gross_kwh_year, 36)
        self.assertEqual(r.generating_power_w, 60)
        with self.assertRaises(ValueError):
            cycling(p, 100, 240, 4, 0.6)


if __name__ == "__main__":
    unittest.main()
