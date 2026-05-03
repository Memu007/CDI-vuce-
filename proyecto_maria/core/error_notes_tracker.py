"""
Sistema de tracking interno de errores para mejoras continuas.
Usa Memory MCP para knowledge graph + JSON backup local.
"""

import json
import logging
import os
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorPriority(Enum):
    """Prioridad calculada según frecuencia"""
    CRITICAL = "critical"  # > 20 en 24h
    HIGH = "high"  # 10-20 en 24h
    MEDIUM = "medium"  # 3-10 en 24h
    LOW = "low"  # 1-2 en 24h


@dataclass
class ErrorNote:
    """Nota de error con metadata para mejoras"""
    error_type: str
    error_message: str
    endpoint: str
    user_plan: Optional[str]
    context: Dict[str, Any]
    improvement_note: str
    timestamp: str
    frequency: int = 1
    priority: str = ErrorPriority.LOW.value

    def to_dict(self):
        return asdict(self)


class ErrorNotesTracker:
    """
    Tracker de errores con notas internas para mejoras.
    Usa Memory MCP + JSON backup local.
    """

    def __init__(self, data_dir: str = None):
        """
        Args:
            data_dir: Directorio para almacenar error_notes.json
        """
        if data_dir is None:
            # Default: proyecto_maria/data/
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'data'
            )

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.json_path = self.data_dir / 'error_notes.json'

        # In-memory storage
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.error_notes: List[ErrorNote] = []
        self.last_errors: Dict[str, ErrorNote] = {}

        # Load existing data
        self._load_from_json()

        # Memory MCP integration flag
        self.memory_mcp_available = self._check_memory_mcp()

    def _check_memory_mcp(self) -> bool:
        """Verifica si Memory MCP está disponible"""
        try:
            # Intentar importar funciones de Memory MCP
            # (esto será llamado desde server que tiene acceso a MCPs)
            return True  # Asumimos disponible, se maneja en track_error
        except Exception:
            logger.warning("Memory MCP no disponible, usando solo JSON backup")
            return False

    def _load_from_json(self):
        """Carga notas existentes desde JSON"""
        if not self.json_path.exists():
            return

        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.error_counts = defaultdict(int, data.get('error_counts', {}))

            notes_data = data.get('error_notes', [])
            self.error_notes = [
                ErrorNote(**note) for note in notes_data
            ]

            logger.info(f"Loaded {len(self.error_notes)} error notes from {self.json_path}")
        except Exception as e:
            logger.error(f"Error loading error notes: {e}")

    def _save_to_json(self):
        """Guarda notas a JSON (backup persistente)"""
        try:
            data = {
                'error_counts': dict(self.error_counts),
                'error_notes': [note.to_dict() for note in self.error_notes],
                'last_updated': datetime.now().isoformat()
            }

            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved {len(self.error_notes)} error notes to {self.json_path}")
        except Exception as e:
            logger.error(f"Error saving error notes: {e}")

    def _calculate_priority(self, error_key: str) -> ErrorPriority:
        """Calcula prioridad basada en frecuencia en últimas 24h"""
        # Contar errores recientes
        count_24h = 0
        cutoff = datetime.now() - timedelta(hours=24)

        for note in self.error_notes:
            if note.error_type == error_key:
                note_time = datetime.fromisoformat(note.timestamp)
                if note_time > cutoff:
                    count_24h += 1

        if count_24h > 20:
            return ErrorPriority.CRITICAL
        elif count_24h >= 10:
            return ErrorPriority.HIGH
        elif count_24h >= 3:
            return ErrorPriority.MEDIUM
        else:
            return ErrorPriority.LOW

    def _generate_improvement_note(self, error: Exception, context: Dict[str, Any]) -> str:
        """Genera nota de mejora automática basada en el error"""
        error_str = str(error)
        error_type = type(error).__name__
        endpoint = context.get('endpoint', 'unknown')

        notes = []

        # Detectar uso de str(e) genérico
        if error_str and len(error_str) > 50:
            notes.append("⚠️ Mensaje de error muy técnico - considerar mensaje user-friendly")

        # Detectar errores de validación
        if 'validation' in error_str.lower() or 'invalid' in error_str.lower():
            notes.append("💡 Error de validación - agregar validación client-side preventiva")

        # Detectar errores de upload
        if 'upload' in endpoint.lower() or 'file' in error_str.lower():
            notes.append("📤 Error en upload - verificar límites y tipos de archivo")

        # Detectar errores de API externa
        if error_type in ['ConnectionError', 'TimeoutError', 'HTTPException']:
            notes.append("🌐 Error de API externa - implementar retry/fallback")

        # Detectar errores de base de datos
        if 'database' in error_str.lower() or 'sql' in error_str.lower():
            notes.append("🗄️ Error de BD - verificar conexión y queries")

        # Default
        if not notes:
            notes.append(f"🔍 Investigar causa raíz de {error_type} en {endpoint}")

        return " | ".join(notes)

    def track_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        improvement_note: str = None
    ):
        """
        Trackea un error con notas para mejoras.

        Args:
            error: Exception capturada
            context: Contexto adicional (endpoint, user_plan, etc.)
            improvement_note: Nota manual de mejora (opcional)
        """
        context = context or {}
        error_type = type(error).__name__
        error_message = str(error)
        endpoint = context.get('endpoint', 'unknown')
        user_plan = context.get('user_plan', None)

        # Generar key única
        error_key = f"{error_type}:{endpoint}"

        # Incrementar contador
        self.error_counts[error_key] += 1

        # Calcular prioridad
        priority = self._calculate_priority(error_key)

        # Generar o usar improvement note
        if improvement_note is None:
            improvement_note = self._generate_improvement_note(error, context)

        # Crear nota
        note = ErrorNote(
            error_type=error_type,
            error_message=error_message[:500],  # Limitar longitud
            endpoint=endpoint,
            user_plan=user_plan,
            context=context,
            improvement_note=improvement_note,
            timestamp=datetime.now().isoformat(),
            frequency=self.error_counts[error_key],
            priority=priority.value
        )

        # Guardar en memoria
        self.error_notes.append(note)
        self.last_errors[error_key] = note

        # Guardar a JSON
        self._save_to_json()

        # Intentar guardar a Memory MCP
        self._save_to_memory_mcp(note)

        logger.info(
            f"Error tracked: {error_key} (count: {note.frequency}, priority: {note.priority})"
        )

    def _save_to_memory_mcp(self, note: ErrorNote):
        """
        Guarda error note a Memory MCP como entity con observations.

        Nota: Esto requiere que el caller (server) tenga acceso a MCPs.
        Si falla, simplemente loguea warning y continúa.
        """
        try:
            # Preparar datos para Memory MCP
            entity_name = f"Error_{note.error_type}_{note.endpoint.replace('/', '_')}"

            observations = [
                f"Occurred at: {note.timestamp}",
                f"Frequency: {note.frequency} times",
                f"Priority: {note.priority}",
                f"Message: {note.error_message[:200]}",
                f"Improvement: {note.improvement_note}"
            ]

            if note.user_plan:
                observations.append(f"User plan: {note.user_plan}")

            # Esta estructura será usada por el server para llamar a Memory MCP
            # El server puede acceder a mcp__memory__create_entities directamente
            self._mcp_entity_data = {
                "entity_name": entity_name,
                "entity_type": "Error",
                "observations": observations,
                "relations": [
                    {
                        "from": entity_name,
                        "to": f"Endpoint_{note.endpoint.replace('/', '_')}",
                        "relationType": "affects"
                    }
                ]
            }

            logger.debug(f"Memory MCP data prepared for: {entity_name}")
        except Exception as e:
            logger.warning(f"Memory MCP save failed (fallback a JSON OK): {e}")

    def get_mcp_sync_data(self) -> List[Dict[str, Any]]:
        """
        Retorna datos pendientes para sincronizar con Memory MCP.
        El servidor puede llamar a esto y usar las funciones MCP.
        """
        # Retornar datos de las últimas 10 notas para sincronizar
        sync_data = []
        for note in self.error_notes[-10:]:
            entity_name = f"Error_{note.error_type}_{note.endpoint.replace('/', '_')}"
            sync_data.append({
                "entity_name": entity_name,
                "entity_type": "Error",
                "observations": [
                    f"Occurred at: {note.timestamp}",
                    f"Frequency: {note.frequency} times",
                    f"Priority: {note.priority}",
                    f"Message: {note.error_message[:200]}",
                    f"Improvement: {note.improvement_note}",
                    f"User plan: {note.user_plan or 'unknown'}"
                ]
            })
        return sync_data

    def get_error_insights(self) -> Dict[str, Any]:
        """
        Retorna insights sobre errores trackeados.

        Returns:
            Dict con summary, top_errors, suggested_improvements
        """
        # Filtrar errores de últimas 24h
        cutoff = datetime.now() - timedelta(hours=24)
        recent_notes = [
            note for note in self.error_notes
            if datetime.fromisoformat(note.timestamp) > cutoff
        ]

        # Agrupar por error_type
        errors_by_type = defaultdict(list)
        for note in recent_notes:
            errors_by_type[note.error_type].append(note)

        # Top errors por frecuencia
        top_errors = []
        for error_type, notes in errors_by_type.items():
            count = len(notes)
            latest = notes[-1]
            top_errors.append({
                'error_type': error_type,
                'endpoint': latest.endpoint,
                'count': count,
                'priority': latest.priority,
                'improvement_note': latest.improvement_note,
                'last_occurrence': latest.timestamp
            })

        # Ordenar por count desc
        top_errors.sort(key=lambda x: x['count'], reverse=True)

        # Contar prioridades
        priority_counts = defaultdict(int)
        for note in recent_notes:
            priority_counts[note.priority] += 1

        # Generar mejoras sugeridas
        suggested_improvements = self._generate_improvement_suggestions(top_errors)

        return {
            'summary': {
                'total_errors_tracked': len(self.error_notes),
                'errors_last_24h': len(recent_notes),
                'unique_error_types': len(errors_by_type),
                'critical_issues': priority_counts.get('critical', 0),
                'high_priority_issues': priority_counts.get('high', 0),
                'medium_priority_issues': priority_counts.get('medium', 0),
                'low_priority_issues': priority_counts.get('low', 0)
            },
            'top_errors': top_errors[:10],  # Top 10
            'suggested_improvements': suggested_improvements,
            'last_updated': datetime.now().isoformat()
        }

    def _generate_improvement_suggestions(self, top_errors: List[Dict]) -> List[str]:
        """Genera sugerencias de mejora basadas en top errors"""
        suggestions = []

        # Analizar patrones
        endpoints_with_errors = defaultdict(int)
        error_types_count = defaultdict(int)

        for err in top_errors:
            endpoints_with_errors[err['endpoint']] += err['count']
            error_types_count[err['error_type']] += err['count']

        # Sugerir por endpoint más problemático
        if endpoints_with_errors:
            worst_endpoint = max(endpoints_with_errors.items(), key=lambda x: x[1])
            suggestions.append(
                f"🔧 Revisar endpoint {worst_endpoint[0]} ({worst_endpoint[1]} errores)"
            )

        # Sugerir por tipo de error más común
        if error_types_count:
            common_error = max(error_types_count.items(), key=lambda x: x[1])
            suggestions.append(
                f"🐛 Implementar mejor handling para {common_error[0]}"
            )

        # Sugerencias específicas basadas en improvement notes
        for err in top_errors[:5]:  # Top 5 errors
            if err['priority'] in ['critical', 'high']:
                suggestions.append(f"⚠️ URGENTE: {err['improvement_note']}")

        return suggestions[:10]  # Max 10 sugerencias

    def clear_old_notes(self, days: int = 30):
        """
        Limpia notas más viejas que N días.

        Args:
            days: Días de retención
        """
        cutoff = datetime.now() - timedelta(days=days)

        original_count = len(self.error_notes)
        self.error_notes = [
            note for note in self.error_notes
            if datetime.fromisoformat(note.timestamp) > cutoff
        ]

        removed = original_count - len(self.error_notes)
        if removed > 0:
            logger.info(f"Cleaned {removed} error notes older than {days} days")
            self._save_to_json()

        return removed


# Global instance (singleton)
_error_tracker_instance: Optional[ErrorNotesTracker] = None


def get_error_tracker() -> ErrorNotesTracker:
    """Obtiene instancia global del error tracker (singleton)"""
    global _error_tracker_instance

    if _error_tracker_instance is None:
        _error_tracker_instance = ErrorNotesTracker()

    return _error_tracker_instance
