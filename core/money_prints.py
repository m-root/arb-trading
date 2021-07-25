import time
from engine.events import *


def printMoney(amountIn, p, gasPrice, profit):
    deadline = int(time.time()) + 600
    tx = printer.functions.printMoney(startToken['address'], amountIn, amountIn, p, deadline).buildTransaction({
        'from': address,
        'value': 0,
        'gasPrice': gasPrice,
        'gas': 1500000,
        "nonce": w3.eth.getTransactionCount(address),
        })
    try:
        gasEstimate = w3.eth.estimateGas(tx)
        print('estimate gas cost:', gasEstimate*gasPrice/1e18)
    except Exception as e:
        print('gas estimate err:', e)
        return None
    if config['start'] == 'usdt' or config['start'] == 'usdc' or config['start'] == 'dai':
        if gasEstimate * gasPrice / 1e18 * 360 >= profit/pow(10, startToken['decimal']):
            print('gas too much, give up...')
            return None
    if config['start'] == 'weth' and gasEstimate * gasPrice >= profit:
        print('gas too much, give up...')
        return None
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=privkey)
    try:
        txhash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return txhash.hex()
    except:
        return None

def flashPrintMoney(amountIn, p, gasPrice, profit):
    tx = printer.functions.flashPrintMoney(startToken['address'], amountIn, p).buildTransaction({
        'from': address,
        'value': 0,
        'gasPrice': gasPrice,
        'gas': 1500000,
        "nonce": w3.eth.getTransactionCount(address),
        })
    try:
        gasEstimate = w3.eth.estimateGas(tx)
        print('estimate gas cost:', gasEstimate*gasPrice/1e18)
    except Exception as e:
        print('gas estimate err:', e)
        return None
    if config['start'] == 'usdt' or config['start'] == 'usdc' or config['start'] == 'dai':
        if gasEstimate * gasPrice / 1e18 * 360 >= profit/pow(10, startToken['decimal']):
            print('gas too much, give up...')
            return None
    if config['start'] == 'weth' and gasEstimate * gasPrice >= profit:
        print('gas too much, give up...')
        return None
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=privkey)
    try:
        txhash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return txhash.hex()
    except:
        return None
