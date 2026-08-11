import os
import sys
import torch
import numpy as np
import soundfile as sf

# Set working directory to project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from melo.api import TTS
from melo import utils

def main():
    print("=" * 65)
    print("🧪 단독 테스트: Raw 768차원 BERT 텐서 ➔ MeloTTS 1x1 Conv1d 프로젝션 검증")
    print("=" * 65)

    # 1. Initialize MeloTTS KR model
    print("[1] MeloTTS 한국어(KR) 모델 로드 중...")
    device = "cpu"
    model = TTS(language="KR", device=device)
    
    text = "안녕하세요 반갑습니다."
    print(f"[2] 테스트 문장: '{text}'")

    # 2. Extract phonemes & tensors using utils.get_text_for_tts_infer
    speaker_ids = model.hps.data.spk2id
    spk_id = list(speaker_ids.values())[0]

    bert_dummy_orig, _, phones, tones, lang_ids = utils.get_text_for_tts_infer(
        text, "KR", model.hps, device, model.symbol_to_id
    )
    phone_len = phones.size(0)
    print(f"-> 추출된 음소 길이(phone_len): {phone_len}")

    # 3. Build dummy tensors simulating SNAP C++ output
    # bert: 1024-dim dummy zeros
    # ja_bert: 768-dim Raw BERT tensor (Simulating SNAP C++ output)
    bert_dummy = torch.zeros(1, 1024, phone_len, dtype=torch.float32).to(device)
    ja_bert_768 = torch.randn(1, 768, phone_len, dtype=torch.float32).to(device)

    print("[3] 입력 텐서 차원 확인:")
    print(f"  - bert (1024차원 입력) shape:   {bert_dummy.shape}")
    print(f"  - ja_bert (768차원 Raw 입력) shape: {ja_bert_768.shape}")

    # 4. Check TextEncoder internal 1x1 Conv1d projection
    enc_p = model.model.enc_p
    print("[4] TextEncoder 내 프로젝션 레이어 규격 확인:")
    print(f"  - text_encoder.ja_bert_proj: {enc_p.ja_bert_proj}")

    with torch.no_grad():
        projected = enc_p.ja_bert_proj(ja_bert_768)
        print(f"  -> 768차원 입력 ➔ Conv1d(768, 192, 1) 통과 후 shape: {projected.shape}")
        print("  ✅ TextEncoder 내 1x1 Conv1d(768 ➔ 192) 차원 변환 성공!")

    # 5. Execute full end-to-end inference with 768-dim ja_bert
    print("[5] SynthesizerTrn 전체 추론(infer) 통과 검증...")
    x_tst = phones.to(device).unsqueeze(0)
    tones_t = tones.to(device).unsqueeze(0)
    lang_ids_t = lang_ids.to(device).unsqueeze(0)
    x_tst_lengths = torch.LongTensor([phones.size(0)]).to(device)
    speakers = torch.LongTensor([spk_id]).to(device)

    with torch.no_grad():
        audio = model.model.infer(
            x_tst,
            x_tst_lengths,
            speakers,
            tones_t,
            lang_ids_t,
            bert_dummy,
            ja_bert_768,
            sdp_ratio=0.2,
            noise_scale=0.6,
            noise_scale_w=0.8,
            length_scale=1.0,
        )[0][0, 0].data.cpu().float().numpy()

    sample_rate = model.hps.data.sampling_rate
    duration = len(audio) / sample_rate
    output_wav = os.path.join(BASE_DIR, "test_768_output.wav")
    sf.write(output_wav, audio, sample_rate)

    print(f"  -> 생성된 오디오 데이터 길이: {len(audio)} 샘플 ({duration:.2f}초)")
    print(f"  -> WAV 파일 저장 위치: {output_wav}")
    print("=" * 65)
    print(" 🎉 단독 테스트 검증 완료: Raw 768차원 텐서가 에러 없이 1x1 Conv1d로 흡수되어 음성 생성 성공!")
    print("=" * 65)

if __name__ == "__main__":
    main()
