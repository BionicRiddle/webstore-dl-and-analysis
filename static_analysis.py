import os
from colorama import Fore, Back, Style
import globals
import json
from time import sleep

dcounter = 0
failedc = 0

def static_analysis(extension, esprima) -> bool:

    try:
        extracted_path = extension.get_extracted_path()


        for file in os.listdir(extracted_path):
            print("File: " + file)

            # Todo: Fix so we also include HTML
            # We only care about .js files (for now)

            if file.endswith(".js"):
                global dcounter
                global failedc
                content = open(os.path.join(extracted_path, file), "r").read()
                try: 
                    dcounter += 1
                    ret = esprima.run("parse", content)
                    pretty = json.dumps(json.loads(ret), indent=4)



                    print(pretty)

                except Exception as e:
                    #print("TODO: failed_extension(str(extension), \"Esprima\", str(e))")
                    pass
                    
    except Exception as e:
        raise Exception("Error in static_analysis: " + str(e))
    
class DummyExtensionObject:
    def __init__(self) -> None:
        self.static_analysis = {}

    def get_static_analysis(self) -> dict:
        return self.static_analysis

    def get_extracted_path(self):
        return "node/test"

    def get_crx_path(self) -> str:
        return "extensions/aaanbpflpadmmnkbnlkdehkpjhgbbehl/AAANBPFLPADMMNKBNLKDEHKPJHGBBEHL_1_0_0_0.crx"

if __name__ == "__main__":
    from esprima import Esprima

    # create dummy object
    dummy = DummyExtensionObject()

    esprima = Esprima()

    try:
            
        static_analysis(dummy, esprima)


    except KeyboardInterrupt:
        esprima.close_process()
    esprima.close_process()