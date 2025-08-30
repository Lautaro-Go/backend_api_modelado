# backend_api_modelado

Numerical Methods Backend (FastAPI + Python)

This project is a backend service built with FastAPI to compute numerical methods for root-finding. It exposes a REST API that processes mathematical expressions sent from a frontend (React) and returns iteration history, convergence results, and curve data ready for visualization.

✨ Features

Implements classical root-finding methods:

Newton–Raphson

Fixed Point Iteration

Aitken’s Δ² acceleration

Safe evaluation of user-defined functions (f(x), g(x), f’(x)).

Automatic numerical derivative when no analytic derivative is provided.

Iteration history with errors and approximations.

Curve sampling to plot f(x) and g(x) with iteration points.

CORS enabled to connect with a React frontend.

🛠️ Tech Stack

Python 3.11+

FastAPI + Uvicorn

Pydantic for data validation

Math/AST-based safe expression parser

🚀 Usage

Install dependencies:
