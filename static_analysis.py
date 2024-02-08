import os
from colorama import Fore, Back, Style
from pyunpack import Archive


def static_analysis(extensions) -> bool:

    try:
        extracted_path = extensions.get_extracted_path()
        for files in os.listdir(extracted_path):

            # Todo: Fix so we also include HTML
            # We only care about .js files (for now)

            if files.endswith(".js"):
                with open(extracted_path + files, "r") as file:

                    #So here it begins
                    print("We have arrived!")


    except Exception as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        return False

class DummyExtensionObject:
    def __init__(self) -> None:
        self.crx_path = "DUMMY_PATH"
    def get_keyword_analysis(self) -> dict:
        return {
            "list_of_urls": [],
            "list_of_actions": [],
            "list_of_common_urls": []
        }

    def get_extracted_path(self):
        return "url"

if __name__ == "__main__":

    originalDirectory = "/mnt/c/Users/sam00/Desktop/MasterThesis/webstore-dl-and-analysis/" 
    path = "/mnt/c/Users/sam00/Desktop/MasterThesis/webstore-dl-and-analysis/extensions/akoiagmmfbjephlbkncmnpdakfklipjd"

    os.chdir(path)

    #Filename: AKOIAGMMFBJEPHLBKNCMNPDAKFKLIPJD_5_0_0_0.crx

    # Unpack files
    Archive("AKOIAGMMFBJEPHLBKNCMNPDAKFKLIPJD_5_0_0_0.crx").extractall(originalDirectory)

    os.chdir(originalDirectory)

    # create dummy object
    dummy = DummyExtensionObject()

    static_analysis(dummy)


    