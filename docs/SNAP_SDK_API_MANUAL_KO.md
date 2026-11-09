# SNAP C/C++ Native SDK API 레퍼런스 매뉴얼 (`v2.1.3`)

> **📌 문서 구분 안내**  
> * **본 문서 (`SNAP_SDK_API_MANUAL_KO.md`):** C/C++ 네이티브 바이너리 SDK(단일 헤더, DLL/SO, `.spak` 암호화 에셋 컨테이너, 메모리 관리) 연동 규격서입니다.  
> * **영문 매뉴얼 (English):** `SNAP_SDK_API_MANUAL.md`를 참조하세요.  
> * **웹/클라우드 HTTP REST API 연동:** JSON 엔드포인트 웹 API 규격은 `SNAP_REST_API_MANUAL_KO.md`를 참조하세요.

> 헤더: `include/snap_api.h` (단독 포함) 및 `include/snap/snap_api.h` (기존 경로 호환)  
> 라이브러리: `snap_cpp.dll` / `libsnap_cpp.so` / `libsnap_cpp.dylib` (순수 C ABI 26개 심볼만 노출)  
> 암호화 언어 팩: `packs/snap_ko.spak` (`.spak` v1 `ChaCha20-Poly1305` 단일 컨테이너)

---

## 1. 개요

`snap_cpp`(`v2.1.3`)는 **불투명 핸들(Opaque Handle)** 기반의 순수 C ABI(`extern "C"`) 라이브러리이며, **100% 인메모리 `.spak` 복호화(Zero-Disk)**를 지원합니다.  
`snap_create()`를 호출할 때마다 독립된 엔진 인스턴스가 생성되므로 단일 프로세스 내에서 다국어(`ko`, `ja`, `en`) 핸들을 공유 상태나 락 경합 없이 동시에 구동할 수 있습니다.

### 라이프사이클

```text
snap_set_license()  (선택 — v2.1.3은 오프라인 기본 허용 스텁 모드)
    │
snap_create("packs/snap_ko.spak", "ko")  ──► NULL 반환 시: snap_get_last_error() 확인
    │
    ├── snap_process()            ──► snap_free(result)
    ├── snap_process_ext()        ──► snap_free(result)
    ├── snap_get_bert_features()  ──► snap_free_tensor(ptr)
    │
snap_destroy()
```

### 에셋 로딩 방식 (`weights_dir`)

`snap_create(weights_dir, lang)`는 단일 암호화 `.spak` 파일과 기존 폴더 구조를 동일한 인터페이스로 지원합니다:

1. **암호화 `.spak` 단일 파일 모드 (SDK 배포 권장):** `"packs/snap_ko.spak"` 경로를 전달합니다. RFC 8439 `ChaCha20-Poly1305` AEAD 무결성 검증 후 ONNX 백본·헤드(`CreateSessionFromArray`)와 사전을 **100% RAM에서만 적재**하고, 임시 평문 버퍼는 즉시 `SecureZero`로 소거합니다(**디스크 임시 파일 생성 0개**).
2. **명시적 디렉터리 모드:** 압축 해제된 가중치 루트 또는 언어 디렉터리 경로를 전달합니다.
3. **환경변수 폴백:** `weights_dir`가 `NULL` 또는 `""`이면 `SNAP_HOME`(미설정 시 `.`)을 참조합니다.

> **⚠️ Windows 11 24H2+ 배포 시 필수 유의사항**  
> Windows 11 24H2 이상에는 구버전 `C:\Windows\System32\onnxruntime.dll`(`v1.17.1`)이 기본 탑재되어 있습니다. 반드시 호스트 실행 파일(`.exe`)과 **동일한 폴더**에 SDK의 `snap_cpp.dll`과 `onnxruntime.dll`(`v1.18.1`)을 함께 배치해야 SDK 전용 ONNX Runtime이 우선 로드됩니다.

### 메모리 소유권 규칙

- `snap_process*()` / `snap_normalize()`가 반환한 문자열 포인터는 반드시 **`snap_free()`**로 해제해야 합니다.
- `snap_get_bert_features()`가 반환한 텐서 및 `word2ph` 포인터는 반드시 **`snap_free_tensor()`**로 해제해야 합니다.
- `snap_version*()` 및 `snap_get_last_error()` 반환 포인터는 내부 정적/스레드 로컬 버퍼이므로 **`snap_free()`에 전달하면 안 됩니다.**
- 사전 빌드 바이너리는 정적 런타임 링크(Windows `/MT`, Linux `-static-libstdc++ -static-libgcc`)를 사용하므로 호출자 측에서 `free()`/`delete`를 직접 호출하면 힙 손상이 발생합니다.

