
import pytest
import asyncio
from httpx import AsyncClient
from proyecto_maria.main import app, pwd_context, hash_password, verify_password
from proyecto_maria.database.connection import get_async_session, init_db
from proyecto_maria.database.models import User, PasswordResetToken
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_password_recovery_flow():
    # 0. Initialize DB (tables)
    await init_db()

    # 1. Setup: Create a test user
    async for session in get_async_session():
        # Cleanup
        from sqlalchemy import delete
        await session.execute(delete(User).where(User.username == "recovery_test_user"))
        await session.execute(delete(PasswordResetToken).where(PasswordResetToken.user_username == "recovery_test_user"))
        await session.commit()
        
        user = User(
            username="recovery_test_user",
            email="recovery@test.com",
            password=hash_password("oldpassword"),
            name="Test User"
        )
        session.add(user)
        await session.commit()
        break # Only need one session

    async with AsyncClient(transport=None, app=app, base_url="http://test") as ac: # transport=None handles ASGI
        # 2. Request Password Reset
        response = await ac.post("/auth/request-password-reset", json={"email": "recovery@test.com"})
        
        # Debug output
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            
        assert response.status_code == 200
        data = response.json()
        assert "Si el email existe" in data["message"]
        
        # In dev mode, we might get the token hint if SMTP fails
        token = data.get("dev_token_hint")
        
        # If token not in response (SMTP working?), fetch from DB
        if not token:
            async for session in get_async_session():
                result = await session.execute(select(PasswordResetToken).where(PasswordResetToken.user_username == "recovery_test_user"))
                reset_token = result.scalars().first()
                if reset_token:
                    token = reset_token.token
                    break # Only need one session

        assert token is not None, "Token could not be retrieved from DB or response"

        # 3. Reset Password
        new_password = "newsecurepassword123"
        response = await ac.post("/auth/reset-password", json={
            "token": token,
            "new_password": new_password
        })
        
        if response.status_code != 200:
            print(f"Reset error: {response.text}")

        assert response.status_code == 200
        assert response.json()["message"] == "Contraseña actualizada exitosamente"

        # 4. Verify new password login (simulated)
        async for session in get_async_session():
            result = await session.execute(select(User).where(User.username == "recovery_test_user"))
            updated_user = result.scalars().first()
            assert verify_password(new_password, updated_user.password)
            assert not verify_password("oldpassword", updated_user.password)

            # Cleanup
            # await session.delete(updated_user)
            # await session.commit()
            break
