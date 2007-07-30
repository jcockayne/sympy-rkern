import sys
sys.path.append(".")

disabled = False
try:
    from ctypes import *
except:
    disabled = True

from sympy import symbols, log, sin, cos
x,y = symbols('xy')

class TestPlotting:
    def __init__(self):
        global disabled
        self.disabled = disabled

    def test_import(self):
        from sympy import Plot

    def test_plot_2d(self):
        from sympy import Plot
        Plot(x, [x, -5, 5, 10], visible=False)
        
    def test_plot_2d_discontinuous(self):
        from sympy import Plot
        Plot(1/x, [x, -1, 1, 2], visible=False)
    
    def test_plot_3d(self):
        from sympy import Plot
        Plot(x*y, [x, -5, 5, 10], [y, -5, 5, 10], visible=False)

    def test_plot_3d_discontinuous(self):
        from sympy import Plot
        Plot(1/x, [x, -3, 3], [y, -1, 1, 1], visible=False)

    def _test_plot_2d_polar(self):
        from sympy import Plot
        Plot(log(x), [x,0,6.282], 'mode=polar', visible=False)
        Plot(1/x, [x,-1,1,4], 'mode=polar', visible=False)

    def test_plot_3d_cylinder(self):
        from sympy import Plot
        Plot(1/y, [x,0,6.282], [y,-1,1,6], 'mode=polar', visible=False)

    def test_plot_3d_spherical(self):
        from sympy import Plot
        Plot(1, [x,0,6.282], [y,0,3.141], 'mode=spherical', visible=False)

    def _test_plot_2d_parametric(self):
        from sympy import Plot
        Plot(sin(x), cos(x), [x, 0, 6.282], 'mode=parametric', visible=False)

    def _test_plot_3d_parametric(self):
        from sympy import Plot
        Plot(sin(x), cos(x), x/5.0, [x, 0, 6.282], 'mode=parametric', visible=False)

    def test_plot_grid(self):
        from sympy import Plot
        Plot(x, [x, -5, 5, 10], grid='xy', visible=False)