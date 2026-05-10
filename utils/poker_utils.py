"""
Базовые утилиты для покерных расчетов
Версия: 0.1.0
"""

from enum import Enum
from typing import List, Tuple, Dict, Optional
import itertools


class Suit(Enum):
    """Масти карт"""
    HEARTS = 'h'
    DIAMONDS = 'd'
    CLUBS = 'c'
    SPADES = 's'
    
    def __str__(self):
        symbols = {'h': '♥', 'd': '♦', 'c': '♣', 's': '♠'}
        return symbols.get(self.value, self.value)


class Rank(Enum):
    """Ранги карт"""
    TWO = '2'
    THREE = '3'
    FOUR = '4'
    FIVE = '5'
    SIX = '6'
    SEVEN = '7'
    EIGHT = '8'
    NINE = '9'
    TEN = 'T'
    JACK = 'J'
    QUEEN = 'Q'
    KING = 'K'
    ACE = 'A'
    
    def __str__(self):
        return self.value


class HandRank(Enum):
    """Покерные комбинации (от слабой к сильной)"""
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9
    
    def __str__(self):
        names = {
            0: "Старшая карта",
            1: "Пара",
            2: "Две пары",
            3: "Тройка",
            4: "Стрит",
            5: "Флеш",
            6: "Фулл-хаус",
            7: "Каре",
            8: "Стрит-флеш",
            9: "Роял-флеш"
        }
        return names.get(self.value, "Неизвестно")


# Порядок рангов для сравнения
RANK_ORDER = {r.value: i for i, r in enumerate(Rank)}
SUIT_ORDER = {s.value: i for i, s in enumerate(Suit)}

# Полная колода
FULL_DECK = [(r.value, s.value) for r in Rank for s in Suit]


def parse_card(card_str: str) -> Tuple[str, str]:
    """
    Парсит строку карты в кортеж (ранг, масть)
    
    Примеры:
        "Ah" -> ('A', 'h')
        "Td" -> ('T', 'd')
        "2c" -> ('2', 'c')
    
    Args:
        card_str: строка из 2 символов (ранг + масть)
    
    Returns:
        Tuple[ранг, масть]
    
    Raises:
        ValueError: если формат карты неверный
    """
    if not card_str or len(card_str) < 2:
        raise ValueError(f"Неверный формат карты: '{card_str}'")
    
    rank = card_str[0].upper()
    suit = card_str[1].lower()
    
    # Проверка валидности
    valid_ranks = [r.value for r in Rank]
    valid_suits = [s.value for s in Suit]
    
    if rank not in valid_ranks:
        raise ValueError(f"Неверный ранг: '{rank}'. Допустимые: {valid_ranks}")
    if suit not in valid_suits:
        raise ValueError(f"Неверная масть: '{suit}'. Допустимые: {valid_suits}")
    
    return (rank, suit)


def format_card(card: Tuple[str, str]) -> str:
    """
    Форматирует карту в читаемый вид
    
    Пример:
        ('A', 'h') -> "A♥"
    """
    suit_symbols = {'h': '♥', 'd': '♦', 'c': '♣', 's': '♠'}
    rank, suit = card
    return f"{rank}{suit_symbols.get(suit, suit)}"


def format_cards(cards: List[Tuple[str, str]]) -> str:
    """Форматирует список карт в строку"""
    return " ".join(format_card(c) for c in cards)


def calculate_pot_odds(pot_size: float, bet_to_call: float) -> float:
    """
    Расчет шансов банка (Pot Odds)
    
    Формула: bet_to_call / (pot_size + bet_to_call)
    
    Args:
        pot_size: текущий размер банка
        bet_to_call: размер ставки для колла
    
    Returns:
        Шансы банка в виде десятичной дроби (0.0 - 1.0)
    
    Example:
        Банк 100$, нужно доставить 20$ 
        -> 20 / (100 + 20) = 0.166 (16.6%)
    """
    if pot_size < 0 or bet_to_call < 0:
        raise ValueError("Размеры ставок не могут быть отрицательными")
    
    total = pot_size + bet_to_call
    if total == 0:
        return 0.0
    
    return bet_to_call / total


