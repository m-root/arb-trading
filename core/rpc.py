from web3 import HTTPProvider
from web3._utils.request import make_post_request, async_make_post_request
from settings.settings import *
from utilities.abi.uniswap_pair import abi as pair_abi
from settings.settings import address_factory_contract
from utilities.abi.uniswap_factory import abi as factory_abi
from typing import List, Dict, Union, Iterable


def generate_json_rpc(method, params, request_id=1):
    return {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': request_id,
    }


def generate_get_block_by_number_json_rpc(block_numbers, include_transactions):
    for idx, block_number in enumerate(block_numbers):
        yield generate_json_rpc(
            method='eth_getBlockByNumber',
            params=[hex(block_number), include_transactions],
            request_id=idx
        )


class RetriableValueError(Exception):
    def __init__(self, error_message):
        self.__error_message = error_message

    def __str__(self):
        return self.__error_message


def generate_get_reserves_json_rpc(pairs, blockNumber='latest'):
    c = web3_ins.eth.contract(abi=factory_abi.abi())
    for pair in pairs:
        yield generate_json_rpc(
            method='eth_call',
            params=[{
                'to': pair['address'],
                'data': c.encodeABI(fn_name='getReserves', args=[]),
            },
                hex(blockNumber) if blockNumber != 'latest' else 'latest',
            ]
        )


def generate_get_receipt_json_rpc(transaction_hashes):
    for idx, transaction_hash in enumerate(transaction_hashes):
        yield generate_json_rpc(
            method='eth_getTransactionReceipt',
            params=[transaction_hash],
            request_id=idx
        )


def rpc_response_batch_to_results(response):
    for response_item in response:
        yield rpc_response_to_result(response_item)


def rpc_response_to_result(response):
    result = response.get('result')
    if result is None:
        error_message = 'result is None in response {}.'.format(response)
        if response.get('error') is None:
            error_message = error_message + ' Make sure Ethereum node is synced.'
            # When nodes are behind a load balancer it makes sense to retry the request in hopes it will go to other,
            # synced node
            raise RetriableValueError(error_message)
        elif response.get('error') is not None:
            # elif response.get('error') is not None and is_retriable_error(response.get('error').get('code')):
            raise RetriableValueError(error_message)
        raise ValueError(error_message)
    return result


class BatchHTTPProvider(HTTPProvider):

    def make_batch_request(self, text):
        self.logger.debug("Making request HTTP. URI: %s, Request: %s",
                          self.endpoint_uri, text)
        request_data = text.encode('utf-8')
        print('----------------------------')
        # print(request_data)
        print(self.get_request_kwargs())
        print('-----------------------------')

        # print(self.get_request_kwargs())
        # print((request_data))
        raw_response = async_make_post_request(
            # self.endpoint_uri,
            # "https://mainnet.infura.io/v3/3ccfb5a8cc7349239102c9600827044b",
            "http://127.0.0.1:8545",
            request_data,
            **self.get_request_kwargs()
        )
        print(type(raw_response))
        response = self.decode_rpc_response(raw_response)
        self.logger.debug("Getting response HTTP. URI: %s, "
                          "Request: %s, Response: %s",
                          self.endpoint_uri, text, response)
        return response


# from web3 import HTTPProvider
# from web3._utils.request import make_post_request
# from web3 import Web3
# from typing import List, Dict, Union, Iterable
#
# from utilities.abi.uniswap_pair import abi as pair_abi
# from settings.settings import address_factory_contract
# from utilities.abi.uniswap_factory import abi as factory_abi
#
# def generate_json_rpc(method:str, params:Union[Dict, List, str, None], request_id=1)->Dict:
#     return {
#         'jsonrpc': '2.0',
#         'method': method,
#         'params': params,
#         'id': request_id,
#     }
#
# def generate_get_block_by_number_json_rpc(block_numbers:List[Union[int,str]], include_transactions:bool)->Iterable[int]:
#     for idx, block_number in enumerate(block_numbers):
#         yield generate_json_rpc(
#             method='eth_getBlockByNumber',
#             params=[hex(block_number), include_transactions],
#             request_id=idx
#         )
#
def generate_get_pair_token01_json_rpc(pairs_address: List[str], token01_fun_topic: str,
                                       blockNumber: Union[int, str] = 'latest') -> Iterable[Dict]:
    for pair in pairs_address:
        yield generate_json_rpc(
            method='eth_call',
            params=[{
                'to': pair,
                'data': '{}'.format(token01_fun_topic[0:10]),
            },
                hex(blockNumber) if blockNumber != 'latest' else 'latest',
            ]
        )


