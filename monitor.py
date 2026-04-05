"""Compatibility launcher.

This module is kept so existing invocations like `python monitor.py`
continue to work after migrating to the package layout.
"""

from sys_monitor.app import main


if __name__ == "__main__":
    main()
