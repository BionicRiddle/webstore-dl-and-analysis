import dns.resolver

answers = dns.resolver.query('google.com', 'MX')
for rdata in answers:
    print('Host', rdata.exchange, 'has preference', rdata.preference)