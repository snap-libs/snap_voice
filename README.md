# SNAP Voice (`snap_voice`)

> 🏠 **[SNAP Project Homepage](https://snap-libs.github.io/snap)**  
> 🌐 **[SNAP Main Hub (`snap`)](https://github.com/snap-libs/snap)** | ⚡ **[SNAP C++ SDK (`snap_cpp`)](https://github.com/snap-libs/snap_cpp)** | 🎙️ **[SNAP Voice (`snap_voice`)](https://github.com/snap-libs/snap_voice)**

**`snap_voice`** 프로젝트는 [**SNAP C++ Engine (`snap_cpp`)**](https://github.com/snap-libs/snap_cpp)을 다양한 백엔드 TTS(Text-to-Speech) 엔진들과 연동하여 고품질의 음성 합성을 제공하는 것을 목적으로 합니다.

그 첫 번째 결실로 **MeloTTS** 백엔드와 SNAP Frontend를 결합하여 크게 향상된 품질의 음성 합성을 구현했습니다. MeloTTS는 다국어를 지원하며 SNAP 엔진 또한 한국어, 일본어, 영어를 지원하지만, 우선 첫 번째 단계로 **한국어 연동 모듈 (`snap_melotts_kr`)**을 구성하여 우선 배포합니다. 나머지 언어 지원 및 기타 백엔드 TTS 연동은 추후 순차적으로 진행할 예정입니다.

> 📄 **Technical Whitepaper (기술 백서)**: 🇬🇧 [**English Version**](docs/SNAP_MeloTTS_Technical_Whitepaper.md) | 🇰🇷 [**한국어 버전**](<docs/SNAP_MeloTTS_Technical_Whitepaper(한국어).md>)

---

## 1. Quick Start: SNAP+MeloTTS 통합 한국어 버전 설치 안내

### Linux
```bash
# 1. 저장소 클론 및 한국어 모듈 이동
git clone https://github.com/snap-libs/snap_voice.git
cd snap_voice/snap_melotts_kr

# 2. 파이썬 의존성 패키지 설치
pip install -r requirements.txt

# 3. C++ 라이브러리 및 모델 자원 세팅
#    (sparse checkout으로 lib + scripts 만 선택적 다운로드, --lang ko로 한국어 모델만 설치)
git clone --depth 1 --filter=blob:none --sparse https://github.com/snap-libs/snap_cpp.git ../snap_cpp
git -C ../snap_cpp sparse-checkout set lib/linux/x64/v1.0.0 scripts
mkdir -p bin && cp -r ../snap_cpp/lib/linux/x64/v1.0.0/* ./bin/
../snap_cpp/scripts/snap_init.sh -y --lang ko

# 4. 음성 합성 데모 실행
python infer_demo.py --text "여기서 3번버스를 타고 3번 갈아타야합니다" --output output_kr.wav
```

### Windows (PowerShell)
```powershell
# 1. 저장소 클론 및 한국어 모듈 이동
git clone https://github.com/snap-libs/snap_voice.git
cd snap_voice/snap_melotts_kr

# 2. 파이썬 의존성 패키지 설치
pip install -r requirements.txt

# 3. C++ 라이브러리 및 모델 자원 세팅
#    (sparse checkout으로 lib + scripts 만 선택적 다운로드, -Lang ko로 한국어 모델만 설치)
git clone --depth 1 --filter=blob:none --sparse https://github.com/snap-libs/snap_cpp.git ../snap_cpp
git -C ../snap_cpp sparse-checkout set lib/windows/x64/v1.0.0 scripts
New-Item -ItemType Directory -Force bin
Copy-Item ../snap_cpp/lib/windows/x64/v1.0.0/* bin/ -Recurse -Force
powershell -ExecutionPolicy Bypass -File ..\snap_cpp\scripts\snap_init.ps1 -Yes -Lang ko

# 4. 음성 합성 데모 실행
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
snap_voice/
 ├── melo/                         # MeloTTS backend core source
 ├── snap_wrapper.py               # SNAP C++ SDK ctypes C-API bindings
 ├── infer_demo.py                 # End-to-end inference demo script
 ├── README.md                     # Main documentation
 └── snap_melotts_kr/              # Korean deployment submodule
      ├── melo/                    # Korean backend source
      ├── snap_wrapper.py          # C-API ctypes bindings
      └── infer_demo.py            # Korean inference demo script
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

---

## 5. Related Links & Repositories

* 🏠 [**`SNAP Project Homepage`**](https://snap-libs.github.io/snap) : SNAP 프로젝트 공식 웹사이트 및 문서 포털
* 🌐 [**`snap-libs/snap`**](https://github.com/snap-libs/snap) : SNAP 프로젝트 메인 허브 저장소
* ⚡ [**`snap-libs/snap_cpp`**](https://github.com/snap-libs/snap_cpp) : C++ 기반 고성능 ITN / G2P / BERT Hidden State 추출 SDK
* 🎙️ [**`snap-libs/snap_voice`**](https://github.com/snap-libs/snap_voice) : 다양한 백엔드 TTS 연동 및 End-to-End 음성 합성 모듈 (MeloTTS 백엔드 포함)
