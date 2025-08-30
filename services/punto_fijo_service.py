def run_punto_fijo(g, x0, tol=1e-8, max_iter=50):
    history = []
    x = x0
    for n in range(max_iter):
        x_next = g(x)
        abs_err = abs(x_next - x)
        rel_err = abs_err / abs(x_next) if x_next != 0 else float('inf')
        history.append((n, x, x_next, abs_err, rel_err))
        if abs_err < tol:
            history.append((n + 1, x_next, g(x_next), 0.0, 0.0))
            return x_next, history
        x = x_next
    return None, history