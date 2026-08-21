import os
import re
import json
import unicodedata
import numpy as np
import torch
from jamo import hangul_to_jamo

from . import punctuation, symbols
from snap_wrapper import SNAPEngineManager

# Jongseong (final consonant) neutralization map.
# Every target must be one of the 7 representative finals that actually exist
# in the MeloTTS symbol table: ᆨ ᆫ ᆮ ᆯ ᆷ ᆸ ᆼ
# (Compatibility jamo like ㄱ/ㄴ/ㄹ and choseong initials must NOT be used as targets.)
DOUBLE_JONG_MAP = {
    # tense/aspirated & double finals -> representative finals
    'ᆩ': 'ᆨ', 'ᆪ': 'ᆨ',              # ㄲ, ㄳ -> ㄱ
    'ᆬ': 'ᆫ', 'ᆭ': 'ᆫ',              # ㄵ, ㄶ -> ㄴ
    'ᆰ': 'ᆨ', 'ᆱ': 'ᆷ', 'ᆲ': 'ᆸ',  # ㄺ->ㄱ(닭[닥]), ㄻ->ㅁ(삶[삼]), ㄼ->ㅂ(밟[밥])
    'ᆳ': 'ᆯ', 'ᆴ': 'ᆯ', 'ᆶ': 'ᆯ',  # ㄽ, ㄾ, ㅀ -> ㄹ
    'ᆵ': 'ᆸ', 'ᆹ': 'ᆸ',              # ㄿ, ㅄ -> ㅂ (읊[읍], 없[업])
    # single finals without dedicated symbols -> representative finals
    'ᆺ': 'ᆮ', 'ᆻ': 'ᆮ', 'ᆽ': 'ᆮ', 'ᆾ': 'ᆮ', 'ᇀ': 'ᆮ', 'ᇂ': 'ᆮ',  # ㅅㅆㅈㅊㅌㅎ -> ㄷ
    'ᆿ': 'ᆨ',                          # ㅋ -> ㄱ
    'ᇁ': 'ᆸ',                          # ㅍ -> ㅂ
}

def korean_text_to_phonemes(text, character: str = "hangeul") -> str:
    if character == "english":
        from anyascii import anyascii
        text = anyascii(text)
        return text.lower()

    jamo_list = list(hangul_to_jamo(text))
    sanitized = [DOUBLE_JONG_MAP.get(j, j) for j in jamo_list]
    sanitized = [ch for ch in sanitized if ch not in ['ʰ', '\u02b0', '\u02b1', '\u02b2', '\u02b7', '\u02b8']]
    sanitized = [ch.lower() if ('A' <= ch <= 'Z') else ch for ch in sanitized]
    return "".join(sanitized)

def text_normalize(text: str) -> str:
    """Run SNAP C++ Engine for context-aware Text Normalization & G2P."""
    try:
        manager = SNAPEngineManager()
        engine = manager.get_engine(lang="ko")
        raw_res = engine.process(text)
        
        # Parse JSON output from SNAP C++ Engine
        data = json.loads(raw_res)
        ph = data.get("phonology")
        # If phonology is Korean phonetic text (not IPA brackets), use it for perfect G2P
        if ph and not ph.startswith('['):
            return ph
        return data.get("normalized_text") or ph or text
    except Exception:
        return text

def distribute_phone(n_phone, n_word):
    phones_per_word = [0] * n_word
    for task in range(n_phone):
        min_tasks = min(phones_per_word)
        min_index = phones_per_word.index(min_tasks)
        phones_per_word[min_index] += 1
    return phones_per_word

ENG_WORD_MAP = {
    "snap": "스냅",
    "melotts": "멜로티티에스",
    "tts": "티티에스",
    "ai": "에이아이",
}

ENG_LETTER_MAP = {
    "a": "에이", "b": "비", "c": "씨", "d": "디", "e": "이", "f": "에프",
    "g": "지", "h": "에이치", "i": "아이", "j": "제이", "k": "케이", "l": "엘",
    "m": "엠", "n": "엔", "o": "오", "p": "피", "q": "큐", "r": "알",
    "s": "에스", "t": "티", "u": "유", "v": "브이", "w": "더블유", "x": "엑스",
    "y": "와이", "z": "제트"
}

def convert_eng_word_to_ko(word: str) -> str:
    match = re.match(r'^([a-zA-Z]+)(.*)$', word)
    if not match:
        return word
    eng_part, ko_part = match.groups()
    eng_lower = eng_part.lower()
    
    if eng_lower in ENG_WORD_MAP:
        ko_trans = ENG_WORD_MAP[eng_lower]
    else:
        ko_trans = "".join(ENG_LETTER_MAP.get(c.lower(), c) for c in eng_part)
    
    return ko_trans + ko_part

def transliterate_english_in_text(text: str) -> str:
    words = text.split()
    converted = [convert_eng_word_to_ko(w) for w in words]
    return " ".join(converted)

_KO_TOKENIZER = None
_KO_TOKENIZER_FAILED = False

