from .card import Card, CardFilter, CardFilterFunctions

class CardCollection:
    def __init__(self):
        self.cards: list[Card] = []
    
    def add_card(self, card: Card):
        self.cards.append(card)
    
    def del_card(self, card:Card):
        self.cards.remove(card)
    
    @property
    def last_card(self):
        return self.cards[-1]
    
class Deck(CardCollection):
    def __init__(self):
        super().__init__()

    def generate_deck(self):
        colors = ["R", "G", "B", "Y"]
        values = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "SKIP", "REVERSE", "+2"]
        for color in colors:
            for value in values:
                self.cards.append(Card(color, value))
                self.cards.append(Card(color, value))
        for x in range(4):
            self.cards.append(Card('WILD', 'WILD'))
            self.cards.append(Card('WILD', 'WILD+4'))
    
    def pop_card(self) -> Card:
        return self.cards.pop()
        

class Hand(CardCollection):
    def __init__(self):
        super().__init__()

    def get_card_by_id(self, id: str) -> Card | None:
        card = next((c for c in self.cards if c.id == int(id)), None)
        return card
    
    def generate_valid_hand(self, last_card: Card, filter: CardFilter | None = None) -> list[Card]:
        cards: list[Card] = []

        if filter is None:
            for card in self.cards:
                if card.validate(last_card): cards.append(card)
        
        if filter is CardFilter:
            cards = CardFilterFunctions.filter(filter_value=filter.value,cards=self.cards, last_card=last_card)
        
        return cards