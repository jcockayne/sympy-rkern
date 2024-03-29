# TODO: there are too many tests in this file. they should be separated.

from sympy.mpmath.libmpf import *
from sympy.mpmath.libelefun import *
from sympy.mpmath import *
import random
import time
import math
import cmath

def mpc_ae(a, b, eps=eps):
    res = True
    res = res and a.real.ae(b.real, eps)
    res = res and a.imag.ae(b.imag, eps)
    return res

#----------------------------------------------------------------------------
# Low-level tests
#

# Advanced rounding test
def test_add_rounding():
    mp.dps = 15
    a = from_float(1e-50)
    assert mpf_sub(mpf_add(fone, a, 53, round_up), fone, 53, round_up) == from_float(2.2204460492503131e-16)
    assert mpf_sub(fone, a, 53, round_up) == fone
    assert mpf_sub(fone, mpf_sub(fone, a, 53, round_down), 53, round_down) == from_float(1.1102230246251565e-16)
    assert mpf_add(fone, a, 53, round_down) == fone

def test_almost_equal():
    assert mpf(1.2).ae(mpf(1.20000001), 1e-7)
    assert not mpf(1.2).ae(mpf(1.20000001), 1e-9)
    assert not mpf(-0.7818314824680298).ae(mpf(-0.774695868667929))


#----------------------------------------------------------------------------
# Test basic arithmetic
#

