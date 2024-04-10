import sys
import time
from datetime import datetime
from collections import defaultdict
import base64
import zipfile
import tempfile
import codecs
import json
import re, os, shutil
from tqdm import tqdm
import operator
import re
import json
import random

# get environment variables

DATE_FORMAT = os.getenv('DATE_FORMAT')
if os.getenv('WSL_DISTRO_NAME'):
    # Running on WSL
    DATE_FORMAT = DATE_FORMAT or "%Y-%m-%d_%H-%M-%S"
else:
    DATE_FORMAT = DATE_FORMAT or "%Y-%m-%d_%H:%M:%S"

now = datetime.now()
start_time = now.strftime(DATE_FORMAT)

def get_tmp_path(version, extension_path, dirpath=""):
    #print("-- Creating tmp path")
    extension_path = extension_path + "/" + version
    #print(version, extension_path)
    if extension_path.endswith('.crx'):
        # Create temp dir (usually in /tmp)

        dirpath = tempfile.mkdtemp()
        #print("-- Tmp path: ", dirpath)
        # Move crx to temp, and add .zip
        shutil.copyfile(extension_path, dirpath + '/extension.zip')
        version_path = dirpath + '/extension.zip'
        try:
            zip_ref = zipfile.ZipFile(version_path, 'r')
            zip_ref.extractall(dirpath + '/' + version)
            zip_ref.close()
        except Exception as e:
            pass
            #print("[+] Error (get_tmp_path) in {}: {}".format(extension_path, 'OK') )
        finally:
            path = dirpath + '/' + version
            return (dirpath, path)
    return None

def getUrl(data, patterns):
    pattern = re.compile(r'\b(' + '|'.join(patterns) + r')\b')
    url = re.findall(pattern, data.lower())

    # Did we find a url?
    if len(url) > 0:
        ## Check if valid url
        return url[0]
   
    return 'No url(s) found'

def getUrls(data, patterns):
    # - Try different patterns (Maybe 3 or so)
    # - Investigate False positives vs False Negatives
    # - Fix so it detects when link simply starts with "www" and not "http" or "https"

    #Combination of different patterns, compiled together
    pattern = re.compile(r'\b(' + '|'.join(patterns) + r')\b')

    #Look for all matches to the pattern in the specified file
    matches = re.findall(pattern, data.lower())

    #Avoid dupliactes
    urls = set()

    #Check if any actual matches were found
    if len(matches) > 0:
        for link in matches:
            urls.add(link)
        return urls
    else:
        #No url's were found
        return 'No url(s) found'

def containsAction(dictionary, action):
    for actions in dictionary:
        if actions == action:
            return True
    return False

def getActions(data, filePath, urlPattern):
    #Fix bugs (Check return types from getUrl, see if it messes up the function)
    # - Bug is that it reads strings as actions, should not do that
    
    # Runs per file

    #Mapping actions (see pattern dict below) to a url and the extension file it resides in
    actionUrlMap = defaultdict(dict)

    #Actions of interest - To be expanded
    pattern = ['fetch', 'post', 'get', 'href', 'xhttp','src', 'FETCH', 'POST', 'GET', 'HREF', 'XHTTP', 'SRC']

    #Compile the pattern(s) (fetch, post, etc are technically individual patterns - need to combine them)
    regex = re.compile(r'\b(' + '|'.join(pattern) + r')\b')

    #data = "jibberish deluxedwawaDwadwadwadwadsa das dsad wad aw d sec-fetch-mode"":""cors"",""sec-fetch-site"":""cross-site"",""Referer:https://appsumo.com/"

    #Looks up the index of each match of a pattern
    actions = [(m.start(0), m.end(0)) for m in regex.finditer(data)]
        
        #if data[ind.start(0):ind.end(0)].lower() not in pattern:
            #print(data[ind.start(0):ind.end(0)])
        #print(data[ind.end(0)])
    #Loop through each action
    for action in actions:
        # Start of supposed url
        startIndex = action[0]     
        
        #End of supposed url
        endIndex = action[1]
        
        #Action runs from indexes action[0] -> action[1]
        #Check ahead of the action to see if a url can be found after it, using the getUrl() function
        if str(getUrl(data[endIndex:endIndex+100], urlPattern)) != 'No url(s) found':
            
            # E.x href, get, fetch etc
            actionType = data[startIndex:endIndex].lower()
            
            #If a url is found, store it in association with the action
        
            # Very much test
            url = getUrl(data[endIndex:endIndex+100], urlPattern)
            
            # If beginning of url is matched too far away ahead, it is likely not part of the action
            # src="/img/list.png"></a> <div class="dropdown-content"> <a target="blank" href="https://www.w3techic.co
            # The href link will match to the src attribute here which is incorrect
            # Addtionally, the href link is cut, should be .com
            
            # Check that the url begins within the first 30 characters
            #print(data[startIndex:endIndex])
            
            if url in data[endIndex+30:endIndex+100]:
                continue
                        
            
            #print(data[startIndex:endIndex+100])
            #print(url not in data[startIndex:endIndex+50])
            
            # Check if action has already been added
            #print("url: " + str(url))
            #print("Actiontype: " + str(actionType))
            #print("")
            
            if actionType in actionUrlMap:
                # Check if domain has already been added
                if url in actionUrlMap[actionType]:
                    if filePath not in actionUrlMap[actionType][url]:
                        #print("Appending to:")
                        #print(str(actionUrlMap[actionType][url]))
                        actionUrlMap[actionType][url].append(filePath)
                else:
                    # Action has been added but the url has not
                    actionUrlMap[actionType][url] = [filePath]
            else:
                #print("Url: " + url)
                actionUrlMap[actionType][url] = [filePath]

    return actionUrlMap

