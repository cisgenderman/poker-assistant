"""
Аналитический движок для расчета вероятностей и генерации рекомендаций
"""

import random
from typing import List, Tuple, Dict, Optional
from enum import Enum
import sys
from pathlib import Path

# Добавляем путь для импорта утилит
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.poker_utils import (
    parse_card, format_cards, calculate_pot_odds,
    calculate_drawing_odds_by_outs, classify_hand_strength,
    HandRank, RANK_ORDER, SUIT_ORDER, FULL_DECK
)
from utils.preflop_charts import PreflopCharts, Position as PreflopPosition


class Action(Enum):
    """Возможные действия в покере"""
    FOLD = "FOLD"
    CHECK = "CHECK"
    CALL = "CALL"
    RAISE = "RAISE"
    
    def __str__(self):
        names = {
            "FOLD": "Фолд",
            "CHECK": "Чек",
            "CALL": "Колл",
            "RAISE": "Рейз"
        }
        return names.get(self.value, self.value)


class Street(Enum):
    """Улицы в покере"""
    PREFLOP = "PREFLOP"
    FLOP = "FLOP"
    TURN = "TURN"
    RIVER = "RIVER"


class PokerAnalyzer:
    """
    Класс для анализа покерной ситуации и генерации рекомендаций
    """
    
    def __init__(self, monte_carlo_iterations: int = 500):
        """
        Args:
            monte_carlo_iterations: количество итераций для симуляции Монте-Карло
        """
        self.monte_carlo_iterations = monte_carlo_iterations
        self.position = PreflopPosition.MP  # По умолчанию
        
    def analyze_situation(
        self,
        player_cards: List[Tuple[str, str]],
        board_cards: List[Tuple[str, str]],
        pot_size: float = 0.0,
        bet_to_call: float = 0.0,
        position: str = "MP",
        stack_size: float = 100.0,
        facing_raise: bool = False,
        facing_threebet: bool = False
    ) -> Dict:
        """
        Полный анализ игровой ситуации
        
        Args:
            player_cards: список из 2 карт игрока
            board_cards: список карт на столе (0-5 карт)
            pot_size: размер банка
            bet_to_call: размер ставки для колла
            position: позиция игрока (UTG, MP, CO, BTN, SB, BB)
            stack_size: размер стека в больших блайндах
            facing_raise: есть ли рейз перед нами
            facing_threebet: есть ли 3-бет перед нами
        
        Returns:
            Словарь с результатами анализа
        """
        # Преобразование позиции
        pos_map = {
            "BTN": PreflopPosition.BTN, "SB": PreflopPosition.SB, "BB": PreflopPosition.BB,
            "UTG": PreflopPosition.UTG, "MP": PreflopPosition.MP, "CO": PreflopPosition.CO
        }
        self.position = pos_map.get(position.upper(), PreflopPosition.MP)
        
        # Определение улицы
        street = self._determine_street(board_cards)
        
        # Базовый результат
        result = {
            "player_cards": player_cards,
            "board_cards": board_cards,
            "pot_size": pot_size,
            "bet_to_call": bet_to_call,
            "street": street,
            "position": position,
            "hand_strength": None,
            "drawing_odds": 0.0,
            "pot_odds": 0.0,
            "outs": 0,
            "equity": 0.0,
            "recommendation": None,
            "reasoning": "",
            "details": {}
        }
        
        # Анализ в зависимости от улицы
        if street == Street.PREFLOP:
            result = self._analyze_preflop(
                result, player_cards, facing_raise, facing_threebet, stack_size
            )
        else:
            result = self._analyze_postflop(
                result, player_cards, board_cards, pot_size, bet_to_call, stack_size
            )
        
        return result
    
    def _determine_street(self, board_cards: List) -> Street:
        """Определение текущей улицы"""
        if not board_cards:
            return Street.PREFLOP
        elif len(board_cards) == 3:
            return Street.FLOP
        elif len(board_cards) == 4:
            return Street.TURN
        else:
            return Street.RIVER
    
    def _analyze_preflop(
        self,
        result: Dict,
        player_cards: List[Tuple[str, str]],
        facing_raise: bool,
        facing_threebet: bool,
        stack_size: float
    ) -> Dict:
        """Анализ префлоп ситуации"""
        
        if len(player_cards) != 2:
            result["recommendation"] = Action.FOLD
            result["reasoning"] = "Недостаточно карт для анализа"
            return result
        
        # Получаем рекомендацию из чартов
        chart_result = PreflopCharts.get_preflop_action(
            player_cards,
            self.position,
            facing_raise=facing_raise,
            facing_threebet=facing_threebet,
            stack_depth=stack_size
        )
        
        # Преобразуем действие
        action_map = {
            "RAISE": Action.RAISE,
            "CALL": Action.CALL,
            "FOLD": Action.FOLD
        }
        
        result["recommendation"] = action_map.get(chart_result["action"], Action.FOLD)
        result["reasoning"] = " | ".join(chart_result["reasoning"])
        result["details"]["hand_ranking"] = chart_result["hand_ranking"]
        result["details"]["hand_name"] = chart_result["hand_name"]
        
        # Расчет примерного эквити (упрощенно)
        result["equity"] = self._estimate_preflop_equity(player_cards)
        
        # Форматируем карты для отображения
        result["hand_description"] = f"{chart_result['hand_name']} (рейтинг: {chart_result['hand_ranking']})"
        
        return result
    
    def _analyze_postflop(
        self,
        result: Dict,
        player_cards: List[Tuple[str, str]],
        board_cards: List[Tuple[str, str]],
        pot_size: float,
        bet_to_call: float,
        stack_size: float
    ) -> Dict:
        """Анализ постфлоп ситуации"""
        
        all_cards = player_cards + board_cards
        
        # Определяем текущую комбинацию
        if len(all_cards) >= 5:
            hand_rank, values = classify_hand_strength(all_cards)
            result["hand_strength"] = {
                "rank": hand_rank,
                "name": str(hand_rank),
                "values": values
            }
        
        # Подсчет аутов
        outs = self._count_outs(player_cards, board_cards)
        result["outs"] = outs
        
        # Расчет вероятности улучшения
        street = result["street"]
        cards_to_come = 2 if street == Street.FLOP else 1
        
        if outs > 0:
            drawing_odds = calculate_drawing_odds_by_outs(outs, cards_to_come)
            result["drawing_odds"] = drawing_odds
        
        # Расчет шансов банка
        if bet_to_call > 0:
            pot_odds = calculate_pot_odds(pot_size, bet_to_call)
            result["pot_odds"] = pot_odds
        else:
            pot_odds = 0.0
            result["pot_odds"] = 0.0
        
        # Оценка эквити (упрощенная)
        result["equity"] = self._estimate_postflop_equity(
            player_cards, board_cards, outs, result["hand_strength"]
        )
        
        # Принятие решения
        result = self._make_postflop_decision(result, bet_to_call, pot_odds, stack_size)
        
        return result
    
    def _count_outs(
        self,
        player_cards: List[Tuple[str, str]],
        board_cards: List[Tuple[str, str]]
    ) -> int:
        """
        Подсчет аутов для улучшения руки
        """
        outs = 0
        all_cards = player_cards + board_cards
        suits = [c[1] for c in all_cards]
        ranks = [RANK_ORDER[c[0]] for c in all_cards]
        
        # Флеш-дро
        for suit in ['h', 'd', 'c', 's']:
            suit_count = suits.count(suit)
            if suit_count == 4:
                outs += 9  # Осталось 9 карт этой масти
                break
        
        # Стрит-дро (упрощенно)
        unique_ranks = sorted(set(ranks))
        
        # Открытое стрит-дро (OESD)
        for i in range(len(unique_ranks) - 3):
            if unique_ranks[i+3] - unique_ranks[i] == 3:
                # 8 аутов на обе стороны
                outs += 8
                break
        
        # Гатшот (если нет OESD)
        if outs < 8:
            for i in range(len(unique_ranks) - 3):
                if unique_ranks[i+3] - unique_ranks[i] <= 4:
                    outs += 4
                    break
        
        # Пара -> две пары/тройка
        if len(ranks) >= 2:
            rank_counts = {}
            for r in ranks:
                rank_counts[r] = rank_counts.get(r, 0) + 1
            
            if max(rank_counts.values()) == 1:
                # Нет пары - 6 аутов на пару
                outs += 6
            elif max(rank_counts.values()) == 2:
                # Есть пара - 5 аутов на улучшение до двух пар/тройки
                outs += 5
        
        return min(outs, 25)  # Максимум 25 аутов
    
    def _estimate_preflop_equity(self, player_cards: List[Tuple[str, str]]) -> float:
        """Упрощенная оценка префлоп эквити против случайной руки"""
        if len(player_cards) != 2:
            return 0.0
        
        r1, r2 = player_cards[0][0], player_cards[1][0]
        suited = player_cards[0][1] == player_cards[1][1]
        
        # Базовое эквити
        ranking = PreflopCharts.get_hand_ranking(r1, r2, suited)
        
        # Примерное соответствие рейтинга эквити
        if ranking <= 5:
            return 0.80  # AA-QQ, AKs
        elif ranking <= 10:
            return 0.70  # JJ-88, AQs
        elif ranking <= 20:
            return 0.60  # 77-66, AJs, KQs
        elif ranking <= 35:
            return 0.50  # Средние руки
        elif ranking <= 60:
            return 0.40  # Слабые руки
        else:
            return 0.30  # Мусор
    
    def _estimate_postflop_equity(
        self,
        player_cards: List[Tuple[str, str]],
        board_cards: List[Tuple[str, str]],
        outs: int,
        hand_strength: Optional[Dict]
    ) -> float:
        """Упрощенная оценка постфлоп эквити"""
        
        if hand_strength and hand_strength["rank"]:
            rank = hand_strength["rank"]
            
            # Готовые сильные комбинации
            if rank.value >= HandRank.STRAIGHT.value:
                return 0.95
            elif rank.value >= HandRank.THREE_OF_KIND.value:
                return 0.85
            elif rank.value >= HandRank.TWO_PAIR.value:
                return 0.75
            elif rank.value >= HandRank.PAIR.value:
                return 0.55
        
        # Оценка по аутам
        if outs >= 15:
            return 0.55  # Сильное комбо-дро
        elif outs >= 12:
            return 0.45  # Сильное дро
        elif outs >= 8:
            return 0.35  # Хорошее дро
        elif outs >= 4:
            return 0.25  # Слабое дро
        else:
            return 0.15  # Без дро
    
    def _make_postflop_decision(
        self,
        result: Dict,
        bet_to_call: float,
        pot_odds: float,
        stack_size: float
    ) -> Dict:
        """Принятие решения на постфлопе"""
        
        drawing_odds = result.get("drawing_odds", 0.0)
        hand_strength = result.get("hand_strength")
        outs = result.get("outs", 0)
        street = result["street"]
        
        reasoning_parts = []
        
        # Если нет ставки для колла
        if bet_to_call == 0:
            # Проверяем, стоит ли беттить
            if hand_strength and hand_strength["rank"].value >= HandRank.TWO_PAIR.value:
                result["recommendation"] = Action.RAISE
                reasoning_parts.append("Сильная готовая рука - ставка для велью")
            elif outs >= 8:
                result["recommendation"] = Action.RAISE
                reasoning_parts.append(f"Сильное дро ({outs} аутов) - полублеф")
            else:
                result["recommendation"] = Action.CHECK
                reasoning_parts.append("Нет причины для ставки - чек")
        
        else:
            # Есть ставка для колла
            if drawing_odds > pot_odds:
                # Математически выгодный колл
                if hand_strength and hand_strength["rank"].value >= HandRank.TWO_PAIR.value:
                    result["recommendation"] = Action.RAISE
                    reasoning_parts.append("Сильная готовая рука - рейз для велью")
                elif outs >= 12:
                    result["recommendation"] = Action.RAISE
                    reasoning_parts.append(f"Сильное дро ({outs} аутов) - рейз для полублефа")
                else:
                    result["recommendation"] = Action.CALL
                    reasoning_parts.append(
                        f"Шансы на улучшение ({drawing_odds:.1%}) > шансов банка ({pot_odds:.1%})"
                    )
            else:
                # Математически невыгодный колл
                if hand_strength and hand_strength["rank"].value >= HandRank.PAIR.value:
                    # С готовой рукой можно коллить даже при плохих шансах
                    if pot_odds > 0.10:  # Не слишком дорого
                        result["recommendation"] = Action.CALL
                        reasoning_parts.append("Готовая рука - колл, несмотря на невыгодные шансы")
                    else:
                        result["recommendation"] = Action.FOLD
                        reasoning_parts.append("Слишком дорогой колл для такой руки")
                else:
                    result["recommendation"] = Action.FOLD
                    reasoning_parts.append(
                        f"Шансы на улучшение ({drawing_odds:.1%}) < шансов банка ({pot_odds:.1%})"
                    )
        
        # Учет размера стека
        if stack_size < 20 and result["recommendation"] in [Action.CALL, Action.RAISE]:
            reasoning_parts.append(f"Короткий стек ({stack_size:.0f}BB) - агрессивная игра")
        
        result["reasoning"] = " | ".join(reasoning_parts)
        
        return result
    
    def format_analysis(self, analysis: Dict) -> str:
        """Форматирование анализа для вывода"""
        lines = []
        
        action = analysis.get("recommendation")
        if action:
            lines.append(f"=== {action.value} ===")
        
        # Карты
        if analysis.get("player_cards"):
            lines.append(f"Рука: {format_cards(analysis['player_cards'])}")
        
        if analysis.get("board_cards"):
            lines.append(f"Стол: {format_cards(analysis['board_cards'])}")
        
        # Статистика
        if analysis.get("pot_size", 0) > 0:
            lines.append(f"Банк: ${analysis['pot_size']:.2f}")
        
        if analysis.get("bet_to_call", 0) > 0:
            lines.append(f"Колл: ${analysis['bet_to_call']:.2f}")
        
        if analysis.get("pot_odds", 0) > 0:
            lines.append(f"Pot Odds: {analysis['pot_odds']:.1%}")
        
        if analysis.get("drawing_odds", 0) > 0:
            lines.append(f"Шансы на улучшение: {analysis['drawing_odds']:.1%}")
        
        if analysis.get("outs", 0) > 0:
            lines.append(f"Ауты: {analysis['outs']}")
        
        if analysis.get("equity", 0) > 0:
            lines.append(f"Эквити: ~{analysis['equity']:.1%}")
        
        # Детали
        if analysis.get("details"):
            for key, value in analysis["details"].items():
                lines.append(f"{key}: {value}")
        
        # Обоснование
        if analysis.get("reasoning"):
            lines.append(f"\n{analysis['reasoning']}")
        
        return "\n".join(lines)


