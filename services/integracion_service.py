from typing import Callable, Dict, List, Tuple, Optional
import math

# ---------- Helpers comunes ----------

def linspace(a: float, b: float, n: int) -> List[float]:
    if n <= 0:
        return [a, b]
    h = (b - a) / n
    return [a + i * h for i in range(n + 1)]

def _is_finite(y: float) -> bool:
    return isinstance(y, (int, float)) and math.isfinite(y)

def _limit_symmetric(f: Callable[[float], float], x: float) -> Optional[float]:
    """
    Estima lim_{t->x} f(t) por diferencias simétricas decrecientes.
    Devuelve None si no puede estimar algo estable.
    """
    steps = [1e-4, 1e-5, 1e-6, 5e-7, 1e-7, 5e-8, 1e-8]
    vals = []
    for h in steps:
        try:
            y1 = f(x + h)
            y2 = f(x - h)
            if _is_finite(y1) and _is_finite(y2):
                vals.append(0.5 * (y1 + y2))
        except Exception:
            continue
    if not vals:
        return None
    vals.sort()
    m = len(vals)
    if m % 2 == 1:
        return vals[m // 2]
    return 0.5 * (vals[m // 2 - 1] + vals[m // 2])

def safe_f(f: Callable[[float], float], x: float) -> float:
    """
    Evalúa f(x). Si hay ZeroDivisionError/NaN/Inf, intenta el límite simétrico.
    Si no se puede estimar, devuelve 0.0 para no romper la integración.
    """
    try:
        y = f(x)
        if _is_finite(y):
            return float(y)
    except ZeroDivisionError:
        pass
    except Exception:
        # probado luego con límite
        pass

    lim = _limit_symmetric(f, x)
    if lim is not None and _is_finite(lim):
        return float(lim)

    try:
        y = f(x)  # reintento para capturar la excepción exacta si se quisiera
    except Exception:
        return 0.0
    return float(y) if _is_finite(y) else 0.0

def sample_curve(f: Callable[[float], float], a: float, b: float, samples: int = 401) -> List[Tuple[float, Optional[float]]]:
    if samples < 2:
        samples = 2
    xs = [a + i * (b - a) / (samples - 1) for i in range(samples)]
    out = []
    for x in xs:
        try:
            y = safe_f(f, x)
        except Exception:
            y = None
        out.append((x, y if _is_finite(y) else None))
    return out

def _points_to_payload(indices, xs, fxs, coefs, contribs) -> List[Dict]:
    points = []
    for i, x, fx, c, ct in zip(indices, xs, fxs, coefs, contribs):
        fx_val = float(fx) if _is_finite(fx) else 0.0
        ct_val = float(ct) if _is_finite(ct) else 0.0
        points.append({
            "index": int(i),
            "x": float(x),
            "fx": fx_val,
            "coefficient": float(c),
            "contribution": ct_val,
        })
    return points

# ---------- Métodos compuestos ----------

def run_rectangulo(f: Callable[[float], float], a: float, b: float, n: int) -> Dict:
    """Regla del rectángulo (punto medio) compuesta."""
    if n < 1:
        n = 1
    h = (b - a) / n
    indices, xs, fxs, contribs = [], [], [], []
    total = 0.0
    for i in range(n):
        xm = (a + i * h + a + (i + 1) * h) / 2.0
        fx = safe_f(f, xm)
        contrib = fx * h
        indices.append(i)
        xs.append(xm)
        fxs.append(fx)
        contribs.append(contrib)
        total += contrib
    points = _points_to_payload(indices, xs, fxs, [1.0] * n, contribs)
    return {"value": float(total), "h": h, "evals": n, "points": points}

def run_trapezoidal(f: Callable[[float], float], a: float, b: float, n: int) -> Dict:
    """Regla trapezoidal compuesta."""
    if n < 1:
        n = 1
    xs = linspace(a, b, n)
    h = (b - a) / n
    fxs = [safe_f(f, x) for x in xs]
    coefs = [1.0] + [2.0] * (n - 1) + [1.0]
    contribs = [fx * c * (h / 2.0) for fx, c in zip(fxs, coefs)]
    total = sum(contribs)
    points = _points_to_payload(range(len(xs)), xs, fxs, coefs, contribs)
    return {"value": float(total), "h": h, "evals": len(xs), "points": points}

def run_simpson_13(f: Callable[[float], float], a: float, b: float, n: int) -> Dict:
    """Simpson 1/3 compuesta: n debe ser par (se ajusta si no lo es)."""
    if n < 2:
        n = 2
    if n % 2 != 0:
        n += 1
    xs = linspace(a, b, n)
    h = (b - a) / n
    fxs = [safe_f(f, x) for x in xs]
    coefs = []
    for i in range(len(xs)):
        if i == 0 or i == n:
            coefs.append(1.0)
        elif i % 2 == 1:
            coefs.append(4.0)
        else:
            coefs.append(2.0)
    contribs = [fx * c * (h / 3.0) for fx, c in zip(fxs, coefs)]
    total = sum(contribs)
    points = _points_to_payload(range(len(xs)), xs, fxs, coefs, contribs)
    return {"value": float(total), "h": h, "evals": len(xs), "points": points}

def run_simpson_38(f: Callable[[float], float], a: float, b: float, n: int) -> Dict:
    """Simpson 3/8 compuesta: n múltiplo de 3 (se ajusta)."""
    if n < 3:
        n = 3
    if n % 3 != 0:
        n = ((n // 3) + 1) * 3
    xs = linspace(a, b, n)
    h = (b - a) / n
    fxs = [safe_f(f, x) for x in xs]
    coefs = []
    for i in range(len(xs)):
        if i == 0 or i == n:
            coefs.append(1.0)
        elif i % 3 == 0:
            coefs.append(2.0)
        else:
            coefs.append(3.0)
    contribs = [fx * c * (3.0 * h / 8.0) for fx, c in zip(fxs, coefs)]
    total = sum(contribs)
    points = _points_to_payload(range(len(xs)), xs, fxs, coefs, contribs)
    return {"value": float(total), "h": h, "evals": len(xs), "points": points}

def run_boole(f: Callable[[float], float], a: float, b: float, n: int) -> Dict:
    """Regla de Boole compuesta: n múltiplo de 4 (se ajusta)."""
    if n < 4:
        n = 4
    if n % 4 != 0:
        n = ((n // 4) + 1) * 4
    xs = linspace(a, b, n)
    h = (b - a) / n
    fxs = [safe_f(f, x) for x in xs]

    coefs = []
    for i in range(len(xs)):
        if i == 0 or i == n:
            coefs.append(7.0)
        elif i % 4 == 0:
            coefs.append(14.0)
        elif i % 2 == 0:
            coefs.append(12.0)
        else:
            coefs.append(32.0)

    contribs = [fx * c * (2.0 * h / 45.0) for fx, c in zip(fxs, coefs)]
    total = sum(contribs)
    points = _points_to_payload(range(len(xs)), xs, fxs, coefs, contribs)
    return {"value": float(total), "h": h, "evals": len(xs), "points": points}

# ---------- Método adaptativo (Simpson recursivo) ----------

def _simpson_panel(f, a, b, fa, fm, fb) -> float:
    return (b - a) * (fa + 4.0 * fm + fb) / 6.0

def _adaptive_recursive(f, a, b, fa, fm, fb, S, tol, depth, evals) -> Tuple[float, float, int]:
    c = (a + b) / 2.0
    fd = safe_f(f, (a + c) / 2.0); evals += 1
    fe = safe_f(f, (c + b) / 2.0); evals += 1

    S_left = _simpson_panel(f, a, c, fa, fd, fm)
    S_right = _simpson_panel(f, c, b, fm, fe, fb)

    if abs(S_left + S_right - S) <= 15.0 * tol:
        err = (S_left + S_right - S) / 15.0
        return S_left + S_right + err, err, evals

    left_val, left_err, evals = _adaptive_recursive(
        f, a, c, fa, fd, fm, S_left, tol / 2.0, depth + 1, evals
    )
    right_val, right_err, evals = _adaptive_recursive(
        f, c, b, fm, fe, fb, S_right, tol / 2.0, depth + 1, evals
    )
    return left_val + right_val, max(abs(left_err), abs(right_err)), evals

def run_adaptativo(f: Callable[[float], float], a: float, b: float, tol: float) -> Dict:
    fa = safe_f(f, a)
    fm = safe_f(f, (a + b) / 2.0)
    fb = safe_f(f, b)
    evals = 3

    S = _simpson_panel(f, a, b, fa, fm, fb)
    value, err_est, evals = _adaptive_recursive(f, a, b, fa, fm, fb, S, tol, 0, evals)

    # Para tener una tabla mínima con el panel base
    points = _points_to_payload(
        [0, 1, 2],
        [a, (a + b) / 2.0, b],
        [fa, fm, fb],
        [1.0, 4.0, 1.0],
        [_simpson_panel(f, a, b, fa, fm, fb)]
    )

    return {
        "value": float(value),
        "h": None,
        "evals": int(evals),
        "error_estimate": abs(err_est),
        "points": points,
    }
