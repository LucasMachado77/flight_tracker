#!/usr/bin/env python3
"""Script para adicionar a coluna flexible_dates às rotas existentes"""

import sqlite3
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def add_flexible_dates_column():
    """Adiciona a coluna flexible_dates à tabela route_watches"""
    
    conn = sqlite3.connect('flight_tracker.db')
    cursor = conn.cursor()
    
    try:
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info(route_watches)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'flexible_dates' not in columns:
            print("Adicionando coluna flexible_dates...")
            
            # Adicionar a coluna
            cursor.execute("""
                ALTER TABLE route_watches 
                ADD COLUMN flexible_dates BOOLEAN NOT NULL DEFAULT 1
            """)
            
            print("Coluna flexible_dates adicionada com sucesso!")
            print("Todas as rotas existentes foram configuradas como 'flexíveis' por padrão.")
            
        else:
            print("Coluna flexible_dates já existe.")
        
        # Verificar quantas rotas existem
        cursor.execute("SELECT COUNT(*) FROM route_watches")
        count = cursor.fetchone()[0]
        print(f"Total de rotas no banco: {count}")
        
        # Mostrar algumas rotas como exemplo
        cursor.execute("""
            SELECT id, origin, destination, departure_date, return_date, flexible_dates 
            FROM route_watches 
            LIMIT 5
        """)
        routes = cursor.fetchall()
        
        print("\nExemplo de rotas:")
        for route in routes:
            mode = "Flexível" if route[5] else "Exato"
            print(f"  ID {route[0]}: {route[1]} -> {route[2]} ({route[3]} até {route[4]}) - {mode}")
        
        conn.commit()
        
    except Exception as e:
        print(f"Erro: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    add_flexible_dates_column()