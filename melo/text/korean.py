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

def korean_text_to_phonemes(text, character: str = "hangeul") -> str:
    if character == "english":
        from anyascii import anyascii
        text = anyascii(text)
        return text

    text = list(hangul_to_jamo(text))
    return "".join(text)

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

def get_bert_feature(text, word2ph, device='cuda'):
    from . import japanese_bert
    return japanese_bert.get_bert_feature(text, word2ph, device=device, model_id=model_id)