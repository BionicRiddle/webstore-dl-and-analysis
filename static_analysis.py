import os
from colorama import Fore, Back, Style

from esprima import Esprima

def static_analysis(extension, esprima) -> bool:

    try:
        print(Fore.GREEN + "Static analysis" + Style.RESET_ALL)
        extracted_path = extension.get_extracted_path()

        for file in os.listdir(extracted_path):

            # Todo: Fix so we also include HTML
            # We only care about .js files (for now)

            if file.endswith(".js"):
                print(Fore.GREEN + "Analyzing file: " + os.path.join(extracted_path, file) + Style.RESET_ALL)
                content = open(os.path.join(extracted_path, file), "r").read()

                esprima.send_input(content)
                print("esprima.send_input(content)")


                print(esprima.read_output())
                print("esprima.read_output()")



    except Exception as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        return False

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

    # create dummy object
    dummy = DummyExtensionObject()

    esprima = Esprima()

    static_analysis(dummy, esprima)

    esprima.close_process()
    