"""Static JavaScript analysis helpers backed by the Esprima sidecar service."""

import json
import os


def static_analysis(extension, esprima) -> bool:
    """Parse JavaScript files in an extracted extension and store their ASTs."""
    try:
        extracted_path = extension.get_extracted_path()
        parsed_results = extension.get_static_analysis() or {}

        for dirpath, _, filenames in os.walk(extracted_path):
            for file in filenames:
                if not file.endswith(".js"):
                    continue

                filepath = os.path.join(dirpath, file)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as source_file:
                    content = source_file.read()

                try:
                    result = esprima.run("parse", content)
                    if result and result != "{}":
                        parsed = json.loads(result)
                        parsed_results[os.path.relpath(filepath, extracted_path)] = parsed
                        # TODO: implement AST analysis
                except Exception:
                    # print("TODO: failed_extension(str(extension), \"Esprima\", str(e))")
                    pass

        if hasattr(extension, "set_static_analysis"):
            extension.set_static_analysis(parsed_results)
        else:
            extension.static_analysis = parsed_results

        return True
    except Exception as e:
        raise Exception("Error in static_analysis: " + str(e))


class DummyExtensionObject:
    """Stub extension object for use in standalone testing of static_analysis."""

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

    dummy = DummyExtensionObject()
    esprima = Esprima()
    try:
        static_analysis(dummy, esprima)
    finally:
        esprima.close_process()