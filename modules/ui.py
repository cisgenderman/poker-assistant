"""
Модуль пользовательского интерфейса на Tkinter
(исправленная версия)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from typing import Callable, Dict, Optional, List, Tuple
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from modules.analyzer import PokerAnalyzer, Action, Street
from utils.poker_utils import parse_card, format_card, format_cards


class PokerAssistantUI:
    """Графический интерфейс покерного помощника"""
    
    # Цветовая схема
    COLORS = {
        "bg_dark": "#1a1a2e",
        "bg_medium": "#16213e",
        "bg_light": "#0f3460",
        "accent_fold": "#e74c3c",    # Красный
        "accent_call": "#2ecc71",    # Зеленый
        "accent_raise": "#e67e22",   # Оранжевый
        "accent_check": "#3498db",   # Синий
        "text_primary": "#ecf0f1",
        "text_secondary": "#bdc3c7",
        "card_player": "#f1c40f",    # Желтый
        "card_board": "#3498db",     # Синий
        "success": "#27ae60",
        "warning": "#f39c12",
        "error": "#c0392b"
    }
    
    def __init__(
        self,
        title: str = "♠ Poker Assistant ♥",
        window_size: Tuple[int, int] = (420, 550),
        always_on_top: bool = True,
        transparency: float = 0.92
    ):
        """
        Инициализация UI
        
        Args:
            title: заголовок окна
            window_size: размер окна (ширина, высота)
            always_on_top: окно поверх всех
            transparency: прозрачность (0.0 - 1.0)
        """
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{window_size[0]}x{window_size[1]}")
        self.root.configure(bg=self.COLORS["bg_dark"])
        
        # Настройки окна
        self.root.attributes('-topmost', always_on_top)
        self.root.attributes('-alpha', transparency)
        
        # Установка иконки (если есть)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Позиционирование окна (правый верхний угол)
        self._position_window(window_size)
        
        # Переменные для отображения
        self.action_var = tk.StringVar(value="ОЖИДАНИЕ")
        self.hand_var = tk.StringVar(value="—")
        self.board_var = tk.StringVar(value="—")
        self.street_var = tk.StringVar(value="PREFLOP")
        self.pot_var = tk.StringVar(value="$0")
        self.bet_var = tk.StringVar(value="$0")
        self.outs_var = tk.StringVar(value="0")
        self.draw_odds_var = tk.StringVar(value="0%")
        self.pot_odds_var = tk.StringVar(value="0%")
        self.equity_var = tk.StringVar(value="0%")
        self.reasoning_var = tk.StringVar(value="Готов к работе")
        self.position_var = tk.StringVar(value="MP")
        
        # Анализатор
        self.analyzer = PokerAnalyzer()
        
        # Режим работы
        self.demo_mode = True
        self.auto_refresh = False
        self.refresh_interval = 2000  # мс
        self.update_callback: Optional[Callable] = None
        
        # Демо-состояния
        self.demo_states = self._create_demo_states()
        self.demo_index = 0
        
        # Флаги
        self.is_running = True
        
        # Создание интерфейса
        self._create_widgets()
        self._create_menu()
        
        # Привязка горячих клавиш
        self._bind_hotkeys()
        
        # Запуск демо-режима
        if self.demo_mode:
            self._start_demo_mode()
    
    def _position_window(self, window_size: Tuple[int, int]):
        """Позиционирование окна в правом верхнем углу"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = screen_width - window_size[0] - 20
        y = 20
        
        self.root.geometry(f"+{x}+{y}")
    
    def _create_label_frame(self, parent, text: str) -> tk.Frame:
        """
        Создание кастомного LabelFrame с правильным цветом текста
        (обход ограничения стандартного LabelFrame)
        """
        # Внешний фрейм с границей
        outer = tk.Frame(parent, bg=self.COLORS["bg_medium"], bd=1, relief=tk.RIDGE)
        
        # Заголовок
        label = tk.Label(
            outer, 
            text=f" {text} ",
            font=("Arial", 10, "bold"),
            fg=self.COLORS["text_primary"],
            bg=self.COLORS["bg_medium"]
        )
        label.pack(anchor=tk.W, padx=10, pady=(0, 0))
        
        # Внутренний фрейм для содержимого
        inner = tk.Frame(outer, bg=self.COLORS["bg_dark"], padx=5, pady=5)
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=(0, 1))
        
        return inner, outer
    
    def _create_widgets(self):
        """Создание всех виджетов"""
        
        # Главный контейнер
        main_frame = tk.Frame(self.root, bg=self.COLORS["bg_dark"], padx=15, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === Заголовок ===
        title_frame = tk.Frame(main_frame, bg=self.COLORS["bg_dark"])
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(
            title_frame,
            text="♠ POKER ASSISTANT ♥",
            font=("Arial", 16, "bold"),
            fg=self.COLORS["text_primary"],
            bg=self.COLORS["bg_dark"]
        )
        title_label.pack(side=tk.LEFT)
        
        # Индикатор режима
        self.mode_label = tk.Label(
            title_frame,
            text="[ДЕМО]",
            font=("Arial", 9),
            fg=self.COLORS["warning"],
            bg=self.COLORS["bg_dark"]
        )
        self.mode_label.pack(side=tk.RIGHT, padx=5)
        
        # === Основная рекомендация ===
        action_frame = tk.Frame(main_frame, bg=self.COLORS["bg_medium"], relief=tk.RAISED, bd=2)
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.action_label = tk.Label(
            action_frame,
            textvariable=self.action_var,
            font=("Arial", 36, "bold"),
            fg=self.COLORS["text_primary"],
            bg=self.COLORS["bg_medium"],
            padx=20,
            pady=15
        )
        self.action_label.pack()
        
        # === Информация о раздаче ===
        info_inner, info_outer = self._create_label_frame(main_frame, "ИНФОРМАЦИЯ О РАЗДАЧЕ")
        info_outer.pack(fill=tk.X, pady=(0, 10))
        
        # Улица и позиция
        street_pos_frame = tk.Frame(info_inner, bg=self.COLORS["bg_dark"])
        street_pos_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(
            street_pos_frame, text="Улица:",
            font=("Arial", 10), fg=self.COLORS["text_secondary"],
            bg=self.COLORS["bg_dark"]
        ).pack(side=tk.LEFT)
        
        tk.Label(
            street_pos_frame, textvariable=self.street_var,
            font=("Arial", 10, "bold"), fg=self.COLORS["text_primary"],
            bg=self.COLORS["bg_dark"]
        ).pack(side=tk.LEFT, padx=(5, 20))
        
        tk.Label(
            street_pos_frame, text="Позиция:",
            font=("Arial", 10), fg=self.COLORS["text_secondary"],
            bg=self.COLORS["bg_dark"]
        ).pack(side=tk.LEFT)
        
        tk.Label(
            street_pos_frame, textvariable=self.position_var,
            font=("Arial", 10, "bold"), fg=self.COLORS["text_primary"],
            bg=self.COLORS["bg_dark"]
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Карты игрока
        player_frame = tk.Frame(info_inner, bg=self.COLORS["bg_dark"])
        player_frame.pack(fill=tk.X, padx=5, pady=2)
        
        tk.Label(
            player_frame, text="Ваши карты:",
            font=("Arial", 10), fg=self.COLORS["text_secondary"],
            bg=self.COLORS["bg_dark"]
        ).pack(side=tk.LEFT)
        
        tk.Label(
            player_frame, textvariable=self.hand_var,
            font=("Arial", 14, "bold"), fg=self.COLORS["card_player"],
            bg=self.COLORS["bg_dark"]
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Карты стола
        board_frame = tk.Frame(info_inner, bg=self.COLORS["bg_dark"])
        board_frame.pack(fill=tk.X, padx=5, pady=2)
        
        tk.Label(
            board_frame, text="Стол:",
            font=("Arial", 10), fg=self.COLORS["text_secondary"],
            bg=self.COLORS["bg_dark"]
        ).pack(side=tk.LEFT)
        
        tk.Label(
            board_frame, textvariable=self.board_var,
            font=("Arial", 12), fg=self.COLORS["card_board"],
            bg=self.COLORS["bg_dark"]
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # Банк и ставка
        money_frame = tk.Frame(info_inner, bg=self.COLORS["bg_dark"])
        money_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(
            money_frame, text="Банк:",
            font=("Arial", 10), fg=self.COLORS["text_secondary"],
            bg=self.COLORS["bg_dark"]
        ).pack(side=tk.LEFT)
        
        tk.Label(
            money_frame, textvariable=self.pot_var,
            font=("Arial", 10, "bold"), fg=self.COLORS["success"],
            bg=self.COLORS["bg_dark"]
        ).pack(side=tk.LEFT, padx=(5, 20))
        
        tk.Label(
            money_frame, text="Колл:",
            font=("Arial", 10), fg=self.COLORS["text_secondary"],
            bg=self.COLORS["bg_dark"]
        ).pack(side=tk.LEFT)
        
        tk.Label(
            money_frame, textvariable=self.bet_var,
            font=("Arial", 10, "bold"), fg=self.COLORS["warning"],
            bg=self.COLORS["bg_dark"]
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # === Статистика ===
        stats_inner, stats_outer = self._create_label_frame(main_frame, "СТАТИСТИКА")
        stats_outer.pack(fill=tk.X, pady=(0, 10))
        
        # Сетка для статистики
        stats_grid = tk.Frame(stats_inner, bg=self.COLORS["bg_dark"])
        stats_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # Ауты
        tk.Label(
            stats_grid, text="Ауты:",
            font=("Arial", 10), fg=self.COLORS["text_secondary"],
            bg=self.COLORS["bg_dark"]
        ).grid(row=0, column=0, sticky="w", padx=(0, 20), pady=3)
        
        tk.Label(
            stats_grid, textvariable=self.outs_var,
            font=("Arial", 12, "bold"), fg=self.COLORS["text_primary"],
            bg=self.COLORS["bg_dark"]
        ).grid(row=0, column=1, sticky="w", pady=3)
        
        # Шансы на улучшение
        tk.Label(
            stats_grid, text="Шансы на улучшение:",
            font=("Arial", 10), fg=self.COLORS["text_secondary"],
            bg=self.COLORS["bg_dark"]
        ).grid(row=1, column=0, sticky="w", padx=(0, 20), pady=3)
        
        tk.Label(
            stats_grid, textvariable=self.draw_odds_var,
            font=("Arial", 12, "bold"), fg=self.COLORS["success"],
            bg=self.COLORS["bg_dark"]
        ).grid(row=1, column=1, sticky="w", pady=3)
        
        # Шансы банка
        tk.Label(
            stats_grid, text="Шансы банка:",
            font=("Arial", 10), fg=self.COLORS["text_secondary"],
            bg=self.COLORS["bg_dark"]
        ).grid(row=2, column=0, sticky="w", padx=(0, 20), pady=3)
        
        tk.Label(
            stats_grid, textvariable=self.pot_odds_var,
            font=("Arial", 12, "bold"), fg=self.COLORS["warning"],
            bg=self.COLORS["bg_dark"]
        ).grid(row=2, column=1, sticky="w", pady=3)
        
        # Эквити
        tk.Label(
            stats_grid, text="Эквити:",
            font=("Arial", 10), fg=self.COLORS["text_secondary"],
            bg=self.COLORS["bg_dark"]
        ).grid(row=3, column=0, sticky="w", padx=(0, 20), pady=3)
        
        tk.Label(
            stats_grid, textvariable=self.equity_var,
            font=("Arial", 12, "bold"), fg=self.COLORS["accent_check"],
            bg=self.COLORS["bg_dark"]
        ).grid(row=3, column=1, sticky="w", pady=3)
        
        # === Обоснование ===
        reason_inner, reason_outer = self._create_label_frame(main_frame, "ОБОСНОВАНИЕ")
        reason_outer.pack(fill=tk.X, pady=(0, 10))
        
        reason_label = tk.Label(
            reason_inner,
            textvariable=self.reasoning_var,
            font=("Arial", 9),
            fg=self.COLORS["text_secondary"],
            bg=self.COLORS["bg_dark"],
            wraplength=350,
            justify=tk.LEFT,
            padx=5,
            pady=8
        )
        reason_label.pack(fill=tk.X)
        
        # === Кнопки управления ===
        control_frame = tk.Frame(main_frame, bg=self.COLORS["bg_dark"])
        control_frame.pack(fill=tk.X)
        
        # Кнопка обновления
        self.refresh_btn = tk.Button(
            control_frame,
            text="⟳ ОБНОВИТЬ",
            command=self._manual_refresh,
            font=("Arial", 10, "bold"),
            bg=self.COLORS["bg_light"],
            fg=self.COLORS["text_primary"],
            activebackground=self.COLORS["bg_medium"],
            activeforeground=self.COLORS["text_primary"],
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2"
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Кнопка автообновления
        self.auto_btn = tk.Button(
            control_frame,
            text="▶ АВТО",
            command=self._toggle_auto_refresh,
            font=("Arial", 10, "bold"),
            bg=self.COLORS["bg_light"],
            fg=self.COLORS["text_primary"],
            activebackground=self.COLORS["bg_medium"],
            activeforeground=self.COLORS["text_primary"],
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2"
        )
        self.auto_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка следующего демо
        self.next_demo_btn = tk.Button(
            control_frame,
            text="→ ДЕМО",
            command=self._next_demo_state,
            font=("Arial", 10, "bold"),
            bg=self.COLORS["bg_light"],
            fg=self.COLORS["text_primary"],
            activebackground=self.COLORS["bg_medium"],
            activeforeground=self.COLORS["text_primary"],
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2"
        )
        self.next_demo_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка выхода
        exit_btn = tk.Button(
            control_frame,
            text="✕ ВЫХОД",
            command=self.quit,
            font=("Arial", 10, "bold"),
            bg=self.COLORS["error"],
            fg=self.COLORS["text_primary"],
            activebackground="#c0392b",
            activeforeground=self.COLORS["text_primary"],
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2"
        )
        exit_btn.pack(side=tk.RIGHT)
        
        # Статус-бар
        self.status_var = tk.StringVar(value="Демо-режим | F5 - обновить | ← → - переключение демо")
        status_bar = tk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("Arial", 8),
            fg=self.COLORS["text_secondary"],
            bg=self.COLORS["bg_dark"],
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def _create_menu(self):
        """Создание меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Обновить", command=self._manual_refresh, accelerator="F5")
        file_menu.add_command(label="Автообновление", command=self._toggle_auto_refresh, accelerator="Ctrl+R")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.quit, accelerator="Ctrl+Q")
        
        # Меню Режим
        mode_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Режим", menu=mode_menu)
        mode_menu.add_command(label="Демо-режим", command=lambda: self._set_mode(True))
        mode_menu.add_command(label="Реальный режим", command=lambda: self._set_mode(False))
        mode_menu.add_separator()
        mode_menu.add_command(label="Следующее демо", command=self._next_demo_state, accelerator="→")
        mode_menu.add_command(label="Предыдущее демо", command=self._prev_demo_state, accelerator="←")
        
        # Меню Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="Горячие клавиши", command=self._show_hotkeys)
        help_menu.add_command(label="О программе", command=self._show_about)
    
    def _bind_hotkeys(self):
        """Привязка горячих клавиш"""
        self.root.bind('<F5>', lambda e: self._manual_refresh())
        self.root.bind('<Control-r>', lambda e: self._toggle_auto_refresh())
        self.root.bind('<Control-q>', lambda e: self.quit())
        self.root.bind('<Right>', lambda e: self._next_demo_state())
        self.root.bind('<Left>', lambda e: self._prev_demo_state())
    
    def _create_demo_states(self) -> List[Dict]:
        """Создание демонстрационных состояний"""
        return [
            {
                "name": "Префлоп: AKs на баттоне",
                "player_cards": [parse_card("Ah"), parse_card("Kh")],
                "board_cards": [],
                "pot_size": 10.0,
                "bet_to_call": 2.0,
                "position": "BTN",
                "facing_raise": False
            },
            {
                "name": "Префлоп: Мусор с UTG",
                "player_cards": [parse_card("7c"), parse_card("2d")],
                "board_cards": [],
                "pot_size": 5.0,
                "bet_to_call": 0.0,
                "position": "UTG",
                "facing_raise": False
            },
            {
                "name": "Флоп: Флеш-дро + гатшот",
                "player_cards": [parse_card("Ah"), parse_card("9h")],
                "board_cards": [parse_card("Kh"), parse_card("7h"), parse_card("2c")],
                "pot_size": 50.0,
                "bet_to_call": 10.0,
                "position": "MP",
                "facing_raise": True
            },
            {
                "name": "Флоп: Топ-пара топ-кикер",
                "player_cards": [parse_card("As"), parse_card("Kd")],
                "board_cards": [parse_card("Ad"), parse_card("7h"), parse_card("2c")],
                "pot_size": 40.0,
                "bet_to_call": 20.0,
                "position": "CO",
                "facing_raise": True
            },
            {
                "name": "Терн: Открытое стрит-дро",
                "player_cards": [parse_card("Jh"), parse_card("Td")],
                "board_cards": [parse_card("9c"), parse_card("8s"), parse_card("2h"), parse_card("3d")],
                "pot_size": 60.0,
                "bet_to_call": 15.0,
                "position": "BTN",
                "facing_raise": True
            },
            {
                "name": "Ривер: Готовый флеш",
                "player_cards": [parse_card("Ah"), parse_card("Th")],
                "board_cards": [parse_card("Kh"), parse_card("7h"), parse_card("2h"), parse_card("8d"), parse_card("Qd")],
                "pot_size": 100.0,
                "bet_to_call": 30.0,
                "position": "CO",
                "facing_raise": True
            },
            {
                "name": "Префлоп: Средняя пара с MP",
                "player_cards": [parse_card("9c"), parse_card("9d")],
                "board_cards": [],
                "pot_size": 0.0,
                "bet_to_call": 0.0,
                "position": "MP",
                "facing_raise": False
            }
        ]
    
    def _start_demo_mode(self):
        """Запуск демо-режима"""
        self.demo_mode = True
        self.mode_label.config(text="[ДЕМО]", fg=self.COLORS["warning"])
        self.status_var.set("Демо-режим | F5 - обновить | ← → - переключение демо")
        self._load_demo_state(0)
    
    def _load_demo_state(self, index: int):
        """Загрузка демо-состояния по индексу"""
        if 0 <= index < len(self.demo_states):
            self.demo_index = index
            state = self.demo_states[index]
            
            # Анализ
            result = self.analyzer.analyze_situation(
                player_cards=state["player_cards"],
                board_cards=state["board_cards"],
                pot_size=state["pot_size"],
                bet_to_call=state["bet_to_call"],
                position=state["position"],
                facing_raise=state.get("facing_raise", False)
            )
            
            # Добавляем название состояния
            result["demo_name"] = state["name"]
            
            # Обновление UI
            self.update_display(result)
            self.status_var.set(f"Демо {index + 1}/{len(self.demo_states)}: {state['name']}")
    
    def _next_demo_state(self):
        """Следующее демо-состояние"""
        if self.demo_mode:
            next_index = (self.demo_index + 1) % len(self.demo_states)
            self._load_demo_state(next_index)
    
    def _prev_demo_state(self):
        """Предыдущее демо-состояние"""
        if self.demo_mode:
            prev_index = (self.demo_index - 1) % len(self.demo_states)
            self._load_demo_state(prev_index)
    
    def _manual_refresh(self):
        """Ручное обновление"""
        if self.update_callback:
            try:
                data = self.update_callback()
                if data:
                    self.update_display(data)
                    self.status_var.set("Обновлено")
            except Exception as e:
                self.status_var.set(f"Ошибка: {e}")
        elif self.demo_mode:
            self._load_demo_state(self.demo_index)
    
    def _toggle_auto_refresh(self):
        """Переключение автообновления"""
        self.auto_refresh = not self.auto_refresh
        
        if self.auto_refresh:
            self.auto_btn.config(text="■ СТОП", bg=self.COLORS["warning"])
            self.status_var.set("Автообновление включено")
            self._auto_refresh_loop()
        else:
            self.auto_btn.config(text="▶ АВТО", bg=self.COLORS["bg_light"])
            self.status_var.set("Автообновление выключено")
    
    def _auto_refresh_loop(self):
        """Цикл автообновления"""
        if self.auto_refresh and self.is_running:
            self._manual_refresh()
            self.root.after(self.refresh_interval, self._auto_refresh_loop)
    
    def _set_mode(self, demo_mode: bool):
        """Переключение режима"""
        self.demo_mode = demo_mode
        
        if demo_mode:
            self._start_demo_mode()
            self.next_demo_btn.config(state=tk.NORMAL)
        else:
            self.mode_label.config(text="[РЕАЛ]", fg=self.COLORS["success"])
            self.status_var.set("Реальный режим | F5 - обновить")
            self.next_demo_btn.config(state=tk.DISABLED)
    
    def update_display(self, data: Dict):
        """
        Обновление отображения данными анализа
        
        Args:
            data: словарь с результатами анализа
        """
        if not data:
            return
        
        # Рекомендация
        action = data.get("recommendation")
        if action:
            self.action_var.set(action.value)
            
            # Цветовая индикация
            action_colors = {
                Action.FOLD: self.COLORS["accent_fold"],
                Action.CALL: self.COLORS["accent_call"],
                Action.RAISE: self.COLORS["accent_raise"],
                Action.CHECK: self.COLORS["accent_check"]
            }
            self.action_label.config(fg=action_colors.get(action, self.COLORS["text_primary"]))
        
        # Карты
        player_cards = data.get("player_cards", [])
        if player_cards:
            self.hand_var.set(format_cards(player_cards))
        else:
            self.hand_var.set("—")
        
        board_cards = data.get("board_cards", [])
        if board_cards:
            self.board_var.set(format_cards(board_cards))
        else:
            self.board_var.set("—")
        
        # Улица
        street = data.get("street")
        if street:
            street_names = {
                Street.PREFLOP: "ПРЕФЛОП",
                Street.FLOP: "ФЛОП",
                Street.TURN: "ТЕРН",
                Street.RIVER: "РИВЕР"
            }
            self.street_var.set(street_names.get(street, str(street)))
        
        # Позиция
        pos = data.get("position", "MP")
        pos_names = {
            "BTN": "Баттон", "SB": "МБ", "BB": "ББ",
            "UTG": "UTG", "MP": "MP", "CO": "CO"
        }
        self.position_var.set(pos_names.get(pos, pos))
        
        # Деньги
        self.pot_var.set(f"${data.get('pot_size', 0):.2f}")
        self.bet_var.set(f"${data.get('bet_to_call', 0):.2f}")
        
        # Статистика
        self.outs_var.set(str(data.get("outs", 0)))
        self.draw_odds_var.set(f"{data.get('drawing_odds', 0):.1%}")
        self.pot_odds_var.set(f"{data.get('pot_odds', 0):.1%}")
        self.equity_var.set(f"{data.get('equity', 0):.1%}")
        
        # Обоснование
        reasoning = data.get("reasoning", "")
        if data.get("demo_name"):
            reasoning = f"[{data['demo_name']}]\n{reasoning}"
        self.reasoning_var.set(reasoning)
    
    def set_update_callback(self, callback: Callable):
        """Установка функции обратного вызова для получения данных"""
        self.update_callback = callback
    
    def _show_hotkeys(self):
        """Показать горячие клавиши"""
        hotkeys_text = """
        Горячие клавиши:
        
        F5          - Обновить анализ
        Ctrl+R      - Включить/выключить автообновление
        Ctrl+Q      - Выход
        →           - Следующее демо
        ←           - Предыдущее демо
        """
        messagebox.showinfo("Горячие клавиши", hotkeys_text)
    
    def _show_about(self):
        """Показать информацию о программе"""
        about_text = """
        Poker Assistant v0.3.0
        
        Прототип приложения-помощника для игры в покер.
        
        Разработано в рамках курсовой работы.
        
        © 2025
        """
        messagebox.showinfo("О программе", about_text)
    
    def run(self):
        """Запуск главного цикла"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit()
    
    def quit(self):
        """Завершение работы"""
        self.is_running = False
        self.auto_refresh = False
        self.root.quit()
        self.root.destroy()


# Тестирование UI
if __name__ == "__main__":
    print("Запуск Poker Assistant UI...")
    print("Режим: Демо")
    print("Для выхода закройте окно или нажмите Ctrl+Q")
    
    ui = PokerAssistantUI()
    ui.run()