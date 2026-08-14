from .symbols import *
from .cleaner import clean_text

_symbol_to_id = {s: i for i, s in enumerate(symbols)}

def cleaned_text_to_sequence(cleaned_text, tones, language, symbol_to_id=None):
    symbol_to_id_map = symbol_to_id if symbol_to_id else _symbol_to_id
    unk_id = symbol_to_id_map.get('UNK', symbol_to_id_map.get('_', 0))
    phones = [symbol_to_id_map.get(symbol, unk_id) for symbol in cleaned_text]
    tone_start = language_tone_start_map[language]
    tones = [i + tone_start for i in tones]
    lang_id = language_id_map[language]
    lang_ids = [lang_id for i in phones]
    return phones, tones, lang_ids

def get_bert(norm_text, word2ph, language, device):
    language = language.upper()
    if language in ['KR', 'KO']:
        from .korean import get_bert_feature as kr_bert
        return kr_bert(norm_text, word2ph, device)
    elif language in ['EN']:
        from .english_bert import get_bert_feature as en_bert
        return en_bert(norm_text, word2ph, device)
    elif language in ['JP']:
        from .japanese_bert import get_bert_feature as jp_bert
        return jp_bert(norm_text, word2ph, device)
    elif language in ['ZH']:
        from .chinese_bert import get_bert_feature as zh_bert
        return zh_bert(norm_text, word2ph, device)
    elif language in ['ZH_MIX_EN']:
        from .chinese_mix import get_bert_feature as zh_mix_en_bert
        return zh_mix_en_bert(norm_text, word2ph, device)
    elif language in ['FR']:
        from .french_bert import get_bert_feature as fr_bert
        return fr_bert(norm_text, word2ph, device)
    elif language in ['SP', 'ES']:
        from .spanish_bert import get_bert_feature as sp_bert
        return sp_bert(norm_text, word2ph, device)
    else:
        raise NotImplementedError(f"Language '{language}' is not supported in get_bert")
