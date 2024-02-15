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

# get environment variables
PRETTY_OUTPUT = os.getenv('PRETTY_OUTPUT', True)
RUN_ALL_VERSIONS = os.getenv('RUN_ALL_VERSIONS', False)
SKIP_TO = os.getenv('SKIP_TO', 0)

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
    test = re.findall(pattern, data.lower())

    if len(test) > 0:
        return test
    else:
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

def getActions(data, extension_path, urlPattern):
    #Fix bugs (Check return types from getUrl, see if it messes up the function)
    # - Bug is that it reads strings as actions, should not do that

    #Mapping actions (see pattern dict below) to a url and the extension file it resides in
    actionUrlMap = defaultdict(list)

    #Actions of interest - To be expanded
    pattern = ['fetch', 'post', 'get', 'href', 'xhttp']

    #Compile the pattern(s) (fetch, post, etc are technically individual patterns - need to combine them)
    regex = re.compile(r'\b(' + '|'.join(pattern) + r')\b')

    #Looks up the index of each match of a pattern
    actions = [(m.start(0), m.end(0)) for m in regex.finditer(data.lower())]
    
    #Loop through each action
    for action in actions:
        #Action runs from indexes action[0] -> action[1]
        #Check ahead of the action to see if a url can be found after it, using the getUrl() function
        if str(getUrl(data[action[0]:action[1]+40], urlPattern)) != 'No url(s) found':

            #If a url is found, store it in association with the action
            actionUrlMap[data[action[0]:action[1]]] = getUrl(data[action[0]:action[1]+50], urlPattern)

    return actionUrlMap

def analyze_data(path):
    ## Path: Path to crx file
    
    
    print("Analyzing data: " + path)

    #Keeps track of how many times the urls are encountered
    commonUrls = defaultdict(int)

    #Keeps track of all urls and the extension(s) and file(s) they're found in
    urlList = defaultdict(list)

    #print("-- analyze_data(",path,")")
    actionUrlExtensionList = defaultdict(list)
    actionsList = defaultdict(list)



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

                        # Actions and any associated url's
                        actions = getActions(data, dirpath + "/" + filename, patterns)

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
                                urlList[url].append(dirpath + "/" + filename)
                        
                        for action in actions:
                            if len(action) > 0 and actions[action] != 'No url(s) found':
                                tmpDict = actions[action], dirpath + "/" + filename
                                actionsList[action].append(tmpDict)
                        
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
    return hits, commonUrls, actionsList, dirpath + "/" + filename, urlList

## --------------- 2 ---------------
def analyze_data2(path):
    dirpath = "NULL"
    filename = "NULL"
    commonUrls = defaultdict(int)
    urlList = defaultdict(list)

    (regexs, keywords) = ([], ["http"]) 
    
    # hits are the results
    hits = []
    
    #read file into data
    with open(path, encoding='utf-8', errors='ignore') as data:
        data = data.read().lower()

        if regexs:
            for regex in regexs:
                matches = re.findall(regex, data)
                for word in matches:
                    #print("---- Hit! Found ", word, " in ", dirpath+"/"+filename)

                    pos = data.find(word)
                    chunk = data[max(0,pos-100):pos+100]

                    hits.append(chunk)

        for word in keywords:
            if word in data:

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

                # Actions and any associated url's
                actions = getActions(data, dirpath + "/" + filename, patterns)

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
                        urlList[url].append(dirpath + "/" + filename)
                        hits.append(chunk)
                
                for action in actions:
                    if len(action) > 0 and actions[action] != 'No url(s) found':
                        tmpDict = actions[action], dirpath + "/" + filename
                        hits.append(actions[action])
                

                ### Legacy, maybe remove, will look into further on
                #hits.append( [word + ':  ' + chunk, dirpath + "/" + filename] )
                

                #print("--------------------------------------------------------\n")
    #print("Return actions: " + str(actions))
    return hits

## --------------- 2 ---------------

