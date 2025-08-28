import importlib.util
import os
from pathlib import Path

from vkbottle.bot import BotLabeler

from StarManager.vkbot.handlers import pm


def find_labelers(folder_path):
    labelers = [pm.bl]
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py") and file not in ("__init__.py", "pm.py"):
                module_path = os.path.join(root, file)
                module_name = os.path.splitext(file)[0]

                spec = importlib.util.spec_from_file_location(module_name, module_path)
                assert spec is not None and spec.loader is not None

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "bl") and isinstance(
                    bl := getattr(module, "bl"), BotLabeler
                ):
                    labelers.append(bl)
    return labelers


found_labelers = find_labelers(Path(__file__).parent)
root_labeler = BotLabeler()

for labeler in found_labelers:
    root_labeler.load(labeler)
