from transformers import AutoTokenizer
import sys
import os


def get_tokenizer_path():
    """Get the absolute path to the tokenizer directory, working both in development and when packaged."""
    try:
        # When running as packaged app
        base_path = sys._MEIPASS
    except Exception:
        # When running in development
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return base_path


def init_ds_tokenizer():
    tokenizer = AutoTokenizer.from_pretrained(get_tokenizer_path(), trust_remote_code=True)
    return tokenizer
