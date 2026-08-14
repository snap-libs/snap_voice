import re
import g2pk
from jamo import hangul_to_jamo
from . import punctuation

# Initialize KakaoBrain g2pk instance
g2p_engine = g2pk.G2p()

def text_normalize(text: str) -> str:
    text = re.sub(r'[\?\!]', '.', text)
    return text

def korean_text_to_phonemes(text, character: str = "hangeul") -> str:
    text = list(hangul_to_jamo(text))
    return "".join(text)

def g2p(norm_text):
    # 1. Apply REAL Python G2P transformation using g2pk
    try:
        g2p_text = g2p_engine(norm_text)
    except Exception:
        g2p_text = norm_text
        
    # 2. Phoneme distribution
    phs = []
    word2ph = []
    
    words = g2p_text.split()
    for word in words:
        if word in punctuation:
            phs.append(word)
            word2ph.append(1)
            continue
            
        phonemes = korean_text_to_phonemes(word)
        phone_len = len(phonemes)
        word2ph.append(phone_len)
        phs.extend(list(phonemes))
        
    phones = ["_"] + phs + ["_"]
    tones = [0 for _ in phones]
    word2ph = [1] + word2ph + [1]
    
    # Return both formatted phonemes and the real transformed text string
    return phones, tones, word2ph, g2p_text
