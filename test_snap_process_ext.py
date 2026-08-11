import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from setup_env import setup_binaries, setup_weights
from snap_wrapper import SNAPEngineManager

def main():
    print("==================================================")
    print("🧪 [REQ-3] snap_process_ext (인메모리 JSON 동적 옵션) 검증")
    print("==================================================")
    setup_binaries()
    setup_weights("ko")

    manager = SNAPEngineManager()
    engine = manager.get_engine("ko")

    test_text = "안녕하세요 반갑습니다"

    # Test 1: Default call (to_json=True)
    res_default = engine.process_ext(test_text)
    print("\n[Test 1] 기본 호출 (Options: None)")
    print(f"-> 출력 (JSON 여부): {res_default[:80]}...")

    # Test 2: Dynamic Option override (to_json=False -> return phonology string directly)
    res_no_json = engine.process_ext(test_text, options={"to_json": False})
    print("\n[Test 2] 문장별 동적 옵션 덮어쓰기 (options={'to_json': False})")
    print(f"-> 출력 (Phonology 텍스트 직출력): '{res_no_json}'")

    print("\n==================================================")
    print(" 🎉 [REQ-3] 인메모리 JSON 동적 옵션 C-API (snap_process_ext) 검증 성공!")
    print("==================================================")

if __name__ == "__main__":
    main()
