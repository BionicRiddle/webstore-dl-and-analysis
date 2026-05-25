"""Utilities for scanning extracted extension files for URLs and related actions."""

import json
import os
import re
from collections import defaultdict
from datetime import datetime

import globals

DATE_FORMAT = os.getenv("DATE_FORMAT")
if os.getenv("WSL_DISTRO_NAME"):
    DATE_FORMAT = DATE_FORMAT or "%Y-%m-%d_%H-%M-%S"
else:
    DATE_FORMAT = DATE_FORMAT or "%Y-%m-%d_%H:%M:%S"

start_time = datetime.now().strftime(DATE_FORMAT)

NO_URLS_FOUND = "No url(s) found"
ANALYZE_EXTENSIONS = frozenset(["js", "html", "json", "ts", "es"])
IGNORE_EXTENSIONS = frozenset(["css", "png", "jpg", "ico", "gif", "svg", "ttf", "woff", "woff2", "eot", "txt", "md"])
ACTION_PATTERN = re.compile(r"\b(fetch|post|get|href|xhttp|src)\b", re.IGNORECASE)
_HTTP_PATTERN = re.compile(r"https?://(?:www\.)?[a-zA-Z0-9\-_#=./]+")
_WWW_PATTERN = re.compile(r"(?:www)\.[a-zA-Z0-9\-_#=./]+")
_URL_PATTERNS = [_HTTP_PATTERN.pattern, _WWW_PATTERN.pattern]
_URL_REGEX = re.compile(r"\b(" + "|".join(_URL_PATTERNS) + r")\b")


def _merge_actions(target, source):
    for action_type, url_map in source.items():
        if action_type not in target:
            target[action_type] = url_map
            continue

        for url, entries in url_map.items():
            if url in target[action_type]:
                target[action_type][url].extend(entries)
            else:
                target[action_type][url] = entries


def getUrls(data, patterns=_URL_REGEX):
    """Return the unique URLs found in a string or a sentinel when none are present."""
    pattern = patterns if isinstance(patterns, re.Pattern) else re.compile(r"\b(" + "|".join(patterns) + r")\b")
    matches = pattern.findall(data.lower())
    urls = set(matches)
    return urls if urls else NO_URLS_FOUND


def getActions(data, filePath, urlPattern=_URL_REGEX):
    """Map actions such as fetch/href/src to nearby URLs and their file context."""
    actionUrlMap = defaultdict(dict)
    actions = [(match.start(0), match.end(0)) for match in ACTION_PATTERN.finditer(data)]

    for startIndex, endIndex in actions:
        # Only scan a short window after the action so nearby URLs are associated cheaply.
        lookahead = data[endIndex:endIndex + 100]
        urls = getUrls(lookahead, urlPattern)
        if urls == NO_URLS_FOUND:
            continue

        actionType = data[startIndex:endIndex].lower()

        for url in urls:
            # Ignore matches that start too far away; they usually belong to later markup.
            if url in data[endIndex + 30:endIndex + 100]:
                continue

            try:
                urlStart = lookahead.lower().index(url) + endIndex
            except ValueError:
                continue

            context = data[max(0, startIndex - 40):urlStart] or "No context available"
            urlAndContext = {
                "filePath": filePath,
                "context": context,
            }

            if url in actionUrlMap[actionType]:
                existing_file_paths = {
                    entry["filePath"] for entry in actionUrlMap[actionType][url]
                }
                if filePath not in existing_file_paths:
                    actionUrlMap[actionType][url].append(urlAndContext)
            else:
                actionUrlMap[actionType][url] = [urlAndContext]

    return actionUrlMap


def analyze_data(path, extensions_path):
    """Analyze extracted extension files and collect URL, action, and hit metadata."""
    commonUrls = defaultdict(int)
    urlList = defaultdict(list)
    actionsList = defaultdict(dict)
    regexs = []
    keywords = ["http", "www"]
    hits = []
    extensionId = os.path.basename(os.path.normpath(extensions_path))
    last_scanned_path = path

    for dirpath, _, filenames in os.walk(path):
        with open("unknown-ext.txt", "a+", encoding="utf-8") as unknown_ext:
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                last_scanned_path = file_path
                extension = filename.rsplit(".", 1)[-1] if "." in filename else "NONE"

                if extension in ANALYZE_EXTENSIONS:
                    with open(file_path, encoding="utf-8", errors="ignore") as dataFile:
                        data = " ".join(dataFile.read().split())

                    if regexs:
                        for regex in regexs:
                            matches = re.findall(regex, data.lower())
                            for word in matches:
                                pos = data.lower().find(word.lower())
                                chunk = data[max(0, pos - 100):pos + 100]
                                hits.append([f"{word}\t{chunk}", file_path])
                        continue

                    if any(word.lower() in data.lower() for word in keywords):
                        relative_file_path = os.path.relpath(file_path, path).replace(os.sep, "/")
                        actions = getActions(data, relative_file_path, _URL_REGEX)
                        chunk = getUrls(data, _URL_REGEX)

                        if chunk != NO_URLS_FOUND:
                            for url in chunk:
                                commonUrls[url] += 1
                                urlList[url].append(f"{extensionId}/{relative_file_path}")

                        _merge_actions(actionsList, actions)
                elif extension in IGNORE_EXTENSIONS or filename == "DS_Store":
                    continue
                else:
                    unknown_ext.write(f"{extension}\t| {file_path}\n")

    return hits, commonUrls, actionsList, last_scanned_path, urlList


def analyze(extension, isInternal, single_extension=None):
    """Run keyword analysis for an extension and store the result on the extension object."""
    crx_path = os.path.normpath(extension.get_crx_path() or "")
    # get_crx_path() normally looks like "<extensions-root>/<extension-id>/<archive>.crx".
    # Keyword analysis needs the parent "<extensions-root>/<extension-id>" directory; if
    # that path is unavailable or malformed, fall back to the extracted directory's parent.
    extensions_path = os.path.dirname(crx_path) if crx_path else os.path.dirname(os.path.normpath(extension.get_extracted_path()))

    commonUrls = defaultdict(int)
    actionsList = defaultdict(dict)
    urlList = defaultdict(list)
    path = extension.get_extracted_path()

    try:
        hits, urls, actions, _, urlAndExtensions = analyze_data(path, extensions_path)

        for url, count in urls.items():
            commonUrls[url] += count

        for url, entries in urlAndExtensions.items():
            urlList[url].extend(entries)

        _merge_actions(actionsList, actions)

        if hits:
            payload = {"ext_id": extension, "hits": hits}
            with open(f"hits_{start_time}.txt", "a+", encoding="utf-8") as hits_file:
                if globals.PRETTY_OUTPUT:
                    hits_file.write(json.dumps(payload, indent=4) + "\n")
                else:
                    hits_file.write(json.dumps(payload) + "\n")

    except Exception as e:
        print("Error on ", extension, ": ", str(e))
        import traceback
        traceback.print_exc()

    extension.set_keyword_analysis({
        "list_of_common_urls": commonUrls,
        "list_of_actions": actionsList,
        "list_of_urls": urlList,
    })


if __name__ == "__main__":
    raise SystemExit("keywords_search.py is intended to be imported and called with an Extension object.")
