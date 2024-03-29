"""This module is intended for solving recurrences or, in other words,
   difference equations. Currently supported are linear, inhomogeneous
   equantions with polynomial or rational coefficients.

   The solutions are obtained among polynomials, rational functions,
   hypergeometric terms, or combinations of hypergeometric term which
   are pairwise dissimilar.
"""

from sympy.core.basic import Basic, S
from sympy.core.numbers import Rational
from sympy.core.symbol import Symbol
from sympy.core.add import Add
from sympy.core.mul import Mul
from sympy.core import sympify

from sympy.simplify import simplify, hypersimp, hypersimilar, collect
from sympy.solvers import solve, solve_undetermined_coeffs
from sympy.polys import Poly, quo, gcd, roots, resultant
from sympy.functions import Binomial, FallingFactorial
from sympy.matrices import Matrix, casoratian
from sympy.concrete import product

def rsolve_poly(coeffs, f, n, **hints):
    """Given linear recurrence operator L of order 'k' with polynomial
       coefficients and inhomogeneous equation Ly = f, where 'f' is a
       polynomial, we seek for all polynomial solutions over field K
       of characteristic zero.

       The algorithm performs two basic steps:

           (1) Compute degree N of the general polynomial solution.
           (2) Find all polynomials of degree N or less of Ly = f.

       There are two methods for computing the polynomial solutions.
       If the degree bound is relatively small, ie. it's smaller than
       or equal to the order of the recurrence, then naive method of
       undetermined coefficients is being used. This gives system
       of algebraic equations with N+1 unknowns.

       In the other case, the algorithm performs transformation of the
       initial equation to an equivalent one, for which the system of
       algebraic equations has only 'r' undeterminates. This method is
       quite sophisticated (in comparison with the naive one) and was
       invented together by Abramov, Bronstein and Petkovsek.

       It is possible to generalize the algorithm implemented here to
       the case of linear q-difference and differential equations.

       Lets say that we would like to compute m-th Bernoulli polynomial
       up to a constant. For this we can use b(n+1) - b(n) == m*n**(m-1)
       recurrence, which has solution b(n) = B_m + C. For example:

       >>> from sympy.core import Symbol
       >>> n = Symbol('n', integer=True)

       >>> rsolve_poly([-1, 1], 4*n**3, n)
       C0 + n**2 - 2*n**3 + n**4

       For more information on implemented algorithms refer to:

       [1] S. A. Abramov, M. Bronstein and M. Petkovsek, On polynomial
           solutions of linear operator equations, in: T. Levelt, ed.,
           Proc. ISSAC '95, ACM Press, New York, 1995, 290-296.

       [2] M. Petkovsek, Hypergeometric solutions of linear recurrences
           with polynomial coefficients, J. Symbolic Computation,
           14 (1992), 243-264.

       [3] M. Petkovsek, H. S. Wilf, D. Zeilberger, A = B, 1996.

    """
    f = sympify(f)

    if not f.is_polynomial(n):
        return None

    homogeneous = f.is_zero

    r = len(coeffs)-1

    coeffs = [ Poly(coeff, n) for coeff in coeffs ]

    polys = [ Poly((), n) ] * (r+1)
    terms = [ (S.Zero, S.NegativeInfinity) ] *(r+1)

    for i in xrange(0, r+1):
        for j in xrange(i, r+1):
            polys[i] += coeffs[j]*Binomial(j, i)

        if not polys[i].is_zero:
            coeff, (exp,) = polys[i].LT
            terms[i] = (coeff, exp)

    d = b = terms[0][1]

    for i in xrange(1, r+1):
        if terms[i][1] > d:
            d = terms[i][1]

        if terms[i][1] - i > b:
            b = terms[i][1] - i

    d, b = int(d), int(b)

    x = Symbol('x', dummy=True)

    degree_poly = S.Zero

    for i in xrange(0, r+1):
        if terms[i][1] - i == b:
            degree_poly += terms[i][0]*FallingFactorial(x, i)

    nni_roots = roots(degree_poly, x, domain='Z',
        predicate=lambda r: r >= 0).keys()

    if nni_roots:
        N = [max(nni_roots)]
    else:
        N = []

    if homogeneous:
        N += [-b-1]
    else:
        N += [f.as_poly(n).degree - b, -b-1]

    N = int(max(N))

    if N < 0:
        if homogeneous:
            if hints.get('symbols', False):
                return (S.Zero, [])
            else:
                return S.Zero
        else:
            return None

    if N <= r:
        C = []
        y = E = S.Zero

        for i in xrange(0, N+1):
            C.append(Symbol('C'+str(i)))
            y += C[i] * n**i

        for i in xrange(0, r+1):
            E += coeffs[i].as_basic()*y.subs(n, n+i)

        solutions = solve_undetermined_coeffs(E-f, C, n)

        if solutions is not None:
            C = [ c for c in C if (c not in solutions) ]
            result = y.subs(solutions)
        else:
            return None # TBD
    else:
        A = r
        U = N+A+b+1

        nni_roots = roots(polys[r], domain='Z',
            predicate=lambda r: r >= 0).keys()

        if nni_roots != []:
            a = max(nni_roots) + 1
        else:
            a = S.Zero

        def zero_vector(k):
            return [S.Zero] * k

        def one_vector(k):
            return [S.One] * k

        def delta(p, k):
            B = S.One
            D = p.subs(n, a+k)

            for i in xrange(1, k+1):
                B *= -Rational(k-i+1, i)
                D += B * p.subs(n, a+k-i)

            return D

        alpha = {}

        for i in xrange(-A, d+1):
            I = one_vector(d+1)

            for k in xrange(1, d+1):
                I[k] = I[k-1] * (x+i-k+1)/k

            alpha[i] = S.Zero

            for j in xrange(0, A+1):
                for k in xrange(0, d+1):
                    B = Binomial(k, i+j)
                    D = delta(polys[j].as_basic(), k)

                    alpha[i] += I[k]*B*D

        V = Matrix(U, A, lambda i, j: int(i == j))

        if homogeneous:
            for i in xrange(A, U):
                v = zero_vector(A)

                for k in xrange(1, A+b+1):
                    if i - k < 0:
                        break

                    B = alpha[k-A].subs(x, i-k)

                    for j in xrange(0, A):
                        v[j] += B * V[i-k, j]

                denom = alpha[-A].subs(x, i)

                for j in xrange(0, A):
                    V[i, j] = -v[j] / denom
        else:
            G = zero_vector(U)

            for i in xrange(A, U):
                v = zero_vector(A)
                g = S.Zero

                for k in xrange(1, A+b+1):
                    if i - k < 0:
                        break

                    B = alpha[k-A].subs(x, i-k)

                    for j in xrange(0, A):
                        v[j] += B * V[i-k, j]

                    g += B * G[i-k]

                denom = alpha[-A].subs(x, i)

                for j in xrange(0, A):
                    V[i, j] = -v[j] / denom

                G[i] = (delta(f, i-A) - g) / denom

        P, Q = one_vector(U), zero_vector(A)

        for i in xrange(1, U):
            P[i] = (P[i-1] * (n-a-i+1)/i).expand()

        for i in xrange(0, A):
            Q[i] = Add(*[ (v*p).expand() for v, p in zip(V[:,i], P) ])

        if not homogeneous:
            h = Add(*[ (g*p).expand() for g, p in zip(G, P) ])

        C = [ Symbol('C'+str(i)) for i in xrange(0, A) ]

        g = lambda i: Add(*[ c*delta(q, i) for c, q in zip(C, Q) ])

        if homogeneous:
            E = [ g(i) for i in xrange(N+1, U) ]
        else:
            E = [ g(i) + delta(h, i) for i in xrange(N+1, U) ]

        if E != []:
            solutions = solve(E, *C)

            if solutions is None:
                if homogeneous:
                    if hints.get('symbols', False):
                        return (S.Zero, [])
                    else:
                        return S.Zero
                else:
                    return None
        else:
            solutions = {}

        if homogeneous:
            result = S.Zero
        else:
            result = h

        for c, q in zip(C, Q):
            if c in solutions:
                s = solutions[c]*q
                C.remove(c)
            else:
                s = c*q

            result += s.expand()

    if hints.get('symbols', False):
        return (result, C)
    else:
        return result

