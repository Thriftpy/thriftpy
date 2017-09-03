import sys

collect_ignore = ["setup.py"]
if sys.version_info < (3, 4):
    collect_ignore.append("test_asyncio.py")
