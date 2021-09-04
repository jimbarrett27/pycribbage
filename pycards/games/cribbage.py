import random

from pycards.cards import make_standard_deck, Cards, Card
from pycards.players import Players, Player
from copy import deepcopy

from itertools import combinations


class CribbagePlayer(Player):

    def give_cards_to_crib(self, n_required):

        if n_required not in {1,2}:
            raise ValueError("Requested weird number of cards for crib")

        cards_to_play = Cards(random.choices(self.hand, k=n_required))
        return self.hand.play_cards(cards_to_play)

    def play_pegging_card(self, current_pegging_score: int):
        """
        Choose a card from the players hand to play during the
        pegging phase.

        Requires the current pegging score.
        """

        if len(self.hand) == 0:
            return None

        if not any(
            card.value + current_pegging_score <= 31
            for card in self.hand
        ):
            return None

        for card in self.hand:
            if card.value + current_pegging_score <= 31:
                self.hand.play_card(card)


class Cribbage:

    def __init__(self, players: Players):

        self.players = players
        self.deal_pile = Cards.standard_deck()
        self.discard_pile = Cards.empty()
        self.crib = Cards.empty()
        self.turn_up_card = None

        self._decide_dealer()

    @property
    def n_players(self):
        return len(self.players)

    @property
    def cards_per_player(self) -> int:

        if self.n_players == 2:
            return 6
        elif self.n_players in {3,4}:
            return 5
        else:
            raise ValueError("Invalid number of players")

    @staticmethod
    def _card_value(card: Card):
        
        if card.value < 9:
            return card.value + 1
        else:
            return 10

    def _decide_dealer(self) -> Player:
        
        self.players.dealer = random.choice(self.players) 

    def _check_for_winner(self):

        for player in self.players:
            if player.score >= 121:
                return True

        return False

    def _fix_deal_pile(self, n_required_cards):
        """
        If there aren't the required number of cards in the deal pile
        then shuffle the discard pile and append them
        """
        if n_required_cards > len(self.deal_pile):
            self.discard_pile.shuffle()
            self.deal_pile += self.discard_pile
    
    def _deal_cards_to_players(self):
        
        n_required_cards = self.n_players * self.cards_per_player
        self._fix_deal_pile(n_required_cards)

        for _ in range(self.cards_per_player):
            for player in self.players:
                player.hand += self.deal_pile.deal_card()


    def _score_hand(self, hand: Cards, is_crib: bool = False):

        hand_score = 0

        print(hand, type(hand))

        effective_hand = deepcopy(hand)
        effective_hand += self.turn_up_card

        # look for 15s
        for n_cards in [2,3,4,5]:
            for cards in combinations(effective_hand, n_cards):
                if sum(self._card_value(card) for card in cards) == 15:
                    hand_score += 2

        # look for pairs
        for card1, card2 in combinations(effective_hand, 2):
            if card1.value == card2.value:
                hand_score += 2

        # look for flushes
        if effective_hand.contains_flush(5):
            hand_score += 5
        # can only get flushes of 4 in certain situations
        elif hand.contains_flush(4) and not is_crib:
            hand_score += 4

        # look for runs
        runs = effective_hand.get_straights(3, 5)
        hand_score += sum(map(len, runs))
        
        # look for knobs
        for card in hand:
            if card.value == 10 and card.suit == self.turn_up_card.suit:
                hand_score += 1

        return hand_score

    def _receive_crib_cards_from_players(self):
        
        for player in self.players:
            if self.n_players == 2:
                self.crib += player.give_cards_to_crib(n_required=2)
            elif self.n_players in {3, 4}:
                self.crib += player.give_cards_to_crib(n_required=1)

        if self.n_players == 3:
            n_required_cards = 1
            self._fix_deal_pile(n_required_cards)
            self.crib += self.deal_pile.deal_card()

    def _choose_turn_up(self):
        n_required_cards = 1
        self._fix_deal_pile(n_required_cards)
        self.turn_up_card = self.deal_pile.play_random_card()

        if self.turn_up_card.value == 10:
            self.players.dealer.score += 2

    def _play_pegging_phase(self):

        # TODO
        pass

    def _score_hands(self):
        
        for player in self.players:
            player.score += self._score_hand(player.hand)

            # TODO: return if winner


    def _discard_hands_and_crib(self):
        
        for player in self.players:
            self.discard_pile += player.hand.play_all()

        self.discard_pile += self.crib.play_all()
        self.discard_pile += self.turn_up_card

    def play(self):

        while True:
            self._deal_cards_to_players()
            self._receive_crib_cards_from_players()
            self._play_pegging_phase()
            self._score_hands()
            self._discard_hands_and_crib()