---

## 2. 핵심 추론 및 관리 API (`snap_api.h`)

### `snap_create`

단일 언어에 대한 SNAP 엔진 인스턴스를 생성하고 `.spak` 컨테이너(또는 디렉터리)에서 모델과 사전을 초기화합니다.

```c
SNAP_API void* snap_create(const char* weights_dir, const char* lang);
```

| 파라미터 | 타입 | 설명 |
|:---|:---|:---|
| `weights_dir` | `const char*` | `.spak` 암호화 파일 경로(예: `"packs/snap_ko.spak"`) 또는 가중치 폴더 경로(UTF-8). `NULL`/`""`이면 `SNAP_HOME` 참조 |
| `lang` | `const char*` | 언어 코드 (`"ko"`, `"ja"`, `"en"`, 대소문자 무관) |

- **반환값:** 성공 시 `void*` 엔진 핸들, 실패 시 `NULL` (원인은 `snap_get_last_error()`로 조회)

```cpp
void* handle = snap_create("packs/snap_ko.spak", "ko");
if (!handle) {
    fprintf(stderr, "초기화 실패: %s\n", snap_get_last_error());
}
```

---

### `snap_get_last_error`

현재 스레드에서 가장 최근에 발생한 초기화 실패, `.spak` AEAD 위변조 검증 실패 또는 추론 예외 메시지를 반환합니다.

```c
SNAP_API const char* snap_get_last_error(void);
```

- **반환값:** 스레드 로컬 UTF-8 에러 문자열 포인터 (에러가 없으면 `""`). **`snap_free()` 호출 금지.**

---

### `snap_set_license`

`snap_create()` 호출 전 라이선스 키를 등록·검증합니다.

```c
SNAP_API int snap_set_license(const char* license_key);
```

- **반환값:** `0`이면 정상 승인, `0`이 아니면 거부 코드. *(참고: `v2.1.3`은 오프라인 기본 허용 스텁 모드로 동작하며 생략하거나 임의 문자열 전달 시 `0`을 반환합니다.)*

---

### `snap_create_device`

실행 디바이스(Execution Provider)를 명시하여 엔진 인스턴스를 생성합니다.

```c
SNAP_API void* snap_create_device(const char* weights_dir, const char* lang, const char* device);
```

| 파라미터 | 타입 | 설명 |
|:---|:---|:---|
| `weights_dir` | `const char*` | `.spak` 파일 경로 또는 가중치 디렉터리 경로 |
| `lang` | `const char*` | 언어 코드 (`"ko"`, `"ja"`, `"en"`) |
| `device` | `const char*` | `"auto"`(기본), `"cuda"`(`"cuda:0"`), `"directml"`, `"coreml"`, `"openvino"`, `"cpu"` |

*요청한 하드웨어 EP를 사용할 수 없으면 크래시 없이 경고를 출력하고 자동으로 `"cpu"`로 폴백합니다.*

---

### `snap_create_with_version`

모델 변형(variant) 및 사전/모델 버전을 명시 고정하여 엔진을 생성합니다.

```c
SNAP_API void* snap_create_with_version(
    const char* weights_dir,
    const char* lang,
    const char* variant,
    const char* dict_version,
    const char* model_version
);
```

---

### `snap_process`

UTF-8 입력 문장에 대해 문맥 기반 텍스트 정규화(TN), 형태소·수량사·동형이의어 분석 및 표준 발음열(G2P) 변환을 수행합니다.

```c
SNAP_API const char* snap_process(void* handle, const char* text_utf8);
```

- **반환값:** 힙에 할당된 UTF-8 JSON 문자열 포인터 (**호출 후 `snap_free()` 필수**), 실패 시 `NULL`

**반환 JSON 예시**

