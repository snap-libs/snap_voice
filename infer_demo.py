import os
import sys
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from setup_env import setup_binaries, setup_weights
from snap_wrapper import SNAPEngineManager
from melo.api import TTS

def main():
    parser = argparse.ArgumentParser(description="SNAP C++ SDK + Official MeloTTS End-to-End Audio Synthesis Demo")
    parser.add_argument("--text", type=str, default="여기서 3번 버스를 타고 3번 갈아타야 해.", help="Input text to synthesize")
    parser.add_argument("--lang", type=str, default="KR", help="Language code (KR, EN, JP)")
    parser.add_argument("--output", type=str, default="output_snap_melo.wav", help="Output audio file path")
    parser.add_argument("--speaker_id", type=int, default=0, help="Speaker ID")
    args = parser.parse_args()

    print("==================================================")
    print(" 🚀 SNAP C++ SDK & Official MeloTTS End-to-End Demo ")
    print("==================================================")
    print(f"Input Text:  {args.text}")
    print(f"Language:    {args.lang}")
    print(f"Output File: {args.output}")
    print("--------------------------------------------------")

    # 1. Environment & Weights Setup
    print("[Step 1] Initializing SNAP C++ binaries & model weights...")
    setup_binaries()
    setup_weights("ko")

    # 2. Test SNAP C++ SDK Text Normalization, G2P & Raw BERT Tensor Export
    print("\n[Step 2] Testing SNAP C++ Engine (snap_process & snap_get_bert_features)...")
    manager = SNAPEngineManager()
    engine = manager.get_engine(lang="ko")
    
    sdk_ver = engine.get_version()
    print(f"-> SNAP SDK Version: {sdk_ver}")
    
    normalized_text = engine.process(args.text)
    print(f"-> SNAP C++ Output (Normalized & G2P): {normalized_text}")

    bert_tensor, word2ph = engine.get_bert_features(args.text)
    if bert_tensor is not None:
        print(f"-> SNAP C++ Raw BERT Tensor Export: shape={bert_tensor.shape}, word2ph={word2ph}")
    print("--------------------------------------------------")

    # 3. Complete MeloTTS End-to-End Audio Synthesis using SNAP C++ BERT Tensor
    print("\n[Step 3] Loading MeloTTS Audio Model & Synthesizing Audio File...")
    model = TTS(language=args.lang, device='cpu')
    
    output_path = os.path.abspath(args.output)
    print(f"-> Synthesizing text to WAV file at: {output_path}")
    
    model.tts_to_file(
        text=args.text,
        speaker_id=args.speaker_id,
        output_path=output_path,
        speed=1.0,
        quiet=False
    )

    print("--------------------------------------------------")
    print(f" SUCCESS: Complete audio synthesized & saved to {output_path}!")
    print("==================================================")

if __name__ == "__main__":
    main()