def calculate_implied_odds(
    pot_size: float, 
    bet_to_call: float, 
    expected_future_winnings: float
) -> float:
    """
    Расчет предполагаемых шансов банка (Implied Odds)
    
    Args:
        pot_size: текущий размер банка
        bet_to_call: размер ставки для колла
        expected_future_winnings: ожидаемый будущий выигрыш
    
    Returns:
        Предполагаемые шансы в виде десятичной дроби
    """
    total_potential = pot_size + bet_to_call + expected_future_winnings
    if total_potential == 0:
        return 0.0
    return bet_to_call / total_potential


def calculate_drawing_odds_by_outs(outs: int, cards_to_come: int = 1) -> float:
    """
    Расчет вероятности улучшения руки по количеству аутов
    
    Правило 4 и 2:
    - На флопе (cards_to_come=2): ауты * 4%
    - На терне (cards_to_come=1): ауты * 2%
    
    Args:
        outs: количество карт, улучшающих руку
        cards_to_come: сколько карт еще выйдет (1 или 2)
    
    Returns:
        Вероятность в виде десятичной дроби
    """
    if cards_to_come == 2:
        # Точная формула для двух карт
        # P = 1 - ((47-outs)/47 * (46-outs)/46)
        unknown_cards = 47  # 52 - 2 карты игрока - 3 флопа
        prob = 1.0
        for i in range(2):
            prob *= (unknown_cards - outs - i) / (unknown_cards - i)
        return 1.0 - prob
    else:
        # Для одной карты
        unknown_cards = 46  # 52 - 2 карты игрока - 4 доски
        return outs / unknown_cards


def quick_drawing_odds(outs: int, street: str = "flop") -> float:
    """
    Быстрый расчет шансов по правилу 4 и 2
    
    Args:
        outs: количество аутов
        street: "flop" или "turn"
    
    Returns:
        Приблизительная вероятность
    """
    multiplier = 4 if street.lower() == "flop" else 2
    return min(outs * multiplier / 100, 1.0)


def get_rank_value(rank: str) -> int:
    """Возвращает числовое значение ранга (2=0, A=12)"""
    return RANK_ORDER.get(rank.upper(), -1)


def compare_cards(card1: str, card2: str) -> int:
    """
    Сравнивает две карты по рангу
    
    Returns:
        1: card1 > card2
        -1: card1 < card2
        0: card1 == card2
    """
    r1 = get_rank_value(card1[0])
    r2 = get_rank_value(card2[0])
    
    if r1 > r2:
        return 1
    elif r1 < r2:
        return -1
    return 0


def sort_cards_by_rank(cards: List[Tuple[str, str]], reverse: bool = True) -> List[Tuple[str, str]]:
    """Сортирует карты по рангу"""
    return sorted(cards, key=lambda c: RANK_ORDER[c[0]], reverse=reverse)


def is_suited(card1: Tuple[str, str], card2: Tuple[str, str]) -> bool:
    """Проверяет, одномастные ли карты"""
    return card1[1] == card2[1]


def is_pair(card1: Tuple[str, str], card2: Tuple[str, str]) -> bool:
    """Проверяет, пара ли это"""
    return card1[0] == card2[0]


def is_connected(card1: Tuple[str, str], card2: Tuple[str, str]) -> bool:
    """
    Проверяет, являются ли карты коннекторами (разница в 1 ранг)
    Например: JT, 98, AK
    """
    r1 = RANK_ORDER[card1[0]]
    r2 = RANK_ORDER[card2[0]]
    diff = abs(r1 - r2)
    return diff == 1 or diff == 12  # 12 для A-2


