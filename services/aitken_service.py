def run_aitken(g, x0, tol=1e-8, max_iter=50):
    history = []
    x = x0
    for n in range(max_iter):
        x1 = g(x)
        x2 = g(x1)
        denom = x2 - 2 * x1 + x
        x_acc = x2 - (x2 - x1) ** 2 / denom if denom != 0 else x2
        abs_err = abs(x_acc - x)
        rel_err = abs_err / abs(x_acc) if x_acc != 0 else float('inf')
        history.append((n, x, x_acc, abs_err, rel_err))
        if abs_err < tol:
            return x_acc, history
        x = x_acc
    return None, history