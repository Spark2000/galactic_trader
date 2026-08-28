from enum import Enum, auto


class ProductType(Enum):
    FOOD = auto()
    # Später auch andere Produkte

    def __str__(self):
        return self.name.title()
