from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest


class InterfaceTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()

    def test_initial_render_and_mass_update(self):
        app = self.app()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "0.118 Wh")
        app.slider(key="mass").set_value(60).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "0.235 Wh")

    def test_zero_output_and_reset(self):
        app = self.app()
        app.slider(key="capture").set_value(0).run()
        self.assertFalse(app.exception)
        self.assertTrue(app.warning)
        self.assertEqual(app.metric[0].value, "0.000 Wh")
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.slider(key="capture").value, 50)

    def test_impossible_usage_displays_error(self):
        app = self.app()
        app.number_input(key="sets").set_value(1000).run()
        self.assertFalse(app.exception)
        self.assertTrue(app.error)

    def test_bike_and_currency_controls(self):
        app = self.app()
        app.number_input(key="bike_power").set_value(200).run()
        app.selectbox(key="currency").set_value("INR").run()
        self.assertFalse(app.exception)
        self.assertIn("INR", app.metric[2].value)
        app.number_input(key="bike_sessions").set_value(100).run()
        self.assertFalse(app.exception)
        self.assertTrue(app.warning)


if __name__ == "__main__":
    unittest.main()
