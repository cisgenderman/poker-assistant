"""
Модуль захвата и распознавания игрового состояния
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageGrab
import pytesseract
import pyautogui
from typing import List, Tuple, Dict, Optional, Any
import re
import sys
from pathlib import Path
import time

# Добавляем путь к конфигу
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config.settings import (
    TEMPLATES_DIR, 
    OCR_CONFIDENCE_THRESHOLD, 
    TESSERACT_PATH,
    TEMPLATE_MATCH_THRESHOLD
)

# Настройка Tesseract
if TESSERACT_PATH and Path(TESSERACT_PATH).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


class ScreenCapture:
    """
    Класс для захвата экрана и распознавания игровых элементов
    """
    
    # Стандартные регионы для поиска (в процентах от размера окна)
    DEFAULT_REGIONS = {
        "player_cards": (0.455, 0.680, 0.091, 0.150),
        "board_cards": (0.386, 0.419, 0.233, 0.111),
        "pot": (0.487, 0.530, 0.025, 0.020),
        "bet": (0.455, 0.770, 0.091, 0.025),
    }
    
    # Точные координаты карт игрока (абсолютные, для 3840x2160)
    PLAYER_CARD_BOUNDS = [
        (1753, 1812),   # Карта 1 (ранг X)
        (1930, 1989),   # Карта 2 (ранг X)
    ]

    PLAYER_X_SHIFT = [0, 0]  # Коррекция X (подберите, если нужно)

    # Y-координаты ранга и масти внутри карты игрока
    PLAYER_RANK_Y = (0, 80)    # Y1:Y2 для ранга
    PLAYER_SUIT_Y = (90, 145)  # Y1:Y2 для масти

    # Точные координаты карт стола (абсолютные, для 3840x2160)
    CARD_BOUNDS = [
        (1482, 1653),  # Карта 1
        (1660, 1828),  # Карта 2
        (1834, 2004),  # Карта 3
        (2012, 2180),  # Карта 4
        (2187, 2355),  # Карта 5
    ]
    
    X_SHIFT = [0, -4, -4, -6, -6]  # Коррекция X для каждой карты
    
    def __init__(self):
        self.screen = None
        self.templates = {}
        self.window_region = None
        self.debug_mode = False
        self.rank_templates = {}
        self.suit_templates = {}
        
        # Загружаем символьные шаблоны
        self._load_symbol_templates()
        
        # Добавляем атрибут для доступа извне
        self.TEMPLATES_DIR = TEMPLATES_DIR
        
        # Создаем папку для шаблонов, если её нет
        TEMPLATES_DIR.mkdir(exist_ok=True)
        
        # Загружаем старые шаблоны карт (для обратной совместимости)
        self._load_card_templates()
        
    def _load_card_templates(self):
        """Загрузка шаблонов карт из папки templates (старый метод)"""
        if not TEMPLATES_DIR.exists():
            print(f"[WARNING] Папка с шаблонами не найдена: {TEMPLATES_DIR}")
            return
        
        templates_path = str(TEMPLATES_DIR)
        
        for filename in os.listdir(templates_path):
            if filename.lower().endswith('.png'):
                card_name = filename[:-4].upper()
                filepath = os.path.join(templates_path, filename)
                
                try:
                    with open(filepath, 'rb') as f:
                        img_bytes = bytearray(f.read())
                        img_array = np.asarray(img_bytes, dtype=np.uint8)
                        template = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        
                    if template is not None:
                        self.templates[card_name] = template
                        print(f"[INFO] Загружен шаблон: {card_name}")
                except Exception as e:
                    print(f"[ERROR] Ошибка загрузки {filename}: {e}")
                    
        print(f"[INFO] Всего загружено шаблонов карт: {len(self.templates)}")

    def _load_symbol_templates(self):
        """Загрузка шаблонов рангов и мастей"""
        self.rank_templates = {}
        self.suit_templates = {}
        
        # Для карт стола
        rank_dir = Path("config/rank_templates")
        suit_dir = Path("config/suit_templates")
        
        # Для карт игрока
        self.rank_templates_player = {}
        self.suit_templates_player = {}
        rank_player_dir = Path("config/rank_templates_player")
        suit_player_dir = Path("config/suit_templates_player")
        
        # Загружаем для стола
        if rank_dir.exists():
            for f in rank_dir.glob("*.png"):
                self.rank_templates[f.stem.upper()] = cv2.imread(str(f))
        if suit_dir.exists():
            for f in suit_dir.glob("*.png"):
                self.suit_templates[f.stem.lower()] = cv2.imread(str(f))
        
        # Загружаем для игрока
        if rank_player_dir.exists():
            for f in rank_player_dir.glob("*.png"):
                self.rank_templates_player[f.stem.upper()] = cv2.imread(str(f))
        if suit_player_dir.exists():
            for f in suit_player_dir.glob("*.png"):
                self.suit_templates_player[f.stem.lower()] = cv2.imread(str(f))
        
        print(f"[INFO] Загружено рангов: {len(self.rank_templates)} (стол) + {len(self.rank_templates_player)} (игрок)")
        print(f"[INFO] Загружено мастей: {len(self.suit_templates)} (стол) + {len(self.suit_templates_player)} (игрок)")
        
    def set_debug_mode(self, enabled: bool = True):
        """Включение/выключение режима отладки"""
        self.debug_mode = enabled
        
    def capture_full_screen(self) -> np.ndarray:
        """Захват всего экрана"""
        screenshot = ImageGrab.grab()
        self.screen = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        return self.screen
    
    def capture_region(self, region: Tuple[int, int, int, int]) -> np.ndarray:
        """Захват области экрана"""
        x, y, w, h = region
        screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def find_poker_window(self, window_title: str = None) -> Optional[Tuple[int, int, int, int]]:
        """Поиск окна покерного клиента"""
        if window_title:
            try:
                windows = pyautogui.getWindowsWithTitle(window_title)
                if windows:
                    window = windows[0]
                    return (window.left, window.top, window.width, window.height)
            except Exception as e:
                print(f"[ERROR] Ошибка поиска окна: {e}")
        return None
    
    def get_game_state(self, window_title: str = None) -> Dict[str, Any]:
        """Получение полного состояния игры"""
        result = {
            "player_cards": [],
            "board_cards": [],
            "pot_size": 0.0,
            "bet_to_call": 0.0,
            "position": "MP",
            "success": False,
            "errors": []
        }
        
        try:
            # Поиск окна или захват всего экрана
            if window_title:
                window_rect = self.find_poker_window(window_title)
                if window_rect:
                    self.window_region = window_rect
                    screen = self.capture_region(window_rect)
                else:
                    result["errors"].append(f"Окно '{window_title}' не найдено")
                    screen = self.capture_full_screen()
            else:
                screen = self.capture_full_screen()
                
            height, width = screen.shape[:2]
            
            if self.debug_mode:
                self._save_debug_image(screen, "full_screen")
            
            # Получаем абсолютные координаты регионов
            board_x, board_y, board_w, board_h = self._get_region_coords(width, height, "board_cards")
            player_x, player_y, player_w, player_h = self._get_region_coords(width, height, "player_cards")
            pot_x, pot_y, pot_w, pot_h = self._get_region_coords(width, height, "pot")
            bet_x, bet_y, bet_w, bet_h = self._get_region_coords(width, height, "bet")
            
            # Распознавание карт игрока (пока старым методом)
            player_cards = self._detect_player_cards_accurate(
                screen,
                player_x, player_y, player_w, player_h
            )
            result["player_cards"] = player_cards[:2]
            
            # Распознавание карт стола (НОВЫЙ ТОЧНЫЙ МЕТОД)
            board_cards = self._detect_board_cards_accurate(
                screen,
                board_x, board_y, board_w, board_h
            )
            result["board_cards"] = board_cards[:5]
            
            # Распознавание чисел (банк, ставка)
            pot_text = self._extract_text_from_region(screen, (pot_x, pot_y, pot_w, pot_h))
            ####
            if self.debug_mode:
                pot_roi = screen[pot_y:pot_y+pot_h, pot_x:pot_x+pot_w]
                cv2.imwrite("debug_pot_roi.png", pot_roi)
                print(f"[DEBUG] Pot region: x={pot_x}, y={pot_y}, w={pot_w}, h={pot_h}")
                print(f"[DEBUG] get_game_state: pot_text = '{pot_text}'")
            ######
            print(f"[DEBUG] ДО вызова _parse_number, pot_text = '{pot_text}'")
            result["pot_size"] = self._parse_number(pot_text)
            print(f"[DEBUG] ПОСЛЕ вызова _parse_number, result = {result['pot_size']}")
            
            # bet_text = self._extract_text_from_region(screen, (bet_x, bet_y, bet_w, bet_h))
            # result["bet_to_call"] = self._parse_number(bet_text)
            result["bet_to_call"] = 0.0
            
            # Проверка успешности
            if result["player_cards"] or result["board_cards"]:
                result["success"] = True
                
        except Exception as e:
            result["errors"].append(f"Ошибка захвата: {str(e)}")
            
        return result
    
    def _detect_player_cards_accurate(
        self,
        image: np.ndarray,
        player_x: int,
        player_y: int,
        player_w: int,
        player_h: int
    ) -> List[Tuple[str, str]]:
        """Точное распознавание карт игрока по символам"""
        
        # Захватываем 
        y1 = max(0, player_y)
        player_roi = image[y1:player_y + player_h, player_x:player_x + player_w]
        
        if self.debug_mode:
            self._save_debug_image(player_roi, "player_roi_full")
        
        THRESHOLD_RANK = 0.45
        THRESHOLD_SUIT = 0.45
        cards = []
        
        for i, (abs_x1, abs_x2) in enumerate(self.PLAYER_CARD_BOUNDS):
            rel_x1 = abs_x1 - player_x
            rel_x2 = abs_x2 - player_x
            
            if rel_x1 < 0 or rel_x2 > player_roi.shape[1]:
                continue
            
            # Берём карту с запасом по Y
            card_roi = player_roi[:, rel_x1:rel_x2]
            
            if card_roi.size == 0:
                continue
            
            if self.debug_mode:
                cv2.imwrite(f"debug_player_card_{i+1}_card.png", card_roi)
            
            # Ранг — в верхней части карты
            rank_roi = card_roi[0:75, 5:card_roi.shape[1]-5]
            # Масть — ниже ранга
            suit_roi = card_roi[90:145, 5:card_roi.shape[1]-5]
            
            if rank_roi.size == 0 or suit_roi.size == 0:
                continue
            
            if self.debug_mode:
                cv2.imwrite(f"debug_player_card_{i+1}_rank.png", rank_roi)
                cv2.imwrite(f"debug_player_card_{i+1}_suit.png", suit_roi)
            
            # Поиск ранга
            best_rank = "?"
            best_rank_val = 0
            for rank, template in self.rank_templates_player.items():  
                if template.shape[0] > rank_roi.shape[0] or template.shape[1] > rank_roi.shape[1]:
                    continue
                result = cv2.matchTemplate(rank_roi, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                if max_val > best_rank_val:
                    best_rank_val = max_val
                    best_rank = rank
            
            # Поиск масти
            best_suit = "?"
            best_suit_val = 0
            for suit, template in self.suit_templates_player.items():
                if template.shape[0] > suit_roi.shape[0] or template.shape[1] > suit_roi.shape[1]:
                    continue
                result = cv2.matchTemplate(suit_roi, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                if max_val > best_suit_val:
                    best_suit_val = max_val
                    best_suit = suit
            
            # Проверка порогов
            if best_rank_val >= THRESHOLD_RANK and best_suit_val >= THRESHOLD_SUIT:
                cards.append((best_rank, best_suit))
                print(f"[INFO] Карта игрока {i+1}: {best_rank}{best_suit} (ранг:{best_rank_val:.2f}, масть:{best_suit_val:.2f})")
            elif best_suit_val >= THRESHOLD_SUIT:
                cards.append(("?", best_suit))
                print(f"[INFO] Карта игрока {i+1}: ?{best_suit} (ранг:{best_rank_val:.2f}, масть:{best_suit_val:.2f})")
        
        return cards

    def _detect_board_cards_accurate(
        self,
        image: np.ndarray,
        board_x: int,
        board_y: int,
        board_w: int,
        board_h: int
    ) -> List[Tuple[str, str]]:
        """Точное распознавание карт стола по символам"""
        
        # Захватываем выше на 40 пикселей
        y1 = max(0, board_y - 40)
        board_roi = image[y1:board_y + board_h, board_x:board_x + board_w]
        
        if self.debug_mode:
            self._save_debug_image(board_roi, "board_roi_accurate")
        
        THRESHOLD_RANK = 0.45
        THRESHOLD_SUIT = 0.45
        cards = []
        
        for i, (abs_x1, abs_x2) in enumerate(self.CARD_BOUNDS):
            rel_x1 = abs_x1 - board_x
            rel_x2 = abs_x2 - board_x
            
            if rel_x1 < 0 or rel_x2 > board_roi.shape[1]:
                continue
                
            card_roi = board_roi[:, rel_x1:rel_x2]
            
            # Сохраняем всю карту
            if self.debug_mode:
                cv2.imwrite(f"debug_card_{i+1}_full.png", card_roi)
            
            shift = self.X_SHIFT[i]
            sym_x1 = max(0, 10 + shift)
            sym_x2 = min(card_roi.shape[1], 65 + shift)
            
            if sym_x2 <= sym_x1:
                continue
            
            # Регионы ранга и масти
            rank_roi = card_roi[0:90, sym_x1:sym_x2]
            suit_roi = card_roi[100:160, sym_x1:sym_x2]
            
            # Сохраняем регионы для отладки
            if self.debug_mode:
                cv2.imwrite(f"debug_card_{i+1}_rank_roi.png", rank_roi)
                cv2.imwrite(f"debug_card_{i+1}_suit_roi.png", suit_roi)
            
            # Поиск ранга
            best_rank = "?"
            best_rank_val = 0
            for rank, template in self.rank_templates.items():
                if template.shape[0] > rank_roi.shape[0] or template.shape[1] > rank_roi.shape[1]:
                    continue
                result = cv2.matchTemplate(rank_roi, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                if max_val > best_rank_val:
                    best_rank_val = max_val
                    best_rank = rank
            
            # Поиск масти
            best_suit = "?"
            best_suit_val = 0
            for suit, template in self.suit_templates.items():
                if template.shape[0] > suit_roi.shape[0] or template.shape[1] > suit_roi.shape[1]:
                    continue
                result = cv2.matchTemplate(suit_roi, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                if max_val > best_suit_val:
                    best_suit_val = max_val
                    best_suit = suit
            
            # Проверка порогов
            if best_rank_val >= THRESHOLD_RANK and best_suit_val >= THRESHOLD_SUIT:
                cards.append((best_rank, best_suit))
                print(f"[INFO] Карта {i+1}: {best_rank}{best_suit} (ранг:{best_rank_val:.2f}, масть:{best_suit_val:.2f})")
            elif best_suit_val >= THRESHOLD_SUIT:
                cards.append(("?", best_suit))
                print(f"[INFO] Карта {i+1}: ?{best_suit} (ранг:{best_rank_val:.2f}, масть:{best_suit_val:.2f})")
        
        return cards
    
    def _get_region_coords(
        self, 
        width: int, 
        height: int, 
        region_name: str
    ) -> Tuple[int, int, int, int]:
        """Получение абсолютных координат региона"""
        rx, ry, rw, rh = self.DEFAULT_REGIONS.get(region_name, (0, 0, 1, 1))
        
        x = int(width * rx)
        y = int(height * ry)
        w = int(width * rw)
        h = int(height * rh)
        
        return (x, y, w, h)
    
    def _detect_cards_in_region(
        self,
        image: np.ndarray,
        region: Tuple[int, int, int, int],
        card_type: str
    ) -> List[Tuple[str, str]]:
        """Обнаружение карт в указанной области (старый метод, для карт игрока)"""
        x, y, w, h = region
        
        img_h, img_w = image.shape[:2]
        x = max(0, min(x, img_w - 1))
        y = max(0, min(y, img_h - 1))
        w = min(w, img_w - x)
        h = min(h, img_h - y)
        
        if w <= 0 or h <= 0:
            return []
            
        roi = image[y:y+h, x:x+w]
        
        if self.debug_mode:
            self._save_debug_image(roi, f"region_{card_type}")
        
        cards = []
        
        if self.templates:
            template_cards = self._find_cards_by_template(roi)
            cards.extend(template_cards)
        
        return cards
    
    def _find_cards_by_template(self, image: np.ndarray) -> List[Tuple[str, str]]:
        """Поиск карт методом сравнения с шаблонами (старый метод)"""
        found_cards = []
        
        for card_name, template in self.templates.items():
            if template.shape[0] > image.shape[0] or template.shape[1] > image.shape[1]:
                continue
                
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= TEMPLATE_MATCH_THRESHOLD)
            
            for pt in zip(*locations[::-1]):
                if len(card_name) >= 2:
                    rank = card_name[0]
                    suit = card_name[1].lower()
                    found_cards.append((rank, suit))
                    
        return self._remove_duplicate_cards(found_cards)
    
    def _extract_text_from_region(
        self,
        image: np.ndarray,
        region: Tuple[int, int, int, int]
    ) -> str:
        """Извлечение текста из области с помощью OCR"""
        if not TESSERACT_PATH or not Path(TESSERACT_PATH).exists():
            return ""
            
        x, y, w, h = region
        
        img_h, img_w = image.shape[:2]
        x = max(0, min(x, img_w - 1))
        y = max(0, min(y, img_h - 1))
        w = min(w, img_w - x)
        h = min(h, img_h - y)
        
        if w <= 0 or h <= 0:
            return ""
            
        roi = image[y:y+h, x:x+w]
        
        if self.debug_mode:
            self._save_debug_image(roi, "pot_original")
        
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Увеличиваем в 2 раза!
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
        # Вариант 1: Без обработки
        text1 = pytesseract.image_to_string(gray, config='--oem 3 --psm 7').strip()
        
        # Вариант 2: Увеличение контраста
        _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        text2 = pytesseract.image_to_string(thresh1, config='--oem 3 --psm 7').strip()
        
        # Вариант 3: Инверсия
        thresh2 = cv2.bitwise_not(thresh1)
        text3 = pytesseract.image_to_string(thresh2, config='--oem 3 --psm 7').strip()

        # Вариант 4: (только цифры)
        text4 = pytesseract.image_to_string(gray, config='--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789').strip()
        
        # Вариант 5: ОРИГИНАЛ без resize (для крупных цифр)
        text5 = pytesseract.image_to_string(roi, config='--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789').strip()

        if self.debug_mode:
            self._save_debug_image(gray, "pot_gray")
            self._save_debug_image(thresh1, "pot_thresh1")
            self._save_debug_image(thresh2, "pot_thresh2")
            print(f"[DEBUG] OCR варианты:")
            print(f"  1 (gray): '{text1}'")
            print(f"  2 (thresh): '{text2}'")
            print(f"  3 (invert): '{text3}'")
            print(f"  4 (whitelist): '{text4}'")
            print(f"  5 (original): '{text5}'")
        # Возвращаем первый непустой результат
        for text in [text5, text4,text3, text2, text1]:
            if text:
                print(f"[DEBUG] _extract_text_from_region возвращает: '{text}'")
                return text
        
        print(f"[DEBUG] _extract_text_from_region возвращает ПУСТО")
        return ""
    
    def _parse_number(self, text: str) -> float:
        """Парсинг числа из текста"""
        if not text:
            return 0.0
        
        # Ищем первое число (целое или дробное)
        match = re.search(r'(\d+(?:[.,]\d+)?)', text)
        if match:
            num_str = match.group(1).replace(',', '.')
            return float(num_str)
        
        return 0.0
    
    def _remove_duplicate_cards(
        self, 
        cards: List[Tuple[str, str]]
    ) -> List[Tuple[str, str]]:
        """Удаление дубликатов карт"""
        seen = set()
        unique = []
        for card in cards:
            key = f"{card[0]}{card[1]}"
            if key not in seen:
                seen.add(key)
                unique.append(card)
        return unique
    
    def _save_debug_image(self, image: np.ndarray, name: str):
        """Сохранение отладочного изображения"""
        debug_dir = Path(__file__).resolve().parent.parent / "debug"
        debug_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = debug_dir / f"{name}_{timestamp}.png"
        cv2.imwrite(str(filename), image)
        print(f"[DEBUG] Сохранено: {filename}")