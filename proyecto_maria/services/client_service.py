"""
Service layer for client management with database integration
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
import logging
import json

from ..database.models import Client, NCMNote, ClientProductHistory
from ..database.connection import get_async_session

logger = logging.getLogger(__name__)

class ClientService:
    """Service for managing clients with PostgreSQL backend"""
    
    @staticmethod
    async def create_client(
        name: str,
        email: str,
        phone: Optional[str] = None,
        cuit: Optional[str] = None,
        address: Optional[str] = None,
        **kwargs
    ) -> Client:
        """Create a new client"""
        async with AsyncSessionLocal() as session:
            client = Client(
                name=name,
                email=email,
                phone=phone,
                cuit=cuit,
                address=address,
                **kwargs
            )
            session.add(client)
            await session.commit()
            await session.refresh(client)
            logger.info(f"✅ Client created: {client.name} ({client.id})")
            return client
    
    @staticmethod
    async def get_client(client_id: str, owner_username: str = None) -> Optional[Client]:
        """Get client by ID. Si se pasa owner_username, filtra por tenant."""
        async with AsyncSessionLocal() as session:
            stmt = select(Client).where(Client.id == client_id)
            if owner_username:
                stmt = stmt.where(Client.owner_username == owner_username)
            result = await session.execute(
                stmt.options(selectinload(Client.ncm_notes))
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_clients(active_only: bool = True, owner_username: str = None) -> List[Client]:
        """Get all clients. Si se pasa owner_username, filtra por tenant."""
        async with AsyncSessionLocal() as session:
            query = select(Client)
            if active_only:
                query = query.where(Client.is_active == True)
            if owner_username:
                query = query.where(Client.owner_username == owner_username)
            
            result = await session.execute(query.order_by(Client.name))
            return result.scalars().all()
    
    @staticmethod
    async def update_client(client_id: str, owner_username: str = None, **updates) -> Optional[Client]:
        """Update client information. Si se pasa owner_username, filtra por tenant."""
        async with AsyncSessionLocal() as session:
            stmt = update(Client).where(Client.id == client_id)
            if owner_username:
                stmt = stmt.where(Client.owner_username == owner_username)
            await session.execute(stmt.values(**updates))
            await session.commit()
            
            # Return updated client
            result = await session.execute(select(Client).where(Client.id == client_id))
            return result.scalar_one_or_none()
    
    @staticmethod
    async def delete_client(client_id: str, soft_delete: bool = True, owner_username: str = None) -> bool:
        """Delete or deactivate client. Si se pasa owner_username, filtra por tenant."""
        async with AsyncSessionLocal() as session:
            if soft_delete:
                stmt = update(Client).where(Client.id == client_id)
                if owner_username:
                    stmt = stmt.where(Client.owner_username == owner_username)
                await session.execute(stmt.values(is_active=False))
            else:
                stmt = delete(Client).where(Client.id == client_id)
                if owner_username:
                    stmt = stmt.where(Client.owner_username == owner_username)
                await session.execute(stmt)
            
            await session.commit()
            logger.info(f"✅ Client {'deactivated' if soft_delete else 'deleted'}: {client_id}")
            return True
    
    @staticmethod
    async def add_ncm_note(client_id: str, ncm_code: str, note: str) -> NCMNote:
        """Add NCM note for client"""
        async with AsyncSessionLocal() as session:
            ncm_note = NCMNote(
                client_id=client_id,
                ncm_code=ncm_code,
                note=note
            )
            session.add(ncm_note)
            await session.commit()
            await session.refresh(ncm_note)
            return ncm_note
    
    @staticmethod
    async def get_ncm_notes(client_id: str) -> Dict[str, str]:
        """Get all NCM notes for client as dict"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(NCMNote)
                .where(NCMNote.client_id == client_id)
            )
            notes = result.scalars().all()
            return {note.ncm_code: note.note for note in notes}
    
    @staticmethod
    async def migrate_from_localstorage(localstorage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate clients and NCM notes from localStorage to database"""
        try:
            clients_data = localstorage_data.get('clients', [])
            ncm_notes_data = localstorage_data.get('ncmNotes', {})

            migrated_clients = []
            async with AsyncSessionLocal() as session:
                for client_data in clients_data:
                    # Check if client already exists
                    existing = await session.execute(
                        select(Client).where(Client.email == client_data.get('email', ''))
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # Create new client
                    client = Client(
                        name=client_data.get('name', 'Cliente Migrado'),
                        email=client_data.get('email', f"cliente_{len(migrated_clients)}@example.com"),
                        phone=client_data.get('phone'),
                        cuit=client_data.get('cuit'),
                        address=client_data.get('address')
                    )
                    session.add(client)
                    await session.flush()  # Get ID

                    migrated_clients.append(client.id)

                    # Migrate NCM notes for this client
                    for ncm_code, note in ncm_notes_data.items():
                        if note:  # Only non-empty notes
                            ncm_note = NCMNote(
                                client_id=client.id,
                                ncm_code=ncm_code,
                                note=note
                            )
                            session.add(ncm_note)

                await session.commit()

            logger.info(f"✅ Migrated {len(migrated_clients)} clients and {len(ncm_notes_data)} NCM notes")
            return {
                "success": True,
                "migrated_clients": len(migrated_clients),
                "migrated_ncm_notes": len(ncm_notes_data),
                "client_ids": migrated_clients
            }

        except Exception as e:
            logger.error(f"❌ Migration error: {e}")
            return {"success": False, "error": str(e)}

    # ==================== AUTO-COMPLETADO INTELIGENTE ====================

    @staticmethod
    async def detect_client_from_text(text: str, owner_username: str = None) -> Optional[Dict[str, Any]]:
        """
        Detectar cliente a partir del texto extraído del PDF
        Busca por CUIT o nombre de empresa. Si se pasa owner_username, filtra por tenant.
        """
        import re

        async with AsyncSessionLocal() as session:
            # Buscar CUIT en el texto (formato: XX-XXXXXXXX-X)
            cuit_pattern = r'\b\d{2}-?\d{8}-?\d\b'
            cuit_matches = re.findall(cuit_pattern, text)

            for cuit_raw in cuit_matches:
                cuit = cuit_raw.replace('-', '')
                stmt = select(Client).where(Client.cuit == cuit)
                if owner_username:
                    stmt = stmt.where(Client.owner_username == owner_username)
                result = await session.execute(stmt)
                client = result.scalar_one_or_none()
                if client:
                    return {
                        "client_id": client.id,
                        "nombre": client.name,
                        "confidence": 0.95,
                        "match_type": "cuit"
                    }

            # Buscar por nombre de empresa
            stmt = select(Client).where(Client.is_active == True)
            if owner_username:
                stmt = stmt.where(Client.owner_username == owner_username)
            clients_result = await session.execute(stmt)
            clients = clients_result.scalars().all()

            for client in clients:
                # Buscar nombre del cliente en el texto (case insensitive)
                if client.name.lower() in text.lower():
                    return {
                        "client_id": client.id,
                        "nombre": client.name,
                        "confidence": 0.80,
                        "match_type": "name"
                    }

            return None

    @staticmethod
    async def get_frequent_products(client_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtener productos frecuentes del cliente para auto-completado"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ClientProductHistory)
                .where(ClientProductHistory.client_id == client_id)
                .order_by(ClientProductHistory.veces_usado.desc(), ClientProductHistory.ultima_vez.desc())
                .limit(limit)
            )
            products = result.scalars().all()

            return [
                {
                    "ncm": p.ncm,
                    "descripcion": p.descripcion,
                    "peso_unitario_avg": p.peso_unitario_avg,
                    "origen_frecuente": p.origen_frecuente,
                    "valor_unitario_avg": p.valor_unitario_avg,
                    "cantidad_avg": p.cantidad_avg,
                    "veces_usado": p.veces_usado,
                    "ultima_vez": p.ultima_vez.isoformat() if p.ultima_vez else None
                }
                for p in products
            ]

    @staticmethod
    async def autocomplete_items(client_id: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Auto-completar items basándose en el historial del cliente
        Busca coincidencias por descripción similar
        """
        from difflib import SequenceMatcher

        # Obtener productos frecuentes del cliente
        frequent_products = await ClientService.get_frequent_products(client_id)

        def similarity(a: str, b: str) -> float:
            """Calcular similaridad entre dos strings (0-1)"""
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()

        def normalize_description(desc: str) -> str:
            """Normalizar descripción para comparación"""
            import re
            # Remover números, caracteres especiales, convertir a lowercase
            desc = re.sub(r'[^a-záéíóúñ\s]', '', desc.lower())
            # Remover espacios múltiples
            desc = re.sub(r'\s+', ' ', desc).strip()
            return desc

        completed_items = []

        for item in items:
            item_desc = item.get('descripcion', '')
            item_ncm = item.get('ncm', '').strip()

            # Si ya tiene NCM, no auto-completar
            if item_ncm and len(item_ncm) >= 6:
                completed_items.append({
                    **item,
                    "autocompleted": False,
                    "confidence": 1.0
                })
                continue

            # Buscar producto similar en historial
            best_match = None
            best_similarity = 0.0

            for product in frequent_products:
                sim = similarity(
                    normalize_description(item_desc),
                    normalize_description(product['descripcion'])
                )

                if sim > best_similarity:
                    best_similarity = sim
                    best_match = product

            # Si encontramos match con >60% similaridad, auto-completar
            if best_match and best_similarity >= 0.6:
                completed_items.append({
                    "descripcion": item.get('descripcion'),
                    "ncm": best_match['ncm'],
                    "peso_unitario": item.get('peso_unitario') or best_match['peso_unitario_avg'] or 0.0,
                    "origen": item.get('origen') or best_match['origen_frecuente'] or 'XX',
                    "cantidad": item.get('cantidad') or 1.0,
                    "valor_unitario": item.get('valor_unitario') or best_match['valor_unitario_avg'] or 0.0,
                    "autocompleted": True,
                    "confidence": round(best_similarity, 2),
                    "matched_product": best_match['descripcion']
                })
            else:
                # No hay match, devolver item original
                completed_items.append({
                    **item,
                    "autocompleted": False,
                    "confidence": 0.0
                })

        return completed_items

    @staticmethod
    async def update_product_history(client_id: str, items: List[Dict[str, Any]]) -> None:
        """
        Actualizar historial de productos del cliente después de procesar operación
        Esto se llama después de confirmar/guardar una operación
        """
        from difflib import SequenceMatcher

        async with AsyncSessionLocal() as session:
            for item in items:
                ncm = item.get('ncm', '').strip()
                descripcion = item.get('descripcion', '').strip()

                if not ncm or not descripcion:
                    continue

                # Buscar si ya existe producto similar
                result = await session.execute(
                    select(ClientProductHistory)
                    .where(
                        ClientProductHistory.client_id == client_id,
                        ClientProductHistory.ncm == ncm
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    # Actualizar estadísticas
                    new_count = existing.veces_usado + 1
                    existing.veces_usado = new_count

                    # Actualizar promedios (media móvil simple)
                    if item.get('peso_unitario', 0) > 0:
                        existing.peso_unitario_avg = (
                            (existing.peso_unitario_avg * (new_count - 1) + item['peso_unitario']) / new_count
                        )

                    if item.get('valor_unitario', 0) > 0:
                        existing.valor_unitario_avg = (
                            (existing.valor_unitario_avg or 0) * (new_count - 1) + item['valor_unitario']
                        ) / new_count

                    if item.get('cantidad', 0) > 0:
                        existing.cantidad_avg = (
                            (existing.cantidad_avg or 0) * (new_count - 1) + item['cantidad']
                        ) / new_count

                    # Actualizar origen si es más frecuente
                    existing.origen_frecuente = item.get('origen', existing.origen_frecuente)
                else:
                    # Crear nuevo registro
                    history_entry = ClientProductHistory(
                        client_id=client_id,
                        ncm=ncm,
                        descripcion=descripcion,
                        peso_unitario_avg=item.get('peso_unitario', 0.0),
                        origen_frecuente=item.get('origen', 'XX'),
                        valor_unitario_avg=item.get('valor_unitario', 0.0),
                        cantidad_avg=item.get('cantidad', 1.0),
                        veces_usado=1
                    )
                    session.add(history_entry)

            await session.commit()
            logger.info(f"✅ Updated product history for client {client_id}: {len(items)} items")

# Import here to avoid circular imports
from ..database.connection import AsyncSessionLocal
