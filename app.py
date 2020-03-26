import decimal

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    # return render_template('index.html')
    # 선택자 정보
    name = '#giName'
    price = 'body > div:nth-child(1) > div > div:nth-child(1) > header > div.stockInfoB > ul > div > div > li:nth-child(2) > div > span.stkN > strong > span'

    # 표준요율
    res = requests.get('https://www.kisrating.com/ratingsStatistics/statics_spread.do')
    soup = BeautifulSoup(res.content, 'html.parser')
    standard_rate = decimal.Decimal(
        soup.select('#con_tab1 > div.table_ty1 > table > tbody > tr:nth-child(11) > td:nth-child(9)')[
            0].text) / decimal.Decimal('100')

    ticker_list = ['000660', '091990', '035760', '263750', '253450', '218410',
                   '247540', '005380', '035720', '207940', '002790', '073490',
                   '000270', '051910', '036570', '006400', '035420', '138080',
                   '009150', '018260', '032500', '230360', '039440', '178320',
                   '033290', '036490', '008770', '018250', '089030', '012330',
                   '192820', '097520', '005930', '068270', '089010', '139480',
                   '060250', '086450', '058470', '009830', '035900', '088800',
                   '035720', '046890', '005380', '215200', '066570', '090430',
                   '033640', '050890', '264450', '039560', '020150', '096770',
                   '003670', '090460',
                   ]
    ticker_list = list(set(ticker_list))

    # 종목별 정보
    info_list = []
    for ticker in ticker_list:
        info = {}
        info["ticker"] = ticker
        # 카카오스탁 정보
        kakao_res = requests.get('https://stockplus.com/api/securities/KOREA-A' + ticker + '.json')
        info["price"] = decimal.Decimal(kakao_res.json()["recentSecurity"]["displayedPrice"])
        info["name"] = kakao_res.json()["recentSecurity"]["name"]
        info["market"] = kakao_res.json()["recentSecurity"]["market"]

        # 에프앤가이드 정보
        fnUrl = 'http://comp.fnguide.com/SVO2/asp/SVD_Main.asp?pGB=1&gicode=A' + ticker + '&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701'
        fnguide_res = requests.get(fnUrl)
        fnguide_soup = BeautifulSoup(fnguide_res.content, 'html.parser')

        # svdMainGrid1 > table > tbody > tr:nth-child(4) > td:nth-child(2)
        info["stock_sum"] = decimal.Decimal(fnguide_soup.select('#svdMainGrid1 > table > tbody > tr:nth-child(4) > td:nth-child(2)')[0].text.replace(",", ""))

        isLink = fnguide_soup.select('#highlight_B_A')[0].attrs['style'] == 'display:none;'
        info["volume"] = decimal.Decimal(fnguide_soup.select('#highlight_D_Y > table > tbody > tr:nth-child(10) > td:nth-child(6)')[0].text.replace(",", ""))
        # 2년후
        info["roe21"] = decimal.Decimal(fnguide_soup.select('#highlight_D_Y > table > tbody > tr:nth-child(18) > td:nth-child(9)')[0].text.replace("\xa0", "0")) / decimal.Decimal('100')
        if info["roe21"] == decimal.Decimal('0'):
            # 1년후
            info["roe21"] = decimal.Decimal(fnguide_soup.select('#highlight_D_Y > table > tbody > tr:nth-child(18) > td:nth-child(8)')[0].text.replace("\xa0", "0")) / decimal.Decimal('100')
        if info["roe21"] == decimal.Decimal('0'):
            info["volume"] = decimal.Decimal(fnguide_soup.select('#highlight_B_Y > table > tbody > tr:nth-child(7) > td:nth-child(6)')[0].text.replace(",", ""))
            # 2년후
            info["roe21"] = decimal.Decimal(fnguide_soup.select('#highlight_B_Y > table > tbody > tr:nth-child(14) > td:nth-child(8)')[0].text.replace("\xa0", "0")) / decimal.Decimal('100')
            if info["roe21"] == decimal.Decimal('0'):
                # 1년후
                info["roe21"] = decimal.Decimal(fnguide_soup.select('#highlight_B_Y > table > tbody > tr:nth-child(14) > td:nth-child(9)')[0].text.replace("\xa0", "0")) / decimal.Decimal('100')

        # 내년
        # 내후년

        if standard_rate.compare(info["roe21"]) > 0 or info["roe21"] == decimal.Decimal('0'):
            continue

        info["stock_cnt"] = fnguide_soup.select('#svdMainGrid1 > table > tbody > tr:nth-child(6) > tr > td')[0].text.split('/ ')[0].replace(",", "")
        info["stock_cnt_w"] = decimal.Decimal(fnguide_soup.select('#svdMainGrid1 > table > tbody > tr:nth-child(6) > tr > td')[0].text.split('/ ')[1].replace(",", ""))

        # 자기주식 정보
        my_res = requests.get('http://comp.fnguide.com/SVO2/asp/SVD_shareanalysis.asp?pGB=1&gicode=A' + ticker + '&cID=&MenuYn=Y&ReportGB=&NewMenuID=109&stkGb=701')
        my_soup = BeautifulSoup(my_res.content, 'html.parser')
        info["my_stock_cnt"] = my_soup.select('#dataTable > tbody > tr:nth-child(5) > td:nth-child(3)')[0].text.replace(",", "").replace("\xa0", "0")
        info["move_stock_cnt"] = decimal.Decimal(info["stock_cnt"]) - decimal.Decimal(info["my_stock_cnt"])

        info["price_w"] = decimal.Decimal(0)
        if (info["stock_cnt_w"].compare(decimal.Decimal('0')) > 0):
            # 카카오스탁 정보
            ticker_w = ticker[:5] + '5'
            kakao_w_res = requests.get('https://stockplus.com/api/securities/KOREA-A' + ticker_w + '.json')
            if (kakao_w_res.status_code == '200'):
                info["price_w"] = decimal.Decimal(kakao_w_res.json()["recentSecurity"]["displayedPrice"])

        info["profit"] = decimal.Decimal(info["volume"]) * (decimal.Decimal(info["roe21"]) - standard_rate)
        # 계속 이익 
        info["continue"] = ((info["volume"] + (info["profit"] / standard_rate)) * decimal.Decimal('100000000')) - (info["stock_cnt_w"] * info["price_w"])
        info["continue_price"] = int(info["continue"] / info["move_stock_cnt"])
        # 10프로 할인 이익
        info["discount10"] = ((info["volume"] + (info["profit"] * decimal.Decimal('0.9') / (decimal.Decimal('1') + standard_rate - decimal.Decimal('0.9')))) * decimal.Decimal('100000000')) - (info["stock_cnt_w"] * info["price_w"])
        info["discount10_price"] = int(info["discount10"] / info["move_stock_cnt"])
        # 20프로 할인 이익
        info["discount20"] = ((info["volume"] + (info["profit"] * decimal.Decimal('0.8') / (decimal.Decimal('1') + standard_rate - decimal.Decimal('0.8')))) * decimal.Decimal('100000000')) - (info["stock_cnt_w"] * info["price_w"])
        info["discount20_price"] = int(info["discount20"] / info["move_stock_cnt"])

        info["roe21"] = info["roe21"] * decimal.Decimal("100")

        if (info["price"].compare(info["continue_price"]) > 0):
            info["cd"] = 4
        elif (info["price"].compare(info["discount10_price"]) > 0):
            info["cd"] = 3
        elif (info["price"].compare(info["discount20_price"]) > 0):
            info["cd"] = 2
        else:
            info["cd"] = 1

        info["continue_diff"] = (info["continue_price"] - info["price"]) / info["price"] * decimal.Decimal("100")
        info["discount10_diff"] = (info["discount10_price"] - info["price"]) / info["price"] * decimal.Decimal("100")
        info["discount20_diff"] = (info["discount20_price"] - info["price"]) / info["price"] * decimal.Decimal("100")

        info["continue"] = info["continue"] / decimal.Decimal(100000000)
        info["discount10"] = info["discount10"] / decimal.Decimal(100000000)
        info["discount20"] = info["discount20"] / decimal.Decimal(100000000)
        info_list.append(info)

    standard_rate = standard_rate * decimal.Decimal("100")

    info_list.sort(reverse=True, key=lambda element: element["stock_sum"])

    return render_template('index.html', info_list=info_list, standard_rate=standard_rate)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)
