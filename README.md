# 🚀 SNAP C++ SDK & MeloTTS 통합 연동 프로젝트 (`snap_melotts`)

[![Repository](https://img.shields.io/badge/GitHub-snap__melotts-blue)](https://github.com/snap-libs/snap_melotts)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

공개된 **SNAP C++ SDK ([snap-libs/snap_cpp](https://github.com/snap-libs/snap_cpp))**와 **MeloTTS** 간의 공개 인터페이스만을 활용한 초경량·고성능 연동 배포 레포지토리입니다.

---

## ⚡ 초고속 빠른 시작: 한국어 전용 (`snap_melotts_kr`) 4단계 설치 & 실행

한국어 사용자는 저장소 클론 후 `snap_melotts_kr` 서브폴더에서 `SNAP_HOME` 앵커 경로를 현재 디렉토리(`.`)로 명시 설정하는 **`snap init . --lang ko`** 명령어를 통해 자원을 설치하고 즉시 음성을 생성할 수 있습니다.

```bash
# 1. 저장소 클론 및 한국어 전용 디렉토리 이동
git clone https://github.com/snap-libs/snap_melotts.git
cd snap_melotts/snap_melotts_kr

# 2. 필수 의존성 라이브러리 설치
pip install -r requirements.txt

# 3. SNAP_HOME을 현재 디렉토리(.)로 명시 설정하여 사전 자원 및 가중치 세팅 (snap init)
snap init . --lang ko

# 4. 한국어 음성 합성 즉시 실행 (WAV 오디오 생성)
python infer_demo.py --text "여기서 3번버스를 타고 3번 갈아타야합니다" --output output_kr.wav
```

---

## 📦 `SNAP_HOME` 앵커 설정 및 자원 다운로드 매커니즘

`snap init . --lang ko` 명령은 **`SNAP_HOME=.` (현재 디렉터리)**을 최상위 `snap_root` 앵커로 명시 설정하고 아래 자원을 해당 `SNAP_HOME` 하위 디렉터리로 자동 다운로드 및 초기화합니다:

* **환경변수 앵커**: `SNAP_HOME=.` (실행 위치 기준 상대 경로 계층 단일 관리)
1. **SNAP C++ INT8 ONNX 모델 및 사전 자원**:
   - `<SNAP_HOME>/models/ko/KO_model_index.json`
   - `<SNAP_HOME>/models/ko/KO_model_bert_int8.onnx` (C++ 문맥 정규화 & Raw 768차원 BERT 텐서 세션)
2. **SNAP C++ 바이너리**:
   - `<SNAP_HOME>/bin/snap_cpp.dll` (Windows) / `libsnap_cpp.so` (Linux)
3. **MeloTTS 음성 합성 백엔드 체크포인트**:
   - Hugging Face 저장소([myshell-ai/MeloTTS-Korean](https://huggingface.co/myshell-ai/MeloTTS-Korean))의 음성 합성 체크포인트 가중치

*(※ 400MB 용량의 PyTorch BERT 모델(`kykim/bert-kor-base`)은 C++ INT8 세션을 100% 재사용하므로 다운로드받지 않습니다!)*

---

## ✨ 핵심 특장점 및 기술 혁신

### 1. PyTorch BERT 모델 다운로드 100% 제거 (Zero BERT Download)
* 파이썬 런타임에서 **400MB 상당의 PyTorch BERT 모델(`kykim/bert-kor-base`) 다운로드 및 가동 로직을 100% 제거**하였습니다.
* SNAP C++ SDK 내부의 단 1개 INT8 ONNX BERT 세션에서 추출된 **Raw 768차원 BERT hidden state 텐서**를 C-API로 직출력받아 MeloTTS 백엔드(`SynthesizerTrn`)로 100% 재사용(Reuse)합니다.

### 2. 수사 문맥 정밀 구분 (Sino vs Native 교정)
* C++ INT8 ONNX 런타임을 통해 문맥 분석을 수행하여 `"3번 버스"`(삼번) vs `"3번 갈아타"`(세번), `"1층"`(일층) vs `"1개"`(한개) 등 원본 MeloTTS 대비 고도화된 정밀 문맥 처리를 달성했습니다.

### 3. C-ABI 상호 호환성 & In-Memory JSON 동적 옵션
* 디스크 I/O 0% 및 C-ABI 파괴 0%의 인메모리 JSON C-API (`snap_process_json_opts`)를 지원하여, 문장(Per-Sentence) 단위로 정적 설정을 실시간 덮어쓰기(Override)할 수 있습니다.

---

## 📁 저장소 구조

```text
snap_melotts/
 ├── melo/                         # MeloTTS 다국어 공통 소스
 ├── snap_wrapper.py               # SNAP C++ SDK ctypes C-API 래퍼
 ├── infer_demo.py                 # 공통 엔드-투-엔드 인퍼런스 데모
 ├── README.md                     # 메인 안내 문서
 └── snap_melotts_kr/              # 🇰🇷 [한국어 전용 패키지 서브모듈]
      ├── melo/                    # 한국어 전용 슬림 백엔드
      ├── snap_wrapper.py          # C-API ctypes 바인딩
      ├── infer_demo.py            # 한국어 전용 1-Click 실행 데모
      └── README.md                # 한국어 서브모듈 가이드
```

---

## 📄 파이썬 코드 연동 예시

```python
from snap_wrapper import SNAPEngineManager
from melo.api import TTS

# 1. SNAP C++ Engine 매니저 초기화 (C++ INT8 ONNX 런타임)
manager = SNAPEngineManager()
engine = manager.get_engine(lang="ko")

# 2. MeloTTS 백엔드 모델 로드
model = TTS(language="KR", device="cpu")

# 3. C++ SDK로부터 텍스트 정규화 & Raw 768차원 BERT 텐서 직출력 수신 (Zero PyTorch Download)
text = "여기서 3번버스를 타고 3번 갈아타야합니다"
norm_text = engine.process(text) # -> "여기서 삼번 버스를 타고 세번 갈아타야 합니다."
bert_tensor, word2ph = engine.get_bert_features(text)

# 4. 음성 파일 생성
model.tts_to_file(text, model.hps.data.spk2id["KR"], "output.wav")
```
