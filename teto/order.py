from __future__ import annotations
from typing import Literal
import uuid

from position import Position


class MarketOrder:
    def __init__(self, size: float, price: float, side: Literal['long', 'short'], tp_price: float | None = None, sl_price: float | None = None, clock=0) -> None:
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

    def check_contract(self, high_price: float, low_price: float) -> bool:
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


class LimitOrder:
    def __init__(self, size: float, price: float, side: Literal['long' , 'short'], tp_price: float | None = None, sl_price: float | None = None, clock=0) -> None:
        self.size = size
        self.price = price
        self.side = side
        self.tp_price = tp_price
        self.sl_price = sl_price
        self.clock = clock

        self.identifier = uuid.uuid4()
    
    def check_contract(self, high_price: float, low_price: float) -> bool:
        
        if self.side == 'long' and self.price <= low_price:
            return True
        elif self.side == 'short' and self.price >= high_price:
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


class StopOrder:
    def __init__(self, size: float, price: float, side: Literal['long', 'short'], tp_price: float | None = None, sl_price: float | None = None, clock=0) -> None:
        self.size = size
        self.price = price
        self.side = side
        self.tp_price = tp_price
        self.sl_price = sl_price
        self.clock = clock

        self.identifier = uuid.uuid4()

    def check_triggering(self, high_price: float, low_price: float) -> bool:
        if self.side == 'long' and self.price >= high_price:
            return True
        elif self.side == 'short' and self.price <= low_price:
            return True
        else:
            return False
    
    def generate_market_order(self) -> MarketOrder:
        return MarketOrder(
            size=self.size,
            price=self.price,
            side=self.side,
            tp_price=self.tp_price,
            sl_price=self.sl_price,
            clock=self.clock
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


class OrderBucket:
    def __init__(self, order: MarketOrder | LimitOrder | StopOrder | None = None) -> None:
        
        self.order_dict: dict[uuid.UUID, MarketOrder | LimitOrder | StopOrder] = {}
        if order is not None:
            self.add(order) # self.order_dict[order.identifier] = order
            
    def add(self, order: MarketOrder | LimitOrder | StopOrder) -> None:
        self.order_dict[order.identifier] = order

    def solve(self, high_price: float, low_price: float) -> list[Position]:
        """
        Return the list of executed orders.
        """

        # 分離: クロックにより、処理するオーダーと処理しないオーダーに分離。
        # -> 処理しないオーダーは、次の処理に回す。
        processing_order_ids: list[uuid.UUID] = [k for k, v in self.order_dict.items() if v.clock > 0]
        unprocessing_order_ids: list[uuid.UUID] = [k for k, v in self.order_dict.items() if v.clock == 0]
        
        # 分離: StopOrderをMarketOrderに変換するため、StopOrderを分離したリストを作成。
        for k in processing_order_ids:
            if not isinstance(self.order_dict[k], StopOrder):
                continue

            if self.order_dict[k].check_triggering(high_price, low_price):
                mo = self.order_dict[k].generate_market_order()
                self.order_dict[k] = mo # IDは変更なしで、オーダーだけ変更する。
        
        # 約定判定処理
        # -> 約定したオーダーは、ポジションに変換し、リストに追加。
        # -> 未約定のオーダーは、次の処理に回す。
        contracted_order_ids: list[uuid.UUID] = []
        uncontracted_order_ids: list[uuid.UUID] = []
        for k in processing_order_ids:
            if isinstance(self.order_dict[k], StopOrder):
                uncontracted_order_ids.append(k)
                continue

            if self.order_dict[k].check_contract(high_price, low_price):
                contracted_order_ids.append(k)
            else:
                uncontracted_order_ids.append(k)
        
        # 約定したオーダーをポジションに変換してリストに追加。
        positions: list[Position] = []
        for k in contracted_order_ids:
            positions.append(self.order_dict[k].generate_position())
  
        # TP/SLオーダーの生成
        # -> 約定したオーダーの中に、TP/SLオーダーが設定されていたら、それを生成。
        tp_sl_order_ids: list[uuid.UUID] = []
        for k in contracted_order_ids:
            if self.order_dict[k].tp_price is not None:
                tp_order = self.order_dict[k].generate_tp_order()
                tp_sl_order_ids.append(tp_order.identifier)
                self.order_dict[tp_order.identifier] = tp_order
        
            if self.order_dict[k].sl_price is not None:
                sl_order = self.order_dict[k].generate_sl_order()
                tp_sl_order_ids.append(sl_order.identifier)
                self.order_dict[sl_order.identifier] = sl_order
        
        # 次のオーダーをセット。
        # -> 未処理（clock==0）のオーダーと、未約定のオーダーと、TP/SLオーダーを、次の処理に渡す。
        next_order_ids = unprocessing_order_ids + uncontracted_order_ids + tp_sl_order_ids
        self.order_dict = {k: v for k, v in self.order_dict.items() if k in next_order_ids}

        # クロックを進める。
        for k in self.order_dict.keys():
            self.order_dict[k].clock += 1
        
        return positions
