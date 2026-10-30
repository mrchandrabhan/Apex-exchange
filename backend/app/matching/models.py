from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"


class MatchingError(ValueError):
    """Base exception for invalid matching-engine operations."""


class DuplicateOrderId(MatchingError):
    pass


class OrderNotFound(MatchingError):
    pass


class OrderNotOpen(MatchingError):
    pass


def to_decimal(value: Decimal | str | int, field_name: str) -> Decimal:
    if isinstance(value, float):
        raise MatchingError(f"{field_name} must not be supplied as a binary float.")
    try:
        parsed = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise MatchingError(f"{field_name} must be a valid decimal value.") from exc

    if not parsed.is_finite():
        raise MatchingError(f"{field_name} must be finite.")
    if parsed <= 0:
        raise MatchingError(f"{field_name} must be greater than zero.")
    decimal_places = max(0, -parsed.normalize().as_tuple().exponent)
    if decimal_places > 8:
        raise MatchingError(f"{field_name} supports at most 8 decimal places.")
    return parsed


@dataclass
class Order:
    order_id: str
    symbol: str
    side: Side
    price: Decimal
    quantity: Decimal
    remaining_quantity: Decimal
    sequence: int
    status: OrderStatus = OrderStatus.OPEN

    @property
    def filled_quantity(self) -> Decimal:
        return self.quantity - self.remaining_quantity


@dataclass(frozen=True)
class Trade:
    trade_id: str
    symbol: str
    price: Decimal
    quantity: Decimal
    buy_order_id: str
    sell_order_id: str
    maker_order_id: str
    taker_order_id: str
    sequence: int