```json
{
  "normalized_text": "차량 세대가 오후 두시 삼십분에 감기 환자를 태우고 출발합니다.",
  "phonology": "차량 세대가 오후 두시 삼십뿌네 감기 환자를 태우고 출발함니다.",
  "numbers": [
    {"label": "native", "span": "3", "start": 3},
    {"label": "native", "span": "2", "start": 10},
    {"label": "sino", "span": "30", "start": 13}
  ],
  "heteronyms": [
    {"conf": 0.9982, "label": "NONE", "span": "감기", "start": 18, "end": 20}
  ],
  "pauses": [
    {"word_idx": 0, "word": "차량", "pause": "NONE"},
    {"word_idx": 1, "word": "세대가", "pause": "P1"},
    {"word_idx": 8, "word": "출발함니다.", "pause": "P3"}
  ],
  "morphemes": [
    {"surface": "차량", "pos": "NNG", "origin": "HANJA", "start": 0, "end": 2},
    {"surface": "세", "pos": "SN", "origin": "HANJA", "start": 3, "end": 4}
  ]
}
```

---

### `snap_process_ext`

문장 단위로 동적 런타임 옵션 JSON(`options_json`)을 전달하여 설정 파일 수정 없이 추론 옵션을 제어합니다.

```c
SNAP_API const char* snap_process_ext(
    void* handle,
    const char* text_utf8,
    const char* options_json
);
```

**주요 동적 옵션 키 (`options_json`)**

| 키 | 타입 | 지원값 | 설명 |
|:---|:---:|:---|:---|
| `to_ipa` / `return_ipa` | `bool` | `true`, `false` | 국제음성기호(IPA) 변환 문자열(`"ipa"`) 포함 여부 |
| `to_ssml` | `bool` | `true`, `false` | W3C 표준 SSML `<break>` / `<phoneme>` 태그 출력 여부 |
| `vowel_length` | `bool` | `true`, `false` | (한국어) 장음 기호(`:`) 표기 활성화 |
| `pronunciation_style` | `string` | `"standard"`, `"colloquial"` 등 | (한국어) 발음 스타일 선택 |
| `tn_only` | `bool` | `true`, `false` | (한국어/일본어/영어) G2P 발음 변환을 생략하고 텍스트 정규화(TN) 결과만 반환 |
| `tn_for_qwen` | `bool` | `true`, `false` | (한국어, 기본값 `false`) Qwen3-TTS 연동 전용 하이브리드 TN 출력 모드 (동철이음어 된소리 치환 및 평음 `'` 경음화 차단 기호 삽입, 진료과목 `-꽈`, 수량 `-껀`, ㄴ첨가/겹받침/한자어 ㄴ+ㄹ 예외 치환) |
| `script` | `string` | `"katakana"`, `"hiragana"`, `"romaji"` | (일본어) 출력 문자 체계 |
| `pitch_accent` | `bool` | `true`, `false` | (일본어) 피치 악센트 기호(`^`, `]`) 표기 |
| `to_json` | `bool` | `true`, `false` | `false` 지정 시 JSON 래핑 없이 순수 발음열 텍스트만 즉시 반환 |

---

### `snap_process_batch` / `snap_process_batch_ext`

다수의 UTF-8 문장을 단일 행렬 패스(Dynamic Batching)로 일괄 추론합니다. 단건 `snap_process()`와 100% 동일한 출력을 보장합니다(권장 배치 크기: CPU `16~32`, GPU `64~128`).

```c
SNAP_API const char* snap_process_batch(void* handle, const char** texts_utf8, int count);

SNAP_API const char* snap_process_batch_ext(
    void* handle,
    const char** texts_utf8,
    int count,
    const char* options_json
);
```

---

### `snap_process_document` / `snap_process_file`

512 토큰을 초과하는 장문 텍스트(`snap_process_document`) 또는 대용량 파일(`snap_process_file`)을 문장 경계 감지기 기반으로 자동 분할·배치 스트리밍 처리합니다.

```c
SNAP_API const char* snap_process_document(void* handle, const char* doc_utf8, const char* options_json);

SNAP_API bool snap_process_file(
    void* handle,
    const char* in_file_path,
    const char* out_file_path,
    const char* options_json
);
```

---

### `snap_normalize`

숫자·기호·단위 텍스트 정규화 결과 문자열만 반환합니다(반환 포인터는 `snap_free()`로 해제).

```c
SNAP_API const char* snap_normalize(void* handle, const char* text_utf8);
```

---

### `snap_free` / `snap_destroy`

```c
SNAP_API void snap_free(const void* result);   // 문자열 버퍼 해제 (NULL 전달 시 안전 무시)
SNAP_API void snap_destroy(void* handle);      // 엔진 인스턴스 및 ONNX 세션 해제
```

