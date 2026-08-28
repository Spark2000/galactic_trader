from enum import Enum


class Product(Enum):
    FOOD = "food"
    FURNITURE = "furniture"
    NAILS = "nails"
    WOOD = "wood"
    # TODO more products e.g. ore, metal, ...

    def __str__(self) -> str:
        """
        Returns a human-readable string of the product name.
        
        >>> str(Product.FOOD)
        'Food'
        """
        return self.value.title()
