import re
import json
from kiwipiepy import Kiwi
from jamo import hangul_to_jamo
from . import punctuation, symbols

kiwi = Kiwi()

def korean_text_to_phonemes(text, character: str = "hangeul") -> str:
    text = list(hangul_to_jamo(text))
    return "".join(text)

def text_normalize(text: str) -> str:
    # Basic normalization for Kiwi frontend
    text = re.sub(r'[\?\!]', '.', text)
    return text

def distribute_phone(n_phone, n_word):
    phones_per_word = [0] * n_word
    for task in range(n_phone):
        min_tasks = min(phones_per_word)
        min_index = phones_per_word.index(min_tasks)
        phones_per_word[min_index] += 1
    return phones_per_word

def g2p(norm_text):
    # Analyze text using Kiwi morphological analyzer
    tokens = kiwi.tokenize(norm_text)
    phs = []
    word2ph = []
    
    for token in tokens:
        surface = token.form
        if surface in punctuation:
            phs.append(surface)
            word2ph.append(1)
            continue
            
        phonemes = korean_text_to_phonemes(surface)
        phone_len = len(phonemes)
        
        # Word-level phoneme distribution
        word2ph.append(phone_len)
        phs.extend(list(phonemes))
        
    phones = ["_"] + phs + ["_"]
    tones = [0 for _ in phones]
    word2ph = [1] + word2ph + [1]
    return phones, tones, word2ph
