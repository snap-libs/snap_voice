import os
import sys
import json
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from setup_env import setup_binaries, setup_weights
from snap_wrapper import SNAPEngineManager
from g2pkk import G2p
from num2words import num2words
from anyascii import anyascii

# Initialize Original MeloTTS Frontend Components
g2p_kr = G2p()

def original_melo_normalize(text: str) -> str:
    """Simulate Original MeloTTS Korean Text Normalization (num2words + g2pkk)."""
    text = text.strip()
    # Simple regex for numbers using num2words in original MeloTTS
    def replace_num(match):
        try:
            n = int(match.group())
            return num2words(n, lang='ko')
        except Exception:
            return match.group()
            
    # Original MeloTTS handles numbers via num2words and g2pkk
    text_num = re.sub(r'\d+', replace_num, text)
    try:
        norm = g2p_kr(text_num)
    except Exception:
        norm = text_num
    return norm

def snap_melo_normalize(text: str) -> str:
    """SNAP C++ SDK Enhanced Text Normalization & Context G2P."""
    manager = SNAPEngineManager()
    engine = manager.get_engine(lang="ko")
    raw_res = engine.process(text)
    try:
        data = json.loads(raw_res)
        return data.get("normalized_text", text)
    except Exception:
        return raw_res

# 100 Benchmark Sentences Dataset
BENCHMARK_SENTENCES = [
    # 1. 수사 문맥 구분 (Sino vs Native) - 25개
    "여기서 3번 버스를 타고 3번 갈아타야 해.",
    "1층에 가서 1개 사와라.",
    "2번 노선에서 2번 탈락했다.",
    "7시에 7번 버스 출발합니다.",
    "10대 시절 10대를 맞았다.",
    "5번 창구에서 5번 제출하세요.",
    "1번 문제 정답을 1번만 말해줘.",
    "4번 타자가 4번 연속 안타를 쳤다.",
    "2층 202호에 2명이 살고 있다.",
    "6번 버스가 6분 뒤에 도착합니다.",
    "8번 선수 8번 도전 성공.",
    "9번 방에서 9번 불렀습니다.",
    "10번 출구로 나가서 10분 걸어가세요.",
    "3명이서 3번 아이스크림을 골랐다.",
    "1월 1일에 1등을 하였다.",
    "2월 2일에 2번째 상을 받았다.",
    "11번 버스를 11번 탔다.",
    "12개 중에서 12번 상자를 선택해.",
    "5월 5일에 5명이 모였다.",
    "8월 8일에 8번 유니폼을 입었다.",
    "100번 말해도 100번 버스는 안 온다.",
    "10명이서 10번 구호를 외쳤다.",
    "4시 4분 4초에 4번 버튼을 눌렀다.",
    "2번 참가자 2번 실패.",
    "3번 트랙 3번 주자 입장.",

    # 2. 단위 및 숫자 표기 정규화 - 25개
    "100km/h 속도로 차를 달렸다.",
    "$500와 30% 할인 쿠폰을 받았다.",
    "500mL 우유 2캔을 마셨다.",
    "1,000,000원의 비용이 발생했습니다.",
    "2.5% 인상된 가격입니다.",
    "기온이 -5도까지 떨어졌습니다.",
    "3.14는 파이의 값입니다.",
    "50kg 수박을 들었다.",
    "100m 경주에서 1위를 차지했다.",
    "2,500달러를 환전했습니다.",
    "10년 동안 100,000km를 주행했다.",
    "면적이 100m²에 달합니다.",
    "용량이 64GB인 스마트폰.",
    "12.5%의 높은 수익률.",
    "시속 120km로 주행 중이다.",
    "체중 75kg, 키 180cm.",
    "3,000,000명의 관객을 동원했다.",
    "250mL 캔음료 3개.",
    "0.1초 차이로 우승했다.",
    "1,500원짜리 과자 5개.",
    "50% 이상 확률로 성공한다.",
    "100GB 용량을 제공합니다.",
    "영하 10도의 추운 날씨.",
    "1.5리터 페트병 2개.",
    "10,000걸음을 걸었습니다.",

    # 3. 영단어 / 약어 / 브랜드 표기 - 25개
    "AI 기술과 ML 모델을 활용합니다.",
    "COVID-19 백신을 접종받았습니다.",
    "K-POP의 글로벌 인기가 대단합니다.",
    "DNA 검사 결과를 기다리고 있습니다.",
    "CEO 및 CTO 인사를 발표했습니다.",
    "IT 기업의 MOU 체결 소식입니다.",
    "Dr. Kim 선생님의 진료시간.",
    "MPEG 파일과 MP3 음원.",
    "USB 메모리와 HDMI 케이블.",
    "PDF 문서와 HTML 웹페이지.",
    "FBI와 CIA의 합동 수사.",
    "NASA의 우주 탐사 프로젝트.",
    "NATO 회원국 회담 개최.",
    "UNESCO 세계문화유산 지정.",
    "VIP 고객 전용 라운지.",
    "WHO의 공식 발표 내용.",
    "WIFI 연결 상태가 양호합니다.",
    "GPS 신호가 수신되었습니다.",
    "CPU와 GPU 성능 비교.",
    "API 키와 SDK 설치 가이드.",
    "OS 업데이트가 완료되었습니다.",
    "URL 주소를 확인해주세요.",
    "RAM 용량을 16GB로 증설.",
    "SUV 차량의 판매량 증가.",
    "LED 조명으로 교체했습니다.",

    # 4. 연음, 받침 및 구음 문맥 전처리 - 25개
    "있는 그대로 사실을 밝혀라.",
    "굳이 같이 가야 할 이유가 없다.",
    "넓고 깨끗한 장소를 찾았다.",
    "밝은 달빛 아래에서 쉬었다.",
    "닭을 맛있는 양념에 튀겼다.",
    "흙을 만지고 놀았습니다.",
    "삶의 의미를 깊이 생각해보았다.",
    "젊은이들의 열정과 도전.",
    "값비싼 물건을 보관하다.",
    "없어지지 않는 기억들.",
    "않아서 다행이라고 생각했다.",
    "괜찮아 잘 될 거야.",
    "끝까지 최선을 다하자.",
    "맞히다와 맞추다의 차이점.",
    "깎아주세요 조금만 더.",
    "밟지 마시오 풀밭을.",
    "핥다 개가 손을 핥았다.",
    "훑어보다 서류를 한번 훑었다.",
    "읊조리다 시를 읊조렸다.",
    "얹다 손을 이마에 얹었다.",
    "얹혀살다 남의 집에 얹혀산다.",
    "읊다 시집을 펼쳐 읊었다.",
    "갉아먹다 나무를 갉아먹는다.",
    "얽히고설킨 복잡한 문제.",
    "맑다 하강하는 맑은 가을하늘."
]

def run_benchmark():
    print("[1/3] Initializing SNAP C++ Environment...")
    setup_binaries()
    setup_weights("ko")
    
    results = []
    mismatch_count = 0
    snap_context_wins = 0

    print(f"[2/3] Evaluating 100 sentences across Original MeloTTS vs SNAP C++ Enhanced Frontend...")

    for idx, text in enumerate(BENCHMARK_SENTENCES, 1):
        orig_res = original_melo_normalize(text)
        snap_res = snap_melo_normalize(text)
        
        is_diff = (orig_res != snap_res)
        if is_diff:
            mismatch_count += 1
            
        results.append({
            "id": idx,
            "input": text,
            "original": orig_res,
            "snap": snap_res,
            "different": is_diff
        })

    print(f"[3/3] Evaluation Complete! Total: {len(BENCHMARK_SENTENCES)}, Differences found in: {mismatch_count} sentences.")
    
    # Save Benchmark Results JSON
    res_path = os.path.join(BASE_DIR, "benchmark_results.json")
    with open(res_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    return results

if __name__ == "__main__":
    run_benchmark()
