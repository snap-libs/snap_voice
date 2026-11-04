# 📢 SNAP Update Notes

> **Release History for SNAP Korean Preprocessing Engine (TTS Frontend & Text Normalization)**  
> Summary of user-facing improvements in Korean pronunciation (G2P), contextual disambiguation, and text normalization (TN) live on the public Cloud API and demos.

[English](SNAP_UPDATE_NOTES.md) | [한국어](SNAP_UPDATE_NOTES_KO.md) | [Back to Main README](../README.md)

---

## 🚀 SNAP Korean Preprocessing Engine v2.1.2 Update (2026.11.04)

Bugs identified in previous versions and subtle edge cases previously missing from the Standard Pronunciation Rules have been reinforced for even more accurate and natural Korean pronunciation. In addition, the SNAP SDK has been updated to seamlessly support a wider range of application environments.

### Highlights
- **20 New Context-Dependent Heteronyms**: Expanded beyond the original 9 heteronyms with **15 `-가(價)` price/josa-homograph words** (`종가`, `공모가`, etc.) and **5 `-권(券·圈·權·拳)` words** (`전권`, `상권`, etc.).
- **Fine-Grained Pronunciation Boundary Fixes**: Added colloquial promise-ending `-(으)ㄹ게(요)` tensification, blocked false palatalization across compound roots (`첫인상[처딘상]`), restored underlying coda liaison with vowel particles (`꽃잎이[꼰니피]`), and removed false `ㄴ`-addition on single Sino-Korean nouns.
- **Numeral & Loanword Interference Cleanup**: Fixed brand + Korean multiplier readings (`페이 8만원 → 팔만원`) and prevented short conversational loanword accents from misfiring inside longer words (`메타버스`, `카페인`).
- **SNAP SDK Updated for Diverse Applications**: Streamlined integration across desktop, server, and air-gapped apps via single-file `.spak` language packs, runtime error diagnostics, and faster batch processing.

---

### 1. 20 New Context-Dependent Heteronyms (`-가`, `-권`)

In addition to the existing 9 heteronyms (`대가`, `시가`, `성적`, `잠자리`, etc.) introduced in v2.0, `v2.1.2` adds contextual disambiguation and compound rules for high-frequency **`-가(價)`** and **`-권(券·圈·權·拳)`** words across finance, real estate, and everyday text.

- **`-가(價)` Contextual Disambiguation (15 New Words) & Price Compounds**
  - **2-Syllable Heteronyms (7 words)**: `종가`, `정가`, `유가`, `주가`, `단가`, `호가`, `지가`
    - Example: `"오늘 주식 종가를 확인했다"` (closing price) → **`[종까]`** vs `"안동 종가를 방문했다"` (head family house) → **`[종가]`**
    - Example: `"국제 유가가 급등했다"` (oil price) → **`[유까]`** vs `"유가 사상을 연구하다"` (Confucian school) → **`[유가]`**
  - **Noun + Subject Particle `-가` Homographs (8 words)**: `공모가`, `매매가`, `전세가`, `판매가`, `실거래가`, `시초가`, `행사가`, `소비자가`
    - Example: `"공모가가 만 원으로 확정됐다"` (offering price) → **`[공모까가]`** vs `"신규 공모가 시작됐다"` (`공모` + particle `가`) → **`[공모가]`**
  - Unambiguous 3- and 4-syllable price compounds (`분양가[부냥까]`, `출고가[출고까]`, `낙찰가[낙찰까]`, `추정가[추정까]`, etc.) also consistently realize `[까]`.
- **`-권(券·圈·權·拳)` Contextual Disambiguation (5 New Words) & Compound Rules**
  - Separates ticket/zone/right compounds (`입장권[입짱꿘]`, `수도권[수도꿘]`, `저작권[저작꿘]`) from book-volume counters (`책 3권[세권]`) and 3-syllable personal names.
  - Disambiguates **5 context-sensitive words (`전권`, `상권`, `이권`, `수권`, `본권`)** from sentence context:
    - Example: `"협상 전권을 위임받았다"` (full authority) → **`[전꿘]`** vs `"시리즈 전권을 구매했다"` (complete book set) → **`[전권]`**
    - Example: `"역세권 상권이 발달했다"` (commercial district) → **`[상꿘]`** vs `"삼국지 상권을 읽었다"` (first volume) → **`[상권]`**

