# ⚡ QUICK START - 2 Minutos

Levanta el proyecto en tiempo récord. **Sin complicaciones.**

---

## 🔑 ANTES DE EMPEZAR: API KEY

Necesitás una API key de Google Gemini (gratis):
1. Ir a https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copiar la key (empieza con `AIzaSy...`)

---

## 🎯 OPCIÓN 1: SCRIPT MÁGICO (RECOMENDADO)

Solo necesitas tener Python 3 instalado.

```bash
# 1. Clonar el repo (si es PC nueva)
git clone https://github.com/Memu007/CDI.git
cd CDI

# 2. Ejecuta el setup (Instala todo)
./setup.sh

# 3. Configura la API key
cp .env.example .env
nano .env
# Busca GEMINI_API_KEY= y pega tu key

# 4. Inicia el servidor
./start_server.sh
```

**Abre:** http://localhost:8080/dashboard

✅ **LISTO!**

---

## 🛠️ OPCIÓN 2: MANUAL (PASO A PASO)

Si prefieres tener el control total:

### Paso 1: Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# o
# venv\Scripts\activate     # Windows
```

### Paso 2: Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 3: Configurar Variables

```bash
cp .env.example .env
nano .env
# Agrega tu GEMINI_API_KEY
```

### Paso 4: Iniciar Servidor

```bash
./start_server.sh
```

---

## 🚨 SOLUCIÓN DE PROBLEMAS

### ❌ "Permission denied" al ejecutar scripts

Dale permisos de ejecución:

```bash
chmod +x setup.sh start_server.sh
```

### ❌ El servidor no arranca

Revisa el log para ver el error exacto:

```bash
cat server_log.txt
```

### ❌ Puerto 8080 ocupado

Edita `gunicorn_conf.py` y cambia el puerto:

```python
bind = "0.0.0.0:8081" # Ejemplo
```

---

## 📚 ¿QUÉ SIGUE?

1.  **Abre el Dashboard:** http://localhost:8080/dashboard
2.  **Prueba subir un Excel:** Usa los ejemplos en `data/`.
3.  **Intenta romperlo:** El sistema tiene rate limiting y seguridad avanzada.

¡A programar! 🚀
