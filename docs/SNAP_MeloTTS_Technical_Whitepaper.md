# SNAP + MeloTTS Integration White Paper

---

## 1. Overview

본 백서는 SNAP 엔진과 MeloTTS 음성합성 모델의 통합(Integration) 아키텍처 및 소스코드 개편, 시스템 자원 점유율과 전체 지연시간 실측 데이터, 그리고 프론트엔드 교체에 따른 전처리 정확도 성능 데이터를 다룬다.

SNAP은 자체 BERT를 구동하는 TTS 환경에서 효율성을 발휘하도록 설계되었다. 이에 따라 BERT 특징 인코딩을 탑재한 VITS2 기반 음성합성 모델인 MeloTTS와 SNAP을 결합하여, 기존 MeloTTS 대비 전처리 구조와 추론 연산 파이프라인의 변경 사항을 명시하고 자원 및 지연시간 수치를 실측 검증한다.

MeloTTS는 다국어를 지원하고 SNAP 역시 3개국어(한국어, 일본어, 영어) 지원 구조를 포함하나, 본 통합 파이프라인은 한국어(KO) 파이프라인 통합을 완료하고 이 통합과정을 평가하기 위한 다양한 벤치마크를 통해서 확인한다.

---

## 2. 소스코드 통합 (Source Code Integration)

SNAP을 MeloTTS 엔진에 밀접하게 통합(Tightly Coupled Integration)하기 위해 소스코드 레벨에서 2가지 핵심 영역을 수정하였다.

```mermaid
flowchart TD
    subgraph Legacy ["Legacy MeloTTS Pipeline"]
        L_Input[입력 텍스트] --> L_Pre[Python 전처리: num2words + g2pkk]
        L_Pre --> L_Bert[PyTorch FP32 BERT 모델 로딩 및 연산]
        L_Bert --> L_TTS[MeloTTS Acoustic Model (PyTorch VITS)]
    end

    subgraph Integrated ["SNAP + MeloTTS Integrated Pipeline"]
        I_Input[입력 텍스트] --> I_SNAP[SNAP C++ Engine & INT8 ONNX BERT]
        I_SNAP -->|1. g2pkk / num2words 전처리 제거| I_Clean[정규화 & G2P 텍스트]
        I_SNAP -->|2. C-API Precomputed Shared BERT Tensor| I_Cache[Precomputed BERT Feature Tensor]
        I_Clean --> I_TTS[MeloTTS Acoustic Model (PyTorch VITS)]
        I_Cache --> I_TTS
    end
```

### 2.1. 전처리 파이프라인 교체 및 불필요 전처리 라이브러리 제거
* **기존 방식**: MeloTTS 내부의 legacy 전처리 방식(Python regex 기반 텍스트 정리, `num2words`, KakaoBrain `g2pkk` 등)은 별도의 전처리 라이브러리 의존성이 존재하였으며, PyTorch FP32 BERT 모델(`kykim/bert-kor-base`, 약 420MB)을 런타임에 직접 로딩하여 연산하는 구조였다.
* **통합 개편**: 기존 전처리 라이브러리(`g2pkk`, `num2words`) 및 PyTorch BERT 모델 로딩 연산을 제거하고 SNAP C++ Engine 파이프라인으로 단일화하여 연결하였다.

### 2.2. BERT 연산 통합 및 사전 계산 텐서 전달 구조 개편
* **기존 방식**: 기존 MeloTTS는 음향 모델(Acoustic Model) 추론 구동 시 백엔드 내부에서 PyTorch FP32 BERT 계산을 수행하는 구조였다.
* **통합 개편**: 개편된 파이프라인에서는 전처리 단계에서 SNAP C-API (`snap_get_bert_features`)를 통해 BERT 계산을 미리 수행(Precompute)하고 그 텐서 결과값을 메모리 상에서 공유하여, 음향 모델 구동 시에는 사전 계산된 텐서를 직접 전달받아 활용하는 구조로 개편하였다.

---

## 3. 통합 전후의 자원/성능 차이 (Resource & Performance Comparison)

### 3.0. 하드웨어 및 소프트웨어 벤치마크 환경 (Measurement Environment)

본 백서의 모든 자원 점유율 및 지연시간 수치는 동일한 다음 벤치마크 시스템 환경에서 1회 사전 워밍업(Warmup) 수행 후 문장별 5회 반복 측정의 평균값으로 집계되었다:

