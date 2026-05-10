"""
Таблицы стартовых рук для префлопа
Адаптировано для 6-max игр
"""

from typing import Dict, Tuple
from enum import Enum


class Position(Enum):
    """Позиции за 6-max столом"""
    BTN = "BTN"   # Button (баттон)
    SB = "SB"     # Small Blind
    BB = "BB"     # Big Blind
    UTG = "UTG"   # Under the Gun
    MP = "MP"     # Middle Position
    CO = "CO"     # Cutoff


# Веса позиций (чем меньше, тем тайтовее играем)
POSITION_TIGHTNESS = {
    Position.UTG: 1.0,  # Самая тайтовая позиция
    Position.MP: 1.2,
    Position.CO: 1.4,
    Position.BTN: 1.8,  # Самая лузовая позиция
    Position.SB: 1.0,   # Тайтово из-за плохой позиции постфлоп
    Position.BB: 1.5,   # Можно защищать шире
}


class PreflopCharts:
    """
    Таблицы стартовых рук для префлопа
    
    Рейтинг рук от 1 (сильнейшая) до 169 (слабейшая)
    """
    
    # Рейтинг всех возможных стартовых рук
    HAND_RANKINGS: Dict[str, int] = {
        # Премиум пары
        "AA": 1, "KK": 2, "QQ": 3, "JJ": 4, "TT": 5,
        "99": 6, "88": 7, "77": 8, "66": 9, "55": 10,
        "44": 11, "33": 12, "22": 13,
        
        # Одномастные руки
        "AKs": 14, "AQs": 15, "AJs": 16, "ATs": 17,
        "A9s": 22, "A8s": 24, "A7s": 27, "A6s": 29, "A5s": 26, "A4s": 30, "A3s": 32, "A2s": 33,
        
        "KQs": 18, "KJs": 20, "KTs": 21, "K9s": 28, "K8s": 36, "K7s": 40, "K6s": 43, "K5s": 46, "K4s": 49, "K3s": 52, "K2s": 55,
        
        "QJs": 19, "QTs": 23, "Q9s": 31, "Q8s": 39, "Q7s": 45, "Q6s": 50, "Q5s": 54, "Q4s": 58, "Q3s": 62, "Q2s": 66,
        
        "JTs": 25, "J9s": 34, "J8s": 42, "J7s": 48, "J6s": 56, "J5s": 60, "J4s": 65, "J3s": 70, "J2s": 75,
        
        "T9s": 35, "T8s": 41, "T7s": 47, "T6s": 53, "T5s": 59, "T4s": 64, "T3s": 69, "T2s": 74,
        
        "98s": 44, "97s": 51, "96s": 57, "95s": 63, "94s": 68, "93s": 73, "92s": 78,
        
        "87s": 61, "86s": 67, "85s": 72, "84s": 77, "83s": 82, "82s": 87,
        
        "76s": 71, "75s": 76, "74s": 81, "73s": 86, "72s": 91,
        
        "65s": 79, "64s": 84, "63s": 89, "62s": 94,
        
        "54s": 85, "53s": 90, "52s": 95,
        
        "43s": 92, "42s": 97,
        
        "32s": 98,
        
        # Разномастные руки
        "AKo": 37, "AQo": 38, "AJo": 80, "ATo": 83, "A9o": 88, "A8o": 93, "A7o": 99, "A6o": 104, "A5o": 109, "A4o": 114, "A3o": 119, "A2o": 124,
        
        "KQo": 100, "KJo": 101, "KTo": 105, "K9o": 110, "K8o": 115, "K7o": 120, "K6o": 125, "K5o": 130, "K4o": 135, "K3o": 140, "K2o": 145,
        
        "QJo": 102, "QTo": 106, "Q9o": 111, "Q8o": 116, "Q7o": 121, "Q6o": 126, "Q5o": 131, "Q4o": 136, "Q3o": 141, "Q2o": 146,
        
        "JTo": 103, "J9o": 107, "J8o": 112, "J7o": 117, "J6o": 122, "J5o": 127, "J4o": 132, "J3o": 137, "J2o": 142,
        
        "T9o": 108, "T8o": 113, "T7o": 118, "T6o": 123, "T5o": 128, "T4o": 133, "T3o": 138, "T2o": 143,
        
        "98o": 129, "97o": 134, "96o": 139, "95o": 144, "94o": 148, "93o": 152, "92o": 156,
        
        "87o": 147, "86o": 150, "85o": 153, "84o": 157, "83o": 161, "82o": 165,
        
        "76o": 149, "75o": 151, "74o": 155, "73o": 159, "72o": 163,
        
        "65o": 154, "64o": 158, "63o": 162, "62o": 166,
        
        "54o": 160, "53o": 164, "52o": 167,
        
        "43o": 168, "42o": 169,
        
        "32o": 170,
    }
    
    # Пороги для разных действий по позициям (максимальный рейтинг)
    OPEN_RAISE_THRESHOLDS = {
        Position.UTG: 25,   # Только сильные руки
        Position.MP: 35,    # Добавляем средние
        Position.CO: 50,    # Ещё шире
        Position.BTN: 70,   # Широкий диапазон
        Position.SB: 45,    # Осторожно из-за позиции
        Position.BB: 100,   # Можно защищать почти всё
    }
    
    # 3-бет диапазон (рейз против опен-рейза)
    THREE_BET_THRESHOLDS = {
        Position.UTG: 10,   # Только премиум
        Position.MP: 15,
        Position.CO: 20,
        Position.BTN: 25,
        Position.SB: 18,
        Position.BB: 22,
    }
    
    # Диапазон для колла 3-бета
    CALL_THREEBET_THRESHOLDS = {
        Position.UTG: 15,
        Position.MP: 20,
        Position.CO: 30,
        Position.BTN: 35,
        Position.SB: 20,
        Position.BB: 40,
    }
    
    @classmethod
    def get_hand_ranking(cls, card1: str, card2: str, suited: bool = None) -> int:
        """
        Получить рейтинг руки
        
        Args:
            card1, card2: строки с рангом карт ('A', 'K', etc.)
            suited: True для одномастных, False для разномастных, None для автоопределения
        
        Returns:
            Рейтинг от 1 до 170 (меньше = сильнее)
        """
        # Сортируем по старшинству
        rank_order = "23456789TJQKA"
        
        r1_val = rank_order.index(card1.upper())
        r2_val = rank_order.index(card2.upper())
        
        if r1_val < r2_val:
            high, low = card2.upper(), card1.upper()
        else:
            high, low = card1.upper(), card2.upper()
        
        if suited is None:
            # Автоопределение: используем одномастный рейтинг по умолчанию
            # (будет переопределено при наличии информации о масти)
            suited = True
        
        if high == low:
            hand_key = f"{high}{low}"
        else:
            hand_key = f"{high}{low}{'s' if suited else 'o'}"
        
        return cls.HAND_RANKINGS.get(hand_key, 170)
    
    @classmethod
    def get_preflop_action(
        cls,
        hand: Tuple[str, str],
        position: Position,
        facing_raise: bool = False,
        facing_threebet: bool = False,
        stack_depth: float = 100.0
    ) -> Dict:
        """
        Получить рекомендуемое действие на префлопе
        
        Args:
            hand: кортеж из двух карт (ранг, масть)
            position: позиция за столом
            facing_raise: есть ли рейз перед нами
            facing_threebet: есть ли 3-бет перед нами
            stack_depth: глубина стека в BB
        
        Returns:
            Словарь с рекомендацией и обоснованием
        """
        rank1, suit1 = hand[0]
        rank2, suit2 = hand[1]
        suited = suit1 == suit2
        
        ranking = cls.get_hand_ranking(rank1, rank2, suited)
        
        result = {
            "action": None,
            "reasoning": [],
            "hand_ranking": ranking,
            "hand_name": f"{max(rank1, rank2)}{min(rank1, rank2)}{'s' if suited else 'o'}"
        }
        
        # Корректировка порогов в зависимости от глубины стека
        depth_multiplier = 1.0
        if stack_depth < 40:
            depth_multiplier = 0.8  # Короткий стек - играем шире
            result["reasoning"].append(f"Короткий стек ({stack_depth:.0f}BB) - играем шире")
        elif stack_depth > 150:
            depth_multiplier = 1.2  # Глубокий стек - играем осторожнее
            result["reasoning"].append(f"Глубокий стек ({stack_depth:.0f}BB) - играем осторожнее")
        
        if facing_threebet:
            # Реакция на 3-бет
            threshold = cls.CALL_THREEBET_THRESHOLDS[position] * depth_multiplier
            
            if ranking <= 8:  # Премиум руки - 4-бет
                result["action"] = "RAISE"
                result["reasoning"].append("Премиум рука - 4-бет для велью")
            elif ranking <= threshold:
                result["action"] = "CALL"
                result["reasoning"].append(f"Рука входит в диапазон колла 3-бета с {position.value}")
            else:
                result["action"] = "FOLD"
                result["reasoning"].append("Рука слишком слабая для колла 3-бета")
                
        elif facing_raise:
            # Реакция на опен-рейз
            threebet_threshold = cls.THREE_BET_THRESHOLDS[position] * depth_multiplier
            call_threshold = cls.OPEN_RAISE_THRESHOLDS[position] * depth_multiplier * 0.7
            
            if ranking <= threebet_threshold:
                result["action"] = "RAISE"
                result["reasoning"].append(f"Рука входит в диапазон 3-бета с {position.value}")
            elif ranking <= call_threshold:
                result["action"] = "CALL"
                result["reasoning"].append(f"Рука входит в диапазон колла с {position.value}")
            else:
                result["action"] = "FOLD"
                result["reasoning"].append("Рука недостаточно сильная для колла рейза")
                
        else:
            # Опен-рейз (мы первые)
            threshold = cls.OPEN_RAISE_THRESHOLDS[position] * depth_multiplier
            
            if ranking <= threshold:
                if ranking <= 10:
                    result["action"] = "RAISE"
                    result["reasoning"].append(f"Сильная рука - опен-рейз с {position.value}")
                else:
                    result["action"] = "RAISE"
                    result["reasoning"].append(f"Рука входит в диапазон опен-рейза с {position.value}")
            else:
                result["action"] = "FOLD"
                result["reasoning"].append("Рука недостаточно сильная для опен-рейза")
        
        return result
    
    @classmethod
    def get_hand_category(cls, rank1: str, rank2: str, suited: bool) -> str:
        """Получить категорию руки для анализа"""
        ranking = cls.get_hand_ranking(rank1, rank2, suited)
        
        if ranking <= 5:
            return "Премиум пара"
        elif ranking <= 13:
            return "Пара"
        elif ranking <= 25:
            return "Премиум"
        elif ranking <= 50:
            return "Сильная"
        elif ranking <= 100:
            return "Средняя"
        elif ranking <= 150:
            return "Слабая"
        else:
            return "Мусорная"


# Для обратной совместимости
def get_preflop_action_simple(card1: str, card2: str, position: str) -> str:
    """
    Упрощенная функция для быстрого получения действия
    
    Args:
        card1, card2: строки вида 'Ah', 'Kd'
        position: 'UTG', 'MP', 'CO', 'BTN', 'SB', 'BB'
    
    Returns:
        'RAISE', 'CALL', или 'FOLD'
    """
    from ..utils.poker_utils import parse_card
    
    pos_map = {
        "BTN": Position.BTN, "SB": Position.SB, "BB": Position.BB,
        "UTG": Position.UTG, "MP": Position.MP, "CO": Position.CO
    }
    
    hand = (parse_card(card1), parse_card(card2))
    pos = pos_map.get(position.upper(), Position.MP)
    
    result = PreflopCharts.get_preflop_action(hand, pos)
    return result["action"]