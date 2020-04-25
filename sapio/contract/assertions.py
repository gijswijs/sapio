from sapio.bitcoinlib.static_types import Amount, Sats


class WithinFee:
    fee_modifier : Amount = Sats(100)

    def __init__(self, contract, b):
        print(contract.amount_range)
        print(contract)
        if contract.amount_range[0] + self.fee_modifier < b:
            raise ValueError("Contract May Burn Funds!")

    @classmethod
    def change_fee_modifier(cls, fee_modifier):
        cls.fee_modifier = fee_modifier


class HasEnoughFunds:
    def __init__(self, contract, b):
        if contract.amount_range[1] > b:
            raise ValueError("Insufficient Funds", "Contract May Burn Funds!", contract, contract.amount_range, b)