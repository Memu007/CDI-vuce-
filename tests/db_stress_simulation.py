"""
Database Stress Test: 1 Year Simulation
========================================
Simulates 3 clients with 4-6 invoices/month for 12 months.
Each invoice has 8-12 items.

Run: python tests/db_stress_simulation.py
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from typing import List
import time

# Ensure we can import proyecto_maria modules
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from proyecto_maria.database.connection import get_async_session, init_db
from proyecto_maria.database.models import Client, Operation, OperationItem

# ==============================================================================
# Configuration
# ==============================================================================
NUM_CLIENTS = 3
MONTHS_TO_SIMULATE = 12
MIN_INVOICES_PER_MONTH = 4
MAX_INVOICES_PER_MONTH = 6
MIN_ITEMS_PER_INVOICE = 8
MAX_ITEMS_PER_INVOICE = 12

# Sample data for realistic simulation
SAMPLE_CLIENTS = [
    {"name": "Importadora China Express S.A.", "email": "admin@chinaexpress.com.ar", "cuit": "30-12345678-9"},
    {"name": "TechGadgets Argentina", "email": "compras@techgadgets.com.ar", "cuit": "30-98765432-1"},
    {"name": "Comercial del Sur Ltda.", "email": "operaciones@delsur.com.ar", "cuit": "30-55667788-0"},
]

SAMPLE_PRODUCTS = [
    ("8471.30.19", "Notebook Intel Core i5 8GB RAM"),
    ("8517.12.99", "Teléfono celular smartphone 6.5 pulgadas"),
    ("8528.72.00", "Monitor LED 27 pulgadas"),
    ("8443.32.99", "Impresora multifunción laser"),
    ("9503.00.99", "Juguete plástico infantil"),
    ("6402.99.90", "Calzado deportivo sintético"),
    ("6110.20.00", "Suéter de algodón"),
    ("8518.30.00", "Auriculares bluetooth"),
    ("8504.40.90", "Cargador USB-C 65W"),
    ("9405.11.00", "Lámpara LED escritorio"),
    ("8523.51.10", "Memoria USB 128GB"),
    ("8471.70.90", "Disco SSD 1TB NVMe"),
    ("3926.90.90", "Funda protectora plástico"),
    ("4202.12.10", "Mochila porta notebook"),
    ("8544.42.00", "Cable HDMI 2 metros"),
]

ORIGINS = ["CN", "TW", "KR", "JP", "US", "DE", "IT"]

# ==============================================================================
# Simulation Logic
# ==============================================================================

async def create_test_clients(session) -> List[str]:
    """Create 3 test clients and return their IDs."""
    client_ids = []
    
    for client_data in SAMPLE_CLIENTS:
        # Check if client already exists
        result = await session.execute(
            select(Client).where(Client.email == client_data["email"])
        )
        existing = result.scalars().first()
        
        if existing:
            client_ids.append(existing.id)
            print(f"  ♻️  Client exists: {client_data['name']}")
        else:
            client = Client(
                id=str(uuid.uuid4()),
                name=client_data["name"],
                email=client_data["email"],
                cuit=client_data["cuit"],
                is_active=True,
            )
            session.add(client)
            client_ids.append(client.id)
            print(f"  ✅ Created: {client_data['name']}")
    
    await session.commit()
    return client_ids

async def generate_monthly_operations(session, client_id: str, year: int, month: int):
    """Generate 4-6 operations for a given month."""
    num_invoices = random.randint(MIN_INVOICES_PER_MONTH, MAX_INVOICES_PER_MONTH)
    
    for invoice_num in range(num_invoices):
        # Random day within the month
        day = random.randint(1, 28)
        op_date = datetime(year, month, day, random.randint(8, 18), random.randint(0, 59))
        
        # Create operation
        operation = Operation(
            id=str(uuid.uuid4()),
            client_id=client_id,
            operation_type="import",
            currency="USD",
            exchange_rate=random.uniform(900, 1100),
            extraction_method="llm_multicapa",
            source_file=f"FC_{year}-{month:02d}-{invoice_num:03d}.pdf",
            created_at=op_date,
        )
        session.add(operation)
        
        # Generate items for this operation
        num_items = random.randint(MIN_ITEMS_PER_INVOICE, MAX_ITEMS_PER_INVOICE)
        total_value = 0.0
        total_weight = 0.0
        
        for _ in range(num_items):
            product = random.choice(SAMPLE_PRODUCTS)
            quantity = random.randint(10, 500)
            unit_value = round(random.uniform(5, 200), 2)
            unit_weight = round(random.uniform(0.1, 5), 3)
            
            item = OperationItem(
                id=str(uuid.uuid4()),
                operation_id=operation.id,
                pieza=product[0],
                descripcion=product[1],
                origen=random.choice(ORIGINS),
                cantidad=quantity,
                valor_unitario=unit_value,
                peso_unitario=unit_weight,
                is_valid=True,
            )
            session.add(item)
            
            total_value += quantity * unit_value
            total_weight += quantity * unit_weight
        
        # Update operation totals
        operation.total_items = num_items
        operation.total_value = round(total_value, 2)
        operation.total_weight = round(total_weight, 2)
        operation.processing_time_ms = random.randint(500, 3000)
    
    await session.commit()

async def run_performance_queries(session) -> dict:
    """Run typical queries and measure performance."""
    results = {}
    
    # Query 1: Total operations per client
    start = time.perf_counter()
    query = select(
        Client.name,
        func.count(Operation.id).label("total_ops")
    ).join(Operation).group_by(Client.name)
    result = await session.execute(query)
    results["ops_per_client"] = {
        "time_ms": round((time.perf_counter() - start) * 1000, 2),
        "data": result.all()
    }
    
    # Query 2: Total items in system
    start = time.perf_counter()
    result = await session.execute(select(func.count(OperationItem.id)))
    total_items = result.scalar()
    results["total_items"] = {
        "time_ms": round((time.perf_counter() - start) * 1000, 2),
        "count": total_items
    }
    
    # Query 3: Most used NCM codes
    start = time.perf_counter()
    query = select(
        OperationItem.pieza,
        func.count(OperationItem.id).label("usage")
    ).group_by(OperationItem.pieza).order_by(func.count(OperationItem.id).desc()).limit(5)
    result = await session.execute(query)
    results["top_ncm"] = {
        "time_ms": round((time.perf_counter() - start) * 1000, 2),
        "data": result.all()
    }
    
    # Query 4: Operations in last "month" (simulated)
    start = time.perf_counter()
    cutoff = datetime.now() - timedelta(days=30)
    query = select(func.count(Operation.id)).where(Operation.created_at >= cutoff)
    result = await session.execute(query)
    results["recent_ops"] = {
        "time_ms": round((time.perf_counter() - start) * 1000, 2),
        "count": result.scalar() or 0
    }
    
    return results

# ==============================================================================
# Main Execution
# ==============================================================================

async def main():
    print("=" * 60)
    print("🔬 DATABASE STRESS TEST: 1 Year Simulation")
    print("=" * 60)
    
    # Initialize DB
    await init_db()
    
    async for session in get_async_session():
        # Step 1: Create clients
        print("\n📋 Step 1: Creating test clients...")
        client_ids = await create_test_clients(session)
        
        # Step 2: Generate 12 months of data
        print(f"\n📅 Step 2: Generating {MONTHS_TO_SIMULATE} months of operations...")
        current_year = datetime.now().year
        
        total_ops = 0
        for month in range(1, MONTHS_TO_SIMULATE + 1):
            for client_id in client_ids:
                await generate_monthly_operations(session, client_id, current_year - 1, month)
                total_ops += 1
            print(f"  ✅ Month {month:02d}/{MONTHS_TO_SIMULATE} complete")
        
        # Step 3: Measure performance
        print("\n⚡ Step 3: Running performance queries...")
        perf_results = await run_performance_queries(session)
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 SIMULATION RESULTS")
        print("=" * 60)
        
        print("\n📈 Operations per client:")
        for name, count in perf_results["ops_per_client"]["data"]:
            print(f"   • {name}: {count} operations")
        print(f"   Query time: {perf_results['ops_per_client']['time_ms']}ms")
        
        print(f"\n📦 Total items in database: {perf_results['total_items']['count']}")
        print(f"   Query time: {perf_results['total_items']['time_ms']}ms")
        
        print("\n🏷️ Top 5 NCM codes:")
        for ncm, usage in perf_results["top_ncm"]["data"]:
            print(f"   • {ncm}: used {usage} times")
        print(f"   Query time: {perf_results['top_ncm']['time_ms']}ms")
        
        print(f"\n📅 Operations in last 30 days: {perf_results['recent_ops']['count']}")
        print(f"   Query time: {perf_results['recent_ops']['time_ms']}ms")
        
        print("\n" + "=" * 60)
        print("✅ STRESS TEST COMPLETE")
        print("=" * 60)
        
        break

if __name__ == "__main__":
    asyncio.run(main())
