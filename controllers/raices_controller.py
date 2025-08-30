from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal, List, Tuple
from services.newton_service import run_newton
from services.punto_fijo_service import run_punto_fijo
from services.aitken_service import run_aitken
from utils.safe_eval import make_safe_func

router = APIRouter()

# --------- Modelos ----------
class MetodoRequest(BaseModel):
    metodo: Literal["newton", "punto_fijo", "aitken"]
    fx: Optional[str] = None
    gx: Optional[str] = None
    dfx: Optional[str] = None
    x0: float
    tol: float = 1e-8
    max_iter: int = 50

class Iteracion(BaseModel):
    n: int
    x: float
    # Newton:
    fx: Optional[float] = None
    dfx: Optional[float] = None
    x_next: Optional[float] = None  # x_{n+1}
    # Aitken:
    x1: Optional[float] = None       # x_{n+1}
    x2: Optional[float] = None       # x_{n+2}
    x_acc: Optional[float] = None    # x* (acelerado)
    # Errores:
    err_abs: float
    err_rel: float

class MetodoResponse(BaseModel):
    metodo: Literal["newton", "punto_fijo", "aitken"]
    resultado: Optional[float]
    convergio: bool
    iteraciones: List[Iteracion]
    # Histórico discreto para compatibilidad (lo dejamos):
    grafico: List[Tuple[float, float]]
    grafico_g: Optional[List[Tuple[float, float]]] = None
    # Curvas densas:
    curva_f: Optional[List[Tuple[float, float]]] = None
    curva_g: Optional[List[Tuple[float, float]]] = None
    # Puntos de iteración (x, y):
    iter_points: Optional[List[Tuple[float, float]]] = None

# --------- Helpers ----------
def _plot_range_from_one(xs: List[float]) -> Tuple[float, float]:
    if not xs:
        return (-5.0, 5.0)
    return (min(xs) - 1.0, max(xs) + 1.0)

def _plot_range_from_two(xs: List[float], ys: List[float]) -> Tuple[float, float]:
    pool = [v for v in xs if isinstance(v, (int, float))] + [v for v in ys if isinstance(v, (int, float))]
    if not pool:
        return (-5.0, 5.0)
    return (min(pool) - 1.0, max(pool) + 1.0)

def _sample_curve(func, x_min: float, x_max: float, n: int = 401) -> List[Tuple[float, float]]:
    if x_max < x_min:
        x_min, x_max = x_max, x_min
    if n < 2:
        n = 2
    step = (x_max - x_min) / (n - 1)
    xs, ys = [], []
    for i in range(n):
        x = x_min + i * step
        try:
            y = func(x)
        except Exception:
            y = None
        xs.append(x); ys.append(y)
    return list(zip(xs, ys))

