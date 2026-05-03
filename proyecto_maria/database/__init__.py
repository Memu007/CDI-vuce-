"""
Database package for MARIA project
"""

from .models import Base, Client, Operation, OperationItem, NCMNote, SystemBackup, APILog
from .connection import (
    init_db, 
    get_async_session, 
    test_connection,
    engine
)

# Import unified DataStore from core module
try:
    from proyecto_maria.core.datastore import DataStore
except ImportError:
    # Fallback: try relative import
    try:
        from ..core.datastore import DataStore
    except ImportError:
        # Last resort: import from legacy database.py
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        try:
            from database import DataStore
        except ImportError:
            # Create minimal fallback if all else fails
            import uuid
            class DataStore:
                def __init__(self):
                    self._data = {}
                    self._mem_clients = {}
                    self._mem_column_mappings = {}
                    self.user_id = "demo_user"

                def list_clients(self):
                    return []

                def get_clients(self):
                    return self.list_clients()

                def create_client(self, cliente):
                    cid = str(uuid.uuid4())
                    return {"id": cid, **cliente}

                def get_column_mapping(self, cliente_id: str) -> dict:
                    return dict(self._mem_column_mappings.get(cliente_id, {}))

                def set_column_mapping(self, cliente_id: str, mapping: dict) -> bool:
                    self._mem_column_mappings[cliente_id] = mapping
                    return True

__all__ = [
    "Base", "Client", "Operation", "OperationItem", "NCMNote", "SystemBackup", "APILog",
    "init_db", "get_async_session", "test_connection",
    "engine", "DataStore"
]