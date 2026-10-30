from decimal import Decimal

import pytest

from app.matching.models import (
    DuplicateOrderId,
    MatchingError,
    OrderNotFound,
    OrderNotOpen,
    OrderStatus,
    Side,
)
from app.matching.order_book import OrderBook


def test_crossing_order_executes_at_resting_maker_price():
    book = OrderBook("BTC/USDT")
    book.submit("ask-1", Side.SELL, "100", "2")

    incoming, trades = book.submit("bid-1", Side.BUY, "105", "1")

    assert incoming.status is OrderStatus.FILLED
    assert len(trades) == 1
    assert trades[0].price == Decimal("100")
    assert trades[0].quantity == Decimal("1")
    assert trades[0].buy_order_id == "bid-1"
    assert trades[0].sell_order_id == "ask-1"
    assert trades[0].maker_order_id == "ask-1"
    assert book.get_order("ask-1").remaining_quantity == Decimal("1")
    assert book.get_order("ask-1").status is OrderStatus.PARTIALLY_FILLED


def test_better_price_has_priority_over_earlier_worse_price():
    book = OrderBook("BTC/USDT")
    book.submit("ask-worse", Side.SELL, "102", "1")
    book.submit("ask-better", Side.SELL, "100", "1")

    _, trades = book.submit("bid", Side.BUY, "102", "1")

    assert len(trades) == 1
    assert trades[0].sell_order_id == "ask-better"
    assert trades[0].price == Decimal("100")


def test_fifo_priority_at_same_price_and_partial_fills():
    book = OrderBook("BTC/USDT")
    book.submit("ask-first", Side.SELL, "100", "1")
    book.submit("ask-second", Side.SELL, "100", "2")

    incoming, trades = book.submit("bid", Side.BUY, "100", "1.5")

    assert [trade.sell_order_id for trade in trades] == ["ask-first", "ask-second"]
    assert [trade.quantity for trade in trades] == [Decimal("1"), Decimal("0.5")]
    assert incoming.status is OrderStatus.FILLED
    assert book.get_order("ask-first").status is OrderStatus.FILLED
    assert book.get_order("ask-second").remaining_quantity == Decimal("1.5")
    assert book.get_order("ask-second").status is OrderStatus.PARTIALLY_FILLED


def test_partially_filled_incoming_order_rests_with_remaining_quantity():
    book = OrderBook("BTC/USDT")
    book.submit("bid-maker", Side.BUY, "100", "2")

    incoming, trades = book.submit("ask-taker", Side.SELL, "99", "0.75")

    assert len(trades) == 1
    assert trades[0].price == Decimal("100")
    assert incoming.status is OrderStatus.FILLED
    assert book.get_order("bid-maker").remaining_quantity == Decimal("1.25")
    assert book.get_order("bid-maker").status is OrderStatus.PARTIALLY_FILLED


def test_partially_filled_incoming_sell_rests_when_its_quantity_exceeds_liquidity():
    book = OrderBook("BTC/USDT")
    book.submit("bid-maker", Side.BUY, "100", "0.5")

    incoming, trades = book.submit("ask-taker", Side.SELL, "99", "2")

    assert len(trades) == 1
    assert incoming.status is OrderStatus.PARTIALLY_FILLED
    assert incoming.remaining_quantity == Decimal("1.5")
    assert book.snapshot()["asks"][0]["quantity"] == "1.5"


def test_cancel_removes_open_order_and_preserves_audit_state():
    book = OrderBook("BTC/USDT")
    book.submit("resting-ask", Side.SELL, "100", "2")

    canceled = book.cancel("resting-ask")

    assert canceled.status is OrderStatus.CANCELED
    assert canceled.remaining_quantity == Decimal("2")
    assert book.snapshot()["asks"] == []
    with pytest.raises(OrderNotOpen):
        book.cancel("resting-ask")


