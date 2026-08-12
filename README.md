# SNAP Voice (`snap_voice`)

> 🏠 **[SNAP Project Homepage](https://snap-libs.github.io/snap)**  
> 🌐 **[SNAP Main Hub (`snap`)](https://github.com/snap-libs/snap)** | ⚡ **[SNAP C++ SDK (`snap_cpp`)](https://github.com/snap-libs/snap_cpp)** | 🎙️ **[SNAP Voice (`snap_voice`)](https://github.com/snap-libs/snap_voice)**

The **`snap_voice`** project aims to deliver high-quality end-to-end speech synthesis by integrating the high-performance [**SNAP C++ Engine (`snap_cpp`)**](https://github.com/snap-libs/snap_cpp) with various backend Text-to-Speech (TTS) engines.

As our first milestone, we integrated the **MeloTTS** backend with the SNAP C++ Frontend, achieving significantly improved speech synthesis quality, precise Inverse Text Normalization (ITN), and contextual Phonetic G2P. While MeloTTS and SNAP C++ support multilingual processing (Korean, Japanese, English), this repository provides an end-to-end integrated module optimized for high-fidelity speech synthesis.

> 📄 **Technical Whitepaper**: 🇬🇧 [**English Version**](docs/SNAP_MeloTTS_Technical_Whitepaper.md) | 🇰🇷 [**Korean Version**](<docs/SNAP_MeloTTS_Technical_Whitepaper(한국어).md>)

---

## 1. Quick Start: Installation & Demo Guide

### Linux
```bash
# 1. Clone the repository
git clone https://github.com/snap-libs/snap_voice.git
cd snap_voice

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Setup C++ shared library and model assets
#    (Sparse checkout lib & scripts from snap_cpp, run setup script for Korean model)
git clone --depth 1 --filter=blob:none --sparse https://github.com/snap-libs/snap_cpp.git ../snap_cpp
git -C ../snap_cpp sparse-checkout set lib/linux/x64/v1.0.0 scripts
mkdir -p bin && cp -r ../snap_cpp/lib/linux/x64/v1.0.0/* ./bin/
../snap_cpp/scripts/snap_init.sh -y --lang ko

# 4. Run speech synthesis inference demo
python infer_demo.py --text "여기서 3번 버스를 타고 3번 갈아타야 합니다." --output output_kr.wav
```

### Windows (PowerShell)
```powershell
# 1. Clone the repository
git clone https://github.com/snap-libs/snap_voice.git
cd snap_voice

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Setup C++ shared library and model assets
#    (Sparse checkout lib & scripts from snap_cpp, run setup script for Korean model)
git clone --depth 1 --filter=blob:none --sparse https://github.com/snap-libs/snap_cpp.git ../snap_cpp
git -C ../snap_cpp sparse-checkout set lib/windows/x64/v1.0.0 scripts
New-Item -ItemType Directory -Force bin
Copy-Item ../snap_cpp/lib/windows/x64/v1.0.0/* bin/ -Recurse -Force
powershell -ExecutionPolicy Bypass -File ..\snap_cpp\scripts\snap_init.ps1 -Yes -Lang ko

# 4. Run speech synthesis inference demo
python infer_demo.py --text "여기서 3번 버스를 타고 3번 갈아타야 합니다." --output output_kr.wav
```

---

## 2. Technical Architecture & Key Features

### A. Direct BERT Hidden State Export
* Consumes raw 768-dimensional BERT hidden state tensors (`[seq_len, 768]`) directly from the SNAP C++ SDK's ONNX session via C-API (`snap_get_bert_features`), eliminating separate PyTorch BERT model instantiation in Python and saving memory.

### B. Context-Aware Text Normalization & G2P
* Delegates text normalization, numeral disambiguation (Sino-Korean vs Native-Korean numerals), and Korean phonetic G2P rules to the high-performance SNAP C++ Engine (`snap_process`).

### C. In-Memory Option Overriding
* Supports per-sentence dynamic configuration overriding using in-memory JSON C-API (`snap_process_ext`) without disk I/O operations.

---

## 3. Directory Layout

```text
snap_voice/
 ├── melo/                         # MeloTTS backend core package
 ├── docs/                         # Technical whitepapers (English & Korean)
 ├── snap_wrapper.py               # SNAP C++ SDK ctypes C-API bindings
 ├── infer_demo.py                 # End-to-end CLI inference demo script
 ├── requirements.txt              # Pure Python dependencies
 └── README.md                     # Main documentation
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
text = "2026년 8월 12일 서울의 날씨는 매우 맑고 기온은 28도입니다."
norm_res = engine.process(text)
bert_tensor, word2ph = engine.get_bert_features(text)

# 4. Synthesize speech to WAV file
model.tts_to_file(text, model.hps.data.spk2id["KR"], "output_demo.wav")
```

---

## 5. Related Links & Repositories

* 🏠 [**`SNAP Project Homepage`**](https://snap-libs.github.io/snap) : Official SNAP project website & portal
* 🌐 [**`snap-libs/snap`**](https://github.com/snap-libs/snap) : SNAP main hub repository
* ⚡ [**`snap-libs/snap_cpp`**](https://github.com/snap-libs/snap_cpp) : High-performance C++ ITN / G2P / BERT Hidden State SDK
* 🎙️ [**`snap-libs/snap_voice`**](https://github.com/snap-libs/snap_voice) : Multilingual end-to-end speech synthesis modules
