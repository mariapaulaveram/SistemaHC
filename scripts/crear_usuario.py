"""
Script para crear el usuario inicial del sistema.

Uso (desde la raíz del proyecto, con la DB corriendo):
    docker compose exec web python scripts/crear_usuario.py

O directamente con Python si tenés las variables de entorno configuradas:
    python scripts/crear_usuario.py
"""

import sys
import os

# Agregar la raíz del proyecto al path para poder importar la app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Usuario
from app.auth import hash_password


def main():
    print("=== Crear usuario HC-System ===\n")

    email = input("Email: ").strip().lower()
    if not email:
        print("Error: el email no puede estar vacío.")
        sys.exit(1)

    password = input("Contraseña: ").strip()
    if len(password) < 8:
        print("Error: la contraseña debe tener al menos 8 caracteres.")
        sys.exit(1)

    db = SessionLocal()
    try:
        existente = db.query(Usuario).filter(Usuario.email == email).first()
        if existente:
            print(f"\nYa existe un usuario con el email '{email}'.")
            sobreescribir = input("¿Actualizar la contraseña? (s/n): ").strip().lower()
            if sobreescribir == "s":
                existente.hashed_password = hash_password(password)
                db.commit()
                print("Contraseña actualizada.")
            else:
                print("Cancelado.")
            return

        usuario = Usuario(email=email, hashed_password=hash_password(password))
        db.add(usuario)
        db.commit()
        print(f"\nUsuario '{email}' creado correctamente.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
