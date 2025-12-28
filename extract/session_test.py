import requests

def url_test():
    proxy_set = {"http": "127.0.0.1:8080","https": "127.0.0.1:8080"}
    session = requests.Session()
    session.verify = False
    session.headers
    session.get(url="http://192.168.198.128:22223/board.php?test=aaa", proxies=proxy_set)

if __name__ == "__main__":
    url_test()