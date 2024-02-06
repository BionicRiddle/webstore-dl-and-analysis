from colorama import Fore, Back, Style
import dns.resolver
import sys

def domain_analysis(domian) -> bool:
    # get A, NS, MX, SOA, AAAA, CNAME records
    # NS record
    try:
        ns = dns.resolver.resolve(domian, 'NS')
        for data in ns:
            print(Fore.GREEN + 'NS Record: %s' % data.to_text() + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        return False

    # A record
    try:
        a = dns.resolver.resolve(domian, 'A')
        for data in a:
            print(Fore.GREEN + 'A Record: %s' % data.to_text() + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        return False

    # AAAA record
    try:
        aaaa = dns.resolver.resolve(domian, 'AAAA')
        for data in aaaa:
            print(Fore.GREEN + 'AAAA Record: %s' % data.to_text() + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        return False

    # MX record

    try:
        mx = dns.resolver.resolve(domian, 'MX')
        for data in mx:
            print(Fore.GREEN + 'MX Record: %s' % data.to_text() + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        return False

    # CNAME record
    try:
        cname = dns.resolver.resolve(domian, 'CNAME')
        for data in cname:
            print(Fore.GREEN + 'CNAME Record: %s' % data.to_text() + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        return False




class DummyObject:
    def __init__(self) -> None:
        self.crx_path = "DUMMY_PATH"
    def get_keyword_analysis(self) -> dict:
        return {
            "list_of_urls": [],
            "list_of_actions": [],
            "list_of_common_urls": []
        }

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(Fore.RED + 'Usage: python3 domain_analysis.py <domain>' + Style.RESET_ALL)
        sys.exit(1)
    domian = sys.argv[1]

    # create dummy object
    dummy = DummyObject()

    domain_analysis(domian)


    