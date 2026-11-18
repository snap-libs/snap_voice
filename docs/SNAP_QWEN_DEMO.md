# 🎙️ SNAP-Qwen TTS v1.1 Live Demo Guide (Qwen3-TTS Korean LoRA)

> **SNAP Korean Preprocessing (`tn_for_qwen`) + Qwen3-TTS 0.6B Korean LoRA Integration Demo**  
> This guide introduces our live TTS demo connecting SNAP's Qwen-dedicated normalization mode with a `Qwen3-TTS 0.6B` LoRA model trained on additional Korean speakers.

[English](SNAP_QWEN_DEMO.md) | [한국어](SNAP_QWEN_DEMO_KO.md) | [Back to Main README](../README.md)

---

## 🎮 Live Web Demo

* **Demo URL**: **[https://huggingface.co/spaces/softguy777/snap_voice_demo6](https://huggingface.co/spaces/softguy777/snap_voice_demo6)**
* **Environment**: Hugging Face Spaces **ZeroGPU** (`snap_qwen` C++ CUDA Engine + SNAP Cloud API)

> [!NOTE]
> **GPU Runtime & Usage Notice (Hugging Face ZeroGPU)**
> * **GPU Allocation Delay**: Because this demo runs on dynamically allocated cloud GPUs, **a brief wait** may occur depending on queue status when synthesizing speech.
> * **Daily Usage Limits**: Under Hugging Face policy, daily usage limits apply depending on your account tier (Unauthenticated / Free Login / PRO account).

---

## 🎧 Listen to Demo Sample WAVs

* [🔊 News Anchor (F · Calm Mid-Low)](https://cdn.jsdelivr.net/gh/snap-libs/snap_voice@117efb6/docs/samples/qwen_demo/01_B01_news_anchor_F.wav) · [🔊 Sports Caster (M · Power Baritone)](https://cdn.jsdelivr.net/gh/snap-libs/snap_voice@117efb6/docs/samples/qwen_demo/02_B03_sports_caster_M.wav)
* [🔊 Show Host (F · Signature Host)](https://cdn.jsdelivr.net/gh/snap-libs/snap_voice@117efb6/docs/samples/qwen_demo/03_B07_show_host_F.wav) · [🔊 Concierge · Guide (F · Art Docent)](https://cdn.jsdelivr.net/gh/snap-libs/snap_voice@117efb6/docs/samples/qwen_demo/04_P02_v2_concierge_F.wav)
* [🔊 Politician · Orator (M · Senior Speech)](https://cdn.jsdelivr.net/gh/snap-libs/snap_voice@117efb6/docs/samples/qwen_demo/05_P03_politician_M.wav) · [🔊 Lovely Aegyo Girl (F · Sweet Voice)](https://cdn.jsdelivr.net/gh/snap-libs/snap_voice@117efb6/docs/samples/qwen_demo/06_L03_aegyo_girl_F.wav)
* [🔊 Shorts Reviewer (M · Tech Reviewer)](https://cdn.jsdelivr.net/gh/snap-libs/snap_voice@117efb6/docs/samples/qwen_demo/07_L08_shorts_reviewer_M.wav) · [🔊 Noir Boss (M · Enforcer)](https://cdn.jsdelivr.net/gh/snap-libs/snap_voice@117efb6/docs/samples/qwen_demo/08_K03_v3_noir_boss_M.wav)
* [🔊 Dark Villain (M · Mastermind)](https://cdn.jsdelivr.net/gh/snap-libs/snap_voice@117efb6/docs/samples/qwen_demo/09_F05_dark_villain_M.wav) · [🔊 Little Mascot (F · 6yo Girl)](https://cdn.jsdelivr.net/gh/snap-libs/snap_voice@117efb6/docs/samples/qwen_demo/10_A06_mascot_girl_F.wav)

---

## 1. Overview: Qwen3-TTS `0.6B` Korean Speaker-Expanded LoRA Model

This demo integrates the SNAP Korean preprocessing frontend with a `Qwen3-TTS (12Hz, 0.6B Base)` LoRA model fine-tuned on an expanded set of Korean speakers across age groups and speaking styles.

* **158 Korean Speaker Voices**:
  - Combines **7** core Korean voices with **151** additional Korean speakers (14 children, 37 teenagers, 44 young adults in their 20s–30s, 33 middle-aged adults in their 40s–50s, and 23 seniors in their 60s–70s).
* **Character & Vocal Style Presets**:
  - Provides **192 character presets** across 6 categories (Broadcast/Media, Professional/Service, Lifestyle, Korean Archetypes, Historical/Fantasy, Anime/Game) with situational tone switching, **243 vocal style presets**, and alternating multi-speaker dialogue synthesis.

---

## 2. SNAP `Qwen Mode` (`tn_for_qwen`) & Korean Pronunciation Calibration

Unlike phoneme-based TTS models, Qwen3-TTS was trained on Text Normalization (TN) and standard Korean orthography rather than phonetic G2P sequences. As a result, passing full phonetic G2P strings from the standard SNAP API does not match the model's orthographic characteristics, whereas passing standard normalized text causes context-dependent Korean heteronyms to skew toward a biased pronunciation.

To address this, we added a dedicated **Qwen mode (`tn_for_qwen`)** to the SNAP API to handle sentence/numeral normalization and context-dependent Korean heteronyms in a format suited for Qwen3-TTS. In addition, for unlearned phonological cases and missing Hangul syllables that Qwen3-TTS struggled to pronounce due to TN-only training, we calibrated the model and engine as much as possible to deliver more accurate Korean pronunciation.

---

## 3. Future Plans

Once stability is verified, we plan to launch a **downloadable local TTS**, an **SDK**, and a **dedicated Studio** supporting audiobook creation.

