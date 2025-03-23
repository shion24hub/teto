"""
オーダーを管理するクラス。
"""

from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Literal
import uuid

from teto.position import Position


class BaseOrder(metaclass=ABCMeta):
    """
    BaseOrder.
    1. オーダー処理の対象になるクラス。MarketOrderとLimitOrderが継承する。
    2. GenerativeOrderが発火条件を満たした場合に生成されるクラス。
    """
    @abstractmethod
    def check_contract(self, high_price: float, low_price: float) -> bool:
        """
        Return True if the order is contracted.
        """
        pass
    
    @abstractmethod
    def generate_position(self) -> Position:
        """
        Return the position object.
        """
        pass
    
    @abstractmethod
    def generate_tp_order(self) -> BaseOrder:
        """
        Return the take profit order object(LimitOrder)
        """
        pass
    
    @abstractmethod
    def generate_sl_order(self) -> BaseOrder:
        """
        Return the stop loss order object(StopOrder)
        """
        pass


class GenerativeOrder(metaclass=ABCMeta):
    """
    GenerativeOrder.
    BaseOrderを生成するオーダーのクラス。StopOrderが継承する。
    """
    @abstractmethod
    def check_triggering(self, high_price: float, low_price: float) -> bool:
        """
        Return True if the order is triggered.
        """
        pass
    
    @abstractmethod
    def generate_base_order(self) -> BaseOrder:
        """
        Return the market order object(MarketOrder)
        """
        pass


class MarketOrder(BaseOrder):
    def __init__(self, size: float, price: float, side: Literal['long', 'short'], tp_price: float | None = None, sl_price: float | None = None, clock=0) -> None:
        """
        <-- INDEX: TEST --> passed.
        """
        self.size = size
        self.price = price
        self.side = side
        self.tp_price = tp_price
        self.sl_price = sl_price
        self.clock = clock

        self.identifier = uuid.uuid4()

    def __repr__(self):
        return f'MarketOrder(size={self.size}, price={self.price}, side={self.side}, tp_price={self.tp_price}, sl_price={self.sl_price}, clock={self.clock})'
    
    def __str__(self):
        return f'MarketOrder(size={self.size}, price={self.price}, side={self.side}, tp_price={self.tp_price}, sl_price={self.sl_price}, clock={self.clock})'
    
    def __eq__(self, other: MarketOrder) -> bool:
        return self.identifier == other.identifier

    def check_contract(self, high_price: float, low_price: float) -> bool:
        """
        <-- INDEX: TEST --> passed.
        """
        # MarketOrderは即時約定する。
        return True

    def generate_position(self) -> Position:
        return Position(
            size=self.size,
            price=self.price,
            side=self.side
        )
    
    def generate_tp_order(self) -> LimitOrder:
        side = 'short' if self.side == 'long' else 'long'

        return LimitOrder(
            size=self.size,
            price=self.tp_price,
            side=side
        )
    
    def generate_sl_order(self) -> StopOrder:
        side = 'short' if self.side == 'long' else 'long'

        return StopOrder(
            size=self.size,
            price=self.sl_price,
            side=side
        )
    
    # 関係し合っている2つのオーダーがあって、どちらかが約定したらもう片方をキャンセルといったような処理ができるようにする。


class LimitOrder(BaseOrder):
    def __init__(self, size: float, price: float, side: Literal['long' , 'short'], tp_price: float | None = None, sl_price: float | None = None, clock=0) -> None:
        """
        <-- INDEX: TEST --> passed.
        """
        self.size = size
        self.price = price
        self.side = side
        self.tp_price = tp_price
        self.sl_price = sl_price
        self.clock = clock

        self.identifier = uuid.uuid4()
    
    def __eq__(self, other: LimitOrder) -> bool:
        return self.identifier == other.identifier
    
    def check_contract(self, high_price: float, low_price: float) -> bool:
        """
        <-- INDEX: TEST --> passed.
        """
        if self.side == 'long' and low_price <= self.price:
            return True
        elif self.side == 'short' and self.price <= high_price:
            return True
        else:
            return False
    
    def generate_position(self) -> Position:
        return Position(
            size=self.size,
            price=self.price,
            side=self.side
        )
    
    def generate_tp_order(self) -> LimitOrder:
        side = 'short' if self.side == 'long' else 'long'

        return LimitOrder(
            size=self.size,
            price=self.tp_price,
            side=side
        )
    
    def generate_sl_order(self) -> StopOrder:
        side = 'short' if self.side == 'long' else 'long'

        return StopOrder(
            size=self.size,
            price=self.sl_price,
            side=side
        )


class StopOrder(GenerativeOrder):
    def __init__(self, size: float, price: float, side: Literal['long', 'short'], tp_price: float | None = None, sl_price: float | None = None, clock=0) -> None:
        """
        <-- INDEX: TEST --> passed.
        """
        self.size = size
        self.price = price
        self.side = side
        self.tp_price = tp_price
        self.sl_price = sl_price
        self.clock = clock

        self.identifier = uuid.uuid4()
    
    def __eq__(self, other: StopOrder) -> bool:
        return self.identifier == other.identifier

    def check_triggering(self, high_price: float, low_price: float) -> bool:
        """
        <-- INDEX: TEST --> passed.
        """
        if self.side == 'long' and high_price >= self.price:
            return True
        elif self.side == 'short' and low_price <= self.price:
            return True
        else:
            return False
    
    def generate_base_order(self) -> MarketOrder:
        return MarketOrder(
            size=self.size,
            price=self.price,
            side=self.side,
            tp_price=self.tp_price,
            sl_price=self.sl_price,
            clock=self.clock
        )


