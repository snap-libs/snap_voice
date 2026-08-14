import os
import sys
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from melo.api import TTS

def main():
    parser = argparse.ArgumentParser(description="SNAP Voice: End-to-End Speech Synthesis Demo (SNAP C++ + MeloTTS)")
    parser.add_argument("--text", type=str, default="여기서 3번 버스를 타고 3번 갈아타야 합니다.", help="Input text to synthesize")
    parser.add_argument("--lang", type=str, default="KR", help="Language code (KR, EN, JP)")
    parser.add_argument("--output", type=str, default="output_kr.wav", help="Output WAV audio file path")
    parser.add_argument("--device", type=str, default="cpu", help="Computation device (cpu, cuda, auto)")
    parser.add_argument("--speaker_id", type=int, default=0, help="Speaker ID (default: 0)")
    parser.add_argument("--speed", type=float, default=1.0, help="Audio playback speed factor (default: 1.0)")
    parser.add_argument("--verify-c-api", action="store_true", help="Optional: verify raw SNAP C++ SDK normalization & BERT C-API")
    args = parser.parse_args()

    print("==================================================")
    print(" 🎙️  SNAP Voice: High-Fidelity Speech Synthesis   ")
    print("==================================================")
    print(f"Input Text:   {args.text}")
    print(f"Language:     {args.lang}")
    print(f"Device:       {args.device}")
    print(f"Output File:  {args.output}")
    print("--------------------------------------------------")

    # Optional: Direct SNAP C++ SDK Verification
    if args.verify_c_api:
        from snap_wrapper import SNAPEngineManager
        print("\n[C-API Check] Direct SNAP C++ SDK Inspection...")
        manager = SNAPEngineManager()
        engine = manager.get_engine(lang="ko")
        sdk_ver = engine.get_version()
        norm_res = engine.process(args.text)
        bert_tensor, word2ph = engine.get_bert_features(args.text)
        print(f" -> SDK Version: {sdk_ver}")
        print(f" -> C++ ITN/G2P Output: {norm_res}")
        if bert_tensor is not None:
            print(f" -> Raw INT8 BERT Tensor Shape: {bert_tensor.shape}")
        print("--------------------------------------------------")

    # 1. Initialize MeloTTS with Integrated SNAP C++ Pipeline
    print("\n[Step 1] Loading MeloTTS & Initializing SNAP C++ Native Pipeline...")
    model = TTS(language=args.lang, device=args.device)

    # 2. Synthesize Speech to WAV File
    output_path = os.path.abspath(args.output)
    print(f"\n[Step 2] Synthesizing audio to: {output_path}")

    model.tts_to_file(
        text=args.text,
        speaker_id=args.speaker_id,
        output_path=output_path,
        speed=args.speed,
        quiet=False
    )

    print("--------------------------------------------------")
    print(f" ✅ SUCCESS: Audio synthesized and saved to:")
    print(f"    {output_path}")
    print("==================================================")

if __name__ == "__main__":
    main()