def analyze_data(path, extensions_path):
    ## Path: Path to crx file
    
    # This is done per extension
    
    
    #print("Analyzing data: " + path)

    #Keeps track of how many times the urls are encountered
    commonUrls = defaultdict(int)

    #Keeps track of all urls and the extension(s) and file(s) they're found in
    urlList = defaultdict(list)

    #print("-- analyze_data(",path,")")
    actionUrlExtensionList = defaultdict(list)
    
    actionsList = defaultdict(dict)



    (regexs, keywords) = ([], ["http"]) 
    

    # hits are the results
    hits = []
    for dirpath, dirnames, filenames in os.walk(path):
        unknown_ext = open("unknown-ext.txt", "a+")
        for filename in filenames:
            try:
                extension = filename.split(".")[-1]
            except:
                extension = "NONE"
            if extension in ["js", "html", "json", "ts", "es"]:
                data = ""
                with open(dirpath + os.sep + filename, encoding='utf-8', errors='ignore') as dataFile:
                    data = " ".join(dataFile.read().split())

                # TODO: Analyze :)
                ## Here you can look at the file content (data) for what you want.
                ## Use strings, REGEX, ML, ...

                if regexs:
                    for regex in regexs:
                        matches = re.findall(regex, data.lower())
                        for word in matches:
                            #print("---- Hit! Found ", word, " in ", dirpath+"/"+filename)

                            pos = data.lower().find(word.lower())
                            chunk = data[max(0,pos-100):pos+100]

                            hits.append( [word + "\t" + chunk, dirpath + "/" + filename] )

                    continue

                for word in keywords:
                    if word.lower() in data.lower():

                        #print("---- Hit! Found ", word, " in ", dirpath+"/"+filename)

                        # Bug: Thinks https://... is a url, look into later - E.x, https://a is considered a link (pattern 1)
                        # Bug: Misses sites whic start with "www" (as far as is known) - Seems to be fixed by combining pattern2 with pattern1
                        # Otherwise seems to be working just fine.
                        
                        # Starting with https or http
                        httpPattern = 'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+' 

                        # Not starting with http or https (e.x, website.com, www.website.com, pizzabakery.net etc)
                        # Not detecting anything it seems, potentially due to not being any "www.example.com" only links present, only ones starting with https / http, need to test
                        wwwPattern = "^[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"


                        patterns = [httpPattern, wwwPattern]
                        
                        # Determine path (I do not like this but I hope it is better performance than doing os.walk or something simmilar again)
                        split = dirpath.split("/")
                        extensionId = extensions_path.split("/")[1]
                        filePath = ""
                        if len(split) > 0:
                            for x in range(3):
                                split.pop(0)
                            for entry in split:
                                filePath = filePath + "/" + entry
                            filePath = filePath + "/"
                        
                        # Actions and any associated url's
                        
                        extensionId = extensions_path.split("/")[1]
                        
                        actions = getActions(data, extensionId + filePath + filename, patterns)
                        
                        #print("Dirpath: " + dirpath + "/" + filename)

                        # Retrieves all url's from the current file (data)
                        # Chunk is old name, perhaps rewrite
                        chunk = getUrls(data, patterns)

                        # Ensure any actual url's were found
                        if chunk != 'No url(s) found':
                            # Loop through each url found
                            for url in chunk:
                                # Simply demonstrates the amount of times a url is encountered, not other information is stored
                                commonUrls[url] += 1

                                # Provides information about where the url is found (extension(s) and filenames(s))
                                urlList[url].append(extensionId + filePath + filename)
                        
                        for action in actions:
                            #print("Action: " + str(actions[action]))
                            if len(action) > 0 and actions[action] != 'No url(s) found':
                                
                                
                                # Check if entry of action already exist
                                if actionsList[action]:
                                    
                                    # For each url
                                    for entry in actions[action]:
                                        # Is the url already entered in actionsList?
                                        if entry in actionsList[action]:
                                            actionsList[action][entry].append(actions[action][entry][0])
                                        else:
                                            actionsList[action][entry] = actions[action][entry]
                                else:
                                    actionsList[action] = actions[action]
                                
                                #tmpDict = actions[action], dirpath + "/" + filename
                                #actionsList[action].append(tmpDict)
                        
                        dict(urlList)

                        ### Legacy, maybe remove, will look into further on
                        #hits.append( [word + ':  ' + chunk, dirpath + "/" + filename] )
                        

                        #print("--------------------------------------------------------\n")
            else:
                # ignore common files ectension "css png jpg"
                if extension in ["css", "png", "jpg", "ico", "gif", "svg", "ttf", "woff", "woff2", "eot", "html", "txt", "md", "DS_Store"]:
                    continue
                # log in file unknown-ext.txt
                unknown_ext.write(extension + "\t| " + dirpath + os.sep + filename + "\n")
        unknown_ext.close()

    #print("Return actions: " + str(actions))
    
    # Duplicates occur here already!
    
    #print("Printing...")
    #for action in actionsList:
        #print(str(actionsList[action]))
    #print("_____________________________________")
    
    
    return hits, commonUrls, actionsList, dirpath + "/" + filename, urlList