def generate_get_allpairs_json_rpc(web3_ins: Web3, blockNumber: Union[int, str] = 'latest') -> Iterable[Dict]:
    c2 = web3_ins.eth.contract(abi=factory_abi.abi(), address=address_factory_contract)
    topic = factory_abi.topic("allPairs")
    num = c2.functions.allPairsLength().call()
    for n in range(0, num):
        yield generate_json_rpc(
            method='eth_call',
            params=[{
                'to': address_factory_contract,
                'data': '{}{:0>64s}'.format(topic[0:10], hex(n)[2:]),
            },
                hex(blockNumber) if blockNumber != 'latest' else 'latest',
            ]
        )


def generate_get_reserves_json_rpc(web3_ins: Web3, pairs: List[Dict], blockNumber: Union[int, str] = 'latest') -> \
Iterable[Dict]:
    c = web3_ins.eth.contract(abi=pair_abi.abi())
    for pair in pairs:
        yield generate_json_rpc(
            method='eth_call',
            params=[{
                'to': pair['address'],
                'data': c.encodeABI(fn_name='getReserves', args=[]),
            },
                hex(blockNumber) if blockNumber != 'latest' else 'latest',
            ]
        )


# def generate_get_receipt_json_rpc(transaction_hashes:List[str])->Iterable[Dict]:
#     for idx, transaction_hash in enumerate(transaction_hashes):
#         yield generate_json_rpc(
#             method='eth_getTransactionReceipt',
#             params=[transaction_hash],
#             request_id=idx
#         )
#
# def rpc_response_batch_to_results(response:List[Dict]):
#     for response_item in response:
#         yield rpc_response_to_result(response_item)
#
# class RetriableValueError(Exception):
#     def __init__(self, error_message):
#         self.__error_message = error_message
#     def __str__(self):
#         return self.__error_message
#
# def rpc_response_to_result(response:Dict):
#     result = response.get('result')
#     if result is None:
#         error_message = 'result is None in response {}.'.format(response)
#         if response.get('error') is None:
#             error_message = error_message + ' Make sure Ethereum node is synced.'
#
#             raise RetriableValueError(error_message)
#         elif response.get('error') is not None:
#             raise RetriableValueError(error_message)
#         raise ValueError(error_message)
#     return result
#
# class BatchHTTPProvider(HTTPProvider):
#
#     def make_batch_request(self, text:str):
#         self.logger.debug("Making request HTTP. URI: %s, Request: %s",
#                           self.endpoint_uri, text)
#         request_data = text.encode('utf-8')
#         print(request_data)
#         raw_response = make_post_request(
#             '"https://mainnet.infura.io/v3/3ccfb5a8cc7349239102c9600827044b",',
#             # self.endpoint_uri,
#             request_data,
#             **self.get_request_kwargs()
#         )
#         response = self.decode_rpc_response(raw_response)
#         self.logger.debug("Getting response HTTP. URI: %s, "
#                           "Request: %s, Response: %s",
#                           self.endpoint_uri, text, response)
#         return response
# '''
# class BatchHTTPProvider(HTTPProvider):
#
#     def make_batch_request(self, text:str):
#         self.logger.debug("Making request HTTP. URI: %s, Request: %s",
#                           self.endpoint_uri, text)
#         request_data = text.encode('utf-8')
#         raw_response = make_post_request(
#             self.endpoint_uri,
#             request_data,
#             **self.get_request_kwargs()
#         )
#         response = self.decode_rpc_response(raw_response)
#         self.logger.debug("Getting response HTTP. URI: %s, "
#                           "Request: %s, Response: %s",
#                           self.endpoint_uri, text, response)
#         return response
#         http://35.75.19.200:8545
# '''

'''
{'jsonrpc': '2.0', 'method': 'eth_call', 'params': [{'to': '0xa1C8cB30C113281B8E6b6bD8d0e3b9827B8B4488', 'data': '0x0902f1ac'}, 'latest'], 'id': 1}
'''
