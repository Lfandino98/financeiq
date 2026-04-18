#!/bin/bash
# install.sh - Script de instalación completa de FinanceIQ

set -e

echo "╔══════════════════════════════════════════╗"
echo "║     FinanceIQ - Instalación Completa     ║"
echo "╚══════════════════════════════════════════╝"

# Verificar Python
echo "🔍 Verificando Python..."
python3 --version || { echo "❌ Python 3 no encontrado"; exit 1; }

# Crear entorno virtual
echo "🐍 Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Crear estructura de directorios
echo "📁 Creando estructura de directorios..."
mkdir -p apps/core/management/commands
mkdir -p apps/api
mkdir -p templates/{auth,dashboard,transactions,goals,analysis,alerts,categories}
mkdir -p static/js
mkdir -p logs
mkdir -p tests

# Crear archivos __init__.py
echo "📝 Creando archivos __init__.py..."
touch apps/__init__.py
touch apps/core/__init__.py
touch apps/api/__init__.py
touch apps/core/management/__init__.py
touch apps/core/management/commands/__init__.py
touch tests/__init__.py
touch config/__init__.py

# Configurar variables de entorno
echo "⚙️ Configurando variables de entorno..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Archivo .env creado - Edita las credenciales de PostgreSQL"
fi

# Ejecutar migraciones
echo "🗄️ Ejecutando migraciones..."
python manage.py makemigrations core
python manage.py migrate

# Crear superusuario
echo "👤 Creando superusuario admin..."
echo "from django.contrib.auth.models import User; \
User.objects.filter(username='admin').exists() or \
User.objects.create_superuser('admin', 'admin@financeiq.com', 'admin1234')" \
| python manage.py shell

# Poblar con datos de ejemplo
echo "🌱 Poblando con datos de ejemplo..."
python manage.py seed_data --username demo --months 3

# Recolectar archivos estáticos
echo "🎨 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Ejecutar tests
echo "🧪 Ejecutando tests..."
python manage.py test tests --verbosity=1

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║         ✅ INSTALACIÓN COMPLETA          ║"
echo "╠══════════════════════════════════════════╣"
echo "║                                          ║"
echo "║  🚀 Iniciar servidor:                    ║"
echo "║     python manage.py runserver           ║"
echo "║                                          ║"
echo "║  🌐 URL: http://localhost:8000           ║"
echo "║                                          ║"
echo "║  👤 Usuario demo:                        ║"
echo "║     usuario:    demo                     ║"
echo "║     contraseña: demo1234                 ║"
echo "║                                          ║"
echo "║  🔧 Panel admin:                         ║"
echo "║     URL:        /admin                   ║"
echo "║     usuario:    admin                    ║"
echo "║     contraseña: admin1234                ║"
echo "║                                          ║"
echo "║  📡 API REST: /api/v1/                   ║"
echo "║                                          ║"
echo "╚══════════════════════════════════════════╝"