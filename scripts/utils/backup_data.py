"""
Sistema de backup automático para MARIA
- Backup automático cada 5 minutos
- Backup de localStorage del navegador
- Rotación automática de backups antiguos
- Integración con el servidor FastAPI
"""
import os
import shutil
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, 'data')
DEST_ROOT = os.path.join(ROOT, 'backups')
MAX_BACKUPS = 20  # Mantener máximo 20 backups

class AutoBackupService:
    def __init__(self):
        self.running = False
        self.backup_interval = 300  # 5 minutos
        
    async def start(self):
        """Inicia el servicio de backup automático"""
        self.running = True
        print("🔄 Servicio de backup automático iniciado")
        
        while self.running:
            try:
                await self.create_backup()
                await self.cleanup_old_backups()
                await asyncio.sleep(self.backup_interval)
            except Exception as e:
                print(f"❌ Error en backup automático: {e}")
                await asyncio.sleep(60)  # Esperar 1 minuto antes de reintentar
    
    def stop(self):
        """Detiene el servicio de backup"""
        self.running = False
        print("⏹️ Servicio de backup automático detenido")
    
    async def create_backup(self):
        """Crea un backup completo"""
        if not os.path.exists(DATA_DIR):
            return
            
        os.makedirs(DEST_ROOT, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        dest = os.path.join(DEST_ROOT, f'data_{ts}')
        
        try:
            shutil.copytree(DATA_DIR, dest)
            print(f"✅ Backup automático creado: {dest}")
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
    
    async def cleanup_old_backups(self):
        """Elimina backups antiguos manteniendo solo los más recientes"""
        if not os.path.exists(DEST_ROOT):
            return
            
        backups = []
        for item in os.listdir(DEST_ROOT):
            path = os.path.join(DEST_ROOT, item)
            if os.path.isdir(path) and item.startswith('data_'):
                backups.append((item, path, os.path.getctime(path)))
        
        # Ordenar por fecha de creación (más reciente primero)
        backups.sort(key=lambda x: x[2], reverse=True)
        
        # Eliminar backups antiguos
        for i, (name, path, _) in enumerate(backups):
            if i >= MAX_BACKUPS:
                try:
                    shutil.rmtree(path)
                    print(f"🗑️ Backup antiguo eliminado: {name}")
                except Exception as e:
                    print(f"❌ Error eliminando backup {name}: {e}")

    def backup_localstorage(self, data: Dict[str, Any]):
        """Backup específico de localStorage del navegador"""
        os.makedirs(DATA_DIR, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(DATA_DIR, f'localStorage_backup_{ts}.json')
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 LocalStorage backup creado: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Error guardando localStorage: {e}")
            return None

# Instancia global del servicio
backup_service = AutoBackupService()

def main() -> None:
    """Función principal para backup manual"""
    if not os.path.exists(DATA_DIR):
        print('No hay carpeta data/ para respaldar')
        return
    os.makedirs(DEST_ROOT, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(DEST_ROOT, f'data_{ts}')
    shutil.copytree(DATA_DIR, dest)
    print(f'Backup manual creado: {dest}')

if __name__ == '__main__':
    main()