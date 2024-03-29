
""" This module contain solvers for all kinds of equations:

    - algebraic, use solve()

    - recurrence, use rsolve()

    - differential, use dsolve()

    -transcendental, use tsolve()

    -nonlinear (numerically), use msolve() (you will need a good starting point)

"""

from sympy.core.sympify import sympify
from sympy.core.basic import Basic, S, C, Mul, Add
from sympy.core.power import Pow
from sympy.core.symbol import Symbol, Wild
from sympy.core.relational import Equality
from sympy.core.function import Derivative, diff
from sympy.core.numbers import ilcm

from sympy.functions import sqrt, log, exp, LambertW
from sympy.simplify import simplify, collect
from sympy.matrices import Matrix, zeros
from sympy.polys import roots

from sympy.utilities import any, all
from sympy.utilities.lambdify import lambdify
from sympy.solvers.numeric import newton

from sympy.solvers.polysys import solve_poly_system

# Codes for guess solve strategy
GS_POLY = 0
GS_RATIONAL = 1
GS_POLY_CV_1 = 2 # can be converted to a polynomial equation via the change of variable y -> x**n
GS_POLY_CV_2 = 3 # can be converted to a polynomial equation multiplying on both sides by x**m
                 # for example, x + 1/x == 0. Multiplying by x yields x**2 + x == 0
GS_RATIONAL_CV_1 = 4 # can be converted to a rational equation via the change of variable y -> x**n
GS_TRASCENDENTAL = 5

def guess_solve_strategy(expr, symbol):
    """
    Tries to guess what approach should be used to solve a specific equation

    Returns
    =======
       - -1: could not guess
       - integer > 0: code representing certain type of equation. See GS_* fields
         on this module for a complete list

    Examples
    ========
    >>> from sympy import Symbol, Rational
    >>> x = Symbol('x')
    >>> guess_solve_strategy(x**2 + 1, x)
    0
    >>> guess_solve_strategy(x**Rational(1,2) + 1, x)
    2
    """
    eq_type = -1
    if expr.is_Add:
        items = expr.args
        for item in items:
            if item.is_Number or item.is_Symbol:
                eq_type = max(eq_type, GS_POLY)
            elif item.is_Mul:
                for arg in item.args:
                    eq_type = max(guess_solve_strategy(arg, symbol), eq_type)
            elif item.is_Pow and item.base.has(symbol):
                if item.exp.is_Integer:
                    if item.exp > 0:
                        eq_type = max(eq_type, GS_POLY)
                    else:
                        eq_type = max(eq_type, GS_POLY_CV_2)
                elif item.exp.is_Rational:
                    eq_type = max(eq_type, GS_POLY_CV_1)
            elif item.is_Function:
                return GS_TRASCENDENTAL

    elif expr.is_Mul:
        # check for rational functions
        num, denom = expr.as_numer_denom()
        if denom != 1 and denom.has(symbol):
            #we have a quotient
            m = max(guess_solve_strategy(num, symbol), guess_solve_strategy(denom, symbol))
            if m == GS_POLY:
                return GS_RATIONAL
            elif m == GS_POLY_CV_1:
                return GS_RATIONAL_CV_1
            else:
                raise NotImplementedError
        else:
            return max(map(guess_solve_strategy, expr.args, [symbol]*len(expr.args)))

    elif expr.is_Symbol:
        return GS_POLY

    elif expr.is_Pow:
        if expr.exp.has(symbol):
            return GS_TRASCENDENTAL
        elif expr.exp.is_Number and expr.base.has(symbol):
            if expr.exp.is_Integer:
                eq_type = max(eq_type, GS_POLY)
            else:
                eq_type = max(eq_type, GS_POLY_CV_1)

    elif expr.is_Function and expr.has(symbol):
        return GS_TRASCENDENTAL

    return eq_type