def test_filled_or_missing_orders_cannot_be_canceled():
    book = OrderBook("BTC/USDT")
    book.submit("ask", Side.SELL, "100", "1")
    book.submit("bid", Side.BUY, "100", "1")

    with pytest.raises(OrderNotOpen):
        book.cancel("ask")
    with pytest.raises(OrderNotFound):
        book.cancel("missing")


@pytest.mark.parametrize(
    ("price", "quantity"),
    [
        ("0", "1"),
        ("100", "0"),
        ("-1", "1"),
        ("NaN", "1"),
        ("100.000000001", "1"),
    ],
)
def test_invalid_price_or_quantity_is_rejected(price, quantity):
    book = OrderBook("BTC/USDT")
    with pytest.raises(MatchingError):
        book.submit("invalid", Side.BUY, price, quantity)


def test_binary_float_values_are_rejected():
    book = OrderBook("BTC/USDT")
    with pytest.raises(MatchingError):
        book.submit("float-price", Side.BUY, 0.1, "1")


def test_order_ids_cannot_be_reused():
    book = OrderBook("BTC/USDT")
    book.submit("duplicate", Side.BUY, "100", "1")
    with pytest.raises(DuplicateOrderId):
        book.submit("duplicate", Side.BUY, "99", "1")


def test_book_never_remains_crossed_after_a_matching_command():
    book = OrderBook("BTC/USDT")
    book.submit("bid", Side.BUY, "101", "1")
    book.submit("ask", Side.SELL, "100", "1")
    snapshot = book.snapshot()
    assert not snapshot["bids"] or not snapshot["asks"]
    book.assert_invariants()


def test_same_order_sequence_replays_to_identical_trades_and_book():
    commands = [
        ("ask-1", Side.SELL, "101", "1"),
        ("ask-2", Side.SELL, "100", "2"),
        ("bid-1", Side.BUY, "101", "1.5"),
        ("bid-2", Side.BUY, "98", "3"),
    ]

    def replay():
        book = OrderBook("BTC/USDT")
        for command in commands:
            book.submit(*command)
        return book

    first, second = replay(), replay()
    assert first.trades == second.trades
    assert first.snapshot() == second.snapshot()
    assert [order.sequence for order in first._orders.values()] == [1, 2, 3, 4]



def test_partially_filled_resting_order_can_be_canceled():
    book = OrderBook("BTC/USDT")
    book.submit("resting-ask", Side.SELL, "100", "2")
    book.submit("small-bid", Side.BUY, "100", "0.5")

    canceled = book.cancel("resting-ask")

    assert canceled.status is OrderStatus.CANCELED
    assert canceled.filled_quantity == Decimal("0.5")
    assert canceled.remaining_quantity == Decimal("1.5")
    assert book.snapshot()["asks"] == []
    book.assert_invariants()


from hypothesis import given, settings, strategies as st


@given(
    st.lists(
        st.tuples(
            st.sampled_from(["BUY", "SELL"]),
            st.integers(min_value=1, max_value=500),
            st.integers(min_value=1, max_value=25),
        ),
        min_size=1,
        max_size=60,
    )
)
@settings(max_examples=100, deadline=None)
def test_generated_order_streams_preserve_fill_conservation_and_book_invariants(commands):
    book = OrderBook("BTC/USDT")
    for index, (side, price, quantity) in enumerate(commands, start=1):
        book.submit(f"generated-{index}", side, str(price), str(quantity))
        book.assert_invariants()

    executed_quantity = sum((trade.quantity for trade in book.trades), Decimal("0"))
    buy_filled = sum(
        (order.filled_quantity for order in book._orders.values() if order.side is Side.BUY),
        Decimal("0"),
    )
    sell_filled = sum(
        (order.filled_quantity for order in book._orders.values() if order.side is Side.SELL),
        Decimal("0"),
    )

    assert buy_filled == executed_quantity
    assert sell_filled == executed_quantity
    assert not book.snapshot()["bids"] or not book.snapshot()["asks"] or (
        Decimal(book.snapshot()["bids"][0]["price"])
        < Decimal(book.snapshot()["asks"][0]["price"])
    )
