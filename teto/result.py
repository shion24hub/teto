

class SolvedTradingResult:
    def __init__(self, size: float, long_price: float, short_price: float, pnl: float) -> None:
        self.size = size
        self.long_price = long_price
        self.short_price = short_price
        self.pnl = pnl