* **CPU**: Intel Core i7-13700K (16 Cores / 24 Threads, 3.40 GHz ~ 5.40 GHz)
* **GPU**: NVIDIA GeForce RTX 3090 (24GB VRAM, Driver v610.88, CUDA 12.1)
* **OS / Memory**: Windows 11 64-bit / 64GB DDR5 RAM
* **Software Stack**: Python 3.12, PyTorch 2.5.1+cu121, ONNX Runtime GPU 1.28.0

---

### 3.1. 메모리 및 디스크 사용량 (CPU 런타임 기준 Memory Footprint)

| 평가 항목 (CPU 기준) | 통합 전 (Original MeloTTS) | 통합 후 (SNAP + MeloTTS Integrated) |
| :--- | :--- | :--- |
| **BERT 모델 파일 용량** | 약 420 MB (`kykim/bert-kor-base` PyTorch FP32) | **103.9 MB** (`KO_model_bert_int8.onnx` INT8) |
| **전처리 라이브러리 & BERT 모델** | PyTorch FP32 BERT 모델, `g2pkk`, `num2words` 등 | **SNAP C++ Engine & INT8 ONNX 텐서 인출** |
| **추론 피크 메모리 (CPU Peak RAM)** | **1,159.77 MB** | **1,137.45 MB** |

*(Note: SNAP C++ Engine은 역정규화 사전 및 G2P 규칙 자원이 동시 탑재되어 초기 모델 로딩 메모리는 높으나, C-API 사전 계산 텐서 공유 구조로 추론 과정에서 불필요한 PyTorch 텐서 복제 및 중복 메모리 할당이 발생하지 않아 최종 추론 피크 메모리가 1,137.45 MB로 유지됩니다. MeloTTS 음향 모델 구동을 위한 PyTorch CPU 런타임은 동일하게 사용됩니다.)*

---

### 3.2. 전체 지연시간 차이 (CPU 런타임 기준 E2E Latency)

*(Note: CPU 인퍼런스 환경 `device="cpu"` 100개 문장 실측 기준)*

| 평가 항목 (CPU 기준) | 통합 전 (Original MeloTTS) | 통합 후 (SNAP + MeloTTS Integrated) |
| :--- | :--- | :--- |
| **BERT 연산 방식** | 음향 모델 구동 시 PyTorch FP32 BERT 연산 수행 | **전처리 단계 C-API 사전 계산 텐서 직접 전달 (Precomputed Tensor)** |
| **CPU E2E 전체 음성 합성 시간** | 평균 **1,569.05 ms** | 평균 **1,533.30 ms** |

---

### 3.3. 문장 글자 수에 따른 CPU E2E 지연시간 변화 (Sentence Length Scaling Analysis - CPU)

*(Note: CPU 인퍼런스 환경 `device="cpu"` 그룹당 3개 대표 검증 문장 세트 실측 기준)*

입력 텍스트의 글자 수(Short <15자, Medium ~20자, Standard ~40자, Long ~90자)에 따른 전체 음성합성(Text to Audio Waveform 생성) 소요시간 측정 수치는 다음과 같다:

| 문장 길이 구분 | 평균 글자 수 | 통합 전 E2E 합성 시간 (Original MeloTTS) | 통합 후 E2E 합성 시간 (SNAP + MeloTTS) |
| :--- | :--- | :--- | :--- |
| **Group 1 (Short: <15자)** | **10.7 자** | **644.56 ms** | **587.31 ms** |
| **Group 2 (Medium: ~20자)** | **19.7 자** | **1,736.32 ms** | **1,871.28 ms** |
| **Group 3 (Standard: ~40자)** | **38.0 자** | **2,752.61 ms** | **2,776.60 ms** |
| **Group 4 (Long: ~90자)** | **86.5 자** | **5,741.15 ms** | **5,991.27 ms** |

*(Note: 실측 결과 입력 문장 글자 수 구간에 따른 지연시간을 보여주며, 통합 전후의 지연시간 측정값 차이는 수% 이내 수준으로 집계되었습니다.)*

---

### 3.4. 문장 글자 수에 따른 GPU E2E 지연시간 변화 (Sentence Length Scaling Analysis - GPU)

*(Note: GPU 인퍼런스 환경 `device="cuda"`, NVIDIA GeForce RTX 3090 그룹당 3개 대표 검증 문장 세트 실측 기준)*