class OrderBucket:
    def __init__(self, order: BaseOrder | GenerativeOrder | None = None) -> None:

        self.base_order_dict: dict[uuid.UUID, BaseOrder] = {}
        self.generative_order_dict: dict[uuid.UUID, GenerativeOrder] = {}
        if order is not None:
            self.add(order)
            
    def add(self, order: BaseOrder | GenerativeOrder) -> None:
        """
        BaseOrderとGenerativeOrderを区別して、それぞれの辞書に追加する。
        <-- INDEX: TEST --> passed.
        """

        if isinstance(order, BaseOrder):
            self.base_order_dict[order.identifier] = order
        elif isinstance(order, GenerativeOrder):
            self.generative_order_dict[order.identifier] = order
        else:
            raise ValueError('order must be BaseOrder or GenerativeOrder.')
    
    def _process_generative_order_triggering(self, ids: list[uuid.UUID], high_price: float, low_price: float) -> None:
        """
        GenerativeOrderの発火イベントの検知。
        -> 発火したGenerativeOrderをBaseOrderに変換して、BaseOrderの辞書に追加。
        -> GenerativeOrderは削除。

        <-- INDEX: TEST --> passed.
        """

        for k in ids:
            if self.generative_order_dict[k].check_triggering(high_price, low_price):
                mo = self.generative_order_dict[k].generate_base_order()
                self.base_order_dict[mo.identifier] = mo
                del self.generative_order_dict[k]

    def _process_base_order_contract(self, ids: list[uuid.UUID], high_price: float, low_price: float) -> list[uuid.UUID]:
        """
        BaseOrderの約定判定処理。
        -> 約定したオーダーのIDを返す。
        """

        contracted_order_ids: list[uuid.UUID] = []
        for k in ids:
            if self.base_order_dict[k].check_contract(high_price, low_price):
                contracted_order_ids.append(k)
        
        return contracted_order_ids
    
    def _convert_base_order_to_position(self, ids: list[uuid.UUID]) -> list[tuple[BaseOrder, Position]]:
        """
        約定したBaseOrderをPositionに変換。
        """

        new_positions: list[tuple[BaseOrder, Position]] = []
        for k in ids:
            order = self.base_order_dict[k]
            new_position = order.generate_position()

            new_positions.append((order, new_position))
        
        return new_positions
    
    def _process_tp_sl_order(self, ids: list[uuid.UUID]) -> None:
        """
        約定したBaseOrderに設定されているTP/SLオーダーを生成。
        -> self.base_order_dict及びself.generative_order_dictに追加。

        <-- INDEX: TEST --> passed.
        """

        for k in ids:
            if self.base_order_dict[k].tp_price is not None:
                tp_order = self.base_order_dict[k].generate_tp_order()

                # TPオーダーはLimitOrderなので、self.base_order_dictに追加。
                self.base_order_dict[tp_order.identifier] = tp_order
        
            if self.base_order_dict[k].sl_price is not None:
                sl_order = self.base_order_dict[k].generate_sl_order()

                # SLオーダーはStopOrderなので、self.generative_order_dictに追加。
                self.generative_order_dict[sl_order.identifier] = sl_order

    def solve(self, high_price: float, low_price: float) -> list[tuple[BaseOrder, Position]]:
        """
        Return the list of executed orders.
        """
        # GenerativeOrderの発火イベントの検知と変換処理。
        # -> 1. 発火したGenerativeOrderをBaseOrderに変換して、self.base_order_dictに追加。
        # -> 2. 発火したGenerativeOrderは、self.generative_order_dictから削除。
        ids_generative_order_to_process: list[uuid.UUID] = [k for k, v in self.generative_order_dict.items() if v.clock > 0]
        self._process_generative_order_triggering(ids_generative_order_to_process, high_price, low_price)

        # BaseOrderの内、処理するもの(clock>0)を取得。
        ids_base_order_to_process: list[uuid.UUID] = [k for k, v in self.base_order_dict.items() if v.clock > 0]
        
        # BaseOrderの約定判定処理
        contracted_order_ids = self._process_base_order_contract(ids_base_order_to_process, high_price, low_price)

        # 約定したBaseOrderをPositionに変換して、リストに格納。
        # new_positions: list[Position] = []
        # for k in contracted_order_ids:
        #     new_positions.append(self.base_order_dict[k].generate_position())
        new_positions = self._convert_base_order_to_position(contracted_order_ids)

        # 約定したBaseOrderに設定されているTP/SLオーダーの処理。
        # -> 1. TPオーダーが生成され、self.base_order_dictに追加。
        # -> 2. SLオーダーが生成され、self.generative_order_dictに追加。
        self._process_tp_sl_order(contracted_order_ids)

        # self.base_order_dictを更新（self.generative_order_dictは変更なし)。
        # -> 1. 約定したBaseOrderを削除。
        self.base_order_dict = {k: v for k, v in self.base_order_dict.items() if k not in contracted_order_ids}

        # self.base_order_dictとself.generative_order_dictのclockを更新。
        for k in self.base_order_dict.keys():
            self.base_order_dict[k].clock += 1
        for k in self.generative_order_dict.keys():
            self.generative_order_dict[k].clock += 1

        return new_positions