def analyze(extensions_path, single_extension=None):
    
    #extensions_path = extension
    #extensions_path = extension.get_crx_path()
    
    print("Analyze: " + extensions_path)
    
    #print("Analyze function Start:")

    #Keeps track of urls, associated action and the file/extension they reside in
    #UrlList = defaultdict(list)
    commonUrls = defaultdict(int)

    #Keeps track of actions and their associated url
    actionsList = defaultdict(list)

    #Keeps track of url's and the extension & file they belong to
    urlList = defaultdict(list)

    extensions = os.listdir(extensions_path)

    # skipTo can by used to skip the first n extensions, does nothing if running a single extension is specified
    skipTo = SKIP_TO
    i = 0
    for extension in tqdm(extensions):
        # Test single extension
        if single_extension and extension != single_extension:
            continue
        else:
            i = i + 1
            if i < skipTo:
                continue
        
        #print("\n\n\nAnalyzing ", extension)

        extension_path = extensions_path + extension
        #print("-- Path to extension: ", extension_path)


        if os.path.isdir(extension_path):
            versions = sorted([d for d in os.listdir(extension_path) if d[-4:] == ".crx"])

            if not versions:
                #print("[+] Warning. No CRX files in dir: {}".format(extension_path))
                continue
                    
            if len(versions) > 1:
                #print("More than one version!!! {}".format(extension))
                print()


            # ONLY RUN LATEST VERSION
            if (not RUN_ALL_VERSIONS):
                #print("Warning! Only running latest version!")
                #print()
                versions = [versions[-1]]
    
            """"""
            for version in versions:
                if not version.startswith('.'):
                    print("Version: " + version)
                    print("Extension_path: " + extension_path)
                    dirpath, path = get_tmp_path(version, extension_path)
            
                    try:
                        # Do the analysis!

                        #[0] = Hits
                        #[1] = Urls encountered
                        #[2] = actions
                        #[3] = extension
                        #[4] = Url list with extensions they reside in
                        result = analyze_data(path)
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
                        for action in actions:
                            #actionsList[action].append(actions[action])
                            #print("Action: " + str(action))
                            #print("actions[action]: " + str(actions[action][0]))
                            actionsList[action].append(actions[action])
                        
                        #print("ActionList123")
                        #for action in actionsList:
                            #print("Action: " + str(action))
                            #for yourMom in actionsList[action]:
                                #print("Your mom: " + str(yourMom))
                            #print("____________")
                        #print(actionsList)

                        if hits:
                            if (PRETTY_OUTPUT):
                                open("hits_"+str(start_time)+".txt", "a+").write( json.dumps({"ext_id": extension, "hits": hits}, indent=4) + "\n" )
                                #print()
                            else:
                                open("hits_"+str(start_time)+".txt", "a+").write( json.dumps({"ext_id": extension, "hits": hits}) + "\n" )
                                #print()

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
    
    #print("Analyze all data:")
    displayData(commonUrls, actionsList, urlList)
    
    
