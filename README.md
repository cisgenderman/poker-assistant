# Poker Assistant

Прототип приложения-помощника для игры в покер (Техасский Холдем).

## Возможности

- Захват экрана и распознавание карт (template matching)
- Распознавание размера банка (Tesseract OCR)
- Расчёт вероятностей и рекомендаций (EV, Pot Odds, Drawing Odds)
- Сохранение истории раздач в PostgreSQL
- Демо-режим с тестовыми сценариями

## Установка

```bash
pip install -r requirements.txt



Требуется:

Python 3.12+

Tesseract OCR

PostgreSQL 16


Запуск
bash
python main.py                    # Демо-режим
python main.py --real             # Реальный режим (захват с экрана)
python main.py --real --debug     # С отладкой
python main.py --stats            # Статистика из БД
python main.py --test             # Тесты анализатора


Структура
text
project/
├── main.py                  # Точка входа
├── config/
│   ├── settings.py          # Настройки
│   ├── rank_templates/      # Шаблоны рангов
│   ├── rank_templates_player/  # Шаблоны рангов игрока
│   ├── suit_templates/      # Шаблоны мастей
│   └── suit_templates_player/  # Шаблоны мастей игрока
├── modules/
│   ├── capture.py           # Захват и распознавание
│   ├── analyzer.py          # Анализ и рекомендации
│   └── ui.py                # Интерфейс (Tkinter)
├── utils/
│   ├── poker_utils.py       # Покерные функции
│   ├── preflop_charts.py    # Таблицы стартовых рук
│   └── database.py          # Работа с PostgreSQL
└── requirements.txt


Горячие клавиши
Клавиша	Действие
F5	Обновить анализ
Ctrl+R	Автообновление
← →	Переключение демо
Ctrl+Q	Выход