def solve(f, *symbols, **flags):
    """Solves equations and systems of equations.

       Currently supported are univariate polynomial and transcendental
       equations and systems of linear and polynomial equations.  Input
       is formed as a single expression or an equation,  or an iterable
       container in case of an equation system.  The type of output may
       vary and depends heavily on the input. For more details refer to
       more problem specific functions.

       By default all solutions are simplified to make the output more
       readable. If this is not the expected behavior,  eg. because of
       speed issues, set simplified=False in function arguments.

       To solve equations and systems of equations of other kind, eg.
       recurrence relations of differential equations use rsolve() or
       dsolve() functions respectively.

       >>> from sympy import *
       >>> x,y = symbols('xy')

       Solve a polynomial equation:

       >>> solve(x**4-1, x)
       [1, -1, -I, I]

       Solve a linear system:

       >>> solve((x+5*y-2, -3*x+6*y-15), x, y)
       {x: -3, y: 1}

    """
    if not symbols:
        raise ValueError('no symbols were given')

    if len(symbols) == 1:
        if isinstance(symbols[0], (list, tuple, set)):
            symbols = symbols[0]

    symbols = map(sympify, symbols)

    if any(not s.is_Symbol for s in symbols):
        raise TypeError('not a Symbol')

    if not isinstance(f, (tuple, list, set)):
        f = sympify(f)

        if isinstance(f, Equality):
            f = f.lhs - f.rhs

        if len(symbols) != 1:
            raise NotImplementedError('multivariate equation')

        symbol = symbols[0]

        strategy = guess_solve_strategy(f, symbol)

        if strategy == GS_POLY:
            poly = f.as_poly( symbol )
            assert poly is not None
            result = roots(poly, cubics=True, quartics=True).keys()

        elif strategy == GS_RATIONAL:
            P, Q = f.as_numer_denom()
            #TODO: check for Q != 0
            return solve(P, symbol, **flags)

        elif strategy == GS_POLY_CV_1:
            # we must search for a suitable change of variable
            # collect exponents
            exponents_denom = list()
            args = list(f.args)
            if isinstance(f, Add):
                for arg in args:
                    if isinstance(arg, Pow):
                        exponents_denom.append(arg.exp.q)
                    elif isinstance(arg, Mul):
                        for mul_arg in arg.args:
                            if isinstance(mul_arg, Pow):
                                exponents_denom.append(mul_arg.exp.q)
            elif isinstance(f, Mul):
                for mul_arg in args:
                    if isinstance(mul_arg, Pow):
                        exponents_denom.append(mul_arg.exp.q)

            assert len(exponents_denom) > 0
            if len(exponents_denom) == 1:
                m = exponents_denom[0]
            else:
                # get the GCD of the denominators
                m = ilcm(*exponents_denom)
            # x -> y**m.
            # we assume positive for simplification purposes
            t = Symbol('t', positive=True, dummy=True)
            f_ = f.subs(symbol, t**m)
            if guess_solve_strategy(f_, t) != GS_POLY:
                raise TypeError("Could not convert to a polynomial equation: %s" % f_)
            cv_sols = solve(f_, t)
            result = list()
            for sol in cv_sols:
                result.append(sol**(S.One/m))

        elif strategy == GS_POLY_CV_2:
            m = 0
            args = list(f.args)
            if isinstance(f, Add):
                for arg in args:
                    if isinstance(arg, Pow):
                        m = min(m, arg.exp)
                    elif isinstance(arg, Mul):
                        for mul_arg in arg.args:
                            if isinstance(mul_arg, Pow):
                                m = min(m, mul_arg.exp)
            elif isinstance(f, Mul):
                for mul_arg in args:
                    if isinstance(mul_arg, Pow):
                        m = min(m, mul_arg.exp)
            f1 = simplify(f*symbol**(-m))
            result = solve(f1, symbol)
            # TODO: we might have introduced unwanted solutions
            # when multiplied by x**-m

        elif strategy == GS_TRASCENDENTAL:
            #a, b = f.as_numer_denom()
            # Let's throw away the denominator for now. When we have robust
            # assumptions, it should be checked, that for the solution,
            # b!=0.
            result = tsolve(f, *symbols)
        elif strategy == -1:
            raise Exception('Could not parse expression %s' % f)
        else:
            raise NotImplementedError("No algorithms where implemented to solve equation %s" % f)

        if flags.get('simplified', True):
            return map(simplify, result)
        else:
            return result
    else:
        if not f:
            return {}
        else:
            polys = []

            for g in f:
                g = sympify(g)

                if isinstance(g, Equality):
                    g = g.lhs - g.rhs

                poly = g.as_poly(*symbols)

                if poly is not None:
                    polys.append(poly)
                else:
                    raise NotImplementedError

            if all(p.is_linear for p in polys):
                n, m = len(f), len(symbols)
                matrix = zeros((n, m + 1))

                for i, poly in enumerate(polys):
                    for coeff, monom in poly.iter_terms():
                        try:
                            j = list(monom).index(1)
                            matrix[i, j] = coeff
                        except ValueError:
                            matrix[i, m] = -coeff

                return solve_linear_system(matrix, *symbols, **flags)
            else:
                return solve_poly_system(polys)