---

### 2. Fine-Grained Standard Pronunciation Boundary Refinements

Edge cases in compound boundaries, verb conjugations, and particle liaison within the 30 NIKL pronunciation articles were refined:

| Scope | Key Fix / Addition | Input → Phonetic Output |
| :--- | :--- | :--- |
| **Colloquial Promise Endings (Art. 27 Note)** | Newly added tensification for promise endings `-(으)ㄹ게(요)` `[께/께요]` while preserving plain `[게]` on adverbial `-게` | `도와줄게` → `[도와줄께]`, `알게 되다` → `[알게 되다]`, `길게` → `[길게]` |
| **Compound Cuts & Letter Names (Art. 15–17)** | Blocked false palatalization across compound roots and corrected Hangul letter-name liaison | `첫인상` → `[처딘상]`, `웃어른` → `[우더른]`, `디귿이` → `[디그시]` |
| **Particle Liaison & `ㄴ/ㄹ` Addition (Art. 29–30)** | Restored underlying coda liaison when vowel particles attach to Sai-siot compounds; refined compound `ㄴ/ㄹ` addition while removing single-word false additions | `꽃잎이` → `[꼰니피]`, `영업용` → `[영엄뇽]`, `방역` → `[방역]` |
| **Native Compounds & Over-Tensification Guards (Art. 26·28)** | Added native `-결`, road `-길(道)`, and `손바닥` tensification; removed false tensification on 4-syllable Sino reduplications and native nouns | `물결` → `[물껼]`, `출근길` → `[출근낄]`, `허허실실` → `[허허실실]`, `돌담` → `[돌담]` |
| **Multi-Syllable Sino Nasalization (Art. 20)** | Extended `-력/-료` suffix nasalization to 3+ syllable compounds while guarding loanwords against false liquidization | `출연료` → `[추련뇨]`, `저작권료` → `[저작꿘뇨]`, `온라인` → `[온라인]` |
| **Conjugation Ordering & Clusters (Art. 5·12)** | Ordered vowel simplification after aspiration/palatalization (`맞혀`), refined non-initial consonant+`ㅢ` and double-coda + `ㅎ` forms | `맞혀` → `[마처]`, `무늬` → `[무니]`, `넓히다` → `[널피다]`, `싫소` → `[실쏘]` |

---

### 3. Numeral Normalization (TN) & Loanword Interference Fixes

- **Brand / Loanword + Korean Multiplier (`만·억·조`) Numeral Readings**
  - Fixed cases where product-model suffix rules (`아이오닉5 → 아이오닉파이브`, `시즌2 → 시즌투`) caused numbers followed immediately by Korean large-unit multipliers (`만`, `억`, `조`) to be misread as English cardinals or digit strings.
  - Examples: `페이 8만원` → **`페이 팔만원`**, `아미 1억` → **`아미 일억`**, `SK이노 832억원` → **`에스케이이노 팔백삼십이억원`**
- **Substring Guard for Conversational Loanword Accents & Surname Homograph Cleanup**
  - Prevented short conversational loanword accents (`버스[뻐스]`, `카페[까페]`, `가스[까쓰]`) from misfiring inside longer single-morpheme words, keeping `메타버스[메타버스]`, `유니버스[유니버스]`, `카페인[카페인]`, `컨센서스[컨센서스]`, `라스베가스[라스베가스]`, and `수세미[수세미]` natural.
  - Cleaned up transliterated English surname collisions that previously suppressed Sino-Korean tensification (`발사체[발싸체]`, `개발사[개발싸]`, `청춘일세[청추닐세]`, `38도[삼십팔도]`).

---

### 4. SNAP SDK Updated to Support Diverse Applications

The C/C++ Native SDK (`v2.1.2`) has been updated to simplify embedding across a wide variety of client, backend, and on-premise applications:

- **Single-File Language Pack (`.spak`) Deployment**: Applications can now load all language models and dictionaries directly in memory from a single `snap_ko.spak` file rather than managing multi-file asset directories.
- **Enhanced Integration & Batch Workloads**: Added thread-safe runtime diagnostics (`snap_get_last_error`) and substantially accelerated multi-sentence batch processing (`snap_process_batch`) for high-volume workloads.
- For full integration details, see the [SNAP C/C++ Native SDK Reference Manual](SNAP_SDK_API_MANUAL.md).
