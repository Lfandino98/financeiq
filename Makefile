# ============================================================
# MAKEFILE - FinanceIQ
# Uso: make <comando>
# ============================================================

.PHONY: help install setup run test seed clean migrate shell

help:
	@echo "╔══════════════════════════════════════╗"
	@echo "║       FinanceIQ - Comandos           ║"
	@echo "╠══════════════════════════════════════╣"
	@echo "║ make install   - Instalar deps       ║"
	@echo "║ make setup     - Configurar proyecto ║"
	@echo "║ make run       - Iniciar servidor    ║"
	@echo "║ make test      - Ejecutar tests      ║"
	@echo "║ make seed      - Poblar con datos    ║"
	@echo "║ make migrate   - Ejecutar migraciones║"
	@echo "║ make shell     - Django shell        ║"
	@echo "║ make clean     - Limpiar archivos    ║"
	@echo "╚══════════════════════════════════════╝"

install:
	pip install -r requirements.txt

setup: install
	cp -n .env.example .env || true
	mkdir -p apps/core/management/commands
	mkdir -p templates/{auth,dashboard,transactions,goals,analysis,alerts,categories}
	mkdir -p static/js
	touch apps/__init__.py
	touch apps/core/__init__.py
	touch apps/api/__init__.py
	touch apps/core/management/__init__.py
	touch apps/core/management/commands/__init__.py
	python manage.py makemigrations core
	python manage.py migrate
	@echo "✅ Proyecto configurado correctamente"

run:
	python manage.py runserver 0.0.0.0:8000

test:
	python manage.py test tests --verbosity=2

test-coverage:
	coverage run --source='.' manage.py test tests
	coverage report
	coverage html

seed:
	python manage.py seed_data --username demo --months 3

seed-full:
	python manage.py seed_data --username demo --months 6 --clear

migrate:
	python manage.py makemigrations
	python manage.py migrate

shell:
	python manage.py shell

superuser:
	python manage.py createsuperuser

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -delete
	rm -rf .coverage htmlcov/
	@echo "✅ Archivos temporales eliminados"

check:
	python manage.py check
	python manage.py validate_templates

collectstatic:
	python manage.py collectstatic --noinput