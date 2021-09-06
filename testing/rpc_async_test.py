import timeit
import asyncio

from aiohttp import ClientSession

from web3.providers.base import JSONBaseProvider
from web3.providers import HTTPProvider
from web3 import Web3


import json
# synchronously request receipts for given transactions
def sync_receipts(web3, transactions):
    for tran in transactions:
        web3.eth.getTransactionReceipt(tran)

# asynchronous JSON RPC API request
async def async_make_request(session, url, method, params):
    # print(session)
    # print(url)
    # print(method)
    # print(params)
    '''
    <aiohttp.client.ClientSession object at 0x7fac280b0650>
    http://localhost:8545
    eth_getTransactionReceipt
    ['0xe0b71bedb5ba63625e350c3ff567305320a7902e9cf80852e3830eca968ae3aa']
    '''
    base_provider = JSONBaseProvider()
    request_data = base_provider.encode_rpc_request(method, params)
    async with session.post(url, data=request_data,
                        headers={'Content-Type': 'application/json'}) as response:
        content = await response.read()
    response = base_provider.decode_rpc_response(content)
    return response

async def run(node_address, transactions):
    tasks = []

    # Fetch all responses within one Client session,
    # keep connection alive for all requests.
    async with ClientSession() as session:
        for tran in transactions:
            task = asyncio.ensure_future(async_make_request(session, node_address,
                                                            'eth_getTransactionReceipt',[tran.hex()]))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
'''
if __name__ == "__main__":
    eth_node_address = "http://localhost:8545"
    web3 = Web3(HTTPProvider(eth_node_address))

    block = web3.eth.getBlock(web3.eth.blockNumber)
    transactions = block['transactions']

    start_time = timeit.default_timer()
    sync_receipts(web3, transactions)
    print('sync: {:.3f}s'.format(timeit.default_timer() - start_time))

    start_time = timeit.default_timer()
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run(eth_node_address, transactions))
    loop.run_until_complete(future)
    print('async: {:.3f}s'.format(timeit.default_timer() - start_time))
'''

header = {'headers': {'Content-Type': 'application/json', 'User-Agent': "Web3.py/5.20.1/<class 'core.rpc.BatchHTTPProvider'>"}}


import json

# Opening JSON file
f = open('testing/sample.json', )

# returns JSON object as
# a dictionary
data = json.load(f)




# asyncio.ensure_future(async_make_request(session, node_address, 'eth_getTransactionReceipt',[tran.hex()]))