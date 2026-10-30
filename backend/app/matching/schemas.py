from decimal import Decimal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from app.matching.models import Side


class OrderCreate(BaseModel):
    order_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=64)
    symbol: str = Field(min_length=3, max_length=20)
    side: Side
    price: Decimal
    quantity: Decimal

    @field_validator("price", "quantity")
    @classmethod
    def validate_decimal_values(cls, value: Decimal) -> Decimal:
        if not value.is_finite() or value <= 0:
            raise ValueError("Price and quantity must be finite values greater than zero.")
        decimal_places = max(0, -value.normalize().as_tuple().exponent)
        if decimal_places > 8:
            raise ValueError("Price and quantity support at most 8 decimal places.")
        return value
