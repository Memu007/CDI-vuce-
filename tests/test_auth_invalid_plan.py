import pytest
import asyncio
from fastapi import Request, Response
from proyecto_maria.auth.dependencies import get_current_user
from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import User
from proyecto_maria.auth.jwt_utils import create_access_token

class MockRequest:
    def __init__(self, token):
        self.cookies = {}
        self.headers = {"Authorization": f"Bearer {token}"}

class MockResponse:
    pass

def test_get_current_user_with_invalid_plan_falls_back_to_premium():
    async def run_test():
        async with AsyncSessionLocal() as session:
            await session.execute(User.__table__.delete().where(User.username.in_(["invalid_plan_user", "none_plan_user"])))
            invalid_user = User(username="invalid_plan_user", password="123", email="inv@test.com", plan="plan_inv_123")
            none_user = User(username="none_plan_user", password="123", email="none@test.com", plan=None)
            session.add_all([invalid_user, none_user])
            await session.commit()
            
        token = create_access_token({"sub": "invalid_plan_user"})
        request = MockRequest(token)
        response = MockResponse()
        
        async with AsyncSessionLocal() as db:
            user_data = await get_current_user(request=request, response=response, db=db)
            
        assert user_data["plan"] == "premium"
        
        token = create_access_token({"sub": "none_plan_user"})
        request = MockRequest(token)
        
        async with AsyncSessionLocal() as db:
            user_data = await get_current_user(request=request, response=response, db=db)
            
        assert user_data["plan"] == "premium"
        
        # cleanup
        async with AsyncSessionLocal() as session:
            await session.execute(User.__table__.delete().where(User.username.in_(["invalid_plan_user", "none_plan_user"])))
            await session.commit()
            
    asyncio.run(run_test())
