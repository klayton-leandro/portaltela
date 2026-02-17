
import importlib.util
import os

_spec = importlib.util.spec_from_file_location(
    "llm_interface",
    os.path.join(os.path.dirname(__file__), "llm-interface.py")
)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

LLMInterface = _module.LLMInterface
LLmInterface = _module.LLmInterface
NewsExtraction = _module.NewsExtraction

__all__ = ['LLMInterface', 'LLmInterface', 'NewsExtraction']
