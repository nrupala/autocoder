# AutoCoder Engine - Method Reference
# Keep this file updated to avoid duplicates

CLASSES_AND_METHODS = {
    "AutoCoderEngine": {
        "line": 235,
        "methods": {
            "__init__": 238,
            "_init_engines": 244,
            "generate": 275,
            "_adjust_for_mode": 309,
            "_fallback_generate": 311,
            "get_status": None,  # TODO: add
        }
    },
    "LlamaCppEngine": {
        "line": 28,
        "methods": {
            "__init__": 31,
            "_find_llama_cpp": 40,
            "load_model": 62,
            "generate": 126,
            "stop": 165,
        }
    },
    "LocalModelManager": {
        "line": 172,
        "methods": {
            "__init__": 175,
            "_scan_models": 177,
            "_detect_quantization": 212,
            "get_models": None,  # TODO: find
            "find_model": None,  # TODO: find
        }
    },
    "OllamaWrapper": {
        "line": 958,
        "methods": {
            "__init__": 962,
            "generate": 966,
        }
    },
    "LMStudioWrapper": {
        "line": 983,
        "methods": {
            "__init__": 986,
            "generate": 990,
        }
    },
}

# Global functions
GLOBALS = {
    "_engine": 1003,
    "get_engine": 1006,
    "generate": 1013,
}

# Known GGUF models
GGUF_MODELS = [
    r"D:\models\lmstudio-community\gemma-3-4b-it-GGUF\gemma-3-4b-it-Q4_K_M.gguf",
    r"D:\models\lmstudio-community\LFM2.5-1.2B-Instruct-GGUF\LFM2.5-1.2B-Instruct-Q8_0.gguf",
    r"D:\models\lmstudio-community\gemma-4-26B-A4B-it-GGUF\mmproj-gemma-4-26B-A4B-it-BF16.gguf",
]