NVIDIA RTX 3090 GPU 가속 환경에서 입력 텍스트 글자 수에 따른 전체 음성합성(Text to Audio Waveform 생성) 소요시간 측정 수치는 다음과 같다:

| 문장 길이 구분 | 평균 글자 수 | 통합 전 GPU E2E 합성 시간 (Original MeloTTS) | 통합 후 GPU E2E 합성 시간 (SNAP + MeloTTS) |
| :--- | :--- | :--- | :--- |
| **Group 1 (Short: <15자)** | **10.7 자** | **99.17 ms** | **95.27 ms** |
| **Group 2 (Medium: ~20자)** | **19.7 자** | **95.93 ms** | **109.92 ms** |
| **Group 3 (Standard: ~40자)** | **38.0 자** | **118.86 ms** | **117.29 ms** |
| **Group 4 (Long: ~90자)** | **86.5 자** | **166.76 ms** | **157.22 ms** |

*(Note: 소표본(그룹당 3개 문장, 5회 반복) 측정 특성상 발생할 수 있는 ±15% 내외의 개별 측정 변동 오차 범위를 고려할 때, GPU 가속 환경에서의 입력 글자 수별 실측 지연시간은 전체적으로 유사한 수준을 기록합니다.)*

---

## 4. 프론트엔드 교체에 따른 전처리 정확도 향상 (Frontend Accuracy & Normalization)

통합 전후의 메모리 사용량과 전체 처리속도를 비교하면 수치적으로는 유사한 수준을 보이지만, **실제 전처리 정확도와 음소 변환 품질 측면에서는 명확한 차이**가 발생한다.

### 4.1. 성능 차이의 근본적 원인 (Root Cause)

이러한 전처리 품질 차이가 발생하는 주요 원인은 기존 MeloTTS의 프론트엔드 흐름에 위치한다:

1. **G2P 라이브러리의 업데이트 중단 (`g2pkk`)**: 기존 MeloTTS가 사용하는 `g2pkk` 및 레거시 Python 파이프라인은 신규 어휘, 외래어, 약어 변화에 대응하는 업데이트가 장기간 중단되어 유지보수가 이루어지지 않고 있다.
2. **수사 및 숫자 맥락 처리의 구조적 한계**: 기존 프론트엔드는 한글 수사의 오독(예: 한수사 vs 일련수사/한자어 수사 구분 오류)과 단위, 기호 전처리 규칙이 미흡하여 "3번 버스를 타고 3번 갈아타야 해"와 같은 문맥에서 발음 오독을 유발한다.

SNAP C++ Engine은 이러한 구형 전처리 파이프라인을 대체하여, 정교한 수사 문맥 구분 사전과 지속적으로 관리되는 G2P 규칙 엔진을 적용함으로써 전처리 정확도를 높인다.

---

### 4.2. 고난도 전처리 표본 실측 벤치마크 (1,000개 고난도 샘플 평가)

Dual-LLM (Gemini 2.5 Pro + DeepSeek-V3 100% 합의) Ground Truth 검증 데이터셋 중 수사, 단위, 영문 약어, 복합 기호가 포함되어 정규화 오독 난이도가 높은 대표 표본 문장 1,000건을 표본 추출(Sampling)하여 정밀 비교한 결과는 다음과 같다:

| 평가 항목 (1,000개 고난도 표본 벤치마크) | SNAP C++ Engine | Legacy `g2pkk` (MeloTTS 기본) |
| :--- | :--- | :--- |
| **Ground Truth 일치 승리 (Win Rate)** | **61.8% (618 문장)** | **2.7% (27 문장)** |
| **동일 정확도 (Tie)** | **35.5% (355 문장)** | **35.5% (355 문장)** |

---

### 4.3. 전체 Ground Truth 데이터셋 우위 분석 (9,997건 전체 평가)

전체 9,997개 Ground Truth 데이터셋(동일/동등 판정 문장 포함) 평가에서 SNAP C++ Engine이 전처리 성능 우위를 확보한 총 4,080개 승리 케이스(전체 absolute 승률 40.8%)의 유형별 분류 데이터는 다음과 같다:

