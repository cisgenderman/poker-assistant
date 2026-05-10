# get_coords.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

import cv2
import time
import pyautogui

print("=" * 50)
print("ОПРЕДЕЛЕНИЕ КООРДИНАТ")
print("=" * 50)
print("\n1. Откройте покерный стол (как на картинке)")
print("2. Разверните клиент на весь экран")
print("3. Дождитесь раздачи карт")
print("4. Нажмите Enter и переключитесь на клиент")
input()

print("Жду 2 секунды...")
time.sleep(2)

# Скриншот
screen = pyautogui.screenshot()
screen.save("poker_table_full.png")

# Размер экрана
width, height = screen.size
print(f"\n✅ Размер экрана: {width}x{height}")
print("✅ Скриншот сохранен: poker_table_full.png")

print("\n" + "=" * 50)
print("ИНСТРУКЦИЯ:")
print("=" * 50)
print("\n1. Откройте poker_table_full.png в Paint")
print("2. Наведите мышь на нужные области и ЗАПИШИТЕ координаты")
print("\nНужные области:")
print("  А) ВАШИ КАРТЫ (внизу справа, QQ на картинке)")
print("  Б) ОБЩИЕ КАРТЫ (в центре, Q 2 7 6 5)")
print("  В) РАЗМЕР БАНКА (над общими картами, 'Pot: 160 p.')")
print("  Г) СТАВКА ДЛЯ КОЛЛА (если есть)")