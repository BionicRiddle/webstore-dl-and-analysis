import os
import threading

# Bara globala variabler

# Environment variables
PRETTY_OUTPUT       = os.getenv('PRETTY_OUTPUT'     , False)
RUN_ALL_VERSIONS    = os.getenv('RUN_ALL_VERSIONS'  , False)
DATE_FORMAT         = os.getenv('DATE_FORMAT'       , "%Y-%m-%d_%H:%M:%S")
NUM_THREADS         = os.getenv('NUM_THREADS'       , 1)
STFU_MODE           = os.getenv('STFU_MODE'         , False)

GODADDY_TLDS = []

checked_domains = set()

# add common domains to checked_domains
checked_domains.add("google.com")
checked_domains.add("facebook.com")
checked_domains.add("youtube.com")
checked_domains.add("yahoo.com")
checked_domains.add("baidu.com")
checked_domains.add("wikipedia.org")
checked_domains.add("reddit.com")
checked_domains.add("qq.com")
checked_domains.add("taobao.com")
checked_domains.add("amazon.com")
checked_domains.add("twitter.com")
checked_domains.add("tmall.com")
checked_domains.add("instagram.com")
checked_domains.add("live.com")
checked_domains.add("vk.com")
checked_domains.add("sohu.com")
checked_domains.add("jd.com")
checked_domains.add("sina.com.cn")
checked_domains.add("weibo.com")
checked_domains.add("360.cn")
checked_domains.add("blogspot.com")
checked_domains.add("linkedin.com")
checked_domains.add("yandex.ru")
checked_domains.add("netflix.com")
checked_domains.add("twitch.tv")
checked_domains.add("mail.ru")
checked_domains.add("microsoft.com")
checked_domains.add("ebay.com")
checked_domains.add("bing.com")
checked_domains.add("aliexpress.com")
checked_domains.add("ok.ru")
checked_domains.add("apple.com")
checked_domains.add("xvideos.com")
checked_domains.add("pinterest.com")
checked_domains.add("paypal.com")
checked_domains.add("imdb.com")
checked_domains.add("adobe.com")
checked_domains.add("tumblr.com")

checked_domains_lock = threading.Lock()