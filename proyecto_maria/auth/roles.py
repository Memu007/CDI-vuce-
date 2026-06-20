from typing import Annotated

from fastapi import Depends, HTTPException, status

from proyecto_maria.auth.dependencies import get_current_user


def require_role(role: str):
    async def checker(user: Annotated[dict, Depends(get_current_user)]):
        roles = user.get("roles", [])
        if role not in roles and "admin" not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
        return user

    return checker
