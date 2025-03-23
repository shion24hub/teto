from teto.order import MarketOrder, LimitOrder, StopOrder, OrderBucket

def test_market_order_init():
    mo = MarketOrder(size=1, price=100, side='long', tp_price=200, sl_price=50)

    assert mo.size == 1
    assert mo.price == 100
    assert mo.side == 'long'
    assert mo.tp_price == 200
    assert mo.sl_price == 50
    assert mo.clock == 0

def test_limit_order_init():
    lo = LimitOrder(size=1, price=100, side='long', tp_price=200, sl_price=50)

    assert lo.size == 1
    assert lo.price == 100
    assert lo.side == 'long'

def test_stop_order_init():
    so = StopOrder(size=1, price=100, side='long', tp_price=200, sl_price=50)

    assert so.size == 1
    assert so.price == 100
    assert so.side == 'long'
    assert so.tp_price == 200
    assert so.sl_price == 50
    assert so.clock == 0

def test_market_order_check_contract():
    mo_long = MarketOrder(size=1, price=100, side='long', tp_price=200, sl_price=50)
    mo_short = MarketOrder(size=1, price=100, side='short', tp_price=200, sl_price=50)

    # 常に約定する。
    assert mo_long.check_contract(high_price=150, low_price=50) == True
    assert mo_short.check_contract(high_price=150, low_price=50) == True

def test_limit_order_check_contract():
    lo_long = LimitOrder(size=1, price=100, side='long', tp_price=200, sl_price=50)
    lo_short = LimitOrder(size=1, price=100, side='short', tp_price=200, sl_price=50)

    assert lo_long.check_contract(high_price=150, low_price=50) == True
    assert lo_short.check_contract(high_price=150, low_price=50) == True

def test_stop_order_check_triggering():
    so_long = StopOrder(size=1, price=100, side='long', tp_price=200, sl_price=50)
    so_short = StopOrder(size=1, price=100, side='short', tp_price=200, sl_price=50)

    assert so_long.check_triggering(high_price=150, low_price=50) == True
    assert so_short.check_triggering(high_price=150, low_price=50) == True

def test_order_bucket_add():
    ob = OrderBucket()
    mo_long = MarketOrder(size=1, price=100, side='long', tp_price=200, sl_price=50)
    mo_short = MarketOrder(size=1, price=100, side='short', tp_price=200, sl_price=50)
    lo_long = LimitOrder(size=1, price=100, side='long', tp_price=200, sl_price=50)
    lo_short = LimitOrder(size=1, price=100, side='short', tp_price=200, sl_price=50)
    so_long = StopOrder(size=1, price=100, side='long', tp_price=200, sl_price=50)
    so_short = StopOrder(size=1, price=100, side='short', tp_price=200, sl_price=50)

    ob.add(mo_long)
    ob.add(mo_short)
    ob.add(lo_long)
    ob.add(lo_short)
    ob.add(so_long)
    ob.add(so_short)

    # 正常系
    assert ob.base_order_dict[mo_long.identifier] == mo_long
    assert ob.generative_order_dict[so_long.identifier] == so_long

    # 異常系
    try:
        ob.generative_order_dict[mo_long.identifier]
        assert False
    except KeyError:
        assert True

    try:
        ob.base_order_dict[so_long.identifier]
        assert False
    except KeyError:
        assert True

def test_order_bucket_generative_order_triggering():
    ob = OrderBucket()
    so_long = StopOrder(size=1, price=100, side='long', tp_price=200, sl_price=50, clock=1)
    so_short = StopOrder(size=1, price=100, side='short', tp_price=200, sl_price=50, clock=1)

    ob.add(so_long)
    ob.add(so_short)

    ids = [so_long.identifier, so_short.identifier]
    ob._process_generative_order_triggering(ids, high_price=150, low_price=50) # 両方発火する。

    print(ob.base_order_dict)
    
    assert ob.base_order_dict != {} # 空ではないはず。
    assert ob.generative_order_dict == {} # 空になっているはず。


def test_order_bucket_process_tp_sl_order():
    ob = OrderBucket()
    mo_long = MarketOrder(size=1, price=100, side='long', tp_price=200, sl_price=50, clock=1)

    ob.add(mo_long)

    ob._process_tp_sl_order([mo_long.identifier])

    assert ob.base_order_dict != {} # TPが生成されるので、空ではないはず。
    assert ob.generative_order_dict != {} # SLが生成されるので、空ではないはず。


def test_order_bucket_solve_1():
    ob = OrderBucket()
    mo_long = MarketOrder(size=1, price=100, side='long', tp_price=200, sl_price=50, clock=1)

    ob.add(mo_long)
    new_positions = ob.solve(high_price=150, low_price=50)

    assert len(ob.base_order_dict) == 1 # TPオーダーが生成されるので、空にはなっていない。
    assert len(ob.generative_order_dict) == 1 #SLオーダーが生成されているので、殻に放っていないはず。

    assert len(new_positions) == 1 # 1つのポジションが生成されるはず。

    assert new_positions[0].size == 1
    assert new_positions[0].price == 100
    assert new_positions[0].side == 'long'

def test_order_bucket_solve_2():
    ob = OrderBucket()
    mo_long = MarketOrder(size=1, price=100, side='long', clock=1)

    ob.add(mo_long)
    new_positions = ob.solve(high_price=150, low_price=50)

    assert len(ob.base_order_dict) == 0 # TPオーダーが生成されないので、空になっているはず。
    assert len(ob.generative_order_dict) == 0 #SLオーダーが生成されていないので、空になっているはず。

    assert len(new_positions) == 1 # 1つのポジションが生成されるはず。

    assert new_positions[0].size == 1
    assert new_positions[0].price == 100
    assert new_positions[0].side == 'long'

def test_order_bucket_solve_3():
    ob = OrderBucket()
    mo_long = MarketOrder(size=1, price=100, side='long', clock=1)
    lo_short = LimitOrder(size=1, price=100, side='short', tp_price=200, sl_price=50, clock=1)

    ob.add(mo_long)
    ob.add(lo_short)
    new_positions = ob.solve(high_price=150, low_price=50)

    assert len(ob.base_order_dict) == 1 # TPオーダーが生成されないので、空になっているはず。
    assert len(ob.generative_order_dict) == 1 #SLオーダーが生成されているので、空になっているはず。

    assert len(new_positions) == 2

    assert new_positions[0].size == 1
    assert new_positions[0].price == 100
    assert new_positions[0].side == 'long'
    assert new_positions[1].size == 1
    assert new_positions[1].price == 100
    assert new_positions[1].side == 'short'