---

## 3. 버전 및 호환성 확인 API (`snap_api.h` / `snap_version.h`)

```c
#define SNAP_VERSION_MAJOR    2
#define SNAP_VERSION_MINOR    1
#define SNAP_VERSION_PATCH    1
#define SNAP_VERSION_STRING   "2.1.3"
#define SNAP_VERSION_NUMBER   20103 // (MAJOR * 10000 + MINOR * 100 + PATCH)

SNAP_API const char* snap_version(void);                    // "2.1.3"
SNAP_API const char* snap_engine_version(const char* lang); // 언어 팩 모델 인덱스 버전 ("2.1.3")
SNAP_API int         snap_version_number(void);             // 20103
SNAP_API void        snap_version_info(int* major, int* minor, int* patch);
SNAP_API int         snap_version_check(int major, int minor); // 호환 시 1, 불일치 시 0
SNAP_API const char* snap_version_verbose(void);            // 플랫폼·컴파일러 포함 상세 문자열
SNAP_API bool        snap_is_gpu_available(void);           // 호스트 GPU/NPU 가속 사용 가능 여부 (true/false)
```

---

## 4. 신경망 TTS 백엔드 텐서 연동 API (`snap_piper` / VITS / MeloTTS)

PyTorch 의존성 없이 C++ 음향 모델에 문맥 BERT 은닉 상태(`[seq_len x hidden_dim]`)와 단어-서브워드 정렬 배열을 직접 전달하기 위한 API입니다.

```c
SNAP_API float* snap_get_bert_features(
    void* handle,
    const char* text_utf8,
    int* out_seq_len,
    int* out_hidden_dim,
    int** out_word2ph,
    int* out_word2ph_len
);

SNAP_API void snap_free_tensor(void* ptr); // features 및 out_word2ph 각각 해제 필수

// 선택: GPU/CPU 2단계 분리 파이프라인 API (include/snap/snap_pipeline_api.h)
SNAP_API float* snap_get_bert_features_with_offsets(
    void* handle, const char* text_utf8,
    int* out_seq_len, int* out_hidden_dim,
    size_t** out_offsets_flat, int* out_offsets_count
);
SNAP_API const char* snap_process_with_hidden(
    void* handle, const char* text_utf8,
    const float* hidden, int seq_len, int hdim,
    const size_t* offsets_flat, int offsets_count,
    const char* options_json
);
SNAP_API void snap_free_offsets(size_t* ptr);
```

---

## 5. C++ 전체 연동 예제 (`.spak` Zero-Disk 모드)

전체 빌드 가능한 샘플은 SDK 패키지 내 `examples/sdk_demo.cpp` 및 `examples/CMakeLists.txt`에 포함되어 있습니다.

```cpp
#include <cstdio>
#include "snap_api.h"

int main() {
    // 1. 버전 및 라이선스(선택) 확인
    if (!snap_version_check(SNAP_VERSION_MAJOR, SNAP_VERSION_MINOR)) {
        std::fprintf(stderr, "ABI 버전 불일치: %s\n", snap_version());
        return 1;
    }
    snap_set_license("OPTIONAL-LICENSE-KEY");

    // 2. 암호화 .spak 언어 팩 인메모리 로드 (디스크 임시 파일 0개)
    void* engine = snap_create("packs/snap_ko.spak", "ko");
    if (!engine) {
        std::fprintf(stderr, "엔진 초기화 실패: %s\n", snap_get_last_error());
        return 1;
    }

    // 3. 한국어 문맥 정규화 및 G2P 추론
    const char* json = snap_process(engine, "차량 3대가 오후 2시 30분에 감기 환자를 태우고 출발합니다.");
    if (json) {
        std::printf("%s\n", json);
        snap_free(json);
    }

    // 4. BERT 은닉 텐서 추출 (TTS 조건 입력용)
    int seq_len = 0, hidden_dim = 0, w2p_len = 0;
    int* word2piece = nullptr;
    float* feat = snap_get_bert_features(engine, "감기 환자", &seq_len, &hidden_dim, &word2piece, &w2p_len);
    if (feat) {
        snap_free_tensor(feat);
        snap_free_tensor(word2piece);
    }

    snap_destroy(engine);
    return 0;
}
```
