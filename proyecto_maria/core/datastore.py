"""
DataStore Unificado para el proyecto MARIA
===========================================

Esta clase consolida las 3 implementaciones previas de DataStore:
1. database.py (legacy, ~500 líneas) - Implementación completa con PostgreSQL
2. database/__init__.py (fallback, ~100 líneas) - Implementación in-memory mínima
3. server_funcional.py líneas 31-43 - Fallback minimal inline

Usa patrón Strategy para alternar entre backends PostgreSQL e in-memory.
Incluye TODOS los métodos necesarios incluyendo column_mapping que causaba bugs.
"""

import os
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any


def _truthy_env(value: Optional[str]) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _safe_int_env(var_name: str, default: int, minimum: int = 0) -> int:
    raw = os.getenv(var_name)
    if raw is None:
        return default
    try:
        val = int(float(raw))
        if val < minimum:
            return minimum
        return val
    except (TypeError, ValueError):
        return default


_PG_STATUS = {
    "attempted": False,
    "available": None,
    "error": None,
}


def _reset_backend_cache_for_tests() -> None:
    """Solo para tests: reinicia el cache de backend."""
    _PG_STATUS.update({"attempted": False, "available": None, "error": None})


class DataStoreBackend:
    """Interfaz base para backends de DataStore"""

    def list_clients(self) -> List[Dict]:
        raise NotImplementedError

    def create_client(self, cliente: dict) -> Dict:
        raise NotImplementedError

    def update_client(self, cliente_id: str, cliente: dict) -> Dict:
        raise NotImplementedError

    def delete_client(self, cliente_id: str) -> bool:
        raise NotImplementedError

    def get_client(self, cliente_id: str) -> Optional[Dict]:
        raise NotImplementedError

    def set_favorite(self, cliente_id: str, favorito: bool) -> bool:
        raise NotImplementedError

    def get_operations_by_client(self, cliente_id: str) -> List[Dict]:
        raise NotImplementedError

    def add_operation(self, cliente_id: str, payload: dict) -> Dict:
        raise NotImplementedError

    def get_ncm_notes(self, ncm: str) -> List[str]:
        raise NotImplementedError

    def add_ncm_note(self, ncm: str, note: str, client_id: Optional[str] = None) -> bool:
        raise NotImplementedError

    def get_column_mapping(self, cliente_id: str) -> Dict:
        raise NotImplementedError

    def set_column_mapping(self, cliente_id: str, mapping: dict) -> bool:
        raise NotImplementedError

    def get_all_operations(self) -> List[Dict]:
        raise NotImplementedError

    def get_operation_by_id(self, operation_id: str) -> Optional[Dict]:
        raise NotImplementedError

    def delete_operation(self, operation_id: str) -> bool:
        raise NotImplementedError


