# 🇰🇷 snap_melotts_kr (한국어 전용 SNAP C++ & MeloTTS 연동 패키지 모듈)

메인 저장소 **`snap_melotts`** 하위의 **한국어 전용 독립 패키지 서브모듈**입니다.

---

## ⚡ 4단계 설치 및 실행 가이드 (Quick Start)

```bash
# 1. snap_melotts 저장소 클론 및 한국어 모듈 이동
git clone https://github.com/snap-libs/snap_melotts.git
cd snap_melotts/snap_melotts_kr

# 2. 필수 의존성 라이브러리 설치
pip install -r requirements.txt

# 3. SNAP_HOME을 현재 디렉토리(.)로 명시 설정하여 사전 모델 자원 및 백엔드 가중치 세팅
snap init . --lang ko

# 4. 한국어 음성 합성 실행 (output_kr.wav 생성)
python infer_demo.py --text "여기서 3번버스를 타고 3번 갈아타야합니다" --output output_kr.wav
```

---

## 📦 `SNAP_HOME` 앵커 매커니즘

`snap init . --lang ko` 실행 시 **`SNAP_HOME=.` (현재 디렉터리)**이 최상위 앵커로 명시 설정되어, 하위의 `bin/` 바이너리 및 `models/ko/` 사전 자원이 `SNAP_HOME` 기준 100% 포터블 상대 경로로 자동 연동 관리됩니다.

---

## 🎯 패키지 특징

1. **PyTorch BERT 모델 다운로드 100% 제거 (Zero BERT Download)**:
   - 400MB 상당의 PyTorch BERT(`kykim/bert-kor-base`) 모델 다운로드 없이, SNAP C++ SDK의 INT8 ONNX 세션에서 추출된 **Raw 768차원 BERT hidden state 텐서**를 100% 재사용하여 음성 생성.
2. **수사 문맥 정밀 구분 (Sino vs Native)**:
   - SNAP C++ INT8 엔진을 통해 `"3번 버스"`(삼번) vs `"3번 갈아타"`(세번) 수사 구분을 100% 정밀 수행.
3. **단일 `SNAP_HOME` 포터블 상대 경로 구조**:
   - 최상위 `snap_melotts_kr` 디렉토리 하나만 앵커로 작동하는 포터블 배포 구조.
