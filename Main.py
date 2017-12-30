import requests,smtplib,time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

'''
TO DO
1. Use a better currency API
2. Limit the call to currency rate API once every 3 hrs (think over it)
3. Try optimizing using order book top instead of LTP for better picture (wherever possible)
'''

currency_rates = {}
positive_trade_list = []
email_subscriber_list = ["yadipadlakha@gmail.com", "deek.n8@gmail.com", "jksk.mutyala@gmail.com", "nagakiranbj@gmail.com"]
cex_withdrawal_fee = {
    'BTC' : '0.001',
    'BCH' : '0.001',
    'ETH' : '0.01' ,
    'XRP' : '0.02' ,
}
koinex_withdrawal_fee = {
    'BTC' : '0.001',
    'BCH' : '0.001',
    'ETH' : '0.003',
    'XRP' : '0.02' ,
    'LTC' : '0.01',
}
binance_withdrawal_fee = {
    'BTC' : '0.001',
    'BCH' : '0.0005',
    'ETH' : '0.01',
    'XRP' : '0.15' ,
    'LTC' : '0.01',
}

def fill_currency_rate():
    payload = {'q':'USD_INR,GBP_INR'}
    resp_curr = requests.get('https://free.currencyconverterapi.com/api/v5/convert',params=payload)
    dict = resp_curr.json()
    currency_rates['USD'] = dict['results']['USD_INR']['val']
    currency_rates['GBP'] = dict['results']['GBP_INR']['val']

    payload = {'q':'EUR_INR'}
    resp_curr = requests.get('https://free.currencyconverterapi.com/api/v5/convert', params=payload)
    dict = resp_curr.json()
    currency_rates['EUR'] = dict['results']['EUR_INR']['val']
    print(currency_rates)

def straight_trade(cex_crypto,cex_price,cex_curr,koinex_price):
    investment = 100000
    fiat_amt = (investment / float(currency_rates[cex_curr])) * 0.998 #cex trade fee
    fee = 0.042  # bank fee
    total_investment = (investment) * 1.035 * ( 1 + fee )
    profit = ((fiat_amt/float(cex_price)) - float(cex_withdrawal_fee[cex_crypto])) * float(koinex_price) * 0.975 - total_investment #koinex withdr fee
    if profit > 500:
        positive_trade_list.append(cex_crypto + ' in ' + cex_curr + ': ' + str(int(profit)))
    print(cex_crypto + ' in ' + cex_curr + ': ' + str(profit))

def rounded_trade(source_cryp,cex_ltp_dict,koinex_ltp_dict,round_dest_crypto_list):
    investment = 100000
    source_cryp_qty = ((investment)/float(koinex_ltp_dict[source_cryp])) - float(koinex_withdrawal_fee[source_cryp])
    for curr in ['USD','GBP','EUR']:
        if curr in 'GBP' and source_cryp in 'XRP':
            continue
        cex_amt = source_cryp_qty * float(cex_ltp_dict[source_cryp + ':' + curr]) * 0.9975 #cex trade fee
        for dest_cryp in ( cryp for cryp in round_dest_crypto_list if cryp not in source_cryp):
            if curr in 'GBP' and dest_cryp in 'XRP':
                continue
            dest_cryp_qty = (cex_amt/float(cex_ltp_dict[dest_cryp + ':' + curr])) - float(cex_withdrawal_fee[dest_cryp])
            profit = (dest_cryp_qty*float(koinex_ltp_dict[dest_cryp]))*0.975 - (investment) #koinex withdrawal fee
            if profit > 500:
                positive_trade_list.append(source_cryp + '->' + curr + '->' + dest_cryp + ': ' + str(int(profit)))
            print('*' + source_cryp + '->' + curr + '->' + dest_cryp + ': ' + str(profit))

def zed_trade(source_cryp,binance_ltp_dict,koinex_ltp_dict,dest_cryp):
    investment = 100000
    source_cryp_qty = ((investment)/float(koinex_ltp_dict[source_cryp])) - float(koinex_withdrawal_fee[source_cryp])
    for curr in ['BTC','ETH']:
        if (source_cryp == curr):
            dest_cryp_amt = (source_cryp_qty * float(binance_ltp_dict[source_cryp + ':' + dest_cryp]) * 0.999)
            profit_direct = (dest_cryp_amt - float(binance_withdrawal_fee[dest_cryp])) * (float(koinex_ltp_dict[dest_cryp])) * 0.975 - (investment)
            if profit_direct > 0:
                positive_trade_list.append(source_cryp + '->' + dest_cryp + ': ' + str(int(profit_direct)))
            print(source_cryp + '->' + dest_cryp + ': ' + str(profit_direct) + ' %')
            continue
        curr_amt = source_cryp_qty * float(binance_ltp_dict[source_cryp + ':' + curr]) * 0.999
        if (dest_cryp == curr):
            profit_direct_no_third = ((curr_amt-float(binance_withdrawal_fee[curr])) * float(koinex_ltp_dict[curr]) * 0.975) - (investment)
            if profit_direct_no_third > 0:
                positive_trade_list.append(source_cryp + '->' + curr + ': ' + str(int(profit_direct_no_third)) + ' #')
            print(source_cryp + '->' + curr + ': ' + str(profit_direct_no_third) + ' #')
            continue
        dest_cryp_qty = (curr_amt/float(binance_ltp_dict[dest_cryp + ':' + curr]))*0.999 - float(binance_withdrawal_fee[dest_cryp])
        profit = dest_cryp_qty*float(koinex_ltp_dict[dest_cryp]) - (investment*1.0025)
        if profit > 500:
            positive_trade_list.append(source_cryp + '->' + curr + '->' + dest_cryp + ': ' + str(int(profit)))
        print(source_cryp + '->' + curr + '->' + dest_cryp + ': ' + str(profit))

