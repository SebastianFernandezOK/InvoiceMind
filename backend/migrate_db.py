#!/usr/bin/env python3
"""
Script de migración para actualizar la base de datos
Agrega las columnas necesarias para el sistema de planes y historial por usuario
"""

import sqlite3
import os

def migrate_database():
    # Ruta a la base de datos
    db_paths = [
        "facturas.db",
        "../facturas.db",
        "historial.db"
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"Migrando base de datos: {db_path}")
            migrate_single_db(db_path)
        else:
            print(f"Base de datos no encontrada: {db_path}")

def migrate_single_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar si la tabla users existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print("Tabla users no existe, será creada automáticamente por SQLAlchemy")
            conn.close()
            return
        
        # Agregar columnas al modelo User si no existen
        columns_to_add = [
            ("plan", "VARCHAR DEFAULT 'basico'"),
            ("procesamientos_restantes", "INTEGER DEFAULT 100"),
            ("procesamientos_totales", "INTEGER DEFAULT 100")
        ]
        
        for column_name, column_def in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
                print(f"✅ Agregada columna {column_name} a tabla users")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"⚠️  Columna {column_name} ya existe en tabla users")
                else:
                    print(f"❌ Error agregando columna {column_name}: {e}")
        
        # Verificar si la tabla historial_archivos existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historial_archivos';")
        if cursor.fetchone():
            # Agregar columna user_id a historial_archivos si no existe
            try:
                cursor.execute("ALTER TABLE historial_archivos ADD COLUMN user_id INTEGER")
                print("✅ Agregada columna user_id a tabla historial_archivos")
                
                # Actualizar registros existentes con user_id = 1 (primer usuario)
                cursor.execute("UPDATE historial_archivos SET user_id = 1 WHERE user_id IS NULL")
                print("✅ Asignados registros existentes al primer usuario")
                
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print("⚠️  Columna user_id ya existe en tabla historial_archivos")
                else:
                    print(f"❌ Error agregando columna user_id: {e}")
        else:
            print("⚠️  Tabla historial_archivos no existe, será creada automáticamente")
        
        # Verificar si la tabla historial_excel existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historial_excel';")
        if not cursor.fetchone():
            # Crear tabla historial_excel
            cursor.execute("""
                CREATE TABLE historial_excel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_archivo VARCHAR NOT NULL,
                    fecha_generado DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cantidad_facturas INTEGER DEFAULT 0,
                    excel_data BLOB NOT NULL,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            print("✅ Creada tabla historial_excel")
        else:
            print("⚠️  Tabla historial_excel ya existe")
        
        conn.commit()
        print(f"✅ Migración completada para {db_path}")
        
    except Exception as e:
        print(f"❌ Error durante la migración de {db_path}: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando migración de base de datos...")
    migrate_database()
    print("✨ Migración completada!")
