from typing import Annotated

from fastapi import Depends, HTTPException, status

from proyecto_maria.auth.dependencies import get_current_user


def roles_de(user) -> list:
    """La columna JSON puede guardar un texto: vale como un único rol entero
    («administrador» no es «admin»); lo que no sea texto ni lista no da roles."""
    roles = user.get("roles")
    if isinstance(roles, str):
        return [roles]
    if isinstance(roles, (list, tuple, set)):
        return list(roles)
    return []


def require_role(role: str):
    async def checker(user: Annotated[dict, Depends(get_current_user)]):
        roles = roles_de(user)
        if role not in roles and "admin" not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
        return user

    return checker
