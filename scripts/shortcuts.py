from scripts.full_export_book import main as export_main
import sys

def epub_only():
    sys.argv = ["full-export", "--format=epub"]
    export_main()

def epub_with_cover():
    sys.argv = [
        "full-export",
        "--format=epub",
        "--cover=./assets/covers/cover-image.jpg"
    ]
    export_main()
