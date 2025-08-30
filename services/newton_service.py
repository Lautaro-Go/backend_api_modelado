from utils.derivative import numerical_derivative

def run_newton(f, x0, df=None, tol=1e-8, max_iter=50):
    history = []
    x = x0
    for n in range(max_iter):
        fx = f(x)
        dfx = df(x) if df else numerical_derivative(f, x)
        if abs(dfx) < 1e-14:
            raise RuntimeError("Derivada cerca de cero; Newton puede fallar")
        x_next = x - fx / dfx
        abs_err = abs(x_next - x)
        rel_err = abs_err / abs(x_next) if x_next != 0 else float('inf')
        history.append((n, x, fx, dfx, abs_err, rel_err))
        if abs_err < tol:
            history.append((n + 1, x_next, f(x_next),
                            df(x_next) if df else numerical_derivative(f, x_next), 0.0, 0.0))
            return x_next, history
        x = x_next
    return None, history