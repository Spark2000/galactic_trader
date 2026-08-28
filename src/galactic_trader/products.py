from enum import Enum


class Product(Enum):
    FOOD = "food"
    # TODO more product e.g. ore, metal, ...

    def __str__(self) -> str:
        """
        Returns a human-readable string of the product name.
        
        >>> str(Product.FOOD)
        'Food'
        """
        return self.value.title()