class PostgreSQLBackend(DataStoreBackend):
    """Backend con PostgreSQL usando psycopg o psycopg2"""

    def __init__(self, db_url: str, user_id: str):
        self.user_id = user_id
        self._conn = None
        self._pg = None

        # Intentar cargar driver
        connect_fn = None
        try:
            import psycopg
            connect_fn = psycopg.connect
            self._pg = "psycopg3"
        except ImportError:
            try:
                import psycopg2
                connect_fn = psycopg2.connect
                self._pg = "psycopg2"
            except ImportError:
                raise ImportError("No se pudo importar psycopg o psycopg2")

        # Conectar con timeout acotado para evitar cuelgues
        timeout_seconds = _safe_int_env("DATASTORE_PG_TIMEOUT_SECONDS", 3, minimum=1)
        connect_kwargs = {}
        if timeout_seconds:
            connect_kwargs["connect_timeout"] = timeout_seconds
        try:
            self._conn = connect_fn(db_url, **connect_kwargs)
        except TypeError:
            # Algunos drivers no soportan connect_timeout como kwarg
            self._conn = connect_fn(db_url)
        if self._pg == "psycopg2":
            self._conn.autocommit = True

        # Asegurar usuario demo
        self.user_id = self._ensure_demo_user()
        self._maybe_seed_clients()

        # Mantener mapeos de columnas en memoria (simplificado)
        self._mem_column_mappings = {}

    def _ensure_demo_user(self) -> str:
        """Asegura un usuario demo para agrupar datos tenant. Retorna user_id."""
        cur = self._conn.cursor()
        cur.execute("SELECT id FROM users WHERE username=%s", ("demo",))
        row = cur.fetchone()
        if row:
            return row[0]
        demo_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO users (id, username, email, password_hash, plan) VALUES (%s,%s,%s,%s,%s)",
            (demo_id, "demo", "demo@example.com", "", "premium"),
        )
        self._commit()
        return demo_id

    def _demo_clients(self):
        return {
            "1": {"id": "1", "user_id": self.user_id, "name": "Empresa ABC S.A.", "email": "contacto@abc.com", "phone": "011-1234-5678", "address": "Calle 123, Buenos Aires", "notes": "Cliente frecuente", "favorite": True},
            "2": {"id": "2", "user_id": self.user_id, "name": "Importadora XYZ Ltda.", "email": "info@xyz.com", "phone": "011-9876-5432", "address": "Av. Corrientes 456, Buenos Aires", "notes": "Requiere documentación especial", "favorite": False},
            "3": {"id": "3", "user_id": self.user_id, "name": "Comercial Sur SRL", "email": "ventas@sursrl.com", "phone": "011-5555-1234", "address": "San Martín 789, La Plata", "notes": "", "favorite": False},
        }

    def _maybe_seed_clients(self) -> None:
        try:
            cur = self._conn.cursor()
            cur.execute("SELECT 1 FROM clients WHERE user_id=%s LIMIT 1", (self.user_id,))
            if cur.fetchone():
                return
            for c in self._demo_clients().values():
                cur.execute(
                    "INSERT INTO clients (id, user_id, name, email, phone, address, notes, favorite) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (c["id"], c["user_id"], c["name"], c["email"], c["phone"], c["address"], c["notes"], c["favorite"]),
                )
            self._commit()
        except Exception:
            pass

    def _commit(self):
        try:
            self._conn.commit()
        except Exception:
            pass

    def list_clients(self) -> List[Dict]:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT id, name, email, phone, address, notes, favorite FROM clients WHERE user_id=%s ORDER BY favorite DESC, name ASC",
            (self.user_id,),
        )
        rows = cur.fetchall()
        return [
            {"id": r[0], "nombre": r[1], "email": r[2], "telefono": r[3], "direccion": r[4], "notas": r[5] or "", "favorito": bool(r[6])}
            for r in rows
        ]

    def create_client(self, cliente: dict) -> Dict:
        cid = str(uuid.uuid4())
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO clients (id, user_id, name, email, phone, address, notes, favorite) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (cid, self.user_id, cliente.get("nombre"), cliente.get("email"), cliente.get("telefono"), cliente.get("direccion"), cliente.get("notas"), False),
        )
        self._commit()
        return {"id": cid, **cliente, "favorito": False}

    def update_client(self, cliente_id: str, cliente: dict) -> Dict:
        cur = self._conn.cursor()
        cur.execute(
            "UPDATE clients SET name=%s, email=%s, phone=%s, address=%s, notes=%s WHERE id=%s AND user_id=%s",
            (cliente.get("nombre"), cliente.get("email"), cliente.get("telefono"), cliente.get("direccion"), cliente.get("notas"), cliente_id, self.user_id),
        )
        self._commit()
        cur.execute("SELECT favorite FROM clients WHERE id=%s AND user_id=%s", (cliente_id, self.user_id))
        fav = cur.fetchone()
        return {"id": cliente_id, **cliente, "favorito": bool(fav[0]) if fav else False}

    def delete_client(self, cliente_id: str) -> bool:
        cur = self._conn.cursor()
        cur.execute("DELETE FROM clients WHERE id=%s AND user_id=%s", (cliente_id, self.user_id))
        self._commit()
        return True

    def get_client(self, cliente_id: str) -> Optional[Dict]:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT id, name, email, phone, address, notes, favorite FROM clients WHERE id=%s AND user_id=%s",
            (cliente_id, self.user_id),
        )
        r = cur.fetchone()
        if not r:
            return None
        return {"id": r[0], "nombre": r[1], "email": r[2], "telefono": r[3], "direccion": r[4], "notas": r[5] or "", "favorito": bool(r[6])}

    def set_favorite(self, cliente_id: str, favorito: bool) -> bool:
        cur = self._conn.cursor()
        cur.execute("UPDATE clients SET favorite=%s WHERE id=%s AND user_id=%s", (favorito, cliente_id, self.user_id))
        self._commit()
        return True

    def get_operations_by_client(self, cliente_id: str) -> List[Dict]:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT id, created_at, total_value, extra FROM operations WHERE user_id=%s AND client_id=%s ORDER BY created_at DESC LIMIT 200",
            (self.user_id, cliente_id),
        )
        rows = cur.fetchall()
        ops = []
        for r in rows:
            extra = r[3] if isinstance(r[3], dict) else {}
            ops.append({
                "operation_id": f"OP_{r[0]}",
                "fecha": r[1].isoformat() if isinstance(r[1], datetime) else str(r[1]),
                "resumen": extra.get("resumen", {"valor_total": float(r[2] or 0)}),
                "items": extra.get("items", []),
            })
        return ops

    def add_operation(self, cliente_id: str, payload: dict) -> Dict:
        items = payload.get("items", [])
        total = 0
        try:
            total = sum((float(i.get("cantidad", 0)) * float(i.get("valor_unitario", 0))) for i in items)
        except Exception:
            total = 0
        resumen = payload.get("resumen", {"grupos": len(set(i.get("pieza", "")[:4] for i in items)), "items": len(items), "valor_total": total})

        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO operations (user_id, client_id, op_code, source, currency, total_value, extra) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id, created_at",
            (self.user_id, cliente_id, payload.get("operation_id"), "grouped", "USD", total, json.dumps({"resumen": resumen, "items": items})),
        )
        row = cur.fetchone()
        self._commit()
        return {"operation_id": f"OP_{row[0]}", "fecha": row[1].isoformat(), "resumen": resumen, "items": items}

    def get_ncm_notes(self, ncm: str) -> List[str]:
        cur = self._conn.cursor()
        cur.execute("SELECT note FROM ncm_notes WHERE user_id=%s AND ncm=%s ORDER BY created_at DESC LIMIT 200", (self.user_id, ncm))
        return [r[0] for r in cur.fetchall()]

    def add_ncm_note(self, ncm: str, note: str, client_id: Optional[str] = None) -> bool:
        cur = self._conn.cursor()
        cur.execute("INSERT INTO ncm_notes (user_id, client_id, ncm, note) VALUES (%s,%s,%s,%s)", (self.user_id, client_id, ncm, note))
        self._commit()
        return True

    def get_column_mapping(self, cliente_id: str) -> Dict:
        # Implementación simplificada: usar memoria por ahora
        return dict(self._mem_column_mappings.get(cliente_id, {}))

    def set_column_mapping(self, cliente_id: str, mapping: dict) -> bool:
        # Normalizar claves a lower y valores a canon
        allowed = {"pieza", "descripcion", "origen", "cantidad", "valor_unitario", "peso_unitario"}
        norm = {}
        for k, v in (mapping or {}).items():
            key = str(k).strip().lower()
            val = str(v).strip().lower()
            if not key or val not in allowed:
                continue
            norm[key] = val
        self._mem_column_mappings[cliente_id] = norm
        return True

    def get_all_operations(self) -> List[Dict]:
        cur = self._conn.cursor()
        cur.execute(
            "SELECT id, created_at, client_id, op_code, total_value, extra FROM operations WHERE user_id=%s ORDER BY created_at DESC LIMIT 1000",
            (self.user_id,),
        )
        rows = cur.fetchall()
        ops: List[Dict] = []
        for r in rows:
            extra = r[5] if isinstance(r[5], dict) else {}
            ops.append({
                "operation_id": f"OP_{r[0]}",
                "timestamp": r[1].isoformat() if isinstance(r[1], datetime) else str(r[1]),
                "client_id": r[2],
                "op_code": r[3],
                "total_value": float(r[4] or 0),
                "items": extra.get("items", []),
                "resumen": extra.get("resumen", {}),
            })
        return ops

    def get_operation_by_id(self, operation_id: str) -> Optional[Dict]:
        numeric_id = operation_id.replace("OP_", "")
        cur = self._conn.cursor()
        cur.execute(
            "SELECT id, created_at, client_id, op_code, total_value, extra FROM operations WHERE user_id=%s AND id=%s LIMIT 1",
            (self.user_id, numeric_id),
        )
        row = cur.fetchone()
        if not row:
            return None
        extra = row[5] if isinstance(row[5], dict) else {}
        return {
            "operation_id": f"OP_{row[0]}",
            "timestamp": row[1].isoformat() if isinstance(row[1], datetime) else str(row[1]),
            "client_id": row[2],
            "op_code": row[3],
            "total_value": float(row[4] or 0),
            "items": extra.get("items", []),
            "resumen": extra.get("resumen", {}),
        }

    def delete_operation(self, operation_id: str) -> bool:
        numeric_id = operation_id.replace("OP_", "")
        cur = self._conn.cursor()
        cur.execute(
            "DELETE FROM operations WHERE user_id=%s AND id=%s",
            (self.user_id, numeric_id),
        )
        deleted = cur.rowcount
        self._conn.commit()
        return deleted > 0


