

def static_analysis(extension) -> bool:
    try:
        extracted_path = extension.get_extracted_path()
        for files in os.listdir(extracted_path):
            if files.endswith(".js"):
                with open(extracted_path + files, "r") as file:


    except Exception as e:
        print(Fore.RED + str(e) + Style.RESET_ALL)
        return False

class DummyObject:
    def __init__(self) -> None:
        self.crx_path = "DUMMY_PATH"
    def get_keyword_analysis(self) -> dict:
        return {
            "list_of_urls": [],
            "list_of_actions": [],
            "list_of_common_urls": []
        }

if __name__ == "__main__":

    path = "path/to/file"

    # create dummy object
    dummy = DummyObject()

    keyword_search(dummy, path)


    