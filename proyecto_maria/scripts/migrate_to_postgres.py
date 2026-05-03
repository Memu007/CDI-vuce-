import sys
import os
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from proyecto_maria.database.connection import engine, Base, get_async_session
from proyecto_maria.database.models import User, Client

USERS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "users.json")
CLIENTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "clients.json")

async def init_db():
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tablas creadas (si no existían)")

async def migrate_users(session: AsyncSession):
    if not os.path.exists(USERS_FILE):
        print("⚠️ No se encontró users.json")
        return

    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users_data = json.load(f)

    print(f"🔄 Migrando {len(users_data)} usuarios...")
    
    for username, data in users_data.items():
        # Check if user exists
        result = await session.execute(select(User).where(User.username == username))
        existing_user = result.scalars().first()
        
        if existing_user:
            print(f"  - Usuario {username} ya existe. Saltando.")
            continue
            
        new_user = User(
            username=username,
            password=data.get("password"),
            name=data.get("name"),
            plan=data.get("plan", "basic"),
            email=data.get("email"),
            is_verified=data.get("is_verified", False),
            roles=data.get("roles", [])
        )
        session.add(new_user)
    
    await session.commit()
    print("✅ Usuarios migrados.")

async def migrate_clients(session: AsyncSession):
    if not os.path.exists(CLIENTS_FILE):
        print("⚠️ No se encontró clients.json")
        return

    with open(CLIENTS_FILE, 'r', encoding='utf-8') as f:
        clients_data = json.load(f)

    print(f"🔄 Migrando {len(clients_data)} clientes...")
    
    for client_data in clients_data:
        client_id = client_data.get("id")
        if not client_id:
            continue
            
        # Check if client exists
        result = await session.execute(select(Client).where(Client.id == client_id))
        existing_client = result.scalars().first()
        
        if existing_client:
            print(f"  - Cliente {client_id} ya existe. Saltando.")
            continue
        
        new_client = Client(
            id=client_id,
            name=client_data.get("name", "Sin Nombre"),
            email=client_data.get("email", f"client_{client_id}@example.com"), # Fallback email
            phone=client_data.get("phone"),
            cuit=client_data.get("cuit"),
            address=client_data.get("address"),
            default_origin=client_data.get("default_origin", "CN"),
            preferred_currency=client_data.get("preferred_currency", "USD"),
            auto_ncm_enabled=client_data.get("auto_ncm_enabled", True)
        )
        session.add(new_client)
        
    await session.commit()
    print("✅ Clientes migrados.")

async def main():
    await init_db()
    
    async with AsyncSession(engine) as session:
        await migrate_users(session)
        await migrate_clients(session)

if __name__ == "__main__":
    asyncio.run(main())
