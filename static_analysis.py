import os
from colorama import Fore, Back, Style

def static_analysis(extension, esprima) -> bool:

    try:
        extracted_path = extension.get_extracted_path()

        for file in os.listdir(extracted_path):

            # Todo: Fix so we also include HTML
            # We only care about .js files (for now)

            if file.endswith(".js"):
                content = open(os.path.join(extracted_path, file), "r").read()
                try: 
                    ret = esprima.run("parse", content)

                except Exception as e:
                    print("TODO: failed_extension(str(extension), \"Esprima\", str(e))")
                    pass
                    
    except Exception as e:
        raise Exception("Error in static_analysis: " + str(e))
    
class DummyExtensionObject:
    def __init__(self) -> None:
        self.static_analysis = {}

    def get_static_analysis(self) -> dict:
        return self.static_analysis

    def get_extracted_path(self):
        return "/tmp/tmp990ocxky"

    def get_crx_path(self) -> str:
        return "extensions/aaanbpflpadmmnkbnlkdehkpjhgbbehl/AAANBPFLPADMMNKBNLKDEHKPJHGBBEHL_1_0_0_0.crx"

if __name__ == "__main__":
    from esprima import Esprima

    # create dummy object
    dummy = DummyExtensionObject()

    esprima = Esprima()

    static_analysis(dummy, esprima)

    esprima.close_process()
    