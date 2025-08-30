import ast
import math

def make_safe_func(expr: str):
    # Reemplaza ^ por ** para que funcione como potencia en Python
    expr = expr.replace('^', '**')

    allowed_names = {k: getattr(math, k) for k in dir(math) if not k.startswith("__")}
    allowed_names.update({"abs": abs, "pow": pow})

    expr_ast = ast.parse(expr, mode='eval')

    for node in ast.walk(expr_ast):
        if isinstance(node, ast.Name):
            if node.id != 'x' and node.id not in allowed_names:
                raise ValueError(f"Nombre no permitido en expresión: {node.id}")
        elif isinstance(node, (
            ast.Call, ast.BinOp, ast.UnaryOp, ast.Expression,
            ast.Load, ast.Add, ast.Sub, ast.Mult, ast.Div,
            ast.Pow, ast.USub, ast.UAdd, ast.Mod, ast.Constant,
            ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.Gt,
            ast.LtE, ast.GtE, ast.And, ast.Or, ast.BoolOp
        )):
            continue
        else:
            raise ValueError(f"Nodo AST no permitido: {type(node).__name__}")

    code = compile(expr_ast, '<string>', 'eval')

    def f(x: float) -> float:
        return eval(code, {'__builtins__': {}}, {**allowed_names, 'x': x})

    return f