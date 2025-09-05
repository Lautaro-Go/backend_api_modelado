from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.raices_controller import router
from controllers.integracion_controller import router as integracion_router

app = FastAPI()

# Habilitar CORS para permitir llamadas desde tu frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # ajustá según tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas con prefijo /api
app.include_router(router, prefix="/api")
app.include_router(integracion_router, prefix="/api")  # queda /api/integracion/resolver