def rsolve_ratio(coeffs, f, n, **hints):
    """Given linear recurrence operator L of order 'k' with polynomial
       coefficients and inhomogeneous equation Ly = f, where 'f' is a
       polynomial, we seek for all rational solutions over field K of
       characteristic zero.

       This procedure accepts only polynomials, however if you are
       interested in solving recurrence with ratinal coefficients
       then use rsolve() with will preprocess equation given and
       run this procedure with polynomial arguments.

       The algorithm performs two basic steps:

           (1) Compute polynomial v(n) which can be used as universal
               denominator of any rational solution of equation Ly = f.

           (2) Construct new linear difference equation by substitution
               y(n) = u(n)/v(n) and solve it for u(n) finding all its
               polynomial solutions. Return None if none were found.

       Algorithm implemented here is a revised version of the original
       Abramov's algorithm, developed in 1989. The new approach is much
       simpler to implement and has better overall efficiency. This
       method can be easily adapted to q-difference equations case.

       Besides finding rational solutions alone, this functions is
       an important part of Hyper algorithm were it is used to find
       particular solution of ingomogeneous part of a recurrence.

       For more information on the implemented algorithm refer to:

       [1] S. A. Abramov, Rational solutions of linear difference
           and q-difference equations with polynomial coefficients,
           in: T. Levelt, ed., Proc. ISSAC '95, ACM Press, New York,
           1995, 285-289

    """
    f = sympify(f)

    if not f.is_polynomial(n):
        return None

    coeffs = map(sympify, coeffs)

    r = len(coeffs)-1

    A, B = coeffs[r], coeffs[0]
    A = A.subs(n, n-r).expand()

    h = Symbol('h', dummy=True)

    res = resultant(A, B.subs(n, n+h), n)

    if not res.is_polynomial(h):
        p, q = res.as_numer_denom()
        res = quo(p, q, h)

    nni_roots = roots(res, h, domain='Z',
        predicate=lambda r: r >= 0).keys()

    if not nni_roots:
        return rsolve_poly(coeffs, f, n, **hints)
    else:
        C, numers = S.One, [S.Zero]*(r+1)

        for i in xrange(int(max(nni_roots)), -1, -1):
            d = gcd(A, B.subs(n, n+i), n)

            A = quo(A, d, n)
            B = quo(B, d.subs(n, n-i), n)

            C *= Mul(*[ d.subs(n, n-j) for j in xrange(0, i+1) ])

        denoms = [ C.subs(n, n+i) for i in range(0, r+1) ]

        for i in range(0, r+1):
            g = gcd(coeffs[i], denoms[i], n)

            numers[i] = quo(coeffs[i], g, n)
            denoms[i] = quo(denoms[i], g, n)

        for i in xrange(0, r+1):
            numers[i] *= Mul(*(denoms[:i] + denoms[i+1:]))

        result = rsolve_poly(numers, f * Mul(*denoms), n, **hints)

        if result is not None:
            if hints.get('symbols', False):
                return (simplify(result[0] / C), result[1])
            else:
                return simplify(result / C)
        else:
            return None

