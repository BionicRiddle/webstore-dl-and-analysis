from colorama import Fore, Back, Style
import json
import globals
from helpers import *
import tldextract

FILTER_PERMISSIONS = [
    "activeTab",
    "alarms",
    "background",
    "bookmarks",
    "browsingData",
    "certificateProvider",
    "clipboardRead",
    "clipboardWrite",
    "contentSettings",
    "contextMenus",
    "cookies",
    "debugger",
    "declarativeContent",
    "declarativeNetRequest",
    "declarativeNetRequestFeedback",
    "declarativeWebRequest",
    "desktopCapture",
    "documentScan",
    "downloads",
    "enterprise.deviceAttributes",
    "enterprise.platformKeys",
    "experimental",
    "fileBrowserHandler",
    "fileSystemProvider",
    "fontSettings",
    "gcm",
    "geolocation",
    "history",
    "identity",
    "idle",
    "loginState",
    "management",
    "nativeMessaging",
    "notifications",
    "pageCapture",
    "platformKeys",
    "power",
    "printerProvider",
    "printing",
    "printingMetrics",
    "privacy",
    "processes",
    "proxy",
    "scripting",
    "search",
    "sessions",
    "signedInDevices",
    "storage",
    "system.cpu",
    "system.display",
    "system.memory",
    "system.storage",
    "tabCapture",
    "tabGroups",
    "tabs",
    "topSites",
    "tts",
    "ttsEngine",
    "unlimitedStorage",
    "vpnProvider",
    "wallpaper",
    "webNavigation",
    "webRequest",
    "webRequestBlocking"
]

# This function will sometimes return a wildcard tld, these are not actually valid tlds
# and should be filtered out, but it is not a bad idea to keep for further analysis
def wildcard_to_normal(wildcard):
    if wildcard == "<all_urls>":
        return "https://wildcard.wildcardtld/"

    if not "*" in wildcard:
        return wildcard

    ret = wildcard
    # replace "*://" with "https://"
    ret = ret.replace("*://", "https://")

    # replace "://*" with "://wildcard.wildcardtld"
    ret = ret.replace("://*/", "://wildcard.wildcardtld/")

    # replace "*." with "wildcard."
    ret = ret.replace("*.", "wildcard.")

    # replace "/*" with "/"
    ret = ret.replace("/*", "/")

    # replace "*" with "wildcard"
    ret = ret.replace("*", "wildcard")

    return ret

def manifest_analysis(manifest):
    urls = []

    # may be wrong and not needed
    # ["permissions"]
    if 'permissions' in manifest:
        permissions = manifest['permissions']
        for permission in permissions:
            if permission not in FILTER_PERMISSIONS:
                urls.append(wildcard_to_normal(permission))
    
    # may be wrong and not needed
    # ["optional_permissions"]
    if 'optional_permissions' in manifest:
        optional_permissions = manifest['optional_permissions']
        for permission in optional_permissions:
            if permission not in FILTER_PERMISSIONS:
                urls.append(wildcard_to_normal(permission))

    # ["externally_connectable"]["matches"]
    if 'externally_connectable' in manifest:
        externally_connectable = manifest['externally_connectable']
        if 'matches' in externally_connectable:
            externally_connectable_matches = externally_connectable['matches']
            for match in externally_connectable_matches:
                urls.append(wildcard_to_normal(match))

    # ["update_url"]
    if 'update_url' in manifest:
        update_url = manifest['update_url']
        urls.append(update_url)

    # ["host_permissions"]
    if 'host_permissions' in manifest:
        host_permissions = manifest['host_permissions']
        for permission in host_permissions:
            urls.append(wildcard_to_normal(permission))

    # ["content_scripts"]["matches"] Should only be V3
    if 'content_scripts' in manifest:
        content_scripts = manifest['content_scripts'][0]
        if 'matches' in content_scripts:
            content_scripts_matches = content_scripts['matches']
            for match in content_scripts_matches:
                urls.append(wildcard_to_normal(match))
    
    # remove duplicates
    return list(set(urls))

if __name__ == '__main__':
    manifest = '''
    {
        "manifest_version": 2,
        "name": "My Extension",
        "version": "versionString",
        "description": "A plain text description",
        "host_permissions": [
            "http://www.google.com/",
            "*://*/*"
        ],
        "permissions": [
            "proxy",
            "permission2"
        ],
        "optional_permissions": [
            "unlimitedStorage"
        ],
        "content_scripts": [
            {
                "matches": ["http://*.nytimes.com/*","https://github.com/*"],
                "css": ["mystyles.css"],
                "js": ["jquery.js", "myscript.js"]
            }
        ],
        "externally_connectable": {
            "matches": ["*://*.example.com/*"]
        },
        "background": {
            "scripts": ["background.js"],
            "persistent": false
        },
        "browser_action": {
            "default_popup": "popup.html",
            "default_icon": {
                "16": "images/icon16.png",
                "48": "images/icon48.png",
                "128": "images/icon128.png"
            }
        },
        "content_security_policy": "script-src 'self' https://example.com; object-src 'self'",
        "web_accessible_resources": [
            "images/*.png"
        ],
        "action": {
            "default_popup": "popup.html",
            "default_icon": "icon.png"
        },
        "icons": {
            "16": "icon16.png",
            "48": "icon48.png",
            "128": "icon128.png"
        }
    }
    '''

    manifest = json.loads(manifest)
    r = manifest_analysis(manifest)
    for i in r:
        print(get_valid_domain(i))