def analyze(extension, isInternal, single_extension=None):
    #extensions_path = extension
    #extensions_path = extension.get_crx_path()
    
    extensions_path = extension.get_crx_path().split("/")[0] + "/" + extension.get_crx_path().split("/")[1]
    
    #print("Analyze: " + str(extensions_path))
    
    #print("Analyze function Start:")

    #Keeps track of urls, associated action and the file/extension they reside in
    #UrlList = defaultdict(list)
    commonUrls = defaultdict(int)

    #Keeps track of actions and their associated url
    actionsList = defaultdict(dict)

    #Keeps track of url's and the extension & file they belong to
    urlList = defaultdict(list)

    
    
    #extension = os.listdir(str(extensions_path))
    
    #print("--- Exists: ---- : " + str(extensions))

        #print("\n\n\nAnalyzing ", extension)
        
        # Check if called via keyword search or not
        
    if isInternal:
        extension_path = extensions_path + extension
    else:
        extension_path = extensions_path
            
        
        #print("-- Path to extension: ", extension_path)
        
        
    #dirpath, path = get_tmp_path(version, extension_path)
    path = extension.get_extracted_path()
    #+ "/" + extension.get_crx_path().split("/")[2]
    #print("Path: " + path)

    try:
        # Do the analysis!

        #[0] = Hits
        #[1] = Urls encountered
        #[2] = actions
        #[3] = extension
        #[4] = Url list with extensions they reside in
    
        
        result = analyze_data(path, extensions_path)
        hits =               result[0] #Hits (?) vad den får ut I guess
        urls =               result[1] #E.x, {"www.yelp.com" : 1, "www.pizza.com", 2}
        actions =            result[2]
        extension_analyzed = result[3] #E.x... tomt
        urlAndExtensions =   result[4] #

        
        for url in urls:
            if url in commonUrls:
                commonUrls[url] += 1
            else:
                commonUrls[url] = 1

        for url in urlAndExtensions:
            urlList[url].append(urlAndExtensions[url])
            
        #print("Returned actions: ")
        #print(str(actionsList))
        
        # TMP REMOVE
        
        #print("Holy shit!")
        
        ## Right here, the list seems to be intact
        
        ## Here we go, may lord have mercy on my soul
        
        
        for action in actions:
            
            # Has the action (href, etc) already been added?
            if action in actionsList:
                for entry in actions[action]:
                    # Has the url already been added
                    if entry in actionsList:
                        actionsList[action][entry].append(actions[action][entry])
                    else:
                        actionsList[action][entry] = actions[action][entry]
                
            else:
                actionsList[action] = actions[action]

        if hits:
            if (PRETTY_OUTPUT):
                open("hits_"+str(start_time)+".txt", "a+").write( json.dumps({"ext_id": extension, "hits": hits}, indent=4) + "\n" )
            else:
                open("hits_"+str(start_time)+".txt", "a+").write( json.dumps({"ext_id": extension, "hits": hits}) + "\n" )

            #Uncomment later   
            #print(extension, hits)

    except Exception as e:
        #print("Error on ", extension, ": ", str(e))
        input("(Paused on error) Enter to continue...")

    #try:
        #shutil.rmtree(dirpath)
    #except:
        #pass
        #print("Error could not delete tmp dir")

    else:
        pass
        #print("[+] Error. No such file or dir: {}".format(extension))
        
        
    # Set extension properties
    extension.set_keyword_analysis ( {
        "list_of_common_urls": commonUrls,
        "list_of_actions":  actionsList,
        "list_of_urls": urlList
    })
    

if __name__ == "__main__":
    #print('------------ Extensions to Analyze: {} ------------')

    ## if -? or -h or --help
    if len(sys.argv) > 1 and sys.argv[1] in ['-?', '-h', '--help']:
        #print("Usage: python3 keywords_search.py [path_to_extensions]")
        #print("Example: python3 keywords_search.py extensions/")
        exit(0)

    extension = None
    ## if extension id is given as argument
    if len(sys.argv) > 1:
        #print("Running single extension: ", sys.argv[1])
        extension = sys.argv[1]



    extensions_path = 'extensions/'
    analyze(extensions_path, extension, True)
    