def send_mails():
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login("thatcryptoboy@gmail.com", "CryptoPunter")

    msg = MIMEMultipart()
    msg['Subject'] = 'Profitable Trades Update'
    msg_str = '\n'.join(positive_trade_list)
    msg.attach(MIMEText(msg_str, 'plain'))

    server.sendmail("thatcryptoboy@gmail.com", email_subscriber_list, msg.as_string())
    server.quit()

def main():
    print("hello")
    fill_currency_rate()
    positive_trade_list.append('All profits are on investment on INR 100000 \n')
    resp_koinex = requests.get('https://koinex.in/api/ticker')
    koinex_json_dict = resp_koinex.json()
    koinex_ltp_dict = koinex_json_dict['prices']

    resp_cex = requests.get('https://cex.io/api/tickers/USD/EUR/GBP/ETH')
    cex_json_dict = resp_cex.json()
    cex_ltp_dict = {}
    for k in ( m for m in cex_json_dict['data'] if any(curr in m['pair'] for curr in ['BTC','BCH','ETH','XRP'])):
        cex_ltp_dict[k['pair']] = k['last']
    payload = {'symbol': 'ETHBTC'}  # payload construction for certain data-heavy 'get' operations
    resp_binance = requests.get('https://api.binance.com/api/v3/ticker/price')
    binance_json_dict = resp_binance.json()
    binance_ltp_dict = {}
    for h in (j for j in binance_json_dict if any(j['symbol'].endswith(cryp) for cryp in ['ETH','BTC'])):
        if any(crypto in h['symbol'] for crypto in ['LTC','BCC','XRP','ETHBTC']):
            if 'BCC' in h['symbol']:
                h['symbol'] = h['symbol'].replace('BCC','BCH')
            binance_ltp_dict[h['symbol'][:3] + ':' + h['symbol'][-3:]] = h['price']
            binance_ltp_dict[h['symbol'][-3:] + ':' + h['symbol'][:3]] = str(1/float(h['price']))
    #CODE FOR STRAIGHT TRADE
    positive_trade_list.append('Straight Trades : Buy crypto on CEX with fiat, send and sell on Koinex \n')
    straight_crypto_list = ['ETH','BTC','BCH','XRP']
    straight_currency_list = ['USD','EUR','GBP']
    for cryp in straight_crypto_list:
        for curr in straight_currency_list:
            if cryp == 'XRP' and curr == 'GBP':
                continue
            straight_trade(cryp,cex_ltp_dict[cryp + ':' + curr],curr,koinex_ltp_dict[cryp])
    #CODE FOR U TRADE
    positive_trade_list.append('\nU Trade(round) : Buy crypto1 on koinex, send to CEX, sell and buy crpto2, send crypto2 to koinex n dump\n')
    round_source_crypto_list = ['ETH','BTC','BCH','XRP']
    round_dest_crypto_list = ['ETH','BTC','BCH','XRP']
    for source_cryp in round_source_crypto_list:
        rounded_trade(source_cryp,cex_ltp_dict,koinex_ltp_dict,round_dest_crypto_list)
    #CODE FOR Z TRADE
    positive_trade_list.append('\nZ Trade(exchange) : Buy crypto1 on koinex, send to Binance, change to crypto2 and send to Koinex and dump\n')
    zed_source_crypto_list = ['ETH','BTC','BCH','XRP','LTC']
    zed_dest_crypto_list = ['ETH','BTC','BCH','XRP','LTC']
    for src_cryp in zed_source_crypto_list:
        for dst_cryp in ( q for q in zed_dest_crypto_list if q not in src_cryp):
            zed_trade(src_cryp,binance_ltp_dict,koinex_ltp_dict,dst_cryp)
    positive_trade_list.append('# : Send crypto1 to binance, selling in ETH or BTC, and bring back to dump on Koinex\n')
    send_mails()
    positive_trade_list.clear()

if __name__ == "__main__":
    # while True:
    main()
        # time.sleep(600)