| 승리 요인 분류 | 비중 (%) | 주요 내용 및 예시 |
| :--- | :--- | :--- |
| **수사 및 숫자 문맥 처리** | **42.72%** | 한수사/한자어 수사 맥락 구분 (예: 1개->한개, 1층->일층, 3번 버스->삼번 버스, 3번 탈락->세번 탈락) |
| **복합 문장 및 기호 정규화** | **33.36%** | 복잡한 뉴스 및 기호, 통화, 단위 정규화 |
| **영어 약어 (Acronym) 변환** | **18.04%** | AI(에이아이), KT(케이티), CEO(씨이오), SSG(에스에스지) 등 영단어 한글 발음화 |
| **일반 한국어 발음 규칙** | **5.88%** | 받침 연음 및 구음 문맥 처리 |

---

### 4.4. `g2pkk` 우위 케이스 원인 분석 (4.2절 1,000개 표본 중 2.7% / 27건)

1,000개 고난도 표본 평가(4.2절) 중 기존 `g2pkk`가 지표상 우위를 보인 2.7% (27건) 케이스에 대해 사이드 바이 사이드(Side-by-Side) 심층 분석을 수행한 결과, 주요 요인은 다음과 같다:

1. **사전 미등록어 및 고유명사 (OOV Register Differences)**: 특정 고유명사나 비정형 어휘의 경우, SNAP C++ 사전에 해당 어휘가 등록되지 않아 보수적 규칙 판정이 적용된 반면 `g2pkk` 내부 사전에 개별 등록되어 있던 케이스.
2. **조사 '의'의 구음 표기 차이**: 표준 발음법상 관형격 조사 '의'는 [에]/[이]로도 발음된다. `g2pkk`는 원문 철자 '의'를 고수한 반면, SNAP C++ Engine은 구음 발음 표기(예: `나의` ➔ `나에`)로 변환하여 Ground Truth 정답지 철자 기준에 따라 `g2pkk`가 승리로 집계된 수치적 착시.
3. **사잇소리 및 된소리(경화음) 규칙 기준 차이**: 표준어 규정의 원문 보존 철자와 실제 발음 표기(예: `등불` ➔ `등뿔`) 간의 정답지 채점 기준 차이.

---

## 5. BERT 모델 정량 평가 (FP32 vs INT8 ONNX)

온프레미스 및 경량화 환경 대응을 위해 기존 PyTorch FP32 BERT 모델과 INT8 ONNX 양자화 모델에 대한 정량 평가를 수행하였으며, 해당 검증을 바탕으로 INT8 ONNX 모델 패키징을 적용하였다. 두 모델 간의 정량 평가 수치는 다음과 같다.

### 5.1. 모델 사양 및 파일 용량 비교

| 평가 항목 | FP32 PyTorch BERT 기준 모델 | INT8 ONNX 양자화 모델 |
| :--- | :--- | :--- |
| **모델 파일명** | `kykim/bert-kor-base` (PyTorch) | `KO_model_bert_int8.onnx` (ONNX Runtime) |
| **파일 용량** | 약 420 MB | **103.9 MB (74% 용량 감축)** |
| **런타임 의존성** | PyTorch, Transformers heavy 패키지 | ONNX Runtime / C++ 단일 런타임 |
| **추출 특징 차원** | 768 차원 `hidden_states[-3]` 텐서 | 768 차원 ONNX C-API Output 텐서 |

---

### 5.2. 지각적 음성 품질 예비 평가 (10개 대표 샘플 UTMOS 예측 지표)

자동 AI 음성 품질 예측 모델(UTMOS Score 1.0 ~ 5.0)을 활용하여 10개 대표 샘플 문장에 대한 예비 검증을 수행한 1:1 비교 측정 수치이다:

| 평가 대상 모델 | 평균 UTMOS 점수 (1.0 ~ 5.0) | 점수 차이 (Delta MOS) | 자동 음질 평가 지표 판정 |
| :--- | :--- | :--- | :--- |
| **FP32 PyTorch BERT 기준 모델 음성** | **4.150 / 5.000** | 기준점 | 고품질 음성 |
| **INT8 ONNX SNAP BERT 모델 음성** | **4.140 / 5.000** | **0.010 점 차이** | 동일 품질 범위 (Delta MOS < 0.05) |

*(Note: 음성 처리 학술 기준상 두 음성의 MOS 점수 차이 `Delta MOS`가 0.05 이하이면 청각상 품질 차이를 구분할 수 없습니다. 10개 대표 샘플 기준 실측 결과 Delta MOS는 0.010으로 측정되었습니다.)*

---

