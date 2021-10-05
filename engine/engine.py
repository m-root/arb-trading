import os
import json
from settings import *
from web3 import Web3
from web3.exceptions import BadFunctionCallOutput
import re

'''
 Pancakeswap and mdex => BSC
'''

class SwapUtils(object):

    ZERO_ADDRESS = Web3.toHex(0x0)

    @staticmethod
    def sort_tokens(token_a, token_b):
        assert token_a != token_b
        (token_0, token_1) = (token_a, token_b) if int(token_a, 16) < int(token_b, 16) else (token_b, token_a)
        assert token_0 != SwapUtils.ZERO_ADDRESS
        return token_0, token_1

    @staticmethod
    def pair_for(factory, hexstr_prefix, hexstr_suffix,token_a, token_b):
        prefix = Web3.toHex(hexstr=hexstr_prefix)
        encoded_tokens = Web3.solidityKeccak(["address", "address"], SwapUtils.sort_tokens(token_a, token_b))
        suffix = Web3.toHex(hexstr=hexstr_suffix)
        raw = Web3.solidityKeccak(["bytes", "address", "bytes", "bytes"], [prefix, factory, encoded_tokens, suffix])
        return Web3.toChecksumAddress(Web3.toHex(raw)[-40:])
    '''
    hexstr_prefix = "ff"
    hexstr_suffix = 96e8ac4277198ff8b6f785478aa9a39f403cb768dd02cbee326c3e7da348845f
    '''

    @staticmethod
    def calculate_quote(amount_a, reserve_a, reserve_b):
        assert amount_a > 0
        assert reserve_a > 0 and reserve_b > 0
        return amount_a * (reserve_b/reserve_a)

    @staticmethod
    def get_amount_out(amount_in, reserve_in, reserve_out):
        """
        Given an input asset amount, returns the maximum output amount of the
        other asset (accounting for fees) given reserves.
        :param amount_in: Amount of input asset.
        :param reserve_in: Reserve of input asset in the pair contract.
        :param reserve_out: Reserve of input asset in the pair contract.
        :return: Maximum amount of output asset.
        """
        assert amount_in > 0
        assert reserve_in > 0 and reserve_out > 0
        amount_in_with_fee = amount_in*997
        numerator = amount_in_with_fee*reserve_out
        denominator = reserve_in*1000 + amount_in_with_fee
        return float(numerator/denominator)

    @staticmethod
    def get_amount_in(amount_out, reserve_in, reserve_out):
        """
        Returns the minimum input asset amount required to buy the given
        output asset amount (accounting for fees) given reserves.
        :param amount_out: Amount of output asset.
        :param reserve_in: Reserve of input asset in the pair contract.
        :param reserve_out: Reserve of input asset in the pair contract.
        :return: Required amount of input asset.
        """
        assert amount_out > 0
        assert reserve_in > 0 and reserve_out > 0
        numerator = reserve_in*amount_out*1000
        denominator = (reserve_out - amount_out)*997
        return float(numerator/denominator + 1)


class SwapObject(object):

    def __init__(self, address, private_key, swap_name, provider=None):
        self.address = Web3.toChecksumAddress(address)
        self.private_key = private_key
        self.provider = provider
        self.name = swap_name

        if re.match(r'^https*:', self.provider):
            provider = Web3.HTTPProvider(self.provider, request_kwargs={"timeout": 60})
        elif re.match(r'^ws*:', self.provider):
            provider = Web3.WebsocketProvider(self.provider)
        elif re.match(r'^/', self.provider):
            provider = Web3.IPCProvider(self.provider)
        else:
            raise RuntimeError("Unknown provider type " + self.provider)
        self.conn = Web3(provider)
        if not self.conn.isConnected():
            raise RuntimeError("Unable to connect to provider at " + self.provider)
        self.gasPrice = self.conn.toWei(15, "gwei"),

    def _create_transaction_params(self, value=0, gas=1500000):
        return {
            "from": self.address,
            "value": value,
            'gasPrice': self.gasPrice,
            "gas": gas,
            "nonce": self.conn.eth.getTransactionCount(self.address),
        }

    def _send_transaction(self, func, params):
        tx = func.buildTransaction(params)
        signed_tx = self.conn.eth.account.sign_transaction(tx, private_key=self.private_key)
        return self.conn.eth.sendRawTransaction(signed_tx.rawTransaction)


