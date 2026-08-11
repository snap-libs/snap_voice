import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(BASE_DIR, "bin")
MODELS_DIR = os.path.join(BASE_DIR, "models")

SNAP_REF_PATH = r"c:\work\snap"

def setup_binaries():
    """Ensure snap_cpp binaries exist in project bin/ directory."""
    os.makedirs(BIN_DIR, exist_ok=True)
    snap_dll = os.path.join(BIN_DIR, "snap_cpp.dll")
    ort_dll = os.path.join(BIN_DIR, "onnxruntime.dll")
    
    if not os.path.exists(snap_dll) or not os.path.exists(ort_dll):
        print("[setup_env] Initializing SNAP C++ binaries...")
        ref_snap_dll = os.path.join(SNAP_REF_PATH, "snap_cpp.dll")
        ref_ort_dll = os.path.join(SNAP_REF_PATH, "onnxruntime.dll")
        
        if os.path.exists(ref_snap_dll):
            shutil.copy2(ref_snap_dll, snap_dll)
        if os.path.exists(ref_ort_dll):
            shutil.copy2(ref_ort_dll, ort_dll)
            
    print(f"[setup_env] Binaries ready in {BIN_DIR}")

def setup_weights(lang: str = "ko"):
    """Ensure SNAP model weights exist under models/<lang>/ according to SNAP C++ SDK spec."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    lang_dir = os.path.join(MODELS_DIR, lang)
    
    if not os.path.exists(lang_dir) or not os.listdir(lang_dir):
        # Look in ref models or weights
        ref_lang_dir = os.path.join(SNAP_REF_PATH, "models", lang)
        if not os.path.exists(ref_lang_dir):
            ref_lang_dir = os.path.join(SNAP_REF_PATH, "weights", lang)
            
        if os.path.exists(ref_lang_dir):
            print(f"[setup_env] Copying SNAP weights for '{lang}' to {lang_dir}...")
            shutil.copytree(ref_lang_dir, lang_dir, dirs_exist_ok=True)
            
    print(f"[setup_env] Weights for '{lang}' ready in {MODELS_DIR}")

if __name__ == "__main__":
    setup_binaries()
    setup_weights("ko")
