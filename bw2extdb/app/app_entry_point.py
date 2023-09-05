import os
import runpy
import sys

import bw2extdb.app


def main() -> None:
    streamlit_script_path = os.path.join(os.path.dirname(bw2extdb.app.__file__), "app.py")
    sys.argv = ["streamlit", "run", streamlit_script_path ]
    runpy.run_module("streamlit", run_name="__main__")


if __name__ == "__main__":
    main()