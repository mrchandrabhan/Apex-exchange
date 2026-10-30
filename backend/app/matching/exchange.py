from app.matching.models import DuplicateOrderId, MatchingError, Order, Trade
from app.matching.order_book import OrderBook


class SimulatedExchange:
    """A set of independent in-memory books for the configured demo markets."""

    def __init__(self, symbols: list[str]) -> None:
        if not symbols:
            raise MatchingError("At least one simulated market is required.")
        self.books = {symbol.upper(): OrderBook(symbol) for symbol in symbols}
        self.order_markets: dict[str, str] = {}

    def get_book(self, symbol: str) -> OrderBook:
        market = self.books.get(symbol.upper())
        if market is None:
            raise MatchingError(f"Unknown market '{symbol}'.")
        return market

    def submit(
        self, order_id: str, symbol: str, side: str, price, quantity
    ) -> tuple[Order, list[Trade]]:
        if order_id in self.order_markets:
            raise DuplicateOrderId(f"Order ID '{order_id}' has already been used.")
        book = self.get_book(symbol)
        order, trades = book.submit(order_id, side, price, quantity)
        self.order_markets[order_id] = book.symbol
        return order, trades

    def get_order(self, order_id: str) -> Order:
        symbol = self.order_markets.get(order_id)
        if symbol is None:
            raise MatchingError(f"Order '{order_id}' was not found.")
        return self.books[symbol].get_order(order_id)

    def cancel(self, order_id: str) -> Order:
        symbol = self.order_markets.get(order_id)
        if symbol is None:
            raise MatchingError(f"Order '{order_id}' was not found.")
        return self.books[symbol].cancel(order_id)

    def reset(self) -> None:
        self.books = {symbol: OrderBook(symbol) for symbol in self.books}
        self.order_markets.clear()
