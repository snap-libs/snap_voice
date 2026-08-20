import copy
import importlib

# Lazy-load language modules to avoid eager imports of unused language dependencies
_language_module_cache = {}
_LANG_TO_MODULE = {
    "EN": "english",
    "KR": "korean",
    "KO": "korean",
    "JP": "japanese",
    "ZH": "chinese",
    "FR": "french",
    "SP": "spanish",
    "ES": "spanish",
}

def _get_language_module(language):
    language = language.upper()
    if language not in _language_module_cache:
        if language not in _LANG_TO_MODULE:
            raise NotImplementedError(f"Language '{language}' is not supported.")
        mod_name = _LANG_TO_MODULE[language]
        _language_module_cache[language] = importlib.import_module(f".{mod_name}", package="melo.text")
    return _language_module_cache[language]

def clean_text(text, language, is_already_normalized=False):
    language_module = _get_language_module(language)
    if is_already_normalized:
        norm_text = text
    else:
        norm_text = language_module.text_normalize(text)
    phones, tones, word2ph = language_module.g2p(norm_text)
    return norm_text, phones, tones, word2ph

def clean_text_bert(text, language, device=None):
    language_module = _get_language_module(language)
    norm_text = language_module.text_normalize(text)
    phones, tones, word2ph = language_module.g2p(norm_text)
    
    word2ph_bak = copy.deepcopy(word2ph)
    for i in range(len(word2ph)):
        word2ph[i] = word2ph[i] * 2
    word2ph[0] += 1
    
    bert = language_module.get_bert_feature(norm_text, word2ph, device=device)
    return norm_text, phones, tones, word2ph_bak, bert

def text_to_sequence(text, language):
    norm_text, phones, tones, word2ph = clean_text(text, language)
    from . import cleaned_text_to_sequence
    return cleaned_text_to_sequence(phones, tones, language)