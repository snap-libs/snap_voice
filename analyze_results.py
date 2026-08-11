import json
import os

res_file = "benchmark_results.json"
if not os.path.exists(res_file):
    print("benchmark_results.json not found!")
    exit(1)

with open(res_file, "r", encoding="utf-8") as f:
    results = json.load(f)

print(f"Total Sentences Evaluated: {len(results)}")
diffs = [r for r in results if r["different"]]
print(f"Total Mismatches/Differences: {len(diffs)} / {len(results)} ({len(diffs)}%)")

print("\n==================================================")
print(" 📊 DETAILED CATEGORY COMPARISON REPORT ")
print("==================================================")

categories = {
    "1. 수사 문맥 구분 (Sino vs Native)": results[0:25],
    "2. 단위 및 숫자 표기 정규화": results[25:50],
    "3. 영단어 / 약어 / 브랜드 표기": results[50:75],
    "4. 연음, 받침 및 구음 문맥 전처리": results[75:100],
}

for cat_name, items in categories.items():
    cat_diffs = [it for it in items if it["different"]]
    print(f"\n### {cat_name} (차이점: {len(cat_diffs)}/{len(items)})")
    print("-" * 50)
    for sample in items[:5]:
        print(f"• 입력 문장: \"{sample['input']}\"")
        print(f"   - 원본 MeloTTS (g2pkk/num2words): {sample['original']}")
        print(f"   - SNAP C++ SDK Engine:          {sample['snap']}")
        print()