def hand_description(card1: Tuple[str, str], card2: Tuple[str, str]) -> str:
    """
    Возвращает текстовое описание стартовой руки
    
    Examples:
        ('A', 'h'), ('K', 'h') -> "AKs (одномастные)"
        ('T', 'c'), ('T', 'd') -> "TT (пара)"
        ('9', 'h'), ('8', 's') -> "98o (разномастные коннекторы)"
    """
    r1, r2 = card1[0], card2[0]
    
    # Сортируем по старшинству
    if RANK_ORDER[r1] < RANK_ORDER[r2]:
        r1, r2 = r2, r1
    
    hand_str = f"{r1}{r2}"
    
    if is_pair(card1, card2):
        return f"{hand_str} (пара)"
    elif is_suited(card1, card2):
        suffix = "s"
        if is_connected(card1, card2):
            return f"{hand_str}{suffix} (одномастные коннекторы)"
        return f"{hand_str}{suffix} (одномастные)"
    else:
        suffix = "o"
        if is_connected(card1, card2):
            return f"{hand_str}{suffix} (разномастные коннекторы)"
        return f"{hand_str}{suffix} (разномастные)"


def classify_hand_strength(cards: List[Tuple[str, str]]) -> Tuple[HandRank, List[int]]:
    """
    Определяет силу покерной комбинации
    
    Args:
        cards: список из 5-7 карт
    
    Returns:
        Tuple[HandRank, List[int]]: (тип комбинации, значения для сравнения)
    """
    if len(cards) < 5:
        raise ValueError("Нужно минимум 5 карт для определения комбинации")
    
    ranks = [RANK_ORDER[c[0]] for c in cards]
    suits = [c[1] for c in cards]
    
    # Подсчет частоты рангов
    rank_counts = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1
    
    counts = sorted(rank_counts.values(), reverse=True)
    unique_ranks = sorted(set(ranks))
    
    # Проверка на флеш
    suit_counts = {}
    for s in suits:
        suit_counts[s] = suit_counts.get(s, 0) + 1
    is_flush = max(suit_counts.values()) >= 5
    
    # Проверка на стрит
    is_straight = False
    straight_high = 0
    
    # Обычный стрит
    for i in range(len(unique_ranks) - 4):
        if unique_ranks[i+4] - unique_ranks[i] == 4:
            is_straight = True
            straight_high = unique_ranks[i+4]
            break
    
    # Особый случай: A-2-3-4-5
    if set([12, 0, 1, 2, 3]).issubset(set(ranks)):
        is_straight = True
        straight_high = 3  # 5 - старшая
    
    # Определение комбинации
    if is_flush and is_straight:
        if straight_high == 12:
            return (HandRank.ROYAL_FLUSH, [straight_high])
        return (HandRank.STRAIGHT_FLUSH, [straight_high])
    
    if 4 in counts:
        quads = [r for r, c in rank_counts.items() if c == 4][0]
        kicker = max([r for r, c in rank_counts.items() if c == 1])
        return (HandRank.FOUR_OF_KIND, [quads, kicker])
    
    if 3 in counts and 2 in counts:
        trips = [r for r, c in rank_counts.items() if c == 3][0]
        pair = [r for r, c in rank_counts.items() if c == 2][0]
        return (HandRank.FULL_HOUSE, [trips, pair])
    
    if is_flush:
        flush_cards = []
        target_suit = max(suit_counts, key=suit_counts.get)
        for c in cards:
            if c[1] == target_suit:
                flush_cards.append(RANK_ORDER[c[0]])
        flush_cards = sorted(flush_cards, reverse=True)[:5]
        return (HandRank.FLUSH, flush_cards)
    
    if is_straight:
        return (HandRank.STRAIGHT, [straight_high])
    
    if 3 in counts:
        trips = [r for r, c in rank_counts.items() if c == 3][0]
        kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)[:2]
        return (HandRank.THREE_OF_KIND, [trips] + kickers)
    
    if counts.count(2) >= 2:
        pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)[:2]
        kicker = max([r for r, c in rank_counts.items() if c == 1])
        return (HandRank.TWO_PAIR, pairs + [kicker])
    
    if 2 in counts:
        pair = [r for r, c in rank_counts.items() if c == 2][0]
        kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)[:3]
        return (HandRank.PAIR, [pair] + kickers)
    
    high_cards = sorted(ranks, reverse=True)[:5]
    return (HandRank.HIGH_CARD, high_cards)


