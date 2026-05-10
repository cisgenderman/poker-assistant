#!/usr/bin/env python3
"""
Poker Assistant - Main Application
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from modules.ui import PokerAssistantUI
from modules.analyzer import PokerAnalyzer
from utils.database import Database


def create_capture_callback(capture_module, analyzer, db, window_title=None):
    """
    Создание callback-функции для обновления UI из модуля захвата
    """
    def callback():
        # Захват состояния игры
        game_state = capture_module.get_game_state(window_title)
        
        if not game_state.get("success"):
            return None
            
        # Анализ ситуации
        result = analyzer.analyze_situation(
            player_cards=game_state.get("player_cards", []),
            board_cards=game_state.get("board_cards", []),
            pot_size=game_state.get("pot_size", 0.0),
            bet_to_call=game_state.get("bet_to_call", 0.0),
            position=game_state.get("position", "MP"),
            facing_raise=game_state.get("bet_to_call", 0) > 0
        )
        
        # Добавляем исходные данные для отображения
        result["pot_size"] = game_state.get("pot_size", 0.0)
        result["bet_to_call"] = game_state.get("bet_to_call", 0.0)
        
        # Сохраняем в базу данных
        if game_state.get("player_cards") or game_state.get("board_cards"):
            db.save_hand(
                game_state.get("player_cards", []),
                game_state.get("board_cards", []),
                result
            )
        
        return result
        
    return callback


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="Poker Assistant - Покерный помощник",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python main.py                    # Запуск в демо-режиме
  python main.py --real             # Запуск в реальном режиме
  python main.py --real --window "PokerStars"  # С указанием окна
  python main.py --calibrate        # Калибровка регионов
  python main.py --test             # Запуск тестов
  python main.py --stats            # Показать статистику из БД
        """
    )
    
    parser.add_argument(
        "--real", "-r",
        action="store_true",
        help="Запуск в реальном режиме (захват с экрана)"
    )
    parser.add_argument(
        "--window", "-w",
        type=str,
        help="Заголовок окна покерного клиента (например, 'PokerStars')"
    )
    parser.add_argument(
        "--calibrate", "-c",
        action="store_true",
        help="Запуск калибровки регионов"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Режим отладки (сохранение изображений)"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Запуск тестов анализатора"
    )
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="Показать статистику из базы данных"
    )
    
    args = parser.parse_args()
    
    if args.test:
        from modules.analyzer import test_analyzer
        test_analyzer()
        return
    
    if args.stats:
        db = Database()
        stats = db.get_statistics()
        hands = db.get_recent_hands(5)
        print("\n" + "=" * 50)
        print("СТАТИСТИКА ИЗ БАЗЫ ДАННЫХ")
        print("=" * 50)
        print(f"Всего раздач: {stats.get('total_hands', 0)}")
        print(f"Средний банк: ${stats.get('avg_pot', 0)}")
        print(f"Среднее эквити: {stats.get('avg_equity', 0)}%")
        print(f"\nПоследние 5 раздач:")
        for hand in hands:
            print(f"  #{hand['id']}: {hand['player_cards']} | {hand['board_cards']} | {hand['recommendation']} | Банк: ${hand['pot_size']:.2f}")
        db.close()
        return
        
    if args.calibrate:
        from modules.capture import ScreenCapture
        capture = ScreenCapture()
        capture.calibrate_regions(args.window)
        return
    
    print("=" * 50)
    print("♠  POKER ASSISTANT v0.4.0  ♥")
    print("=" * 50)
    
    # Подключаем базу данных
    print("[INFO] Подключение к базе данных...")
    db = Database()
    
    # Создание UI
    ui = PokerAssistantUI()
    analyzer = PokerAnalyzer()
    
    if args.real:
        print("[INFO] Запуск в РЕАЛЬНОМ режиме")
        
        try:
            from modules.capture import ScreenCapture
            capture = ScreenCapture()
            
            if args.debug:
                capture.set_debug_mode(True)
                print("[DEBUG] Режим отладки включен (изображения сохраняются в /debug)")
                
            # Проверка шаблонов
            if not capture.rank_templates and not capture.templates:
                print("\n[WARNING] Шаблоны карт не найдены!")
                print("[INFO] Продолжение в демо-режиме...")
                ui._set_mode(demo_mode=True)
            else:
                # Установка callback для захвата (с передачей db)
                callback = create_capture_callback(capture, analyzer, db, args.window)
                ui.set_update_callback(callback)
                ui._set_mode(demo_mode=False)
                
                if args.window:
                    print(f"[INFO] Поиск окна: '{args.window}'")
                    
        except ImportError as e:
            print(f"[ERROR] Не удалось загрузить модуль захвата: {e}")
            print("[INFO] Продолжение в демо-режиме...")
            ui._set_mode(demo_mode=True)
        except Exception as e:
            print(f"[ERROR] Ошибка инициализации захвата: {e}")
            print("[INFO] Продолжение в демо-режиме...")
            ui._set_mode(demo_mode=True)
    else:
        print("[INFO] Запуск в ДЕМО режиме")
        ui._set_mode(demo_mode=True)
    
    print("\n[INFO] Горячие клавиши:")
    print("       F5 - обновить")
    print("       Ctrl+R - автообновление")
    print("       ←/→ - переключение демо")
    print("       Ctrl+Q - выход")
    print("=" * 50)
    
    # Запуск UI
    ui.run()
    
    # Закрываем соединение с БД
    db.close()
    
    print("\n[INFO] Poker Assistant завершен")


if __name__ == "__main__":
    main()