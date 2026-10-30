from collections import deque
from decimal import Decimal
from typing import Deque

from app.matching.models import (
    DuplicateOrderId,
    MatchingError,
    Order,
    OrderNotFound,
    OrderNotOpen,
    OrderStatus,
    Side,
    Trade,
    to_decimal,
)


class OrderBook:
    """Deterministic in-memory limit-order book for one simulated market.

    Better prices execute first. Orders at the same price execute FIFO by the
    monotonically increasing acceptance sequence. Trades execute at the resting
    maker order's price. This implementation is single-process and in-memory;
    it is a correctness-focused learning engine, not a production exchange.
    """

    def __init__(self, symbol: str) -> None:
        if not symbol or "/" not in symbol:
            raise MatchingError("A market symbol such as BTC/USDT is required.")
        self.symbol = symbol.upper()
        self._bids: dict[Decimal, Deque[Order]] = {}
        self._asks: dict[Decimal, Deque[Order]] = {}
        self._orders: dict[str, Order] = {}
        self._trades: list[Trade] = []
        self._order_sequence = 0
        self._trade_sequence = 0

    def submit(
        self,
        order_id: str,
        side: Side | str,
        price: Decimal | str | int,
        quantity: Decimal | str | int,
    ) -> tuple[Order, list[Trade]]:
        if not order_id or len(order_id) > 64:
            raise MatchingError("order_id must contain 1 to 64 characters.")
        if order_id in self._orders:
            raise DuplicateOrderId(f"Order ID '{order_id}' has already been used.")

        try:
            order_side = side if isinstance(side, Side) else Side(str(side).upper())
        except ValueError as exc:
            raise MatchingError("side must be BUY or SELL.") from exc

        order_price = to_decimal(price, "price")
        order_quantity = to_decimal(quantity, "quantity")

        self._order_sequence += 1
        incoming = Order(
            order_id=order_id,
            symbol=self.symbol,
            side=order_side,
            price=order_price,
            quantity=order_quantity,
            remaining_quantity=order_quantity,
            sequence=self._order_sequence,
        )
        self._orders[order_id] = incoming

        generated = self._match(incoming)
        if incoming.remaining_quantity == 0:
            incoming.status = OrderStatus.FILLED
        elif incoming.filled_quantity > 0:
            incoming.status = OrderStatus.PARTIALLY_FILLED
            self._add_to_book(incoming)
        else:
            incoming.status = OrderStatus.OPEN
            self._add_to_book(incoming)

        self.assert_invariants()
        return incoming, generated

    def _match(self, incoming: Order) -> list[Trade]:
        opposite = self._asks if incoming.side is Side.BUY else self._bids
        generated: list[Trade] = []

        while incoming.remaining_quantity > 0 and opposite:
            best_price = min(opposite) if incoming.side is Side.BUY else max(opposite)
            crosses = (
                incoming.price >= best_price
                if incoming.side is Side.BUY
                else incoming.price <= best_price
            )
            if not crosses:
                break

            level = opposite[best_price]
            maker = level[0]
            executed = min(incoming.remaining_quantity, maker.remaining_quantity)

            incoming.remaining_quantity -= executed
            maker.remaining_quantity -= executed
            if maker.remaining_quantity == 0:
                maker.status = OrderStatus.FILLED
                level.popleft()
            else:
                maker.status = OrderStatus.PARTIALLY_FILLED

            self._trade_sequence += 1
            if incoming.side is Side.BUY:
                buy_order_id, sell_order_id = incoming.order_id, maker.order_id
            else:
                buy_order_id, sell_order_id = maker.order_id, incoming.order_id

            trade = Trade(
                trade_id=f"{self.symbol.replace('/', '-')}-T{self._trade_sequence:08d}",
                symbol=self.symbol,
                price=maker.price,
                quantity=executed,
                buy_order_id=buy_order_id,
                sell_order_id=sell_order_id,
                maker_order_id=maker.order_id,
                taker_order_id=incoming.order_id,
                sequence=self._trade_sequence,
            )
            self._trades.append(trade)
            generated.append(trade)

            if not level:
                del opposite[best_price]

        return generated

    def _add_to_book(self, order: Order) -> None:
        book = self._bids if order.side is Side.BUY else self._asks
        book.setdefault(order.price, deque()).append(order)

    def cancel(self, order_id: str) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise OrderNotFound(f"Order '{order_id}' was not found.")
        if order.status not in {OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED}:
            raise OrderNotOpen(
                f"Order '{order_id}' cannot be canceled from status {order.status.value}."
            )

        book = self._bids if order.side is Side.BUY else self._asks
        level = book.get(order.price)
        if level is None:
            raise MatchingError("Open order is missing from its price level.")
        try:
            level.remove(order)
        except ValueError as exc:
            raise MatchingError("Open order is missing from its price level.") from exc
        if not level:
            del book[order.price]

        order.status = OrderStatus.CANCELED
        self.assert_invariants()
        return order

    def get_order(self, order_id: str) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise OrderNotFound(f"Order '{order_id}' was not found.")
        return order

    @property
    def trades(self) -> tuple[Trade, ...]:
        return tuple(self._trades)

    def snapshot(self, depth: int = 20) -> dict:
        if depth < 1 or depth > 100:
            raise MatchingError("depth must be between 1 and 100.")

        def levels(book: dict[Decimal, Deque[Order]], reverse: bool) -> list[dict]:
            result = []
            for price in sorted(book, reverse=reverse)[:depth]:
                orders = book[price]
                result.append(
                    {
                        "price": str(price),
                        "quantity": str(sum((o.remaining_quantity for o in orders), Decimal("0"))),
                        "order_count": len(orders),
                    }
                )
            return result

        return {
            "symbol": self.symbol,
            "bids": levels(self._bids, reverse=True),
            "asks": levels(self._asks, reverse=False),
        }

    def assert_invariants(self) -> None:
        if self._bids and self._asks and max(self._bids) >= min(self._asks):
            raise AssertionError("Order book cannot remain crossed after matching.")

        seen: set[str] = set()
        for side, book in ((Side.BUY, self._bids), (Side.SELL, self._asks)):
            for price, queue in book.items():
                last_sequence = 0
                for order in queue:
                    if order.order_id in seen:
                        raise AssertionError("An active order appears more than once.")
                    seen.add(order.order_id)
                    if order.side is not side or order.price != price:
                        raise AssertionError("Order is stored on the wrong book side or price.")
                    if order.remaining_quantity <= 0:
                        raise AssertionError("An active order must have positive remaining quantity.")
                    if order.sequence <= last_sequence:
                        raise AssertionError("Orders at one price level must remain FIFO.")
                    last_sequence = order.sequence

        for order in self._orders.values():
            if order.filled_quantity < 0 or order.filled_quantity > order.quantity:
                raise AssertionError("Filled quantity must stay within original quantity.")
            active = order.status in {OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED}
            if active != (order.order_id in seen):
                raise AssertionError("Order status and active book membership disagree.")
            if order.status is OrderStatus.FILLED and order.remaining_quantity != 0:
                raise AssertionError("Filled orders must have zero remaining quantity.")
            if order.status is OrderStatus.CANCELED and order.remaining_quantity <= 0:
                raise AssertionError("Canceled orders must retain positive unfilled quantity.")