def solve_linear_system(system, *symbols, **flags):
    """Solve system of N linear equations with M variables, which means
       both Cramer and over defined systems are supported. The possible
       number of solutions is zero, one or infinite. Respectively this
       procedure will return None or dictionary with solutions. In the
       case of over definend system all arbitrary parameters are skiped.
       This may cause situation in with empty dictionary is returned.
       In this case it means all symbols can be assigne arbitray values.

       Input to this functions is a Nx(M+1) matrix, which means it has
       to be in augmented form. If you are unhappy with such setting
       use 'solve' method instead, where you can input equations
       explicitely. And don't worry aboute the matrix, this function
       is persistent and will make a local copy of it.

       The algorithm used here is fraction free Gaussian elimination,
       which results, after elimination, in upper-triangular matrix.
       Then solutions are found using back-substitution. This approach
       is more efficient and compact than the Gauss-Jordan method.

       >>> from sympy import *
       >>> x, y = symbols('xy')

       Solve the following system:

              x + 4 y ==  2
           -2 x +   y == 14

       >>> system = Matrix(( (1, 4, 2), (-2, 1, 14)))
       >>> solve_linear_system(system, x, y)
       {x: -6, y: 2}

    """
    matrix = system[:,:]
    syms = list(symbols)

    i, m = 0, matrix.cols-1  # don't count augmentation

    while i < matrix.lines:
        if i == m:
            # an overdetermined system
            if any(matrix[i:,m]):
                return None   # no solutions
            else:
                # remove trailing rows
                matrix = matrix[:i,:]
                break

        if not matrix[i, i]:
            # there is no pivot in current column
            # so try to find one in other colums
            for k in xrange(i+1, m):
                if matrix[i, k]:
                    break
            else:
                if matrix[i, m]:
                    return None   # no solutions
                else:
                    # zero row or was a linear combination of
                    # other rows so now we can safely skip it
                    matrix.row_del(i)
                    continue

            # we want to change the order of colums so
            # the order of variables must also change
            syms[i], syms[k] = syms[k], syms[i]
            matrix.col_swap(i, k)

        pivot_inv = S.One / matrix [i, i]

        # divide all elements in the current row by the pivot
        matrix.row(i, lambda x, _: x * pivot_inv)

        for k in xrange(i+1, matrix.lines):
            if matrix[k, i]:
                coeff = matrix[k, i]

                # subtract from the current row the row containing
                # pivot and multiplied by extracted coefficient
                matrix.row(k, lambda x, j: simplify(x - matrix[i, j]*coeff))

        i += 1

    # if there weren't any problmes, augmented matrix is now
    # in row-echelon form so we can check how many solutions
    # there are and extract them using back substitution

    simplified = flags.get('simplified', True)

    if len(syms) == matrix.lines:
        # this system is Cramer equivalent so there is
        # exactly one solution to this system of equations
        k, solutions = i-1, {}

        while k >= 0:
            content = matrix[k, m]

            # run back-substitution for variables
            for j in xrange(k+1, m):
                content -= matrix[k, j]*solutions[syms[j]]

            if simplified:
                solutions[syms[k]] = simplify(content)
            else:
                solutions[syms[k]] = content

            k -= 1

        return solutions
    elif len(syms) > matrix.lines:
        # this system will have infinite number of solutions
        # dependent on exactly len(syms) - i parameters
        k, solutions = i-1, {}

        while k >= 0:
            content = matrix[k, m]

            # run back-substitution for variables
            for j in xrange(k+1, i):
                content -= matrix[k, j]*solutions[syms[j]]

            # run back-substitution for parameters
            for j in xrange(i, m):
                content -= matrix[k, j]*syms[j]

            if simplified:
                solutions[syms[k]] = simplify(content)
            else:
                solutions[syms[k]] = content

            k -= 1

        return solutions
    else:
        return None   # no solutions

