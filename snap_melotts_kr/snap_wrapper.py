import os
import sys
import ctypes
from typing import Optional, Dict

class SNAPEngine:
    """Python ctypes wrapper for the official SNAP C++ SDK (snap_cpp).
    
    Uses only single `snap_root` anchor and resolves all relative paths internally.
    Ref: https://github.com/snap-libs/snap_cpp
    """
    
    def __init__(self, snap_root: str, lang: str, dll_path: Optional[str] = None):
        self.snap_root = os.path.abspath(snap_root)
        self.lang = lang.lower()
        
        # Set SNAP_HOME anchor environment variable
        os.environ["SNAP_HOME"] = self.snap_root
        
        # Explicitly resolve C++ shared library path from snap_root/bin based on OS (Windows or Linux)
        if not dll_path:
            lib_name = "snap_cpp.dll" if os.name == 'nt' else "libsnap_cpp.so"
            dll_path = os.path.join(self.snap_root, "bin", lib_name)
            
        self.dll_path = os.path.abspath(dll_path)
        if not os.path.exists(self.dll_path):
            raise FileNotFoundError(
                f"SNAP C++ SDK library not found at: {self.dll_path}\n"
                f"Please ensure the C++ shared library exists at '{self.snap_root}/bin/'."
            )
            
        # Add DLL directory to Windows DLL search path
        dll_dir = os.path.dirname(self.dll_path)
        if hasattr(os, 'add_dll_directory') and os.name == 'nt':
            try:
                os.add_dll_directory(dll_dir)
            except Exception:
                pass
                
        # Load C++ shared library
        self._lib = ctypes.CDLL(self.dll_path)
        self._setup_c_signatures()
        
        # Initialize engine handle via snap_create(snap_root, lang)
        root_bytes = self.snap_root.encode('utf-8')
        lang_bytes = self.lang.encode('utf-8')
        
        self.handle = self._lib.snap_create(root_bytes, lang_bytes)
        if not self.handle:
            raise RuntimeError(f"Failed to create SNAP Engine handle for lang '{lang}' at snap_root '{self.snap_root}'")

    def _setup_c_signatures(self):
        self._lib.snap_create.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self._lib.snap_create.restype = ctypes.c_void_p
        
        self._lib.snap_process.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self._lib.snap_process.restype = ctypes.c_void_p
        
        self._lib.snap_free.argtypes = [ctypes.c_void_p]
        self._lib.snap_free.restype = None
        
        self._lib.snap_destroy.argtypes = [ctypes.c_void_p]
        self._lib.snap_destroy.restype = None
        
        if hasattr(self._lib, 'snap_version'):
            self._lib.snap_version.argtypes = []
            self._lib.snap_version.restype = ctypes.c_char_p

        if hasattr(self._lib, 'snap_get_bert_features'):
            self._lib.snap_get_bert_features.argtypes = [
                ctypes.c_void_p,
                ctypes.c_char_p,
                ctypes.POINTER(ctypes.c_int),
                ctypes.POINTER(ctypes.c_int),
                ctypes.POINTER(ctypes.POINTER(ctypes.c_int)),
                ctypes.POINTER(ctypes.c_int)
            ]
            self._lib.snap_get_bert_features.restype = ctypes.POINTER(ctypes.c_float)

        if hasattr(self._lib, 'snap_process_ext'):
            self._lib.snap_process_ext.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
            self._lib.snap_process_ext.restype = ctypes.c_void_p

    def process(self, text: str) -> str:
        if not self.handle or not text:
            return text
            
        text_bytes = text.encode('utf-8')
        res_ptr = self._lib.snap_process(self.handle, text_bytes)
        
        if not res_ptr:
            return text
            
        try:
            result_bytes = ctypes.string_at(res_ptr)
            result_str = result_bytes.decode('utf-8')
        finally:
            self._lib.snap_free(res_ptr)
            
        return result_str

    def process_ext(self, text: str, options: Optional[Dict] = None) -> str:
        """Run SNAP inference with per-sentence dynamic options (in-memory JSON)."""
        if not self.handle or not text:
            return text

        if not hasattr(self._lib, 'snap_process_ext'):
            return self.process(text)

        import json
        text_bytes = text.encode('utf-8')
        opts_json_bytes = json.dumps(options or {}).encode('utf-8')

        res_ptr = self._lib.snap_process_ext(self.handle, text_bytes, opts_json_bytes)
        if not res_ptr:
            return text

        try:
            result_bytes = ctypes.string_at(res_ptr)
            result_str = result_bytes.decode('utf-8')
        finally:
            self._lib.snap_free(res_ptr)

        return result_str

    def get_bert_features(self, text: str):
        """Export Raw BERT hidden states tensor directly from SNAP C++ SDK.
        Returns: (bert_tensor [1, 768, seq_len], word2ph_list)
        """
        import numpy as np
        import torch

        if not self.handle or not text:
            return None, None

        if not hasattr(self._lib, 'snap_get_bert_features'):
            return None, None

        text_bytes = text.encode('utf-8')
        out_seq_len = ctypes.c_int()
        out_hidden_dim = ctypes.c_int()
        out_word2ph = ctypes.POINTER(ctypes.c_int)()
        out_word2ph_len = ctypes.c_int()

        tensor_ptr = self._lib.snap_get_bert_features(
            self.handle,
            text_bytes,
            ctypes.byref(out_seq_len),
            ctypes.byref(out_hidden_dim),
            ctypes.byref(out_word2ph),
            ctypes.byref(out_word2ph_len)
        )

        if not tensor_ptr:
            return None, None

        try:
            seq_len = out_seq_len.value
            hidden_dim = out_hidden_dim.value
            flat_size = seq_len * hidden_dim

            arr = np.ctypeslib.as_array(tensor_ptr, shape=(flat_size,)).reshape(seq_len, hidden_dim).copy()
            bert_tensor = torch.from_numpy(arr).float().t().unsqueeze(0)

            word2ph = []
            if out_word2ph and out_word2ph_len.value > 0:
                w2ph_arr = np.ctypeslib.as_array(out_word2ph, shape=(out_word2ph_len.value,)).copy()
                word2ph = w2ph_arr.tolist()
                if hasattr(self._lib, 'snap_free_tensor'):
                    self._lib.snap_free_tensor(out_word2ph)

            return bert_tensor, word2ph
        finally:
            if hasattr(self._lib, 'snap_free_tensor'):
                self._lib.snap_free_tensor(tensor_ptr)

    def get_version(self) -> str:
        if hasattr(self._lib, 'snap_version'):
            ver_ptr = self._lib.snap_version()
            if ver_ptr:
                return ctypes.string_at(ver_ptr).decode('utf-8')
        return "1.0.0"

    def __del__(self):
        if hasattr(self, 'handle') and self.handle and hasattr(self, '_lib') and self._lib:
            try:
                self._lib.snap_destroy(self.handle)
                self.handle = None
            except Exception:
                pass


class SNAPEngineManager:
    """Multi-language modular manager using single snap_root anchor."""
    
    _instance = None
    
    def __new__(cls, snap_root: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.engines: Dict[str, SNAPEngine] = {}
            base_dir = os.path.dirname(os.path.abspath(__file__))
            cls._instance.snap_root = snap_root or base_dir
        return cls._instance

    def get_engine(self, lang: str = "ko") -> SNAPEngine:
        lang = lang.lower()
        if lang not in self.engines:
            print(f"[SNAPEngineManager] Lazy loading SNAP C++ Engine (snap_root='{self.snap_root}', lang='{lang}')...")
            self.engines[lang] = SNAPEngine(
                snap_root=self.snap_root,
                lang=lang
            )
        return self.engines[lang]