class SwapClient(SwapObject):

    def __init__(self, address, private_key, factory_address, ABI_JSON, ROUTER_ABI_JSON, ERC20_ABI_JSON, PAIR_ABI_JSON, MAX_APPROVAL_INT,provider=None):
        super().__init__(address, private_key, provider)

        self.ABI_JSON = ABI_JSON
        self.ROUTER_ABI_JSON = ROUTER_ABI_JSON
        self.ERC20_ABI_JSON = ERC20_ABI_JSON
        self.PAIR_ABI_JSON = PAIR_ABI_JSON
        self.MAX_APPROVAL_INT = MAX_APPROVAL_INT

        self.ADDRESS = factory_address
        self.ABI = json.load(open(os.path.abspath(f"{os.path.dirname(os.path.abspath(__file__))}"
                                             f"/assests/" + self.ABI_JSON)))

        self.ROUTER_ADDRESS = sushiswap_router_address
        self.ROUTER_ABI = json.load(open(os.path.abspath(f"{os.path.dirname(os.path.abspath(__file__))}/assests/" + self.ROUTER_ABI_JSON)))

        self.MAX_APPROVAL_HEX = "0x" + "f" * 64
        self.MAX_APPROVAL_INT = int(self.MAX_APPROVAL_HEX, 16)
        self.ERC20_ABI = json.load(open(os.path.abspath(f"{os.path.dirname(os.path.abspath(__file__))}/assests/" + self.ERC20_ABI_JSON)))['abi']

        self.PAIR_ABI = json.load(open(os.path.abspath(f"{os.path.dirname(os.path.abspath(__file__))}/assests/" + self.PAIR_ABI_JSON)))['abi']
        self.contract = self.conn.eth.contract(address=Web3.toChecksumAddress(self.ADDRESS), abi=self.ABI) #todo
        self.router = self.conn.eth.contract(
            address=Web3.toChecksumAddress(self.ROUTER_ADDRESS), abi=self.ROUTER_ABI)





    # Utilities
    # -----------------------------------------------------------
    def _is_approved(self, token):
        erc20_contract = self.conn.eth.contract(
            address=Web3.toChecksumAddress(token), abi=self.PAIR_ABI)
        print(erc20_contract, token)
        approved_amount = erc20_contract.functions.allowance(self.address, self.router.address).call()
        return approved_amount >= self.MAX_APPROVAL_INT

    def is_approved(self, token):
        return self._is_approved(token, self.MAX_APPROVAL_INT)

    def approve(self, token):
        if self._is_approved(token, self.MAX_APPROVAL_INT):
            return

        print(f"Approving {self.MAX_APPROVAL_INT} of {token}")
        erc20_contract = self.conn.eth.contract(
            address=Web3.toChecksumAddress(token), abi=self.ERC20_ABI)

        func = erc20_contract.functions.approve(self.router.address,  self.MAX_APPROVAL_INT)
        params = self._create_transaction_params()
        tx = self._send_transaction(func, params)

        try:
            self.conn.eth.waitForTransactionReceipt(tx, timeout=6000)  # TODO raise exception on timeout
        except Exception as e:
            print(e)


    # Factory Read-Only Functions
    # -----------------------------------------------------------
    def get_pair(self, token_a, token_b):
        addr_1 = self.conn.toChecksumAddress(token_a)
        addr_2 = self.conn.toChecksumAddress(token_b)
        return self.contract.functions.getPair(addr_1, addr_2).call()

    def get_pair_by_index(self, pair_index):
        try:
            return self.contract.functions.allPairs(pair_index).call()
        except BadFunctionCallOutput:
            return "0x0000000000000000000000000000000000000000"

    def get_total_num_pairs(self):
        return self.contract.functions.allPairsLength().call()

    def get_fee(self):
        return self.contract.functions.feeTo().call()

    def get_fee_setter(self):
        """
        :return: Address allowed to change the fee.
        """
        return self.contract.functions.feeToSetter().call()


    # Router Read-Only Functions
    # -----------------------------------------------------------
    def get_factory(self, query_chain=False):
        if query_chain:
            return self.router.functions.factory().call()
        return self.ADDRESS

    def get_weth_address(self):
        return self.router.functions.WETH().call()

    # Router State-Changing Functions
    # -----------------------------------------------------------
    def add_liquidity(self, token_a, token_b, amount_a, amount_b, min_a, min_b, to_address, deadline):
        self.approve(token_a, amount_a)
        self.approve(token_b, amount_b)
        func = self.router.functions.addLiquidity(token_a, token_b, amount_a, amount_b, min_a, min_b, to_address, deadline)
        params = self._create_transaction_params(gas=3000000)  #FIXME
        return self._send_transaction(func, params)

    def remove_liquidity(self, token_a, token_b, liquidity, min_a, min_b, to_address, deadline):
        self.approve(self.get_pair(token_a, token_b), liquidity)
        func = self.router.functions.removeLiquidity(token_a, token_b, liquidity, min_a, min_b, to_address, deadline)
        params = self._create_transaction_params()
        return self._send_transaction(func, params)

    def swap_exact_tokens_for_tokens(self, amount, min_out, token_a, token_b, to_address, deadline):
        self.approve(token_a, amount)
        func = self.router.functions.swapExactTokensForTokens(amount, min_out, [token_a,token_b], to_address, deadline)
        params = self._create_transaction_params()
        return self._send_transaction(func, params)

    def swap_tokens_for_exact_tokens(self, amount_out, amount_in_max, token_a, token_b, to, deadline):
        self.approve(token_a, amount_out)
        func = self.router.functions.swapTokensForExactTokens(amount_out, amount_in_max, [token_a,token_b], to, deadline)
        params = self._create_transaction_params()
        return self._send_transaction(func, params)

    # -----------------------------------------------------------
    # Pair Read-Only Functions
    # -----------------------------------------------------------
    def get_token_0(self, pair):
        pair_contract = self.conn.eth.contract(
            address=Web3.toChecksumAddress(pair), abi=self.PAIR_ABI)
        return pair_contract.functions.token0().call()

    def get_token_1(self, pair):
        pair_contract = self.conn.eth.contract(
            address=Web3.toChecksumAddress(pair), abi=self.PAIR_ABI)
        return pair_contract.functions.token1().call()

    def get_reserves(self, token_a, token_b):
        (token0, token1) = SwapUtils.sort_tokens(token_a['address'], token_b['address'])
        pair_contract = self.conn.eth.contract(
            address=Web3.toChecksumAddress(
                self.get_pair(token_a['address'], token_b['address'])),
            abi=self.PAIR_ABI
        )
        reserve = pair_contract.functions.getReserves().call()
        return reserve if token0 == token_a['address'] else [reserve[1], reserve[0], reserve[2]]

    def get_exact_reserves(self, token_a, token_b):
        reserves = self.get_reserves(token_a,token_b)
        reserves = [reserves[0]/10**token_a['decimals'],reserves[1]/10**token_b['decimals'],reserves[2]]
        return reserves

    def get_price_0_cumulative_last(self, pair):
        """
        Gets the cumulative price of the pair calculated relatively
        to token_0.
        """
        pair_contract = self.conn.eth.contract(
            address=Web3.toChecksumAddress(pair), abi=self.PAIR_ABI)
        return pair_contract.functions.price0CumulativeLast().call()

    def get_price_1_cumulative_last(self, pair):
        """
        Gets the cumulative price of the pair calculated relatively
        to token_1.
        """
        pair_contract = self.conn.eth.contract(
            address=Web3.toChecksumAddress(pair), abi=self.PAIR_ABI)
        return pair_contract.functions.price1CumulativeLast().call()

    def get_k_last(self, pair):
        """
        Returns the product of the reserves as of the most recent
        liquidity event.
        """
        pair_contract = self.conn.eth.contract(
            address=Web3.toChecksumAddress(pair), abi=self.PAIR_ABI)
        return pair_contract.functions.kLast().call()

    def get_amounts_out(self, amount_in, path):
        assert len(path) >= 2
        amounts = [amount_in]
        current_amount = amount_in
        for p0, p1 in zip(path, path[1:]):
            r = self.get_reserves(p0, p1)
            current_amount = SwapUtils.get_amount_out(
                current_amount, r[0], r[1]
            )
            amounts.append(current_amount)
        return amounts

    def get_amounts_in(self, amount_out, path):
        assert len(path) >= 2
        amounts = [amount_out]
        current_amount = amount_out
        for p0, p1 in reversed(list(zip(path, path[1:]))):
            r = self.get_reserves(p0, p1)
            current_amount = SwapUtils.get_amount_in(
                current_amount, r[0], r[1]
            )
            amounts.insert(0, current_amount)
        return amounts