def solve_undetermined_coeffs(equ, coeffs, sym, **flags):
    """Solve equation of a type p(x; a_1, ..., a_k) == q(x) where both
       p, q are univariate polynomials and f depends on k parameters.
       The result of this functions is a dictionary with symbolic
       values of those parameters with respect to coefficiens in q.

       This functions accepts both Equations class instances and ordinary
       SymPy expressions. Specification of parameters and variable is
       obligatory for efficiency and simplicity reason.

       >>> from sympy import *
       >>> a, b, c, x = symbols('a', 'b', 'c', 'x')

       >>> solve_undetermined_coeffs(Eq(2*a*x + a+b, x), [a, b], x)
       {a: 1/2, b: -1/2}

       >>> solve_undetermined_coeffs(Eq(a*c*x + a+b, x), [a, b], x)
       {a: 1/c, b: -1/c}

    """
    if isinstance(equ, Equality):
        # got equation, so move all the
        # terms to the left hand side
        equ = equ.lhs - equ.rhs

    system = collect(equ.expand(), sym, evaluate=False).values()

    if not any([ equ.has(sym) for equ in system ]):
        # consecutive powers in the input expressions have
        # been successfully collected, so solve remaining
        # system using Gaussian ellimination algorithm
        return solve(system, *coeffs, **flags)
    else:
        return None # no solutions

def solve_linear_system_LU(matrix, syms):
    """ LU function works for invertible only """
    assert matrix.lines == matrix.cols-1
    A = matrix[:matrix.lines,:matrix.lines]
    b = matrix[:,matrix.cols-1:]
    soln = A.LUsolve(b)
    solutions = {}
    for i in range(soln.lines):
        solutions[syms[i]] = soln[i,0]
    return solutions