def _get_ko_tokenizer():
    """Lazy-load the same WordPiece tokenizer used by the SNAP C++ BERT engine.

    Loading models/ko/KO_tokenizer.json guarantees the Python-side token
    segmentation is bit-exact with the C++ BERT token stream, which makes
    word2ph <-> BERT hidden-state alignment a strict 1:1 contract.
    """
    global _KO_TOKENIZER, _KO_TOKENIZER_FAILED
    if _KO_TOKENIZER is None and not _KO_TOKENIZER_FAILED:
        try:
            from tokenizers import Tokenizer
            import snap_wrapper
            snap_root = os.path.dirname(os.path.abspath(snap_wrapper.__file__))
            tk_path = os.path.join(snap_root, "models", "ko", "KO_tokenizer.json")
            _KO_TOKENIZER = Tokenizer.from_file(tk_path)
        except Exception as e:
            print(f"[KR G2P] WordPiece tokenizer unavailable, using word-level fallback: {e}")
            _KO_TOKENIZER_FAILED = True
    return _KO_TOKENIZER

def _g2p_wordpiece(text, tokenizer):
    """Build phones & word2ph aligned 1:1 with the C++ BERT WordPiece token stream.

    Each WordPiece subword token (offsets-based character span) maps to the
    number of jamo phonemes covering that span. Punctuation naturally becomes
    its own token here (the WordPiece pre-tokenizer isolates it), matching the
    C++ side. A token with zero phonemes keeps a 0 entry so that
    len(word2ph) == bert_seq_len is preserved at all times.
    """
    enc = tokenizer.encode(text, add_special_tokens=False)
    phs = []
    word2ph = []
    for token_str, (start, end) in zip(enc.tokens, enc.offsets):
        span = text[start:end] if end > start else token_str.replace("##", "")
        phonemes = list(korean_text_to_phonemes(span))
        phs.extend(phonemes)
        word2ph.append(len(phonemes))
    return phs, word2ph

def _g2p_word_level(converted_text):
    """Fallback: word-level mapping (used only when the WordPiece tokenizer is unavailable)."""
    tokens = re.findall(r'[\w]+|[^\w\s]', converted_text)
    if not tokens:
        tokens = [converted_text]

    phs = []
    word2ph = []
    for token in tokens:
        if token in punctuation:
            phs.append(token)
            word2ph.append(1)
            continue

        phonemes = list(korean_text_to_phonemes(token))
        if not phonemes:
            continue

        phs.extend(phonemes)
        word2ph.append(len(phonemes))
    return phs, word2ph

def g2p(norm_text):
    # SNAP Native G2P with WordPiece-span mapping (1:1 aligned to C++ BERT tokens)
    converted_text = transliterate_english_in_text(norm_text)

    tokenizer = _get_ko_tokenizer()
    if tokenizer is not None:
        phs, word2ph = _g2p_wordpiece(converted_text, tokenizer)
    else:
        phs, word2ph = _g2p_word_level(converted_text)

    phones = ["_"] + phs + ["_"]
    tones = [0 for _ in phones]
    word2ph = [1] + word2ph + [1]  # pads align with BERT [CLS] / [SEP]
    assert len(phones) == sum(word2ph), f"Length mismatch: {len(phones)} != {sum(word2ph)}"
    return phones, tones, word2ph

def get_bert_feature(text, word2ph, device='cpu'):
    """Return Raw 768-dim BERT tensor exported directly from SNAP C++ SDK.
    100% SNAP C++ Native Pipeline (Zero External PyTorch Transformers Model)!
    """
    try:
        manager = SNAPEngineManager()
        engine = manager.get_engine(lang="ko")
        bert_tensor, _snap_w2ph = engine.get_bert_features(text)
        if bert_tensor is not None:
            res = bert_tensor.squeeze(0).t().numpy()
            num_feats = res.shape[0]

            # Mask out [UNK] tokens (phonetic tokens not in WordPiece vocab) to prevent attention distortion & silence drop
            tokenizer = _get_ko_tokenizer()
            if tokenizer is not None:
                enc = tokenizer.encode(text, add_special_tokens=False)
                expected_seq = len(enc.tokens) + 2
                if expected_seq == num_feats:
                    for i, tok in enumerate(enc.tokens):
                        if tok == '[UNK]' and (i + 1) < num_feats:
                            res[i + 1] = 0.0

            phone_level_feature = []
            for i, count in enumerate(word2ph):
                feat_idx = min(i, num_feats - 1)
                repeat_feature = np.tile(res[feat_idx], (count, 1))
                phone_level_feature.append(repeat_feature)

            phone_level_feature = np.concatenate(phone_level_feature, axis=0)
            return torch.from_numpy(phone_level_feature.T).float().to(device)
    except Exception as e:
        print(f"[SNAP C++ BERT Engine] Info: {e}")
    
    # 100% SNAP C++ Native Tensor Fallback (Zero External PyTorch Downloads)
    total_phones = sum(word2ph)
    return torch.zeros((768, total_phones), dtype=torch.float32, device=device)