
from polynomial import Poly

def LexPoly(*args):
    """Returns a polynomial with lexicographic order of terms. """
    return Poly(*args, **{ 'order' : 'lex' })

from algorithms import poly_div, poly_pdiv, poly_groebner, poly_lcm, poly_gcd, \
    poly_half_gcdex, poly_gcdex, poly_sqf, poly_resultant, poly_subresultants, \
    poly_decompose

from rootfinding import poly_root_factors, poly_sturm

def poly_quo(f, g, *symbols):
    """Wrapper for poly_div() """
    return poly_div(f, g, *symbols)[0]

def poly_rem(f, g, *symbols):
    """Wrapper for poly_div() """
    return poly_div(f, g, *symbols)[1]

def poly_pquo(f, g, *symbols):
    """Wrapper for poly_pdiv() """
    return poly_pdiv(f, g, *symbols)[0]

def poly_prem(f, g, *symbols):
    """Wrapper for poly_pdiv() """
    return poly_pdiv(f, g, *symbols)[1]

def _conv_args(n, args):
    symbols = args[n:]

    if len(symbols) == 1 and isinstance(symbols[0], (tuple, list)):
        return args[:n] + tuple(symbols[0])
    else:
        return args

def _map_basic(f, n, *args, **kwargs):
    result = f(*_conv_args(n, args), **kwargs)

    if isinstance(result, (list, tuple, set)):
        return result.__class__(g.as_basic() for g in result)
    else:
        return result.as_basic()

_funcs = {
    'quo'           : 2,
    'rem'           : 2,
    'pdiv'          : 2,
    'pquo'          : 2,
    'prem'          : 2,
    'groebner'      : 1,
    'lcm'           : 2,
    'gcd'           : 2,
    'gcdex'         : 2,
    'half_gcdex'    : 2,
    'subresultants' : 2,
    'resultant'     : 2,
    'sqf'           : 1,
    'decompose'     : 1,
    'root_factors'  : 1,
    'sturm'         : 1,
}

_func_def = \
"""
def %s(*args, **kwargs):
    return _map_basic(poly_%s, %d, *args, **kwargs)

%s.__doc__ = poly_%s.__doc__
"""

for _func, _n in _funcs.iteritems():
    exec _func_def % (_func, _func, _n, _func, _func)

def div(*args, **kwargs):
    q, r = poly_div(*_conv_args(2, args), **kwargs)

    if type(q) is not list:
        q = q.as_basic()
    else:
        q = [ p.as_basic() for p in q ]

    return q, r.as_basic()

div.__doc__ = poly_div.__doc__