# Test that integer arithmetic is exact
def test_aintegers():
    # XXX: re-fix this so that all operations are tested with all rounding modes
    random.seed(0)
    for prec in [6, 10, 25, 40, 100, 250, 725]:
      for rounding in ['down', 'up', 'floor', 'ceiling', 'nearest']:
        mp.dps = prec
        M = 10**(prec-2)
        M2 = 10**(prec//2-2)
        for i in range(10):
            a = random.randint(-M, M)
            b = random.randint(-M, M)
            assert mpf(a, rounding=rounding) == a
            assert int(mpf(a, rounding=rounding)) == a
            assert int(mpf(str(a), rounding=rounding)) == a
            assert mpf(a) + mpf(b) == a + b
            assert mpf(a) - mpf(b) == a - b
            assert -mpf(a) == -a
            a = random.randint(-M2, M2)
            b = random.randint(-M2, M2)
            assert mpf(a) * mpf(b) == a*b
            assert mpf_mul(from_int(a), from_int(b), mp.prec, rounding) == from_int(a*b)
    mp.dps = 15

def test_exact_sqrts():
    for i in range(20000):
        assert sqrt(mpf(i*i)) == i
    random.seed(1)
    for prec in [100, 300, 1000, 10000]:
        mp.dps = prec
        for i in range(20):
            A = random.randint(10**(prec//2-2), 10**(prec//2-1))
            assert sqrt(mpf(A*A)) == A
    mp.dps = 15
    for i in range(100):
        for a in [1, 8, 25, 112307]:
            assert sqrt(mpf((a*a, 2*i))) == mpf((a, i))
            assert sqrt(mpf((a*a, -2*i))) == mpf((a, -i))


def test_sqrt_rounding():
    for i in [2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15]:
        i = from_int(i)
        for dps in [7, 15, 83, 106, 2000]:
            mp.dps = dps
            a = mpf_pow_int(mpf_sqrt(i, mp.prec, round_down), 2, mp.prec, round_down)
            b = mpf_pow_int(mpf_sqrt(i, mp.prec, round_up), 2, mp.prec, round_up)
            assert mpf_lt(a, i)
            assert mpf_gt(b, i)
    random.seed(1234)
    prec = 100
    for rnd in [round_down, round_nearest, round_ceiling]:
        for i in range(100):
            a = mpf_rand(prec)
            b = mpf_mul(a, a)
            assert mpf_sqrt(b, prec, rnd) == a
    mp.dps = 15

def test_odd_int_bug():
    assert to_int(from_int(3), round_nearest) == 3

def test_exact_cbrt():
    for i in range(0, 20000, 200):
        assert cbrt(mpf(i*i*i)) == i
    random.seed(1)
    for prec in [100, 300, 1000, 10000]:
        mp.dps = prec
        A = random.randint(10**(prec//2-2), 10**(prec//2-1))
        assert cbrt(mpf(A*A*A)) == A
    mp.dps = 15


#----------------------------------------------------------------------------
# Constants and functions
#

tpi = "3.1415926535897932384626433832795028841971693993751058209749445923078\
1640628620899862803482534211706798"
te = "2.71828182845904523536028747135266249775724709369995957496696762772407\
663035354759457138217852516642743"
tdegree = "0.017453292519943295769236907684886127134428718885417254560971914\
4017100911460344944368224156963450948221"
teuler = "0.5772156649015328606065120900824024310421593359399235988057672348\
84867726777664670936947063291746749516"
tln2 = "0.693147180559945309417232121458176568075500134360255254120680009493\
393621969694715605863326996418687542"
tln10 = "2.30258509299404568401799145468436420760110148862877297603332790096\
757260967735248023599720508959829834"
tcatalan = "0.91596559417721901505460351493238411077414937428167213426649811\
9621763019776254769479356512926115106249"
tkhinchin = "2.6854520010653064453097148354817956938203822939944629530511523\
4555721885953715200280114117493184769800"
tglaisher = "1.2824271291006226368753425688697917277676889273250011920637400\
2174040630885882646112973649195820237439420646"
tapery = "1.2020569031595942853997381615114499907649862923404988817922715553\
4183820578631309018645587360933525815"
tphi = "1.618033988749894848204586834365638117720309179805762862135448622705\
26046281890244970720720418939113748475"

def test_constants():
    for prec in [3, 7, 10, 15, 20, 37, 80, 100, 29]:
        mp.dps = prec
        assert pi == mpf(tpi)
        assert e == mpf(te)
        assert degree == mpf(tdegree)
        assert euler == mpf(teuler)
        assert ln2 == mpf(tln2)
        assert ln10 == mpf(tln10)
        assert catalan == mpf(tcatalan)
        assert khinchin == mpf(tkhinchin)
        assert glaisher == mpf(tglaisher)
        assert phi == mpf(tphi)
    mp.dps = 15

def test_str_1000_digits():
    mp.dps = 1001
    # last digit may be wrong
    assert str(mpf(2)**0.5)[-10:-1] == '9518488472'[:9]
    assert str(pi)[-10:-1] == '2164201989'[:9]
    mp.dps = 15

def test_str_10000_digits():
    mp.dps = 10001
    # last digit may be wrong
    assert str(mpf(2)**0.5)[-10:-1] == '5873258351'[:9]
    assert str(pi)[-10:-1] == '5256375678'[:9]
    mp.dps = 15

def test_float_sqrt():
    mp.dps = 15
    # These should round identically
    for x in [0, 1e-7, 0.1, 0.5, 1, 2, 3, 4, 5, 0.333, 76.19]:
        assert sqrt(mpf(x)) == float(x)**0.5
    assert sqrt(-1) == 1j
    assert sqrt(-2).ae(cmath.sqrt(-2))
    assert sqrt(-3).ae(cmath.sqrt(-3))
    assert sqrt(-100).ae(cmath.sqrt(-100))
    assert sqrt(1j).ae(cmath.sqrt(1j))
    assert sqrt(-1j).ae(cmath.sqrt(-1j))
    assert sqrt(math.pi + math.e*1j).ae(cmath.sqrt(math.pi + math.e*1j))
    assert sqrt(math.pi - math.e*1j).ae(cmath.sqrt(math.pi - math.e*1j))

def test_hypot():
    assert hypot(0, 0) == 0
    assert hypot(0, 0.33) == mpf(0.33)
    assert hypot(0.33, 0) == mpf(0.33)
    assert hypot(-0.33, 0) == mpf(0.33)
    assert hypot(3, 4) == mpf(5)

def test_exp():
    assert exp(0) == 1
    assert exp(10000).ae(mpf('8.8068182256629215873e4342'))
    assert exp(-10000).ae(mpf('1.1354838653147360985e-4343'))
    a = exp(mpf((1, 8198646019315405L, -53, 53)))
    assert(a.bc == bitcount(a.man))
    mp.prec = 67
    a = exp(mpf((1, 1781864658064754565L, -60, 61)))
    assert(a.bc == bitcount(a.man))
    mp.prec = 53
    assert exp(ln2 * 10).ae(1024)
    assert exp(2+2j).ae(cmath.exp(2+2j))

def test_issue_33():
    mp.dps = 512
    a = exp(-1)
    b = exp(1)
    mp.dps = 15
    assert (+a).ae(0.36787944117144233)
    assert (+b).ae(2.7182818284590451)

def test_log():
    assert log(1) == 0
    for x in [0.5, 1.5, 2.0, 3.0, 100, 10**50, 1e-50]:
        assert log(x).ae(math.log(x))
        assert log(x, x) == 1
    assert log(1024, 2) == 10
    assert log(10**1234, 10) == 1234
    assert log(2+2j).ae(cmath.log(2+2j))

def test_trig_hyperb_basic():
    for x in (range(100) + range(-100,0)):
        t = x / 4.1
        assert cos(mpf(t)).ae(math.cos(t))
        assert sin(mpf(t)).ae(math.sin(t))
        assert tan(mpf(t)).ae(math.tan(t))
        assert cosh(mpf(t)).ae(math.cosh(t))
        assert sinh(mpf(t)).ae(math.sinh(t))
        assert tanh(mpf(t)).ae(math.tanh(t))
    assert sin(1+1j).ae(cmath.sin(1+1j))
    assert sin(-4-3.6j).ae(cmath.sin(-4-3.6j))
    assert cos(1+1j).ae(cmath.cos(1+1j))
    assert cos(-4-3.6j).ae(cmath.cos(-4-3.6j))

def test_degrees():
    assert cos(0*degree) == 1
    assert cos(90*degree).ae(0)
    assert cos(180*degree).ae(-1)
    assert cos(270*degree).ae(0)
    assert cos(360*degree).ae(1)
    assert sin(0*degree) == 0
    assert sin(90*degree).ae(1)
    assert sin(180*degree).ae(0)
    assert sin(270*degree).ae(-1)
    assert sin(360*degree).ae(0)

def random_complexes(N):
    random.seed(1)
    a = []
    for i in range(N):
        x1 = random.uniform(-10, 10)
        y1 = random.uniform(-10, 10)
        x2 = random.uniform(-10, 10)
        y2 = random.uniform(-10, 10)
        z1 = complex(x1, y1)
        z2 = complex(x2, y2)
        a.append((z1, z2))
    return a

def test_complex_powers():
    for dps in [15, 30, 100]:
        # Check accuracy for complex square root
        mp.dps = dps
        a = mpc(1j)**0.5
        assert a.real == a.imag == mpf(2)**0.5 / 2
    mp.dps = 15
    random.seed(1)
    for (z1, z2) in random_complexes(100):
        assert (mpc(z1)**mpc(z2)).ae(z1**z2, 1e-12)
    assert (e**(-pi*1j)).ae(-1)
    mp.dps = 50
    assert (e**(-pi*1j)).ae(-1)
    mp.dps = 15

def test_complex_sqrt_accuracy():
    def test_mpc_sqrt(lst):
        for a, b in lst:
            z = mpc(a + j*b)
            assert mpc_ae(sqrt(z*z), z)
            z = mpc(-a + j*b)
            assert mpc_ae(sqrt(z*z), -z)
            z = mpc(a - j*b)
            assert mpc_ae(sqrt(z*z), z)
            z = mpc(-a - j*b)
            assert mpc_ae(sqrt(z*z), -z)
    random.seed(2)
    N = 10
    mp.dps = 30
    dps = mp.dps
    test_mpc_sqrt([(random.uniform(0, 10),random.uniform(0, 10)) for i in range(N)])
    test_mpc_sqrt([(i + 0.1, (i + 0.2)*10**i) for i in range(N)])
    mp.dps = 15

def test_atan():
    assert atan(-2.3).ae(math.atan(-2.3))
    assert atan2(1,1).ae(math.atan2(1,1))
    assert atan2(1,-1).ae(math.atan2(1,-1))
    assert atan2(-1,-1).ae(math.atan2(-1,-1))
    assert atan2(-1,1).ae(math.atan2(-1,1))
    assert atan2(-1,0).ae(math.atan2(-1,0))
    assert atan2(1,0).ae(math.atan2(1,0))
    assert atan2(0,0) == 0
    assert atan(1e-50) == 1e-50
    assert atan(1e50).ae(pi/2)
    assert atan(-1e-50) == -1e-50
    assert atan(-1e50).ae(-pi/2)
    assert atan(10**1000).ae(pi/2)
    for dps in [25, 70, 100, 300, 1000]:
        mp.dps = dps
        assert (4*atan(1)).ae(pi)
    mp.dps = 15

def test_areal_inverses():
    assert asin(mpf(0)) == 0
    assert asinh(mpf(0)) == 0
    assert acosh(mpf(1)) == 0
    assert isinstance(asin(mpf(0.5)), mpf)
    assert isinstance(asin(mpf(2.0)), mpc)
    assert isinstance(acos(mpf(0.5)), mpf)
    assert isinstance(acos(mpf(2.0)), mpc)
    assert isinstance(atanh(mpf(0.1)), mpf)
    assert isinstance(atanh(mpf(1.1)), mpc)

    random.seed(1)
    for i in range(50):
        x = random.uniform(0, 1)
        assert asin(mpf(x)).ae(math.asin(x))
        assert acos(mpf(x)).ae(math.acos(x))

        x = random.uniform(-10, 10)
        assert asinh(mpf(x)).ae(cmath.asinh(x).real)
        assert isinstance(asinh(mpf(x)), mpf)
        x = random.uniform(1, 10)
        assert acosh(mpf(x)).ae(cmath.acosh(x).real)
        assert isinstance(acosh(mpf(x)), mpf)
        x = random.uniform(-10, 0.999)
        assert isinstance(acosh(mpf(x)), mpc)

        x = random.uniform(-1, 1)
        assert atanh(mpf(x)).ae(cmath.atanh(x).real)
        assert isinstance(atanh(mpf(x)), mpf)

def test_complex_functions():
    for x in (range(10) + range(-10,0)):
        for y in (range(10) + range(-10,0)):
            z = complex(x, y)/4.3 + 0.01j
            assert exp(mpc(z)).ae(cmath.exp(z))
            assert log(mpc(z)).ae(cmath.log(z))
            assert cos(mpc(z)).ae(cmath.cos(z))
            assert sin(mpc(z)).ae(cmath.sin(z))
            assert tan(mpc(z)).ae(cmath.tan(z))
            assert sinh(mpc(z)).ae(cmath.sinh(z))
            assert cosh(mpc(z)).ae(cmath.cosh(z))
            assert tanh(mpc(z)).ae(cmath.tanh(z))

def test_complex_inverse_functions():
    for (z1, z2) in random_complexes(30):
        # apparently cmath uses a different branch, so we
        # can't use it for comparison
        assert sinh(asinh(z1)).ae(z1)
        #
        assert acosh(z1).ae(cmath.acosh(z1))
        assert atanh(z1).ae(cmath.atanh(z1))
        assert atan(z1).ae(cmath.atan(z1))
        # the reason we set a big eps here is that the cmath
        # functions are inaccurate
        assert asin(z1).ae(cmath.asin(z1), rel_eps=1e-12)
        assert acos(z1).ae(cmath.acos(z1), rel_eps=1e-12)
        one = mpf(1)
    for i in range(-9, 10, 3):
        for k in range(-9, 10, 3):
            a = 0.9*j*10**k + 0.8*one*10**i
            b = cos(acos(a))
            assert b.ae(a)
            b = sin(asin(a))
            assert b.ae(a)
    one = mpf(1)
    err = 2*10**-15
    for i in range(-9, 9, 3):
        for k in range(-9, 9, 3):
            a = -0.9*10**k + j*0.8*one*10**i
            b = cosh(acosh(a))
            assert b.ae(a, err)
            b = sinh(asinh(a))
            assert b.ae(a, err)

def test_reciprocal_functions():
    assert sec(3).ae(-1.01010866590799375)
    assert csc(3).ae(7.08616739573718592)
    assert cot(3).ae(-7.01525255143453347)
    assert sech(3).ae(0.0993279274194332078)
    assert csch(3).ae(0.0998215696688227329)
    assert coth(3).ae(1.00496982331368917)
    assert asec(3).ae(1.23095941734077468)
    assert acsc(3).ae(0.339836909454121937)
    assert acot(3).ae(0.321750554396642193)
    assert asech(0.5).ae(1.31695789692481671)
    assert acsch(3).ae(0.327450150237258443)
    assert acoth(3).ae(0.346573590279972655)

def test_ldexp():
    mp.dps = 15
    assert ldexp(mpf(2.5), 0) == 2.5
    assert ldexp(mpf(2.5), -1) == 1.25
    assert ldexp(mpf(2.5), 2) == 10
    assert ldexp(mpf('inf'), 3) == mpf('inf')

def test_frexp():
    mp.dps = 15
    assert frexp(0) == (0.0, 0)
    assert frexp(9) == (0.5625, 4)
    assert frexp(1) == (0.5, 1)
    assert frexp(0.2) == (0.8, -2)
    assert frexp(1000) == (0.9765625, 10)

def test_aliases():
    assert ln(7) == log(7)
    assert log10(3.75) == log(3.75,10)
    assert degrees(5.6) == 5.6 / degree
    assert radians(5.6) == 5.6 * degree
    assert power(-1,0.5) == j
    assert modf(25,7) == 4.0 and isinstance(modf(25,7), mpf)

def test_arg_sign():
    assert arg(3) == 0
    assert arg(-3).ae(pi)
    assert arg(j).ae(pi/2)
    assert arg(-j).ae(-pi/2)
    assert arg(0) == 0
    assert isnan(atan2(3,nan))
    assert isnan(atan2(nan,3))
    assert isnan(atan2(0,nan))
    assert isnan(atan2(nan,0))
    assert isnan(atan2(nan,nan))
    assert arg(inf) == 0
    assert arg(-inf).ae(pi)
    assert isnan(arg(nan))
    #assert arg(inf*j).ae(pi/2)
    assert sign(0) == 0
    assert sign(3) == 1
    assert sign(-3) == -1
    assert sign(inf) == 1
    assert sign(-inf) == -1
    assert isnan(sign(nan))
    assert sign(j) == j
    assert sign(-3*j) == -j
    assert sign(1+j).ae((1+j)/sqrt(2))

def test_misc_bugs():
    # test that this doesn't raise an exception
    mp.dps = 1000
    log(1302)
    mp.dps = 15

def test_arange():
    assert arange(10) == [mpf('0.0'), mpf('1.0'), mpf('2.0'), mpf('3.0'),
                          mpf('4.0'), mpf('5.0'), mpf('6.0'), mpf('7.0'),
                          mpf('8.0'), mpf('9.0')]
    assert arange(-5, 5) == [mpf('-5.0'), mpf('-4.0'), mpf('-3.0'),
                             mpf('-2.0'), mpf('-1.0'), mpf('0.0'),
                             mpf('1.0'), mpf('2.0'), mpf('3.0'), mpf('4.0')]
    assert arange(0, 1, 0.1) == [mpf('0.0'), mpf('0.10000000000000001'),
                                 mpf('0.20000000000000001'),
                                 mpf('0.30000000000000004'),
                                 mpf('0.40000000000000002'),
                                 mpf('0.5'), mpf('0.60000000000000009'),
                                 mpf('0.70000000000000007'),
                                 mpf('0.80000000000000004'),
                                 mpf('0.90000000000000002')]
    assert arange(17, -9, -3) == [mpf('17.0'), mpf('14.0'), mpf('11.0'),
                                  mpf('8.0'), mpf('5.0'), mpf('2.0'),
                                  mpf('-1.0'), mpf('-4.0'), mpf('-7.0')]
    assert arange(0.2, 0.1, -0.1) == [mpf('0.20000000000000001')]
    assert arange(0) == []
    assert arange(1000, -1) == []
    assert arange(-1.23, 3.21, -0.0000001) == []

def test_linspace():
    assert linspace(2, 9, 7) == [mpf('2.0'), mpf('3.166666666666667'),
        mpf('4.3333333333333339'), mpf('5.5'), mpf('6.666666666666667'),
        mpf('7.8333333333333339'), mpf('9.0')] == linspace(mpi(2, 9), 7)
    assert linspace(2, 9, 7, endpoint=0) == [mpf('2.0'), mpf('3.0'), mpf('4.0'),
        mpf('5.0'), mpf('6.0'), mpf('7.0'), mpf('8.0')]
    assert linspace(2, 7, 1) == [mpf(2)]

def test_float_cbrt():
    mp.dps = 30
    for a in arange(0,10,0.1):
        assert cbrt(a*a*a).ae(a, eps)
    assert cbrt(-1).ae(0.5 + j*sqrt(3)/2)
    one_third = mpf(1)/3
    for a in arange(0,10,2.7) + [0.1 + 10**5]:
        a = mpc(a + 1.1j)
        r1 = cbrt(a)
        mp.dps += 10
        r2 = pow(a, one_third)
        mp.dps -= 10
        assert r1.ae(r2, eps)
    mp.dps = 100
    for n in range(100, 301, 100):
        w = 10**n + j*10**-3
        z = w*w*w
        r = cbrt(z)
        assert mpc_ae(r, w, eps)
    mp.dps = 15

def test_root():
    mp.dps = 30
    random.seed(1)
    a = random.randint(0, 10000)
    p = a*a*a
    r = nthroot(mpf(p), 3)
    assert r == a
    for n in range(4, 10):
        p = p*a
        assert nthroot(mpf(p), n) == a
    mp.dps = 40
    for n in range(10, 5000, 100):
        for a in [random.random()*10000, random.random()*10**100]:
            r = nthroot(a, n)
            r1 = pow(a, mpf(1)/n)
            assert r.ae(r1)
            r = nthroot(a, -n)
            r1 = pow(a, -mpf(1)/n)
            assert r.ae(r1)
    # XXX: this is broken right now
    # tests for nthroot rounding
    for rnd in ['nearest', 'up', 'down']:
        mp.rounding = rnd
        for n in [-5, -3, 3, 5]:
            prec = 50
            for i in xrange(10):
                mp.prec = prec
                a = rand()
                mp.prec = 2*prec
                b = a**n
                mp.prec = prec
                r = nthroot(b, n)
                assert r == a
    mp.dps = 30
    for n in range(3, 21):
        a = (random.random() + j*random.random())
        assert nthroot(a, n).ae(pow(a, mpf(1)/n))
        assert mpc_ae(nthroot(a, n), pow(a, mpf(1)/n))
        a = (random.random()*10**100 + j*random.random())
        r = nthroot(a, n)
        mp.dps += 4
        r1 = pow(a, mpf(1)/n)
        mp.dps -= 4
        assert r.ae(r1)
        assert mpc_ae(r, r1, eps)
        r = nthroot(a, -n)
        mp.dps += 4
        r1 = pow(a, -mpf(1)/n)
        mp.dps -= 4
        assert r.ae(r1)
        assert mpc_ae(r, r1, eps)
    mp.dps = 15
    assert nthroot(4, 1) == 4
    assert nthroot(4, 0) == 1
    assert nthroot(4, -1) == 0.25
    assert nthroot(inf, 1) == inf
    assert nthroot(inf, 2) == inf
    assert nthroot(inf, 3) == inf
    assert nthroot(inf, -1) == 0
    assert nthroot(inf, -2) == 0
    assert nthroot(inf, -3) == 0
    assert nthroot(j, 1) == j
    assert nthroot(j, 0) == 1
    assert nthroot(j, -1) == -j
    assert isnan(nthroot(nan, 1))
    assert isnan(nthroot(nan, 0))
    assert isnan(nthroot(nan, -1))
    assert isnan(nthroot(inf, 0))

def test_perturbation_rounding():
    mp.dps = 100
    a = pi/10**50
    b = -pi/10**50
    c = 1 + a
    d = 1 + b
    mp.dps = 15
    assert exp(a) == 1
    assert exp(a, rounding='c') > 1
    assert exp(b, rounding='c') == 1
    assert exp(a, rounding='f') == 1
    assert exp(b, rounding='f') < 1
    assert cos(a) == 1
    assert cos(a, rounding='c') == 1
    assert cos(b, rounding='c') == 1
    assert cos(a, rounding='f') < 1
    assert cos(b, rounding='f') < 1
    for f in [sin, atan]:
        assert f(a) == +a
        assert f(a, rounding='c') > a
        assert f(a, rounding='f') < a
        assert f(b) == +b
        assert f(b, rounding='c') > b
        assert f(b, rounding='f') < b
    assert ln(c) == +a
    assert ln(d) == +b
    assert ln(c, rounding='c') > a
    assert ln(c, rounding='f') < a
    assert ln(d, rounding='c') > b
    assert ln(d, rounding='f') < b
    assert cosh(a) == 1
    assert cosh(b) == 1
    assert cosh(a, rounding='c') > 1
    assert cosh(b, rounding='c') > 1
    assert cosh(a, rounding='f') == 1
    assert cosh(b, rounding='f') == 1
    assert sinh(a) == +a
    assert sinh(b) == +b
    assert sinh(a, rounding='c') > a
    assert sinh(b, rounding='c') > b
    assert sinh(a, rounding='f') < a
    assert sinh(b, rounding='f') < b

def test_integer_parts():
    assert floor(3.2) == 3
    assert ceil(3.2) == 4
    assert floor(3.2+5j) == 3+5j
    assert ceil(3.2+5j) == 4+5j
