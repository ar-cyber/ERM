# NEW MODULES SHOULD NOT USE THE MENUS FILE FOR ITS MODULES. PLEASE USE THE UI FOLDERS.
#
# THIS IS A STUB FOR OLD MODULES BEFORE THEIR REWRITE HAPPENS

import pkgutil
import importlib

__all__ = []

for module in pkgutil.iter_modules(["ui"]):
    mod = importlib.import_module(f"ui.{module.name}")
    for attr in dir(mod):
        if not attr.startswith("_"):
            globals()[attr] = getattr(mod, attr)
            __all__.append(attr)