def dsolve(eq, funcs):
    """
    Solves any (supported) kind of differential equation.

    Usage
    =====
        dsolve(f, y(x)) -> Solve a differential equation f for the function y


    Details
    =======
        @param f: ordinary differential equation (either just the left hand
            side, or the Equality class)

        @param y: indeterminate function of one variable

        - you can declare the derivative of an unknown function this way:
        >>> from sympy import *
        >>> x = Symbol('x') # x is the independent variable

        >>> f = Function("f")(x) # f is a function of x
        >>> f_ = Derivative(f, x) # f_ will be the derivative of f with respect to x

        - This function just parses the equation "eq" and determines the type of
        differential equation by its order, then it determines all the coefficients and then
        calls the particular solver, which just accepts the coefficients.
        - "eq" can be either an Equality, or just the left hand side (in which
          case the right hand side is assumed to be 0)
        - see test_ode.py for many tests, that serve also as a set of examples
          how to use dsolve

    Examples
    ========
        >>> from sympy import *
        >>> x = Symbol('x')

        >>> f = Function('f')
        >>> dsolve(Derivative(f(x),x,x)+9*f(x), f(x))
        C1*sin(3*x) + C2*cos(3*x)
        >>> dsolve(Eq(Derivative(f(x),x,x)+9*f(x)+1, 1), f(x))
        C1*sin(3*x) + C2*cos(3*x)

    """

    if isinstance(eq, Equality):
        if eq.rhs != 0:
            return dsolve(eq.lhs-eq.rhs, funcs)
        eq = eq.lhs

    #currently only solve for one function
    if isinstance(funcs, Basic) or len(funcs) == 1:
        if isinstance(funcs, (list, tuple)): # normalize args
            f = funcs[0]
        else:
            f = funcs

        x = f.args[0]
        f = f.func

        #We first get the order of the equation, so that we can choose the
        #corresponding methods. Currently, only first and second
        #order odes can be handled.
        order = deriv_degree(eq, f(x))

        if  order > 2 :
           raise NotImplementedError("dsolve: Cannot solve " + str(eq))
        elif order == 2:
            return solve_ODE_second_order(eq, f(x))
        elif order == 1:
            return solve_ODE_first_order(eq, f(x))
        else:
            raise NotImplementedError("Not a differential equation!")

def deriv_degree(expr, func):
    """ get the order of a given ode, the function is implemented
    recursively """
    a = Wild('a', exclude=[func])

    order = 0
    if isinstance(expr, Derivative):
        order = len(expr.symbols)
    else:
        for arg in expr.args:
            if isinstance(arg, Derivative):
                order = max(order, len(arg.symbols))
            elif expr.match(a):
                order = 0
            else :
                for arg1 in arg.args:
                    order = max(order, deriv_degree(arg1, func))

    return order

def solve_ODE_first_order(eq, f):
    """
    solves many kinds of first order odes, different methods are used
    depending on the form of the given equation. Now the linear
    case is implemented.
    """
    from sympy.integrals.integrals import integrate
    x = f.args[0]
    f = f.func

    #linear case: a(x)*f'(x)+b(x)*f(x)+c(x) = 0
    a = Wild('a', exclude=[f(x)])
    b = Wild('b', exclude=[f(x)])
    c = Wild('c', exclude=[f(x)])

    r = eq.match(a*diff(f(x),x) + b*f(x) + c)
    if r:
        t = C.exp(integrate(r[b]/r[a], x))
        tt = integrate(t*(-r[c]/r[a]), x)
        return (tt + Symbol("C1"))/t

    #other cases of first order odes will be implemented here

    raise NotImplementedError("solve_ODE_first_order: Cannot solve " + str(eq))

