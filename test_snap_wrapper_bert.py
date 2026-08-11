import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from setup_env import setup_binaries, setup_weights
from snap_wrapper import SNAPEngineManager

def main():
    print("==================================================")
    print("🧪 SNAP C++ SDK get_bert_features C-API ctypes 연동 검증")
    print("==================================================")
    setup_binaries()
    setup_weights("ko")

    manager = SNAPEngineManager()
    engine = manager.get_engine("ko")

    test_text = "안녕하세요 반갑습니다"
    print(f"입력 텍스트: '{test_text}'")

    bert_tensor, word2ph = engine.get_bert_features(test_text)
    if bert_tensor is not None:
        print("  ✅ SNAP C++ SDK로부터 BERT hidden states 텐서 수신 성공!")
        print(f"  - bert_tensor shape: {bert_tensor.shape}")
        print(f"  - word2ph list:       {word2ph}")
    else:
        print("  ❌ get_bert_features 호출 실패!")

if __name__ == "__main__":
    main()
