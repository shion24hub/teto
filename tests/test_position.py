from teto.position import Position, PositionBucket, SolvedTradingResult


def test_bucket_init_normal():
    p1 = Position(size=1, price=100, side='long')
    p2 = Position(size=2, price=200, side='short')
    pb = PositionBucket(long_position=p1, short_position=p2)

    assert pb.pos_long.size == 1
    assert pb.pos_long.price == 100
    assert pb.pos_short.size == 2
    assert pb.pos_short.price == 200


# def test_bucket_init_error():
#     p1 = Position(size=1, price=100, side='long')
#     p2 = Position(size=2, price=200, side='short')
#     try:
#         pb = PositionBucket(long_position=p2, short_position=p1)
#         assert False
#     except ValueError:
#         assert True


def test_position_add_simply():
    pb = PositionBucket()
    p3 = Position(size=3, price=300, side='long')
    pb.add(p3)

    assert pb.pos_long.size == 3
    assert pb.pos_long.price == 300
    assert pb.pos_short.size == 0
    assert pb.pos_short.price == 0

def test_position_add_complex():
    pb = PositionBucket()
    p1 = Position(size=1, price=100, side='long')
    p2 = Position(size=2, price=200, side='short')
    p3 = Position(size=3, price=300, side='long')
    p4 = Position(size=4, price=400, side='short')

    pb.add(p1)
    pb.add(p2)
    pb.add(p3)
    pb.add(p4)

    # 加重平均
    assert pb.pos_long.size == 4
    assert pb.pos_long.price == (1*100 + 3*300) / 4
    assert pb.pos_short.size == 6
    assert pb.pos_short.price == (2*200 + 4*400) / 6

def test_position_solve_remaining_short():
    pb = PositionBucket()
    p1 = Position(size=1, price=100, side='long')
    p2 = Position(size=2, price=200, side='short')
    p3 = Position(size=3, price=300, side='long')
    p4 = Position(size=4, price=400, side='short')

    pb.add(p1)
    pb.add(p2)
    pb.add(p3)
    pb.add(p4)

    print(pb.pos_long)
    print(pb.pos_short)

    result = pb.solve()
    print(pb.pos_long)
    print(pb.pos_short)

    assert pb.pos_long.size == 0
    assert pb.pos_long.price == 0
    assert pb.pos_short.size == 2
    assert pb.pos_short.price == (2*200 + 4*400) / 6

    assert result.size == 4
    assert result.long_price == (1*100 + 3*300) / 4
    assert result.short_price == (2*200 + 4*400) / 6
    assert result.pnl == 4 * ((2*200 + 4*400) / 6 - (1*100 + 3*300) / 4)

def test_position_solve_remaining_long():
    pb = PositionBucket()
    p1 = Position(size=1, price=100, side='short')
    p2 = Position(size=2, price=200, side='long')
    p3 = Position(size=3, price=300, side='long')
    p4 = Position(size=4, price=400, side='long')

    pb.add(p1)
    pb.add(p2)
    pb.add(p3)
    pb.add(p4)

    result = pb.solve()

    assert pb.pos_long.size == 8
    assert pb.pos_long.price == (2*200 + 3*300 + 4*400) / 9
    assert pb.pos_short.size == 0
    assert pb.pos_short.price == 0

    assert result.size == 1
    assert result.long_price == (2*200 + 3*300 + 4*400) / 9
    assert result.short_price == 100
    assert result.pnl == 1 * (100 - (2*200 + 3*300 + 4*400) / 9)

def test_position_solve_nothing():
    pb = PositionBucket()
    p1 = Position(size=1, price=100, side='short')
    p2 = Position(size=2, price=200, side='short')
    p3 = Position(size=3, price=300, side='short')
    p4 = Position(size=4, price=400, side='short')

    pb.add(p1)
    pb.add(p2)
    pb.add(p3)
    pb.add(p4)

    result = pb.solve()

    assert pb.pos_long.size == 0
    assert pb.pos_long.price == 0
    assert pb.pos_short.size == 10
    assert pb.pos_short.price == (1*100 + 2*200 + 3*300 + 4*400) / 10

    assert result.size == 0
    assert result.long_price == 0
    assert result.short_price == 0
    assert result.pnl == 0






    


