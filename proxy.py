import requests
from bs4 import BeautifulSoup


def set_new_proxy():
    env_file = '.env'
    proxy = get_https_proxy()

    with open(env_file, 'a') as f:
        f.write(f'https_proxy={proxy}')


def get_https_proxy(body_proxy=None):
    if not body_proxy:
        body_proxy = requests.get('https://free-proxy-list.net/anonymous-proxy.html').text

    s = BeautifulSoup(body_proxy)
    for proxy_tr in s.find('table').find_all('tr'):
        socket_data = list(proxy_tr.find_all('td'))
        if not socket_data:
            continue

        ip, port, code, _, _, _, is_https, _ = list(proxy_tr.find_all('td'))
        exclude_codes = {'RU'}
        if code in exclude_codes or is_https.get_text() != 'yes':
            continue

        https_proxy = 'https://{ip}:{port}'.format(ip=ip.get_text(), port=port.get_text())

        print(https_proxy)
        try:
            r = requests.get(
                'https://api.telegram.org/api/',
                proxies={'https': https_proxy},
                timeout=0.5,
            )
            print(r.status_code)
            if r.status_code != 200:
                continue

            return https_proxy
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            print('error')
            continue


if __name__ == '__main__':
    set_new_proxy()
