import math
import re
from .lhopital import LHopitalAnalyzer

def make_safe_function(expr: str, lhopital_points: dict = None):
    """
    Convierte un string como 'sin(x)/x' en una función segura de Python f(x).
    Aplica reemplazo de ^ -> ** y funciones de math.
    Si lhopital_points se pasa, en esos x devuelve directamente el valor del límite.
    """
    expr = expr.replace("^", "**")

    allowed_names = {k: getattr(math, k) for k in dir(math) if not k.startswith("__")}
    allowed_names.update({"abs": abs, "pow": pow, "pi": math.pi, "e": math.e})

    code = compile(expr, "<string>", "eval")

    def f(x: float) -> float:
        if lhopital_points and x in lhopital_points:
            return lhopital_points[x]
        return eval(code, {"__builtins__": {}}, {**allowed_names, "x": x})

    return f

def check_for_singularities(expr: str, a: float, b: float):
    """
    Revisa si hay puntos singulares tipo 0/0 en [a,b].
    Usa LHopitalAnalyzer para calcular límites removibles.
    Devuelve (has_singularity, [(xcrit, limit)], message)
    """
    analyzer = LHopitalAnalyzer(expr)
    critical_points = analyzer.find_critical_points(a, b)

    if not critical_points:
        return False, [], "No se encontraron singularidades."

    lhopital_values = []
    for xcrit in critical_points:
        limit_val = analyzer.apply_lhopital(xcrit)
        if limit_val is not None and math.isfinite(limit_val):
            lhopital_values.append((xcrit, limit_val))

    if lhopital_values:
        return True, lhopital_values, "Se aplicó L'Hôpital en puntos críticos."
    else:
        return True, [], "Hay singularidades no removibles."
