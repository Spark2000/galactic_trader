from enum import Enum


class Product(Enum):
    FOOD = "food"
    # TODO more product e.g. ore, metal, ...

    def __str__(self) -> str:
        return self.value.title()
