# 🎙️ SNAP-Qwen TTS v1.1 실시간 데모 안내 (Qwen3-TTS 한국어 LoRA)

> **SNAP 한국어 전처리(`tn_for_qwen`) + Qwen3-TTS 0.6B 한국어 LoRA 모델 연동 데모**  
> SNAP 전처리 엔진에 Qwen-TTS 전용 정규화 모드를 추가하고, 한국인 화자 데이터를 추가 학습한 `Qwen3-TTS 0.6B` LoRA 모델과 연동한 실시간 음성합성 데모를 안내합니다.

[English](SNAP_QWEN_DEMO.md) | [한국어](SNAP_QWEN_DEMO_KO.md) | [메인 페이지로 돌아가기](../README_KO.md)

---

## 🎮 실시간 웹 데모 바로가기

* **데모 주소**: **[https://huggingface.co/spaces/softguy777/snap_voice_demo6](https://huggingface.co/spaces/softguy777/snap_voice_demo6)**
* **구동 환경**: Hugging Face Spaces **ZeroGPU** (`snap_qwen` C++ CUDA 엔진 + SNAP Cloud API 연동)

> [!NOTE]
> **GPU 구동 및 이용 안내 (Hugging Face ZeroGPU)**
> * **GPU 할당 대기 시간**: 본 데모는 GPU로 구동되며, 음성합성 요청 시 클라우드 GPU를 실시간으로 할당받으므로 **대기열 상태에 따라 약간의 초기 대기 시간**이 발생할 수 있습니다.
> * **계정별 일일 사용 제한**: Hugging Face 정책에 따라 접속자의 계정 종류(비로그인 / 무료 로그인 / PRO 계정)별로 일일 사용량 제한이 적용됩니다.

---

## 🎧 Demo 예제 WAV 들어보기

* [🔊 뉴스 앵커 (여 · 차분 중저음)](samples/qwen_demo/01_B01_news_anchor_F.wav) · [🔊 스포츠 아나운서 (남 · 파워 바리톤)](samples/qwen_demo/02_B03_sports_caster_M.wav)
* [🔊 쇼호스트 · 셀러 (여 · 간판 쇼호스트)](samples/qwen_demo/03_B07_show_host_F.wav) · [🔊 친절 안내원 (여 · 청아 미술도슨트)](samples/qwen_demo/04_P02_v2_concierge_F.wav)
* [🔊 정치인 · 웅변가 (남 · 중후 원로연설)](samples/qwen_demo/05_P03_politician_M.wav) · [🔊 사랑스러운 애교녀 (여 · 달콤 꿀보이스)](samples/qwen_demo/06_L03_aegyo_girl_F.wav)
* [🔊 유튜브 · 쇼츠 리뷰어 (남 · 텐션 테크리뷰어)](samples/qwen_demo/07_L08_shorts_reviewer_M.wav) · [🔊 느와르 보스 (남 · 쩌렁 행동대장형)](samples/qwen_demo/08_K03_v3_noir_boss_M.wav)
* [🔊 다크 빌런 · 흑막 (남 · 서늘 중저음흑막)](samples/qwen_demo/09_F05_dark_villain_M.wav) · [🔊 발랄 꼬마 마스코트 (여 · 반짝 6세마스코트)](samples/qwen_demo/10_A06_mascot_girl_F.wav)

---

## 1. 데모 개요: Qwen3-TTS `0.6B` 한국어 화자 확장 LoRA 모델

본 데모는 `Qwen3-TTS (12Hz, 0.6B Base)` 모델에 다양한 연령대와 스타일의 한국인 화자 데이터를 추가하여 LoRA로 파인튜닝하고, 앞단에 SNAP 한국어 전처리기를 연동하여 구성했습니다.

* **통합 한국인 화자 158종**:
  - 기본 코어 화자 **7종**에 한국인 화자 **151종**(아동 14명, 청소년 37명, 20·30대 청년 44명, 40·50대 중장년 33명, 60·70대 노년층 23명)을 추가 학습했습니다.
* **캐릭터 & 발성 스타일 프리셋**:
  - 방송·미디어, 전문직·서비스, 일상, 사극·판타지, 애니·게임 등 6개 분야 **192종 캐릭터 프리셋**(상황별 스타일 전환 지원)과 낭독·뉴스·대화·중계·구연 등 **243종 발성 프리셋**, 다화자 교대 합성을 지원합니다.

---

## 2. SNAP `Qwen Mode` (`tn_for_qwen`) 연동 및 한국어 발음 보정

Qwen3-TTS는 한국어 발음열(G2P)이 아니라 텍스트 정규화(TN)된 일반 철자를 기반으로 학습된 TTS 모델입니다. 따라서 기존 SNAP API의 완전한 발음열을 그대로 전달하면 원문 철자 기반 모델 특성과 맞지 않는 부분이 있고, 일반 정규화 문장을 넣으면 여러 가지 동철이음어의 발음이 한쪽으로 편향되는 현상이 일어납니다.

이에 맞춰 SNAP API에 **Qwen-TTS 전용 전처리 모드(`tn_for_qwen`)**를 새롭게 추가하여 문장·숫자·단위 정규화와 문맥에 따른 동철이음어 처리가 자연스럽게 이루어지도록 수정했습니다. 아울러 모델이 일반 TN 데이터 위주로 학습되면서 미처 학습되지 않아 발음하기 어려웠던 일부 음운 예외 및 누락된 한글 음절들에 대해서도 정확한 한국어 발음에 가깝게 소리 낼 수 있도록 모델과 엔진 수준에서 가능한 범위까지 보정을 적용했습니다.

---

## 3. 향후 계획

안정화가 확인되면, 로컬 환경에서 구동하는 **다운로드형 TTS**, **SDK**, 그리고 오디오북 제작 등이 가능한 **전용 Studio** 출시를 계획하고 있습니다.