def rsolve_hyper(coeffs, f, n, **hints):
    """Given linear recurrence operator L of order 'k' with polynomial
       coefficients and inhomogeneous equation Ly = f we seek for all
       hypergeometric solutions over field K of characteristic zero.

       The inhomogeneous part can be either hypergeometric or a sum
       of a fixed number of pairwise dissimilar hypergeometric terms.

       The algorithm performs three basic steps:

           (1) Group together similar hypergeometric terms in the
               inhomogeneous part of Ly = f, and find particular
               solution using Abramov's algorithm.

           (2) Compute generating set of L and find basis in it,
               so that all solutions are lineary independent.

           (3) Form final solution with the number of arbitrary
               constants equal to dimension of basis of L.

       Term a(n) is hypergeometric if it is anihilated by first order
       linear difference equations with polynomial coefficients or, in
       simpler words, if consecutive term ratio is a rational function.

       The output of this procedure is a linear combination of fixed
       number of hypergeometric terms. However the underlying method
       can generate larger class of solutions - D'Alembertian terms.

       Note also that this method not only computes the kernel of the
       inhomogeneous equation, but also reduces in to a basis so that
       solutions generated by this procedure are lineary independent

       For more information on the implemented algorithm refer to:

       [1] M. Petkovsek, Hypergeometric solutions of linear recurrences
           with polynomial coefficients, J. Symbolic Computation,
           14 (1992), 243-264.

       [2] M. Petkovsek, H. S. Wilf, D. Zeilberger, A = B, 1996.

    """
    coeffs = map(sympify, coeffs)

    f = sympify(f)

    r, kernel = len(coeffs)-1, []

    if not f.is_zero:
        if f.is_Add:
            similar = {}

            for g in f.expand().args:
                if not g.is_hypergeometric(n):
                    return None

                for h in similar.iterkeys():
                    if hypersimilar(g, h, n):
                        similar[h] += g
                        break
                else:
                    similar[g] = S.Zero

            inhomogeneous = []

            for g, h in similar.iteritems():
                inhomogeneous.append(g+h)
        elif f.is_hypergeometric(n):
            inhomogeneous = [f]
        else:
            return None

        for i, g in enumerate(inhomogeneous):
            coeff, polys = S.One, coeffs[:]
            denoms = [ S.One ] * (r+1)

            s = hypersimp(g, n)

            for j in xrange(1, r+1):
                coeff *= s.subs(n, n+j-1)

                p, q = coeff.as_numer_denom()

                polys[j] *= p
                denoms[j] = q

            for j in xrange(0, r+1):
                polys[j] *= Mul(*(denoms[:j] + denoms[j+1:]))

            R = rsolve_poly(polys, Mul(*denoms), n)

            if not (R is None  or  R is S.Zero):
                inhomogeneous[i] *= R
            else:
                return None

            result = Add(*inhomogeneous)
    else:
        result = S.Zero

    Z = Symbol('Z', dummy=True)

    p, q = coeffs[0], coeffs[r].subs(n, n-r+1)

    p_factors = [ z for z in roots(p, n).iterkeys() ]
    q_factors = [ z for z in roots(q, n).iterkeys() ]

    factors = [ (S.One, S.One) ]

    for p in p_factors:
        for q in q_factors:
            if p.is_integer and q.is_integer and p <= q:
                continue
            else:
                factors += [(n-p, n-q)]

    p = [ (n-p, S.One) for p in p_factors ]
    q = [ (S.One, n-q) for q in q_factors ]

    factors = p + factors + q

    for A, B in factors:
        polys, degrees = [], []
        D = A*B.subs(n, n+r-1)

        for i in xrange(0, r+1):
            a = Mul(*[ A.subs(n, n+j) for j in xrange(0, i) ])
            b = Mul(*[ B.subs(n, n+j) for j in xrange(i, r) ])

            poly = quo(coeffs[i]*a*b, D, n)
            polys.append(poly.as_poly(n))

            if not poly.is_zero:
                degrees.append(polys[i].degree)

        d, poly = max(degrees), S.Zero

        for i in xrange(0, r+1):
            coeff = polys[i].coeff(d)

            if coeff is not S.Zero:
                poly += coeff * Z**i

        for z in roots(poly, Z).iterkeys():
            if not z.is_real or z.is_zero:
                continue

            C = rsolve_poly([ polys[i]*z**i for i in xrange(r+1) ], 0, n)

            if C is not None  and  C is not S.Zero:
                ratio = z * A * C.subs(n, n + 1) / B / C
                K = product(simplify(ratio), (n, 0, n-1))

                if casoratian(kernel+[K], n) != 0:
                    kernel.append(K)

    symbols = [ Symbol('C'+str(i)) for i in xrange(len(kernel)) ]

    for C, ker in zip(symbols, kernel):
        result += C * ker

    if hints.get('symbols', False):
        return (result, symbols)
    else:
        return result

def rsolve(eq, seq):
    """

    """
    pass
