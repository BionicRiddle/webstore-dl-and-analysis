import sys
import time
from datetime import datetime
import base64
import zipfile
import tempfile
import codecs
import json
import re, os, shutil
from tqdm import tqdm
import operator

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
    print("-- Creating tmp path")
    extension_path = extension_path + "/" + version
    print(version, extension_path)
    if extension_path.endswith('.crx'):
        # Create temp dir (usually in /tmp)

        dirpath = tempfile.mkdtemp()
        print("-- Tmp path: ", dirpath)
        # Move crx to temp, and add .zip
        shutil.copyfile(extension_path, dirpath + '/extension.zip')
        version_path = dirpath + '/extension.zip'
        try:
            zip_ref = zipfile.ZipFile(version_path, 'r')
            zip_ref.extractall(dirpath + '/' + version)
            zip_ref.close()
        except Exception as e:
            print("[+] Error (get_tmp_path) in {}: {}".format(extension_path, 'OK') )
        finally:
            path = dirpath + '/' + version
            return (dirpath, path)
    return None






def analyze_data(path):
    print("-- analyze_data(",path,")")

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
                            print("---- Hit! Found ", word, " in ", dirpath+"/"+filename)

                            pos = data.lower().find(word.lower())
                            chunk = data[max(0,pos-100):pos+100]

                            hits.append( [word + "\t" + chunk, dirpath + "/" + filename] )

                    continue

                for word in keywords:
                    if word.lower() in data.lower():
                        print("---- Hit! Found ", word, " in ", dirpath+"/"+filename)

                        pos = data.lower().find(word.lower())
                        chunk = data[max(0,pos-100):pos+100]

                        hits.append( [word + "\t" + chunk, dirpath + "/" + filename] )
            else:
                # ignore common files ectension "css png jpg"
                if extension in ["css", "png", "jpg", "ico", "gif", "svg", "ttf", "woff", "woff2", "eot", "html", "txt", "md", "DS_Store"]:
                    continue
                # log in file unknown-ext.txt
                unknown_ext.write(extension + "\t| " + dirpath + os.sep + filename + "\n")
        unknown_ext.close()

    return hits



def analyze(extensions_path, single_extension=None):
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

        print("\n\n\nAnalyzing ", extension)

        extension_path = extensions_path + extension
        print("-- Path to extension: ", extension_path)


        if os.path.isdir(extension_path):
            versions = sorted([d for d in os.listdir(extension_path) if d[-4:] == ".crx"])

            if not versions:
                print("[+] Warning. No CRX files in dir: {}".format(extension_path))
                continue
                    
            if len(versions) > 1:
                print("More than one version!!! {}".format(extension))


            # ONLY RUN LATEST VERSION
            if (not RUN_ALL_VERSIONS):
                print("Warning! Only running latest version!")
                versions = [versions[-1]]
    
            for version in versions:
                if not version.startswith('.'):
                    dirpath, path = get_tmp_path(version, extension_path)

                    try:
                        # Do the analysis!
                        hits = analyze_data(path)
                        if hits:
                            if (PRETTY_OUTPUT):
                                open("hits_"+str(start_time)+".txt", "a+").write( json.dumps({"ext_id": extension, "hits": hits}, indent=4) + "\n" )
                            else:
                                open("hits_"+str(start_time)+".txt", "a+").write( json.dumps({"ext_id": extension, "hits": hits}) + "\n" )
                            print(extension, hits)

                    except Exception as e:
                        print("Error on ", extension, ": ", str(e))
                        input("(Paused on error) Enter to continue...")

                    try:
                        shutil.rmtree(dirpath)
                    except:
                        print("Error could not delete tmp dir")

        else:
            print("[+] Error. No such file or dir: {}".format(extension))



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
    analyze(extensions_path, extension)
