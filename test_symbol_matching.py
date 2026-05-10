import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

import cv2
import time
import numpy as np
from modules.capture import ScreenCapture

print("=" * 50)
print("РАСПОЗНАВАНИЕ КАРТ (РАНГ + МАСТЬ)")
print("=" * 50)

# Загружаем шаблоны РАНГОВ
rank_templates = {}
rank_dir = Path("config/rank_templates")
if rank_dir.exists():
    for f in rank_dir.glob("*.png"):
        rank_templates[f.stem.upper()] = cv2.imread(str(f))
        print(f"  Загружен ранг: {f.stem.upper()}")
else:
    print("  ⚠️ Папка rank_templates не найдена!")

# Загружаем шаблоны МАСТЕЙ
suit_templates = {}
suit_dir = Path("config/suit_templates")
for f in suit_dir.glob("*.png"):
    suit_templates[f.stem.lower()] = cv2.imread(str(f))
    print(f"  Загружена масть: {f.stem.lower()}")

capture = ScreenCapture()

print("\nЖду 3 секунды... ПЕРЕКЛЮЧИТЕСЬ НА ПОКЕР!")
time.sleep(3)

screen = capture.capture_full_screen()
height, width = screen.shape[:2]

rx, ry, rw, rh = capture.DEFAULT_REGIONS["board_cards"]
board_x = int(width * rx)
board_y = int(height * ry)
w = int(width * rw)
h = int(height * rh)

# Захватываем выше на 40 пикселей (как в save_ranks.py)
y1 = max(0, board_y - 40)
board_roi = screen[y1:board_y+h, board_x:board_x+w]

CARD_BOUNDS = [
    (1482, 1653),
    (1660, 1828),
    (1834, 2004),
    (2012, 2180),
    (2187, 2355),
]

X_SHIFT = [0, -4, -4, -6, -6]

THRESHOLD_RANK = 0.45
THRESHOLD_SUIT = 0.45
cards = []

for i, (abs_x1, abs_x2) in enumerate(CARD_BOUNDS):
    x1 = abs_x1 - board_x
    x2 = abs_x2 - board_x
    card_roi = board_roi[:, x1:x2]
    
    shift = X_SHIFT[i]
    sym_x1 = max(0, 10 + shift)
    sym_x2 = min(card_roi.shape[1], 65 + shift)
    
    if sym_x2 <= sym_x1:
        print(f"  Карта {i+1}: ошибка региона")
        continue
    
    # Регионы (как в save_ranks.py)
    rank_roi = card_roi[0:90, sym_x1:sym_x2]      # РАНГ
    suit_roi = card_roi[100:160, sym_x1:sym_x2]   # МАСТЬ (сдвинута вниз, т.к. board_roi поднят)
    
    # Поиск ранга
    best_rank = "?"
    best_rank_val = 0
    for rank, template in rank_templates.items():
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
    for suit, template in suit_templates.items():
        if template.shape[0] > suit_roi.shape[0] or template.shape[1] > suit_roi.shape[1]:
            continue
        result = cv2.matchTemplate(suit_roi, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        if max_val > best_suit_val:
            best_suit_val = max_val
            best_suit = suit
    
    # Результат
    if best_rank_val >= THRESHOLD_RANK and best_suit_val >= THRESHOLD_SUIT:
        cards.append((best_rank, best_suit))
        print(f"  Карта {i+1}: {best_rank}{best_suit} (ранг:{best_rank_val:.2f}, масть:{best_suit_val:.2f})")
    elif best_suit_val >= THRESHOLD_SUIT:
        cards.append(("?", best_suit))
        print(f"  Карта {i+1}: ?{best_suit} (ранг:{best_rank_val:.2f}, масть:{best_suit_val:.2f})")
    else:
        print(f"  Карта {i+1}: ?? (ранг:{best_rank_val:.2f}, масть:{best_suit_val:.2f})")

print(f"\n{'='*50}")
print(f"Карты: {cards}")