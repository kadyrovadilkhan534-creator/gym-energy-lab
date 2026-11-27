"""Optional Manim scene for the stack-to-electricity energy path.

Render with: manim -pqh gym_energy_animation.py StackEnergy
It reads the same Inputs defaults and weight_stack calculation as the app.
"""

from manim import *

from model import Inputs, weight_stack


class StackEnergy(Scene):
    def construct(self):
        p = Inputs()
        r = weight_stack(p)
        title = Text("Where one set's energy goes", font_size=32, color=WHITE)
        title.to_edge(UP)
        self.play(Write(title))

        stack = VGroup(Rectangle(width=1.2, height=1.1, color=BLUE_B),
                       Text(f"{p.mass_kg:g} kg", font_size=22)).move_to(LEFT * 5 + UP)
        pulley = Circle(radius=0.55, color=GRAY_B).move_to(LEFT * 2.8 + UP)
        pulley.add(Line(pulley.get_left(), pulley.get_right(), color=GRAY_B))
        generator = RoundedRectangle(width=1.5, height=1, corner_radius=0.12,
                                     color=TEAL_B).move_to(RIGHT * 0.1 + UP)
        generator.add(Text("Generator", font_size=20).move_to(generator.get_center()))
        lamp = VGroup(Circle(radius=0.35, color=YELLOW),
                      Line(ORIGIN, DOWN * 0.5, color=YELLOW)).move_to(RIGHT * 4 + UP)
        cable = Arrow(generator.get_right(), lamp.get_left(), buff=0.12, color=YELLOW)
        rope = always_redraw(lambda: Line(stack.get_top(), pulley.get_bottom(), color=WHITE))
        self.play(Create(rope), FadeIn(stack), Create(pulley), FadeIn(generator))
        self.play(stack.animate.shift(DOWN * 0.55), Rotate(pulley, -PI / 3),
                  run_time=1.7)
        self.play(GrowArrow(cable), FadeIn(lamp))
        self.play(Indicate(lamp, color=YELLOW))

        rows = VGroup(
            Text(f"Available: {r.source_wh_per_session:.3f} Wh", font_size=22),
            Text(f"Not captured: {r.mechanical_loss_wh_per_session:.3f} Wh", font_size=22, color=ORANGE),
            Text(f"Generator/conversion heat: {r.generator_heat_loss_wh_per_session:.3f} Wh", font_size=22, color=RED),
            Text(f"Electricity: {r.gross_wh_per_session:.3f} Wh", font_size=22, color=GREEN_B),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).to_edge(DOWN, buff=0.4)
        self.play(LaggedStart(*(Write(row) for row in rows), lag_ratio=0.2))
        self.wait(2)
