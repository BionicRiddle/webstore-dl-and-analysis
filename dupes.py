import os
import tldextract

file = open('found_domains_dupes.txt', 'r')

lines = file.readlines()

file.close()

out = {}

filtered = []

invalid_tlds = ["EE","IN","IS","EDU","CI","JP","RS","SO","SH","LA","TW","IE","GE","GS","COM.TW","UK","DZ"]

for line in lines:
    if line not in filtered:
        filtered.append(line)

for line in filtered:
    if line not in out:
        if "google" in line:
            continue
        if "goo" in line:
            continue
        if "bit.ly" in line:
            continue
        if "amazon" in line:
            continue
        if "aws" in line:
            continue
        key = tldextract.extract(line).suffix
        if key.upper() in invalid_tlds:
            continue
        lineo = line + "\t\t" + tldextract.extract(line).domain + "\t\t" + tldextract.extract(line).suffix
        if key not in out:
            out[key] = [lineo]
        else:
            out[key].append(lineo)

file_out = open('found_domains_grouped.txt', 'w')

for key in out.keys():
    file_out.write("=== " + key + " ===\n")
    for value in out[key]:
        file_out.write("\t" + value + "\n\n")
