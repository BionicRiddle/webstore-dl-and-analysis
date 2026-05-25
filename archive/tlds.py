import time
import tldextract

test = [
    "http://www.google.com",
    "http://www.google.co.uk",
    "http://www.google.com.au",
    "http://localhost.localhost",
    "http://localhost",
    "localhost",
    "http://localhost.localhost",
    "http://ec2-54-252-254-241.ap-southeast-2.compute.amazonaws.com/djhkfhdskj",
    "http://jdklsajdklas.dsajkldj.djaskdljsa",
    "http://www.google.com.au/some/path",
    "http://www.google.com.au/some/path/",
    "http://www.djhskalk.com.au/some/path/file",
    "http://www.djhskalk.com.au/some/path/file/",
    ]


times = []

for url in test:
    timer = time.time()
    # get tld
    domain = tldextract.extract(url).domain + "." + tldextract.extract(url).suffix

    times.append(time.time() - timer)
    print("%s \t %s" % (domain, url,))

# print average time in decimal form 15 decimal places, no e-00
print(format(sum(times)/len(times), '.10f'))