def analyze2(extensions_path, single_extension=None):
    
     # Used to retrieve tmp path
    version = extensions_path.get_crx_path().split("/")[2]
    extensions_path = extensions_path.get_crx_path().split("/")[0] + "/" + extensions_path.get_crx_path().split("/")[1]
    
    # tmp
    print("CRX Name: " + version)
    print("CRX Path: " + extensions_path)
        
    #print("Analyze function Start:")

    #Keeps track of urls, associated action and the file/extension they reside in
    #UrlList = defaultdict(list)
    commonUrls = defaultdict(int)

    #Keeps track of actions and their associated url
    actionsList = defaultdict(list)

    #Keeps track of url's and the extension & file they belong to
    urlList = defaultdict(list)

    extensions = os.listdir(extensions_path)

    # skipTo can by used to skip the first n extensions, does nothing if running a single extension is specified
    skipTo = SKIP_TO
    i = 0
    
    #print("Still alive")
    
    for extension in tqdm(extensions):
        # Test single extension
        if single_extension and extension != single_extension:
            continue
        else:
            i = i + 1
            if i < skipTo:
                continue
        
    #print("Alive 2")
        #print("\n\n\nAnalyzing ", extension)

    extension_path = extensions_path + extension
        #print("-- Path to extension: ", extension_path)

        ##
    """"
    if os.path.isdir(extension_path):
        versions = sorted([d for d in os.listdir(extension_path) if d[-4:] == ".crx"])

        if not versions:
            #print("[+] Warning. No CRX files in dir: {}".format(extension_path))
            pass
                
        if len(versions) > 1:
            #print("More than one version!!! {}".format(extension))
            print()


        # ONLY RUN LATEST VERSION
        if (not RUN_ALL_VERSIONS):
            #print("Warning! Only running latest version!")
            #print()
            versions = [versions[-1]]

        
        for version in versions:
            if not version.startswith('.'):
                print("Version: " + version)
                print("Extension_path: " + extension_path)
                dirpath, path = get_tmp_path(version, extension_path)
    """
        
    #print("HELLO?")
    # Do the analysis!

    #[0] = Hits
    #[1] = Urls encountered
    #[2] = actions
    #[3] = extension
    #[4] = Url list with extensions they reside in
    dirpath, path = get_tmp_path(version, extensions_path)
    
    print("Path: " + path)
    
    result = analyze_data(path)
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
    for action in actions:
        #actionsList[action].append(actions[action])
        #print("Action: " + str(action))
        #print("actions[action]: " + str(actions[action][0]))
        actionsList[action].append(actions[action])
    
    #print("ActionList123")
    #for action in actionsList:
        #print("Action: " + str(action))
        #for yourMom in actionsList[action]:
            #print("Your mom: " + str(yourMom))
        #print("____________")
    #print(actionsList)

    if hits:
        if (PRETTY_OUTPUT):
            open("hits_"+str(start_time)+".txt", "a+").write( json.dumps({"ext_id": extension, "hits": hits}, indent=4) + "\n" )
            #print()
        else:
            open("hits_"+str(start_time)+".txt", "a+").write( json.dumps({"ext_id": extension, "hits": hits}) + "\n" )
            #print()

        #Uncomment later   
        #print(extension, hits)


    #try:
        #shutil.rmtree(dirpath)
    #except:
        #pass
        #print("Error could not delete tmp dir")
        
    #print("[+] Error. No such file or dir: {}".format(extension))

    #print("Analyze all data:")
    displayData(commonUrls, actionsList, urlList)

def displayData(commonUrls, actionsList, urlList):
    #Create file to save the data
    #f = open("Results " + str(datetime.now()) + ".txt", "w")

    #Set how many links you want displayed:
    index_display = 10

    #print("-----Common Urls-----")
    #print(str(commonUrls))
    #print("\n")

    #print("-----Action List-----")
    #print(str(actionsList))
    #print("\n")

    #print("-----Url List-----")
    #print(str(urlList))
    #print("\n")

    """"
    json_commonUrls = json.dumps(commonUrls, indent=4)
    json_actionsList = json.dumps(actionsList, indent=4)
    json_urlList = json.dumps(urlList, indent=4)

    #with open("sample.json", "w") as outfile:

    f1 = open("commonUrls", "w")
    f2 = open("actionsLists", "w")
    f3 = open("urlList", "w")

    f1.write(json_commonUrls)
    f2.write(json_actionsList)
    f3.write(json_urlList)
    """
    
    

if __name__ == "__main__":
    print('------------ Extensions to Analyze: {} ------------')

    ## if -? or -h or --help
    if len(sys.argv) > 1 and sys.argv[1] in ['-?', '-h', '--help']:
        print("Usage: python3 keywords_search.py [path_to_extensions]")
        print("Example: python3 keywords_search.py extensions/")
        exit(0)

    extension = None
    ## if extension id is given as argument
    if len(sys.argv) > 1:
        print("Running single extension: ", sys.argv[1])
        extension = sys.argv[1]



    extensions_path = 'extensions/'
    analyze2(extensions_path, extension)
    