# Тестирование анализатора
if __name__ == "__main__":
    print("=" * 60)
    print("Тестирование PokerAnalyzer")
    print("=" * 60)
    
    analyzer = PokerAnalyzer()
    
    # Тест 1: Префлоп
    print("\n[Тест 1] Префлоп анализ")
    result1 = analyzer.analyze_situation(
        player_cards=[('A', 'h'), ('K', 'h')],
        board_cards=[],
        position="BTN",
        facing_raise=False
    )
    print(analyzer.format_analysis(result1))
    
    # Тест 2: Флеш-дро на флопе
    print("\n" + "-" * 40)
    print("\n[Тест 2] Флеш-дро на флопе")
    result2 = analyzer.analyze_situation(
        player_cards=[('A', 'h'), ('9', 'h')],
        board_cards=[('K', 'h'), ('7', 'h'), ('2', 'c')],
        pot_size=50.0,
        bet_to_call=10.0,
        position="MP"
    )
    print(analyzer.format_analysis(result2))
    
    # Тест 3: Готовая пара
    print("\n" + "-" * 40)
    print("\n[Тест 3] Готовая пара")
    result3 = analyzer.analyze_situation(
        player_cards=[('K', 's'), ('Q', 'd')],
        board_cards=[('K', 'c'), ('7', 'h'), ('2', 's')],
        pot_size=30.0,
        bet_to_call=15.0,
        position="CO"
    )
    print(analyzer.format_analysis(result3))
    
    print("\n" + "=" * 60)
    print("Тестирование завершено!")
    print("=" * 60)