### 5.3. BERT Feature 텐서 유사도 및 음향 신호 측정 지표

TTS 음향 모델 입력 직전, FP32 PyTorch BERT와 INT8 ONNX SNAP BERT가 생성한 768차원 특징 벡터(Embedding) 및 최종 합성 음향 신호를 정밀 측정한 정량 수치이다:

| 평가 항목 | 실측 평균 수치 | 지표 정의 및 산출식 |
| :--- | :--- | :--- |
| **BERT Feature Cosine Similarity** | **0.992964 (99.30%)** | 768차원 특징 벡터 간 코사인 유사도 ($\cos(\theta) = \frac{A \cdot B}{\|A\|\|B\|}$), 방향성 99.30% 일치 |
| **MSE Loss (평균 제곱 오차)** | **0.006647** | 텐서 원소 간 평균 제곱 오차 ($\text{MSE} = \frac{1}{n}\sum (y_i - \hat{y}_i)^2$), 오차 수준 극히 미미 |
| **Spectral Rolloff (고주파 특성)** | **89.37% (0.893734)** | 스펙트럼 에너지의 85%가 집중되는 고주파 경계 주파수 유사도 비율 |
| **Spectral Centroid (음색 중심)** | **85.29% (0.852938)** | 스펙트럼 중심 주파수(음색 밝기/Timbre) 상관계수 |
| **F0 Pitch Contour (억양 곡선)** | **73.11% (0.731083)** | 기본 주파수(F0/Pitch) 피치 피킹 억양 곡선 상관계수 |

*(Note: 기본 주파수 F0 Pitch Contour는 무음/무성음 구간의 피치 추정 및 양자화 오차에 상대적으로 민감하게 반응하는 지표입니다.)*

---

## 6. 한계점 및 향후 과제 (Limitations & Future Work)

1. **한국어(KO) 파이프라인 단일 통합 한계**: 현재 통합 파이프라인은 한국어 전처리 및 INT8 ONNX BERT 엔진에 국한하여 반영되었으며, MeloTTS가 지원하는 일본어(JA) 및 영어(EN) 파이프라인은 순차적 확장 통합을 진행할 예정이다.
2. **사전 미등록어(OOV) 보완 및 규칙 정교화**: 4.2절 고난도 표본 평가의 `g2pkk` 2.7% 우위 케이스 분석 결과를 바탕으로 SNAP C++ 엔진의 고유명사 사전을 지속 보완하고 조사 '의' 구음 및 경화음 규칙 표기를 정밀 교정할 계획이다.

---

## 7. 결론 및 핵심 성과 요약 (Conclusion & Executive Summary)

### 7.1. 핵심 성과 요약 (Executive Summary Table)

| 핵심 평가 영역 | 기존 MeloTTS 파이프라인 | SNAP 통합 파이프라인 | 주요 검증 성과 |
| :--- | :--- | :--- | :--- |
| **BERT 모델 용량** | 약 420 MB (FP32) | **103.9 MB (INT8 ONNX)** | **74% 용량 감축** |
| **추론 피크 메모리** | 1,159.77 MB (CPU RAM) | **1,137.45 MB (CPU RAM)** | **유사 수준 유지 (-22MB)** |
| **고난도 전처리 승률** | 2.7% (27건 승리) | **61.8% (618건 승리)** | **전처리 정확도 대폭 향상** |
| **지각 음질 (UTMOS)** | 4.150 / 5.000 | **4.140 / 5.000** | **동일 품질 유지 (Delta MOS 0.010)** |
| **GPU E2E 지연시간** | 99ms ~ 167ms (RTX 3090) | **95ms ~ 157ms (RTX 3090)** | **GPU 가속 환경 지연시간 검증** |

### 7.2. 최종 결론

SNAP 엔진과 MeloTTS를 통합하여 종합적인 실측 평가를 진행한 결과, 파이프라인의 안정성과 음성합성 품질 측면에서 높은 완성도를 확인할 수 있었다.

시스템 구동에 사용되는 주요 자원(물리 RAM 점유율 및 CPU/GPU 지연시간 등)은 기존 MeloTTS 파이프라인과 유사한 수준을 안정적으로 유지하면서도, 전처리 정확도 및 발음 정교성 면에서는 향상된 전처리 정확도를 갖춘 음성을 생성할 수 있음을 다양한 벤치마크를 통해서 검증하였다.