def compare_hands(hand1: List[Tuple[str, str]], hand2: List[Tuple[str, str]]) -> int:
    """
    Сравнивает две покерные руки
    
    Returns:
        1: hand1 сильнее
        -1: hand2 сильнее
        0: руки равны
    """
    rank1, values1 = classify_hand_strength(hand1)
    rank2, values2 = classify_hand_strength(hand2)
    
    if rank1.value > rank2.value:
        return 1
    elif rank1.value < rank2.value:
        return -1
    
    # Одинаковые комбинации - сравниваем значения
    for v1, v2 in zip(values1, values2):
        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
    
    return 0


# Тесты для проверки работоспособности
if __name__ == "__main__":
    print("=" * 50)
    print("Тестирование poker_utils.py")
    print("=" * 50)
    
    # Тест парсинга карт
    print("\n1. Парсинг карт:")
    card = parse_card("Ah")
    print(f"   'Ah' -> {card}")
    assert card == ('A', 'h')
    print("   ✅ OK")
    
    # Тест форматирования
    print("\n2. Форматирование:")
    formatted = format_card(('A', 'h'))
    print(f"   ('A', 'h') -> {formatted}")
    print("   ✅ OK")
    
    # Тест расчета шансов банка
    print("\n3. Расчет Pot Odds:")
    pot_odds = calculate_pot_odds(100, 20)
    print(f"   Банк: 100, Ставка: 20 -> {pot_odds:.1%}")
    assert abs(pot_odds - 0.1666) < 0.01
    print("   ✅ OK")
    
    # Тест аутов
    print("\n4. Расчет вероятности по аутам:")
    prob_flop = calculate_drawing_odds_by_outs(9, 2)  # Флеш-дро на флопе
    prob_turn = calculate_drawing_odds_by_outs(9, 1)  # Флеш-дро на терне
    print(f"   9 аутов на флопе: {prob_flop:.1%}")
    print(f"   9 аутов на терне: {prob_turn:.1%}")
    print("   ✅ OK")
    
    # Тест описания руки
    print("\n5. Описание стартовой руки:")
    desc1 = hand_description(('A', 'h'), ('K', 'h'))
    desc2 = hand_description(('T', 'c'), ('T', 'd'))
    desc3 = hand_description(('9', 's'), ('8', 'h'))
    print(f"   Ah Kh -> {desc1}")
    print(f"   Tc Td -> {desc2}")
    print(f"   9s 8h -> {desc3}")
    print("   ✅ OK")
    
    # Тест определения комбинации
    print("\n6. Определение комбинации:")
    # Роял-флеш
    royal = [parse_card(c) for c in ["Ah", "Kh", "Qh", "Jh", "Th"]]
    rank, values = classify_hand_strength(royal)
    print(f"   Ah Kh Qh Jh Th -> {rank}")
    assert rank == HandRank.ROYAL_FLUSH
    print("   ✅ OK")
    
    # Фулл-хаус
    full_house = [parse_card(c) for c in ["As", "Ad", "Ac", "Kh", "Ks"]]
    rank, values = classify_hand_strength(full_house)
    print(f"   As Ad Ac Kh Ks -> {rank}")
    assert rank == HandRank.FULL_HOUSE
    print("   ✅ OK")
    
    print("\n" + "=" * 50)
    print("Все тесты пройдены! ✅")
    print("=" * 50)