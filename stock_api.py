import requests
import re

class StockAPI:
    def __init__(self):
        self.sina_base_url = "http://hq.sinajs.cn/list="
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "http://finance.sina.com.cn"
        }

    def get_realtime_quote(self, stock_code):
        try:
            url = self.sina_base_url + stock_code
            response = requests.get(url, headers=self.headers, timeout=10)
            response.encoding = 'gbk'

            pattern = r'="(.+)"'
            match = re.search(pattern, response.text)

            if not match:
                return None

            data = match.group(1).split(',')

            if len(data) < 32:
                return None

            try:
                current = float(data[3]) if data[3] else 0
                close = float(data[2]) if data[2] else 0
            except:
                return None

            if current == 0 and close == 0:
                return None

            return {
                'name': data[0],
                'open': float(data[1]) if data[1] else 0,
                'close': close,
                'current': current,
                'high': float(data[4]) if data[4] else 0,
                'low': float(data[5]) if data[5] else 0,
                'date': data[30] if len(data) > 30 else '',
                'time': data[31] if len(data) > 31 else '',
                'volume': int(float(data[8])) if data[8] else 0,
                'amount': float(data[9]) if data[9] else 0
            }
        except Exception as e:
            print(f"获取股票数据失败: {e}")
            return None

    def calculate_change(self, current, close):
        if close == 0:
            return 0, 0
        change = current - close
        change_percent = (change / close) * 100
        return round(change, 2), round(change_percent, 2)

    def format_quote(self, stock_code):
        info = self.get_realtime_quote(stock_code)

        if not info:
            return None

        if info['current'] == 0 and info['close'] == 0:
            return None

        change, change_percent = self.calculate_change(info['current'], info['close'])

        trend = "📈 上涨" if change >= 0 else "📉 下跌"
        trend_icon = "↑" if change >= 0 else "↓"

        return f"""📊 **{info['name']}** ({stock_code.upper()})

💰 当前价格: ¥{info['current']}
   涨跌额: {trend_icon}¥{abs(change)} ({change_percent:+.2f}%) {trend}
   昨收价: ¥{info['close']}
   开盘价: ¥{info['open']}

📈 今日行情:
   最高价: ¥{info['high']}
   最低价: ¥{info['low']}

📉 交易数据:
   成交量: {info['volume']:,} 股
   成交额: ¥{info['amount']:,.2f}

🕐 更新时间: {info['date']} {info['time']}"""

    def batch_quote(self, stock_codes):
        results = []
        for code in stock_codes:
            result = self.format_quote(code)
            if result:
                results.append(result)
        return "\n\n".join(results)

stock_api = StockAPI()

if __name__ == "__main__":
    print("测试股票查询...")
    print(stock_api.format_quote("sh600519"))
    print("\n" + "="*50 + "\n")
    print(stock_api.format_quote("sz000001"))
