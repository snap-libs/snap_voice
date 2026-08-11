# SNAP C++ SDK & MeloTTS Integration (`snap_melotts`)

This repository provides an integration of the **SNAP C++ SDK (`snap_cpp`)** with the **MeloTTS** backend using public C-API interfaces.

---

## 1. Quick Start: Korean Module (`snap_melotts_kr`)

Follow these steps to initialize resources and run audio synthesis:

```bash
# 1. Clone repository and enter Korean submodule directory
git clone https://github.com/snap-libs/snap_melotts.git
cd snap_melotts/snap_melotts_kr

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Initialize SNAP C++ model resources and backend weights (SNAP_HOME=.)
snap init . --lang ko

# 4. Run audio synthesis demo
python infer_demo.py --text "여기서 3번버스를 타고 3번 갈아타야합니다" --output output_kr.wav
```

---

## 2. Technical Architecture & Features

### A. Direct BERT Hidden State Export
* Consumes raw 768-dimensional BERT hidden state tensors (`[seq_len, 768]`) directly from the SNAP C++ SDK's ONNX session via C-API (`snap_get_bert_features`), eliminating separate PyTorch BERT model instantiation in Python.

### B. Text Normalization & G2P Integration
* Delegates Korean text normalization and numeral disambiguation (Sino-Korean vs Native-Korean numerals) to the SNAP C++ Engine (`snap_process`).

### C. In-Memory Option Overriding
* Supports per-sentence dynamic configuration overriding using in-memory JSON C-API (`snap_process_ext`) without disk I/O operations.

---

## 3. Directory Layout

```text
snap_melotts/
 ├── melo/                         # MeloTTS backend core source
 ├── snap_wrapper.py               # SNAP C++ SDK ctypes C-API bindings
 ├── infer_demo.py                 # End-to-end inference demo script
 ├── README.md                     # Main documentation
 └── snap_melotts_kr/              # Korean deployment submodule
      ├── melo/                    # Korean backend source
      ├── snap_wrapper.py          # C-API ctypes bindings
      ├── infer_demo.py            # Korean inference demo script
      └── README.md                # Submodule documentation
```

---

## 4. Python API Usage

```python
from snap_wrapper import SNAPEngineManager
from melo.api import TTS

# 1. Initialize SNAP C++ Engine Manager
manager = SNAPEngineManager()
engine = manager.get_engine(lang="ko")

# 2. Load MeloTTS model
model = TTS(language="KR", device="cpu")

# 3. Obtain text normalization & raw BERT hidden state tensor via C-API
text = "여기서 3번버스를 타고 3번 갈아타야합니다"
norm_text = engine.process(text)
bert_tensor, word2ph = engine.get_bert_features(text)

# 4. Synthesize audio file
model.tts_to_file(text, model.hps.data.spk2id["KR"], "output.wav")
```
