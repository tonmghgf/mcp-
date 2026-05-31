import requests
import re

url = 'http://hq.sinajs.cn/list=sh600519'
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'http://finance.sina.com.cn'
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.encoding = 'gbk'
    print('状态码:', response.status_code)
    print('原始响应:', response.text[:500])

    pattern = r'="(.+)"'
    match = re.search(pattern, response.text)
    if match:
        data = match.group(1).split(',')
        print('数据长度:', len(data))
        print('股票名称:', data[0] if data else 'N/A')
        print('当前价格:', data[3] if len(data) > 3 else 'N/A')
    else:
        print('未匹配到数据')
except Exception as e:
    print('错误:', e)

input('按回车退出...')