class InMemoryBackend(DataStoreBackend):
    """Backend en memoria (sin persistencia)"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._mem_clients = {}
        self._mem_operations = []
        self._mem_operations_by_client = {}
        self._mem_notes = {}
        self._mem_column_mappings = {}

        # Seed demo clients
        for cid, c in self._demo_clients().items():
            self._mem_clients[cid] = c

    def _demo_clients(self):
        return {
            "1": {"id": "1", "user_id": self.user_id, "name": "Empresa ABC S.A.", "email": "contacto@abc.com", "phone": "011-1234-5678", "address": "Calle 123, Buenos Aires", "notes": "Cliente frecuente", "favorite": True},
            "2": {"id": "2", "user_id": self.user_id, "name": "Importadora XYZ Ltda.", "email": "info@xyz.com", "phone": "011-9876-5432", "address": "Av. Corrientes 456, Buenos Aires", "notes": "Requiere documentación especial", "favorite": False},
            "3": {"id": "3", "user_id": self.user_id, "name": "Comercial Sur SRL", "email": "ventas@sursrl.com", "phone": "011-5555-1234", "address": "San Martín 789, La Plata", "notes": "", "favorite": False},
        }

    def list_clients(self) -> List[Dict]:
        return [
            {"id": c["id"], "nombre": c["name"], "email": c["email"], "telefono": c["phone"], "direccion": c["address"], "notas": c["notes"], "favorito": c.get("favorite", False)}
            for c in sorted(self._mem_clients.values(), key=lambda x: (not x.get("favorite", False), x["name"]))
        ]

    def create_client(self, cliente: dict) -> Dict:
        cid = str(uuid.uuid4())
        self._mem_clients[cid] = {
            "id": cid,
            "user_id": self.user_id,
            "name": cliente.get("nombre"),
            "email": cliente.get("email"),
            "phone": cliente.get("telefono"),
            "address": cliente.get("direccion"),
            "notes": cliente.get("notas"),
            "favorite": False,
        }
        return {"id": cid, **cliente, "favorito": False}

    def update_client(self, cliente_id: str, cliente: dict) -> Dict:
        if cliente_id in self._mem_clients:
            self._mem_clients[cliente_id].update({
                "name": cliente.get("nombre"),
                "email": cliente.get("email"),
                "phone": cliente.get("telefono"),
                "address": cliente.get("direccion"),
                "notes": cliente.get("notas"),
            })
            return {"id": cliente_id, **cliente, "favorito": self._mem_clients[cliente_id].get("favorite", False)}
        raise KeyError("Cliente no encontrado")

    def delete_client(self, cliente_id: str) -> bool:
        return self._mem_clients.pop(cliente_id, None) is not None

    def get_client(self, cliente_id: str) -> Optional[Dict]:
        c = self._mem_clients.get(cliente_id)
        if not c:
            return None
        return {"id": c["id"], "nombre": c["name"], "email": c["email"], "telefono": c["phone"], "direccion": c["address"], "notas": c["notes"], "favorito": c.get("favorite", False)}

    def set_favorite(self, cliente_id: str, favorito: bool) -> bool:
        if cliente_id in self._mem_clients:
            self._mem_clients[cliente_id]["favorite"] = favorito
            return True
        return False

    def get_operations_by_client(self, cliente_id: str) -> List[Dict]:
        return list(self._mem_operations_by_client.get(cliente_id, []))

    def add_operation(self, cliente_id: str, payload: dict) -> Dict:
        items = payload.get("items", [])
        total = 0
        try:
            total = sum((float(i.get("cantidad", 0)) * float(i.get("valor_unitario", 0))) for i in items)
        except Exception:
            total = 0
        resumen = payload.get("resumen", {"grupos": len(set(i.get("pieza", "")[:4] for i in items)), "items": len(items), "valor_total": total})

        op = {"operation_id": f"OP_{len(self._mem_operations)+1}", "fecha": datetime.utcnow().isoformat()+"Z", "resumen": resumen, "items": items}
        self._mem_operations.append(op)
        self._mem_operations_by_client.setdefault(cliente_id, []).append(op)
        return op

    def get_ncm_notes(self, ncm: str) -> List[str]:
        return list(self._mem_notes.get(ncm, []))

    def add_ncm_note(self, ncm: str, note: str, client_id: Optional[str] = None) -> bool:
        self._mem_notes.setdefault(ncm, []).append(note)
        return True

    def get_column_mapping(self, cliente_id: str) -> Dict:
        return dict(self._mem_column_mappings.get(cliente_id, {}))

    def set_column_mapping(self, cliente_id: str, mapping: dict) -> bool:
        # Normalizar claves a lower y valores a canon
        allowed = {"pieza", "descripcion", "origen", "cantidad", "valor_unitario", "peso_unitario"}
        norm = {}
        for k, v in (mapping or {}).items():
            key = str(k).strip().lower()
            val = str(v).strip().lower()
            if not key or val not in allowed:
                continue
            norm[key] = val
        self._mem_column_mappings[cliente_id] = norm
        return True

    def get_all_operations(self) -> List[Dict]:
        return list(self._mem_operations)

    def get_operation_by_id(self, operation_id: str) -> Optional[Dict]:
        for op in self._mem_operations:
            if op.get("operation_id") == operation_id:
                return op
        return None

    def delete_operation(self, operation_id: str) -> bool:
        original_len = len(self._mem_operations)
        self._mem_operations = [
            op for op in self._mem_operations
            if op.get("operation_id") != operation_id
        ]
        for client_id, ops in list(self._mem_operations_by_client.items()):
            self._mem_operations_by_client[client_id] = [
                op for op in ops if op.get("operation_id") != operation_id
            ]
        return len(self._mem_operations) < original_len


class DataStore:
    """
    DataStore unificado que soporta PostgreSQL y fallback in-memory.

    Usa patrón Strategy para delegar a backend apropiado según configuración.
    Mantiene compatibilidad con API legacy.
    """

    def __init__(self) -> None:
        self._backend = None
        self._using_pg = False
        self.user_id = None

        backend_pref = os.getenv("DATASTORE_BACKEND", "auto").strip().lower()
        if backend_pref not in {"auto", "postgres", "memory"}:
            backend_pref = "auto"
        disable_db = _truthy_env(os.getenv("DATASTORE_DISABLE_DB"))
        db_url = os.environ.get("DATABASE_URL")

        if backend_pref == "memory" or disable_db:
            self._init_in_memory_backend("flags forzaron backend en memoria")
            return

        if not db_url:
            if backend_pref == "postgres":
                raise RuntimeError("DATABASE_URL es obligatorio cuando DATASTORE_BACKEND=postgres")
            self._init_in_memory_backend("DATABASE_URL no configurada")
            return

        if _PG_STATUS["attempted"] and not _PG_STATUS["available"]:
            cached_error = _PG_STATUS["error"] or "error previo"
            if backend_pref == "postgres":
                raise RuntimeError(f"Backend PostgreSQL deshabilitado por error previo: {cached_error}")
            self._init_in_memory_backend(f"PostgreSQL deshabilitado tras error previo ({cached_error})")
            return

        try:
            self._backend = self._create_postgres_backend(db_url)
            self.user_id = self._backend.user_id
            self._using_pg = True
            print(f"✅ DataStore usando PostgreSQL (backend: {self._backend._pg})")
            return
        except Exception as exc:
            if backend_pref == "postgres":
                raise RuntimeError(f"No se pudo inicializar PostgreSQL: {exc}") from exc
            self._init_in_memory_backend(f"No se pudo conectar a PostgreSQL ({exc})")

    def _init_in_memory_backend(self, reason: str) -> None:
        if reason:
            print(f"⚠️ {reason}")
        self.user_id = str(uuid.uuid4())
        self._backend = InMemoryBackend(self.user_id)
        self._using_pg = False
        print("✅ DataStore usando backend in-memory")

    def _create_postgres_backend(self, db_url: str) -> PostgreSQLBackend:
        global _PG_STATUS
        try:
            backend = PostgreSQLBackend(db_url, str(uuid.uuid4()))
        except Exception as exc:
            _PG_STATUS.update({"attempted": True, "available": False, "error": str(exc)})
            raise
        else:
            _PG_STATUS.update({"attempted": True, "available": True, "error": None})
            return backend

    # -------- Delegación a backend --------

    def list_clients(self) -> List[Dict]:
        return self._backend.list_clients()

    def get_clients(self) -> List[Dict]:
        """Alias para compatibilidad"""
        return self.list_clients()

    def create_client(self, cliente: dict) -> Dict:
        return self._backend.create_client(cliente)

    def update_client(self, cliente_id: str, cliente: dict) -> Dict:
        return self._backend.update_client(cliente_id, cliente)

    def delete_client(self, cliente_id: str) -> bool:
        return self._backend.delete_client(cliente_id)

    def get_client(self, cliente_id: str) -> Optional[Dict]:
        return self._backend.get_client(cliente_id)

    def set_favorite(self, cliente_id: str, favorito: bool) -> bool:
        return self._backend.set_favorite(cliente_id, favorito)

    def get_operations_by_client(self, cliente_id: str) -> List[Dict]:
        return self._backend.get_operations_by_client(cliente_id)

    def add_operation(self, cliente_id: str, payload: dict) -> Dict:
        return self._backend.add_operation(cliente_id, payload)

    def get_ncm_notes(self, ncm: str) -> List[str]:
        return self._backend.get_ncm_notes(ncm)

    def add_ncm_note(self, ncm: str, note: str, client_id: Optional[str] = None) -> bool:
        return self._backend.add_ncm_note(ncm, note, client_id)

    def get_column_mapping(self, cliente_id: str) -> Dict:
        """Obtiene el mapeo de columnas para un cliente"""
        return self._backend.get_column_mapping(cliente_id)

    def set_column_mapping(self, cliente_id: str, mapping: dict) -> bool:
        """Establece el mapeo de columnas para un cliente"""
        return self._backend.set_column_mapping(cliente_id, mapping)

    def get_all_operations(self) -> List[Dict]:
        if hasattr(self._backend, "get_all_operations"):
            return self._backend.get_all_operations()
        return []

    def get_operation_by_id(self, operation_id: str) -> Optional[Dict]:
        if hasattr(self._backend, "get_operation_by_id"):
            return self._backend.get_operation_by_id(operation_id)
        return None

    def delete_operation(self, operation_id: str) -> bool:
        if hasattr(self._backend, "delete_operation"):
            return self._backend.delete_operation(operation_id)
        return False

    # -------- Métricas y exportación --------

    def compute_metrics(self, cliente_id: str) -> dict:
        ops = self.get_operations_by_client(cliente_id)
        total_ops = len(ops)
        total_items = sum(int((op.get('resumen') or {}).get('items', 0)) for op in ops)
        valor_total = float(sum((op.get('resumen') or {}).get('valor_total', 0.0) for op in ops))
        ultimo = ops[0]['fecha'] if ops else None
        prom_items = (total_items / total_ops) if total_ops else 0.0
        return {
            'total_operaciones': total_ops,
            'total_items': total_items,
            'valor_total': round(valor_total, 2),
            'promedio_items_por_operacion': round(prom_items, 2),
            'ultimo_movimiento': ultimo,
        }

    def build_csv(self, cliente_id: str) -> str:
        import io
        import csv
        ops = self.get_operations_by_client(cliente_id)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['operation_id', 'fecha', 'ncm', 'descripcion', 'origen', 'cantidad', 'valor_unitario', 'peso_unitario', 'valor_total_item'])
        for op in ops:
            fecha = op.get('fecha')
            for it in (op.get('items') or []):
                try:
                    qty = float(it.get('cantidad') or 0)
                except Exception:
                    qty = 0.0
                try:
                    unit = float(it.get('valor_unitario') or 0)
                except Exception:
                    unit = 0.0
                writer.writerow([
                    op.get('operation_id'), fecha, it.get('pieza'), it.get('descripcion'), it.get('origen'),
                    it.get('cantidad'), it.get('valor_unitario'), it.get('peso_unitario'), round(qty*unit, 2)
                ])
        return output.getvalue()

    # -------- Estado --------

    @property
    def using_postgres(self) -> bool:
        return self._using_pg
