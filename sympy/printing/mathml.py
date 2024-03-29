"""
A MathML printer.
"""

from sympy import Basic, sympify
from printer import Printer

class MathMLPrinter(Printer):
    printmethod = "_mathml_"

    def __init__(self, *args, **kwargs):
        Printer.__init__(self, *args, **kwargs)
        from xml.dom.minidom import Document
        self.dom = Document()

    def doprint(self, e):
        return self._print(e).toprettyxml()

    def mathml_tag(self, e):
        """Returns the MathML tag for an expression."""
        translate = {
            'Add': 'plus',
            'Mul': 'times',
            'Derivative': 'diff',
            'Number': 'cn',
            'Pow': 'power',
            'Symbol': 'ci',
            'Integral': 'int'
        }

        for cls in e.__class__.__mro__:
            n = cls.__name__
            if n in translate:
                return translate[n]

        # Not found in the MRO set
        n = e.__class__.__name__
        return n.lower()

    def _print_Matrix(self, m):
        x = self.dom.createElement('matrix')
        for i in range(m.lines):
            x_r = self.dom.createElement('matrixrow')
            for j in range(m.cols):
                x_r.appendChild(self._print(m[i,j]))
            x.appendChild(x_r)
        return x

    def _print_Limit(self, e):
        x = self.dom.createElement('apply')
        x.appendChild(self.dom.createElement(self.mathml_tag(e)))

        x_1 = self.dom.createElement('bvar')
        x_2 = self.dom.createElement('lowlimit')
        x_1.appendChild(self._print(e.args[1]))
        x_2.appendChild(self._print(e.args[2]))

        x.appendChild(x_1)
        x.appendChild(x_2)
        x.appendChild(self._print(e.args[0]))

        return x


    def _print_Integral(self, e):
        def lime_recur(limits):
            x = self.dom.createElement('apply')
            x.appendChild(self.dom.createElement(self.mathml_tag(e)))
            bvar_elem = self.dom.createElement('bvar')
            bvar_elem.appendChild(self._print(limits[0][0]))
            x.appendChild(bvar_elem)

            if limits[0][1]:
                low_elem = self.dom.createElement('lowlimit')
                low_elem.appendChild(self._print(limits[0][1][0]))
                x.appendChild(low_elem)
                up_elem = self.dom.createElement('uplimit')
                up_elem.appendChild(self._print(limits[0][1][1]))
                x.appendChild(up_elem)
            if len(limits) == 1:
                x.appendChild(self._print(e.function))
            else:
                x.appendChild(lime_recur(limits[1:]))
            return x

        limits = list(e.limits)
        limits.reverse()
        return lime_recur(limits)

    def _print_Symbol(self, sym):
        x = self.dom.createElement(self.mathml_tag(sym))
        x.appendChild(self.dom.createTextNode(sym.name))
        return x

    def _print_Pow(self, e):
        x = self.dom.createElement('apply')
        x_1 = self.dom.createElement(self.mathml_tag(e))
        x.appendChild(x_1)
        x.appendChild(self._print(e.base))
        x.appendChild(self._print(e.exp))
        return x

    def _print_Number(self, e):
        x = self.dom.createElement(self.mathml_tag(e))
        x.appendChild(self.dom.createTextNode(str(e)))
        return x

    def _print_Derivative(self, e):
        x = self.dom.createElement('apply')
        x.appendChild(self.dom.createElement(self.mathml_tag(e)))

        x_1 = self.dom.createElement('bvar')
        for sym in e.symbols:
            x_1.appendChild(self._print(sym))

        x.appendChild(x_1)
        x.appendChild(self._print(e.expr))
        return x

    def _print_Function(self, e):
        x = self.dom.createElement("apply")
        x.appendChild(self.dom.createElement(self.mathml_tag(e)))
        for arg in e.args:
            x.appendChild(self._print(arg))
        return x

    def _print_Basic(self, e):
        x = self.dom.createElement(self.mathml_tag(e))
        for arg in e:
            x.appendChild(self._print(arg))
        return x

    def _print_AssocOp(self, e):
        x = self.dom.createElement('apply')
        x_1 = self.dom.createElement(self.mathml_tag(e))
        x.appendChild(x_1)
        for arg in e.args:
            x.appendChild(self._print(arg))
        return x

def mathml(expr):
    """Returns the MathML representation of expr"""
    s = MathMLPrinter()
    return s.doprint(sympify(expr))

def print_mathml(expr):
    """
    Print's a pretty representation of the MathML code for expr

    >>> from sympy import *
    >>> from sympy.printing.mathml import print_mathml
    >>> x = Symbol('x')
    >>> print_mathml(x+1) #doctest: +NORMALIZE_WHITESPACE
    <apply>
        <plus/>
        <cn>
                1
        </cn>
        <ci>
                x
        </ci>
    </apply>
    """
    print mathml(expr)