def solve_ODE_second_order(eq, f):
    """
    solves many kinds of second order odes, different methods are used
    depending on the form of the given equation. Now the constanst
    coefficients case and a special case are implemented.
    """
    x = f.args[0]
    f = f.func

    #constant coefficients case: af''(x)+bf'(x)+cf(x)=0
    a = Wild('a', exclude=[x])
    b = Wild('b', exclude=[x])
    c = Wild('c', exclude=[x])

    r = eq.match(a*f(x).diff(x,x) + c*f(x))
    if r:
        return Symbol("C1")*C.sin(sqrt(r[c]/r[a])*x)+Symbol("C2")*C.cos(sqrt(r[c]/r[a])*x)

    r = eq.match(a*f(x).diff(x,x) + b*diff(f(x),x) + c*f(x))
    if r:
        r1 = solve(r[a]*x**2 + r[b]*x + r[c], x)
        if r1[0].is_real:
            if len(r1) == 1:
                return (Symbol("C1") + Symbol("C2")*x)*exp(r1[0]*x)
            else:
                return Symbol("C1")*exp(r1[0]*x) + Symbol("C2")*exp(r1[1]*x)
        else:
            r2 = abs((r1[0] - r1[1])/(2*S.ImaginaryUnit))
            return (Symbol("C2")*C.cos(r2*x) + Symbol("C1")*C.sin(r2*x))*exp((r1[0] + r1[1])*x/2)

    #other cases of the second order odes will be implemented here

    #special equations, that we know how to solve
    t = x*C.exp(f(x))
    tt = a*t.diff(x, x)/t
    r = eq.match(tt.expand())
    if r:
        return -solve_ODE_1(f(x), x)

    t = x*C.exp(-f(x))
    tt = a*t.diff(x, x)/t
    r = eq.match(tt.expand())
    if r:
        #check, that we've rewritten the equation correctly:
        #assert ( r[a]*t.diff(x,2)/t ) == eq.subs(f, t)
        return solve_ODE_1(f(x), x)

    neq = eq*C.exp(f(x))/C.exp(-f(x))
    r = neq.match(tt.expand())
    if r:
        #check, that we've rewritten the equation correctly:
        #assert ( t.diff(x,2)*r[a]/t ).expand() == eq
        return solve_ODE_1(f(x), x)

    raise NotImplementedError("solve_ODE_second_order: cannot solve " + str(eq))

def solve_ODE_1(f, x):
    """ (x*exp(-f(x)))'' = 0 """
    C1 = Symbol("C1")
    C2 = Symbol("C2")
    return -C.log(C1+C2/x)

x = Symbol('x', dummy=True)
a,b,c,d,e,f,g,h = [Wild(t, exclude=[x]) for t in 'abcdefgh']
patterns = None

def _generate_patterns():
    """Generates patterns for transcendental equations.

    This is lazily calculated (called) in the tsolve() function and stored in
    the patterns global variable.
    """

    tmp1 = f ** (h-(c*g/b))
    tmp2 = (-e*tmp1/a)**(1/d)
    global patterns
    patterns = [
        (a*(b*x+c)**d + e   , ((-(e/a))**(1/d)-c)/b),
        (    b+c*exp(d*x+e) , (log(-b/c)-e)/d),
        (a*x+b+c*exp(d*x+e) , -b/a-LambertW(c*d*exp(e-b*d/a)/a)/d),
        (    b+c*f**(d*x+e) , (log(-b/c)-e*log(f))/d/log(f)),
        (a*x+b+c*f**(d*x+e) , -b/a-LambertW(c*d*f**(e-b*d/a)*log(f)/a)/d/log(f)),
        (    b+c*log(d*x+e) , (exp(-b/c)-e)/d),
        (a*x+b+c*log(d*x+e) , -e/d+c/a*LambertW(a/c/d*exp(-b/c+a*e/c/d))),
        (a*(b*x+c)**d + e*f**(g*x+h) , -c/b-d*LambertW(-tmp2*g*log(f)/b/d)/g/log(f))
    ]

