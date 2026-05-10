"""
Модуль для работы с базой данных PostgreSQL
Сохраняет историю раздач и статистику
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import DATABASE_CONFIG


class Database:
    """Класс для работы с PostgreSQL"""
    
    def __init__(self):
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Подключение к базе данных"""
        try:
            self.conn = psycopg2.connect(**DATABASE_CONFIG)
            print("[DB] Подключено к PostgreSQL")
        except Exception as e:
            print(f"[DB] Ошибка подключения: {e}")
            print("[DB] База данных будет недоступна")
            self.conn = None
    
    def create_tables(self):
        """Создание таблиц, если их нет"""
        if not self.conn:
            return
        
        try:
            cur = self.conn.cursor()
            
            # Таблица раздач
            cur.execute("""
                CREATE TABLE IF NOT EXISTS hands (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    player_cards TEXT NOT NULL,
                    board_cards TEXT DEFAULT '',
                    pot_size REAL DEFAULT 0,
                    bet_to_call REAL DEFAULT 0,
                    position TEXT DEFAULT 'MP',
                    recommendation TEXT,
                    hand_strength TEXT,
                    drawing_odds REAL DEFAULT 0,
                    pot_odds REAL DEFAULT 0,
                    equity REAL DEFAULT 0,
                    notes TEXT DEFAULT ''
                )
            """)
            
            # Таблица оппонентов
            cur.execute("""
                CREATE TABLE IF NOT EXISTS opponents (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    hands_played INTEGER DEFAULT 0,
                    vpip REAL DEFAULT 0,
                    pfr REAL DEFAULT 0,
                    aggression REAL DEFAULT 0,
                    last_seen TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Таблица статистики по раздачам
            cur.execute("""
                CREATE TABLE IF NOT EXISTS hand_stats (
                    id SERIAL PRIMARY KEY,
                    hand_id INTEGER REFERENCES hands(id),
                    opponent_id INTEGER REFERENCES opponents(id),
                    action TEXT,
                    amount REAL DEFAULT 0,
                    street TEXT
                )
            """)
            
            self.conn.commit()
            cur.close()
            print("[DB] Таблицы созданы")
        except Exception as e:
            print(f"[DB] Ошибка создания таблиц: {e}")
            self.conn.rollback()
    
    def save_hand(self, player_cards, board_cards, result):
        """Сохранение раздачи в базу"""
        if not self.conn:
            return
        
        try:
            cur = self.conn.cursor()
            
            cur.execute("""
                INSERT INTO hands (
                    player_cards, board_cards, pot_size, bet_to_call,
                    position, recommendation, hand_strength,
                    drawing_odds, pot_odds, equity
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                self._format_cards(player_cards),
                self._format_cards(board_cards),
                result.get("pot_size", 0),
                result.get("bet_to_call", 0),
                result.get("position", "MP"),
                str(result.get("recommendation", "")),  # Преобразуем Action в строку
                str(result.get("hand_strength", "")),
                result.get("drawing_odds", 0),
                result.get("pot_odds", 0),
                result.get("equity", 0)
            ))
            
            hand_id = cur.fetchone()[0]
            self.conn.commit()
            cur.close()
            print(f"[DB] Раздача #{hand_id} сохранена")
            return hand_id
            
        except Exception as e:
            print(f"[DB] Ошибка сохранения: {e}")
            self.conn.rollback()
            return None
    
    def get_recent_hands(self, limit=10):
        """Получить последние раздачи"""
        if not self.conn:
            return []
        
        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT * FROM hands 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
            
            hands = cur.fetchall()
            cur.close()
            return hands
        except Exception as e:
            print(f"[DB] Ошибка чтения: {e}")
            return []
    
    def get_statistics(self):
        """Получить общую статистику"""
        if not self.conn:
            return {}
        
        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT 
                    COUNT(*) as total_hands,
                    ROUND(AVG(pot_size)::numeric, 2) as avg_pot,
                    ROUND(AVG(equity)::numeric * 100, 1) as avg_equity
                FROM hands
            """)
            
            stats = cur.fetchone()
            cur.close()
            return stats
        except Exception as e:
            print(f"[DB] Ошибка статистики: {e}")
            return {}
    
    def _format_cards(self, cards):
        """Форматирование карт для хранения"""
        if not cards:
            return ""
        return " ".join(f"{r}{s}" for r, s in cards)
    
    def close(self):
        """Закрытие соединения"""
        if self.conn:
            self.conn.close()
            print("[DB] Соединение закрыто")