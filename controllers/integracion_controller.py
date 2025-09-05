from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Tuple

# Usa tus utilidades del código original (L'Hôpital + parser seguro)
# Ajustá el import si tu estructura de carpetas difiere.
from utils.expressions import make_safe_function, check_for_singularities

# Servicios con los métodos y helpers de muestreo
from services.integracion_service import (
    run_rectangulo,
    run_trapezoidal,
    run_simpson_13,
    run_simpson_38,
    run_boole,
    run_adaptativo,
    sample_curve,
)

router = APIRouter()

# ---------- Modelos de E/S ----------

MetodoIntegracion = Literal[
    "rectangulo",
    "trapezoidal",
    "simpson_13",
    "simpson_38",
    "boole",
    "adaptativo",
]

class PuntoTabla(BaseModel):
    index: int
    x: float
    fx: float
    coefficient: float
    contribution: float

class IntegracionRequest(BaseModel):
    metodo: MetodoIntegracion
    fx: str = Field(..., description="Función f(x) a integrar. Ej: 'sin(x)/x'")
    a: float
    b: float
    n: Optional[int] = Field(10, ge=1, description="Subdivisiones para métodos compuestos")
    tol: Optional[float] = Field(1e-6, gt=0, description="Tolerancia para método adaptativo")

class IntegracionResponse(BaseModel):
    metodo: MetodoIntegracion
    value: float
    step_size: Optional[float] = None
    function_evaluations: int
    error_estimate: Optional[float] = None
    points: List[PuntoTabla]
    curva_f: List[Tuple[float, Optional[float]]]  # (x, f(x))

# ---------- Endpoint ----------

@router.post("/integracion/resolver", response_model=IntegracionResponse)
def resolver_integracion(req: IntegracionRequest):
    try:
        a = float(req.a)
        b = float(req.b)
        if a == b:
            raise HTTPException(status_code=400, detail="a y b no pueden ser iguales")

        # Normalizamos la expresión a sintaxis Python
        expr = (req.fx or "").replace("^", "**").strip()
        if not expr:
            raise HTTPException(status_code=400, detail="fx es requerido")

        # 1) Detectar singularidades con tu analizador (L'Hôpital)
        #    Esto devuelve una lista de (x_critico, valor_limite)
        _has_sing, critical_list, _msg = check_for_singularities(expr, a, b)

        # 2) Construir f(x) respetando esos puntos críticos (evalúa el límite en esos x)
        lhopital_points = {float(xc): float(val) for (xc, val) in critical_list}
        f = make_safe_function(expr, lhopital_points=lhopital_points)

        # 3) Ejecutar el método
        metodo = req.metodo
        n = int(req.n or 10)

        if metodo == "rectangulo":
            res = run_rectangulo(f, a, b, n)
        elif metodo == "trapezoidal":
            res = run_trapezoidal(f, a, b, n)
        elif metodo == "simpson_13":
            res = run_simpson_13(f, a, b, n)  # ajusta par internamente
        elif metodo == "simpson_38":
            res = run_simpson_38(f, a, b, n)  # ajusta múltiplo de 3 internamente
        elif metodo == "boole":
            res = run_boole(f, a, b, n)       # ajusta múltiplo de 4 internamente
        elif metodo == "adaptativo":
            tol = float(req.tol or 1e-6)
            res = run_adaptativo(f, a, b, tol)
        else:
            raise HTTPException(status_code=400, detail="Método no reconocido")

        # Curva para graficar en el front
        curva_f = sample_curve(f, a, b)

        return IntegracionResponse(
            metodo=metodo,
            value=res["value"],
            step_size=res.get("h"),
            function_evaluations=res.get("evals", 0),
            error_estimate=res.get("error_estimate"),
            points=res["points"],
            curva_f=curva_f,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