def tsolve(eq, sym):
    """
    Solves a transcendental equation with respect to the given
    symbol. Various equations containing mixed linear terms, powers,
    and logarithms, can be solved.

    Only a single solution is returned. This solution is generally
    not unique. In some cases, a complex solution may be returned
    even though a real solution exists.

        >>> from sympy import *
        >>> x = Symbol('x')

        >>> tsolve(3**(2*x+5)-4, x)
        [(-5*log(3) + log(4))/(2*log(3))]

        >>> tsolve(log(x) + 2*x, x)
        [1/2*LambertW(2)]

    """
    if patterns is None:
        _generate_patterns()
    eq = sympify(eq)
    if isinstance(eq, Equality):
        eq = eq.lhs - eq.rhs
    sym = sympify(sym)
    eq2 = eq.subs(sym, x)
    # First see if the equation has a linear factor
    # In that case, the other factor can contain x in any way (as long as it
    # is finite), and we have a direct solution
    r = Wild('r')
    m = eq2.match((a*x+b)*r)
    if m and m[a]:
        return [(-b/a).subs(m).subs(x, sym)]
    for p, sol in patterns:
        m = eq2.match(p)
        if m:
            return [sol.subs(m).subs(x, sym)]

    # let's also try to inverse the equation
    lhs = eq
    rhs = S.Zero

    while True:
        indep, dep = lhs.as_independent(sym)

        # dep + indep == rhs
        if lhs.is_Add:
            # this indicates we have done it all
            if indep is S.Zero:
                break

            lhs = dep
            rhs-= indep

        # dep * indep == rhs
        else:
            # this indicates we have done it all
            if indep is S.One:
                break

            lhs = dep
            rhs/= indep

    #                    -1
    # f(x) = g  ->  x = f  (g)
    if lhs.is_Function and lhs.nargs==1 and hasattr(lhs, 'inverse'):
        rhs = lhs.inverse() (rhs)
        lhs = lhs.args[0]

        sol = solve(lhs-rhs, sym)
        return sol

    elif lhs.is_Add:
        # just a simple case - we do variable substitution for first function,
        # and if it removes all functions - let's call solve.
        #      x    -x                   -1
        # UC: e  + e   = y      ->  t + t   = y
        t = Symbol('t', dummy=True)
        terms = lhs.args

        # find first term which is Function
        for f1 in lhs.args:
            if f1.is_Function:
                break
        else:
            assert False, 'tsolve: at least one Function expected at this point'

        # perform the substitution
        lhs_ = lhs.subs(f1, t)

        # if no Functions left, we can proceed with usual solve
        if not (lhs_.is_Function or
                any(term.is_Function for term in lhs_.args)):
            cv_sols = solve(lhs_ - rhs, t)
            cv_inv = solve( t - f1, sym )[0]
            sols = list()
            for sol in cv_sols:
                sols.append(cv_inv.subs(t, sol))
            return sols


    raise ValueError("unable to solve the equation")


def msolve(args, f, x0, tol=None, maxsteps=None, verbose=False, norm=None,
           modules=['mpmath', 'sympy']):
    """
    Solves a nonlinear equation system numerically.

    f is a vector function of symbolic expressions representing the system.
    args are the variables.
    x0 is a starting vector close to a solution.

    Be careful with x0, not using floats might give unexpected results.

    Use modules to specify which modules should be used to evaluate the
    function and the Jacobian matrix. Make sure to use a module that supports
    matrices. For more information on the syntax, please see the docstring
    of lambdify.

    Currently only fully determined systems are supported.

    >>> from sympy import Symbol, Matrix
    >>> x1 = Symbol('x1')
    >>> x2 = Symbol('x2')
    >>> f1 = 3 * x1**2 - 2 * x2**2 - 1
    >>> f2 = x1**2 - 2 * x1 + x2**2 + 2 * x2 - 8
    >>> msolve((x1, x2), (f1, f2), (-1., 1.))
    [-1.19287309935246]
    [ 1.27844411169911]
    """
    if isinstance(f,  (list,  tuple)):
        f = Matrix(f).T
    if len(args) != f.cols:
        raise NotImplementedError('need exactly as many variables as equations')
    if verbose:
        print 'f(x):'
        print f
    # derive Jacobian
    J = f.jacobian(args)
    if verbose:
        print 'J(x):'
        print J
    # create functions
    f = lambdify(args, f.T, modules)
    J = lambdify(args, J, modules)
    # solve system using Newton's method
    kwargs = {}
    if tol:
        kwargs['tol'] = tol
    if maxsteps:
        kwargs['maxsteps'] = maxsteps
    kwargs['verbose'] = verbose
    if norm:
        kwargs['norm'] = norm
    x = newton(f, x0, J, **kwargs)
    return x