# --------- Endpoint ----------
@router.post("/resolver", response_model=MetodoResponse)
def resolver_metodo(req: MetodoRequest):
    try:
        curva_f = curva_g = None
        grafico_g = None
        iter_points = None

        if req.metodo == "newton":
            if not req.fx:
                raise HTTPException(status_code=400, detail="f(x) es requerido para Newton")
            f = make_safe_func(req.fx)
            df = make_safe_func(req.dfx) if req.dfx else None

            resultado, hist = run_newton(f, req.x0, df, req.tol, req.max_iter)

            # Iteraciones: agregamos x_{n+1} explícito
            iteraciones: List[Iteracion] = []
            xs_hist: List[float] = []
            for h in hist:
                n, x, fx, dfx, err_abs, err_rel = h
                xs_hist.append(x)
                # x_{n+1} = x - f(x)/f'(x) (cuando dfx ≠ 0)
                x_next = None
                try:
                    if dfx is not None and abs(dfx) > 0:
                        x_next = x - fx / dfx
                except Exception:
                    x_next = None
                iteraciones.append(Iteracion(
                    n=n, x=x, fx=fx, dfx=dfx, x_next=x_next,
                    err_abs=err_abs, err_rel=err_rel
                ))

            # Rango como el original (solo xs, ±1)
            x_min, x_max = _plot_range_from_one(xs_hist)
            curva_f = _sample_curve(f, x_min, x_max)

            # Puntos de iteración y “grafico” con f(x)
            iter_points = [(x, f(x)) for x in xs_hist]
            grafico = iter_points[:]

            # Si hay g(x), damos curva_g también
            if req.gx:
                g = make_safe_func(req.gx)
                curva_g = _sample_curve(g, x_min, x_max)

        elif req.metodo == "punto_fijo":
            if not req.gx:
                raise HTTPException(status_code=400, detail="g(x) es requerido para Punto Fijo")
            g = make_safe_func(req.gx)
            resultado, hist = run_punto_fijo(g, req.x0, req.tol, req.max_iter)

            xs = [h[1] for h in hist]
            xs_next = [h[2] for h in hist]
            x_min, x_max = _plot_range_from_two(xs, xs_next)

            # Iteraciones (ya traen x_next)
            iteraciones = [
                Iteracion(n=h[0], x=h[1], x_next=h[2], err_abs=h[3], err_rel=h[4])
                for h in hist
            ]

            # Curvas
            curva_g = _sample_curve(g, x_min, x_max)

            grafico_g = [(x, g(x)) for x in xs]  # histórico g(x) en x_n

            grafico = None
            iter_points = None

            # Si hay f(x), preferimos graficar f también (como en el original)
            if req.fx:
                f = make_safe_func(req.fx)
                curva_f = _sample_curve(f, x_min, x_max)
                grafico = [(x, f(x)) for x in xs]
                iter_points = [(x, f(x)) for x in xs]
            else:
                grafico = [(x, g(x)) for x in xs]
                iter_points = [(x, g(x)) for x in xs]

        elif req.metodo == "aitken":
            if not req.gx:
                raise HTTPException(status_code=400, detail="g(x) es requerido para Aitken")
            g = make_safe_func(req.gx)
            resultado, hist = run_aitken(g, req.x0, req.tol, req.max_iter)
            # Nuestro service guarda: (n, x, x_acc, err_abs, err_rel)
            # Para mostrar columnas como el original, calculamos x1=g(x) y x2=g(x1).
            iteraciones: List[Iteracion] = []
            xs = []
            xs_acc = []
            for (n, x, x_acc, err_abs, err_rel) in hist:
                xs.append(x); xs_acc.append(x_acc)
                try:
                    x1 = g(x)
                except Exception:
                    x1 = None
                try:
                    x2 = g(x1) if x1 is not None else None
                except Exception:
                    x2 = None
                iteraciones.append(Iteracion(
                    n=n, x=x, x1=x1, x2=x2, x_acc=x_acc,
                    err_abs=err_abs, err_rel=err_rel
                ))

            x_min, x_max = _plot_range_from_two(xs, xs_acc)

            # Curvas
            curva_g = _sample_curve(g, x_min, x_max)
            grafico_g = [(x, g(x)) for x in xs]

            grafico = None
            iter_points = None
            if req.fx:
                f = make_safe_func(req.fx)
                curva_f = _sample_curve(f, x_min, x_max)
                grafico = [(x, f(x)) for x in xs]
                iter_points = [(x, f(x)) for x in xs]
            else:
                grafico = [(x, g(x)) for x in xs]
                iter_points = [(x, g(x)) for x in xs]

        else:
            raise HTTPException(status_code=400, detail="Método no reconocido")

        return MetodoResponse(
            metodo=req.metodo,
            resultado=resultado,
            convergio=resultado is not None,
            iteraciones=iteraciones,
            grafico=grafico,
            grafico_g=grafico_g,
            curva_f=curva_f,
            curva_g=curva_g,
            iter_points=iter_points
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
