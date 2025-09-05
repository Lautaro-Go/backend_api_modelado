import sympy as sp

class LHopitalAnalyzer:
    def __init__(self, expr: str):
        self.expr_str = expr
        self.x = sp.Symbol("x")
        try:
            self.expr = sp.sympify(expr.replace("^", "**"))
        except Exception:
            self.expr = None

    def find_critical_points(self, a: float, b: float):
        """
        Busca candidatos a singularidades en [a,b].
        Ejemplo: denominador que se anula.
        """
        if self.expr is None:
            return []
        denom = sp.denom(self.expr)
        roots = sp.solve(sp.Eq(denom, 0), self.x)
        crits = []
        for r in roots:
            try:
                val = float(r.evalf())
                if a <= val <= b:
                    crits.append(val)
            except Exception:
                continue
        return crits

    def apply_lhopital(self, x0: float):
        """
        Aplica L'Hôpital para evaluar el límite de expr en x0.
        """
        if self.expr is None:
            return None
        limit_val = sp.limit(self.expr, self.x, x0)
        try:
            return float(limit_val.evalf())
        except Exception:
            return None
