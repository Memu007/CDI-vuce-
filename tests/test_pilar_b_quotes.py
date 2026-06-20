import pytest
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select

from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import Operation, OperationItem, PublicQuote

# Manual mount of quote_router for TestClient
from proyecto_maria.main import app
has_quote = any(getattr(route, "path", "").startswith("/api/quotes") for route in app.routes)
if not has_quote:
    from proyecto_maria.routers import quote_router
    app.include_router(quote_router.router)

@pytest.fixture
async def test_operation(auth_override):
    op_id = f"test_op_{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as session:
        op = Operation(
            id=op_id,
            owner_username=auth_override["username"],
            op_code="QUOTE-1",
            client_id="test_client"
        )
        item = OperationItem(
            id=f"item_{uuid.uuid4().hex[:8]}",
            operation_id=op_id,
            pieza="8517.12.31",
            descripcion="Smartphone",
            origen="CN",
            cantidad=100,
            valor_unitario=150.0,
            peso_unitario=0.2
        )
        session.add(op)
        session.add(item)
        await session.commit()
    return op_id

@pytest.fixture
async def other_operation():
    op_id = f"test_op_other_{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as session:
        op = Operation(
            id=op_id,
            owner_username="another_user",
            op_code="QUOTE-2",
            client_id="test_client"
        )
        session.add(op)
        await session.commit()
    return op_id

def test_share_quote_unauth(client):
    from fastapi import HTTPException
    from proyecto_maria.main import app
    from proyecto_maria.auth.dependencies import get_current_user
    
    def override_auth():
        raise HTTPException(status_code=401, detail="No autenticado")
        
    app.dependency_overrides[get_current_user] = override_auth
    try:
        res = client.post("/api/quotes/share", json={"operation_id": "any"})
        assert res.status_code == 401
    finally:
        app.dependency_overrides.pop(get_current_user, None)

def test_share_quote_valid(client, auth_override, test_operation):
    res = client.post("/api/quotes/share", json={"operation_id": test_operation})
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert "expires_at" in data
    assert "share_url" in data

def test_share_quote_invalid_operation(client, auth_override, other_operation):
    res = client.post("/api/quotes/share", json={"operation_id": other_operation})
    assert res.status_code == 404

def test_share_quote_missing_operation_id(client, auth_override):
    res = client.post("/api/quotes/share", json={})
    assert res.status_code == 400

def test_get_public_quote_valid(client, auth_override, test_operation):
    res_share = client.post("/api/quotes/share", json={"operation_id": test_operation})
    token = res_share.json()["token"]
    
    res = client.get(f"/api/quotes/public/{token}")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data["snapshot"]
    items = data["snapshot"]["items"]
    assert len(items) > 0
    assert "alicuotas" in items[0]
    assert "costo_total" in items[0]

def test_get_public_quote_not_found(client):
    res = client.get("/api/quotes/public/nonexistent")
    assert res.status_code == 404

@pytest.mark.asyncio
async def test_get_public_quote_expired(client, auth_override, test_operation):
    res_share = client.post("/api/quotes/share", json={"operation_id": test_operation})
    token = res_share.json()["token"]
    
    async with AsyncSessionLocal() as session:
        quote_query = await session.execute(select(PublicQuote).where(PublicQuote.token_id == token))
        quote = quote_query.scalars().first()
        quote.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        await session.commit()
    
    res = client.get(f"/api/quotes/public/{token}")
    assert res.status_code == 410
    
    async with AsyncSessionLocal() as session:
        quote_query = await session.execute(select(PublicQuote).where(PublicQuote.token_id == token))
        assert quote_query.scalars().first() is None

def test_get_public_quote_rate_limit(client, auth_override, test_operation, monkeypatch):
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = True
    
    res_share = client.post("/api/quotes/share", json={"operation_id": test_operation})
    token = res_share.json()["token"]
    
    # Send 11 requests
    # Limit is 10/minute
    for i in range(10):
        res = client.get(f"/api/quotes/public/{token}")
        assert res.status_code in (200, 429)
        
    res = client.get(f"/api/quotes/public/{token}")
    assert res.status_code == 429
    
    limiter.enabled = False

@pytest.fixture
async def multi_item_operation(auth_override):
    op_id = f"test_op_{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as session:
        op = Operation(
            id=op_id,
            owner_username=auth_override["username"],
            op_code="QUOTE-MULTI",
            client_id="test_client"
        )
        item1 = OperationItem(
            id=f"item_1_{uuid.uuid4().hex[:8]}",
            operation_id=op_id,
            pieza="8517.12.31",
            descripcion="Smartphone",
            origen="CN",
            cantidad=100,
            valor_unitario=150.0,
            peso_unitario=0.2
        )
        item2 = OperationItem(
            id=f"item_2_{uuid.uuid4().hex[:8]}",
            operation_id=op_id,
            pieza="9999.00.00",
            descripcion="Otro",
            origen="CN",
            cantidad=10,
            valor_unitario=50.0,
            peso_unitario=1.0
        )
        session.add_all([op, item1, item2])
        await session.commit()
    return op_id

def test_share_quote_tarifar_returns_reordered_items(client, auth_override, multi_item_operation, monkeypatch):
    import proyecto_maria.routers.quote_router as qr
    
    def mock_calcular_aranceles(items, tc_usd):
        # Devuelve alícuotas en orden inverso (9999.00.00 primero, 8517.12.31 segundo)
        # Identificando por 'ncm' como lo hace el backend de VUCE
        return {"items": [
            {
                "item": {"ncm": "9999.00.00"},
                "calculo": {
                    "simulacion_id": "sim_9999",
                    "alicuotas": {"die": 0.0, "te": 0.0},
                    "total_usd": 500.0
                }
            },
            {
                "item": {"ncm": "8517.12.31"},
                "calculo": {
                    "simulacion_id": "sim_8517",
                    "alicuotas": {"die": 0.16, "te": 0.03},
                    "total_usd": 15000.0
                }
            }
        ]}
        
    monkeypatch.setattr(qr.TARIFAR_CLIENT, "calcular_aranceles", mock_calcular_aranceles)
    
    res = client.post("/api/quotes/share", json={"operation_id": multi_item_operation})
    assert res.status_code == 200
    token = res.json()["token"]
    
    # Check public quote correctly assigned alicuotas by NCM, not position
    res_pub = client.get(f"/api/quotes/public/{token}")
    assert res_pub.status_code == 200
    items = res_pub.json()["snapshot"]["items"]
    
    # Buscar el item de Smartphone (8517.12.31) y el Otro (9999.00.00)
    item_8517 = next(i for i in items if i["pieza"] == "8517.12.31")
    item_9999 = next(i for i in items if i["pieza"] == "9999.00.00")
    
    assert item_8517["alicuotas"]["die"] == 0.16
    assert item_9999["alicuotas"]["die"] == 0.0

def test_share_quote_tarifar_fails_returns_503(client, auth_override, test_operation, monkeypatch):
    import proyecto_maria.routers.quote_router as qr
    
    def mock_calcular_aranceles_error(items, tc_usd):
        raise Exception("timeout de tarifar")
        
    monkeypatch.setattr(qr.TARIFAR_CLIENT, "calcular_aranceles", mock_calcular_aranceles_error)
    
    res = client.post("/api/quotes/share", json={"operation_id": test_operation})
    assert res.status_code == 503
    assert res.json()["detail"] == "fuente_arancelaria_no_disponible"
