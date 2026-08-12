import re
import json
import unicodedata
from transformers import AutoTokenizer
from jamo import hangul_to_jamo

from . import punctuation, symbols
from snap_wrapper import SNAPEngineManager

# Korean BERT model (MeloTTS standard model)
model_id = 'kykim/bert-kor-base'
tokenizer = AutoTokenizer.from_pretrained(model_id)

DOUBLE_JONG_MAP = {
    'ᆪ': 'ㄱ',
    'ᆬ': 'ㄴ',
    'ᆭ': 'ㄴ',
    'ᆰ': 'ㄹ',
    'ᆱ': 'ㄹ',
    'ᆲ': 'ㄹ',
    'ᆳ': 'ㄹ',
    'ᆴ': 'ㄹ',
    'ᆵ': 'ㄹ',
    'ᆶ': 'ㄹ',
    'ᆹ': 'ㅂ',
}

def korean_text_to_phonemes(text, character: str = "hangeul") -> str:
    if character == "english":
        from anyascii import anyascii
        text = anyascii(text)
        return text

    jamo_list = list(hangul_to_jamo(text))
    sanitized = [DOUBLE_JONG_MAP.get(j, j) for j in jamo_list]
    return "".join(sanitized)

def text_normalize(text: str) -> str:
    """Run SNAP C++ Engine for context-aware Text Normalization & G2P."""
    manager = SNAPEngineManager()
    engine = manager.get_engine(lang="ko")
    raw_res = engine.process(text)
    
    # Parse JSON output from SNAP C++ Engine
    try:
        data = json.loads(raw_res)
        return data.get("normalized_text", text)
    except Exception:
        return raw_res

def distribute_phone(n_phone, n_word):
    phones_per_word = [0] * n_word
    for task in range(n_phone):
        min_tasks = min(phones_per_word)
        min_index = phones_per_word.index(min_tasks)
        phones_per_word[min_index] += 1
    return phones_per_word

def g2p(norm_text):
    tokenized = tokenizer.tokenize(norm_text)
    phs = []
    ph_groups = []
    for t in tokenized:
        if not t.startswith("#"):
            ph_groups.append([t])
        else:
            ph_groups[-1].append(t.replace("#", ""))
    word2ph = []
    for group in ph_groups:
        text = ""
        for ch in group:
            text += ch
        if text == '[UNK]':
            phs += ['_']
            word2ph += [1]
            continue
        elif text in punctuation:
            phs += [text]
            word2ph += [1]
            continue

        phonemes = korean_text_to_phonemes(text)
        phone_len = len(phonemes)
        word_len = len(group)

        aaa = distribute_phone(phone_len, word_len)
        assert len(aaa) == word_len
        word2ph += aaa

        phs += phonemes
    phones = ["_"] + phs + ["_"]
    tones = [0 for i in phones]
    word2ph = [1] + word2ph + [1]
    assert len(word2ph) == len(tokenized) + 2
    return phones, tones, word2ph

def get_bert_feature(text, word2ph, device='cpu'):
    """Return Raw 768-dim BERT tensor exported directly from SNAP C++ SDK.
    Zero PyTorch BERT model loading!
    """
    import numpy as np
    import torch
    
    manager = SNAPEngineManager()
    engine = manager.get_engine(lang="ko")
    bert_tensor, snap_w2ph = engine.get_bert_features(text)
    
    if bert_tensor is not None:
        # bert_tensor shape: [1, 768, seq_len] -> res: [seq_len, 768]
        res = bert_tensor.squeeze(0).t().numpy()
        phone_level_feature = []
        for i in range(len(word2ph)):
            repeat_feature = np.tile(res[i], (word2ph[i], 1))
            phone_level_feature.append(repeat_feature)
        phone_level_feature = np.concatenate(phone_level_feature, axis=0)
        return torch.from_numpy(phone_level_feature.T).float().to(device)
    
    # Fallback if C-API is not present
    from . import japanese_bert
    return japanese_bert.get_bert_feature(text, word2ph, device=device, model_id=model_id)