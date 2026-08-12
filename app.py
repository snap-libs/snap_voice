import os
import sys
import json
import subprocess
import gradio as gr

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def setup_environment():
    """Ensure Linux C++ binaries and models are ready on Hugging Face Spaces."""
    bin_dir = os.path.join(BASE_DIR, "bin")
    os.makedirs(bin_dir, exist_ok=True)
    
    lib_name = "snap_cpp.dll" if os.name == 'nt' else "libsnap_cpp.so"
    lib_path = os.path.join(bin_dir, lib_name)
    
    if not os.path.exists(lib_path) and os.name != 'nt':
        print("[Setup] Linux binaries not found. Setting up snap_cpp binaries and models...")
        try:
            temp_dir = os.path.join(BASE_DIR, "snap_cpp_temp")
            if not os.path.exists(temp_dir):
                subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", "https://github.com/snap-libs/snap_cpp.git", temp_dir], check=True)
                subprocess.run(["git", "-C", temp_dir, "sparse-checkout", "set", "lib/linux/x64/v1.0.0", "scripts"], check=True)
            
            src_lib_dir = os.path.join(temp_dir, "lib", "linux", "x64", "v1.0.0")
            if os.path.exists(src_lib_dir):
                for f in os.listdir(src_lib_dir):
                    src_f = os.path.join(src_lib_dir, f)
                    dst_f = os.path.join(bin_dir, f)
                    if os.path.isfile(src_f):
                        with open(src_f, 'rb') as rf, open(dst_f, 'wb') as wf:
                            wf.write(rf.read())
            
            init_script = os.path.join(temp_dir, "scripts", "snap_init.sh")
            if os.path.exists(init_script):
                os.chmod(init_script, 0o755)
                subprocess.run([init_script, "-y", "--lang", "ko"], cwd=BASE_DIR, check=True)
                
            print("[Setup] Environment setup complete!")
        except Exception as e:
            print(f"[Setup Warning] Auto-setup failed: {e}")

# Run environment setup
setup_environment()

from snap_wrapper import SNAPEngineManager
from melo.api import TTS

# Global Engine & Model Initialization
print("[Initialization] Loading SNAP Engine Manager & MeloTTS Model...")
manager = SNAPEngineManager()
engine = manager.get_engine(lang="ko")
melo_model = TTS(language="KR", device="cpu")
print("[Initialization] Initialization Complete!")

# Check ZeroGPU environment
try:
    import spaces
    HAS_SPACES = True
    print("[ZeroGPU] spaces package detected. GPU acceleration enabled.")
except ImportError:
    HAS_SPACES = False
    print("[ZeroGPU] spaces package not found. Running in standard environment.")

def _synthesize_core(text, speed):
    if not text or not text.strip():
        return None, json.dumps({"error": "텍스트를 입력해주세요."}, ensure_ascii=False, indent=2)
    
    text = text.strip()
    
    # 1. SNAP C++ Engine Normalization & G2P JSON
    try:
        raw_norm = engine.process(text)
        try:
            norm_json = json.loads(raw_norm)
            norm_formatted = json.dumps(norm_json, ensure_ascii=False, indent=2)
        except Exception:
            norm_formatted = raw_norm
    except Exception as e:
        norm_formatted = json.dumps({"error": f"SNAP Engine Processing Error: {str(e)}"}, ensure_ascii=False, indent=2)
    
    # 2. Audio Synthesis via MeloTTS
    output_path = os.path.join(BASE_DIR, "output_hf_demo.wav")
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception:
            pass
            
    try:
        melo_model.tts_to_file(
            text=text,
            speaker_id=0,
            output_path=output_path,
            speed=speed,
            quiet=True
        )
    except Exception as e:
        return None, json.dumps({"error": f"MeloTTS Synthesis Error: {str(e)}"}, ensure_ascii=False, indent=2)
    
    return output_path, norm_formatted

if HAS_SPACES:
    @spaces.GPU
    def synthesize_speech(text, speed):
        return _synthesize_core(text, speed)
else:
    def synthesize_speech(text, speed):
        return _synthesize_core(text, speed)

# CSS styling matching snap-demo design system
CSS = """
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+KR:wght@400;500;600;700&display=swap');

body, .gradio-container {
    font-family: 'Pretendard', 'Noto Sans KR', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
}

.header-panel {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
}

.link-btn {
    text-decoration: none;
    background: #21262d;
    border: 1px solid #30363d;
    color: #c9d1d9;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.15s ease;
}

.link-btn:hover {
    background: #30363d;
    color: #ffffff;
}

.section-card {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 12px !important;
    padding: 20px !important;
    margin-bottom: 16px !important;
}

.primary-btn {
    background: #1f6feb !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 12px 20px !important;
    font-size: 15px !important;
    transition: background 0.15s ease !important;
    width: 100% !important;
    margin-top: 10px !important;
}

.primary-btn:hover {
    background: #388bfd !important;
}

.example-btn {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    color: #c9d1d9 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    align-items: center !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    line-height: 1.45 !important;
    padding: 10px 16px !important;
    margin-bottom: 8px !important;
    width: 100% !important;
    white-space: normal !important;
    word-break: break-word !important;
    min-height: 48px !important;
    box-sizing: border-box !important;
    border-radius: 6px !important;
    transition: all 0.15s ease !important;
}

.example-btn:hover {
    background: #30363d !important;
    color: #58a6ff !important;
    border-color: #58a6ff !important;
}

.quick-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)) !important;
    gap: 10px !important;
    width: 100% !important;
}
"""

HEAD = """
<meta name="title" content="SNAP Voice (MeloTTS + SNAP C++ Engine) Live Demo">
<meta name="description" content="고성능 SNAP C++ ITN/G2P/BERT 파이프라인과 MeloTTS 백엔드가 결합된 초고속 고품질 한국어 음성 합성 라이브 데모입니다.">
<meta name="keywords" content="tts, melotts, snap, text-normalization, speech-synthesis, g2p, zeroGPU">
"""

with gr.Blocks(css=CSS, head=HEAD, title="SNAP Voice Live Demo") as demo:
    # Header Panel
    gr.HTML("""
    <div class="header-panel">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div>
                <h1 style="font-size: 22px; font-weight: 700; margin: 0; color: #f0f6fc;">
                    🎙️ SNAP Voice <span style="color: #58a6ff;">(MeloTTS + SNAP C++ Engine) Live Demo</span>
                </h1>
                <p style="margin: 4px 0 0 0; color: #8b949e; font-size: 13px;">
                    고성능 C++ ITN/G2P/BERT 하이든 스테이트 추출 파이프라인과 MeloTTS 백엔드를 결합한 고품질 음성 합성 데모
                </p>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <a href="https://github.com/snap-libs/snap_voice" target="_blank" class="link-btn">GitHub Repository</a>
                <a href="https://snap-libs.github.io/snap/" target="_blank" class="link-btn">Official Website</a>
                <a href="https://github.com/snap-libs/snap_voice/blob/master/docs/SNAP_MeloTTS_Technical_Whitepaper(%ED%95%9C%EA%B5%AD%EC%96%B4).md" target="_blank" class="link-btn">기술 백서</a>
            </div>
        </div>
    </div>
    """)

    # Main 2-Column Layout
    with gr.Row(equal_height=False):
        # Left Column: Input Configuration
        with gr.Column(scale=5, elem_classes=["section-card"]):
            gr.Markdown("### 📥 Input Configuration")
            
            text_input = gr.Textbox(
                lines=4,
                placeholder="합성할 텍스트 입력 (예: 안녕하세요! SNAP과 MeloTTS가 만나 고품질 음성을 생성합니다.)",
                value="안녕하세요! SNAP과 MeloTTS가 만나 고품질 음성을 생성합니다.",
                label="합성할 텍스트 (Input Text)"
            )
            
            speed_slider = gr.Slider(
                minimum=0.5,
                maximum=2.0,
                value=1.0,
                step=0.1,
                label="음성 속도 (Speed Ratio)"
            )
            
            synth_btn = gr.Button("🚀 음성 합성 (Synthesize Speech)", elem_classes=["primary-btn"])

        # Right Column: Output & Analysis
        with gr.Column(scale=7, elem_classes=["section-card"]):
            gr.Markdown("### 📊 Synthesized Audio & SNAP Analysis")
            
            audio_output = gr.Audio(
                label="1. 생성된 오디오 (Output WAV)",
                type="filepath",
                autoplay=True
            )
            
            norm_output = gr.Code(
                label="2. SNAP C++ Normalization & G2P Output (JSON)",
                language="json"
            )

    # Bottom Panel: Quick Test Cases
    with gr.Column(elem_classes=["section-card"]):
        gr.Markdown("### 💡 Quick Test Cases (한국어 대표 예제 문장)")
        
        with gr.Row():
            with gr.Column(scale=1):
                ex1 = gr.Button("• 안녕하세요! SNAP과 MeloTTS가 만나 고품질 음성을 생성합니다.", elem_classes=["example-btn"])
                ex2 = gr.Button("• 여기서 3번 버스를 타고 3번 갈아타야 합니다.", elem_classes=["example-btn"])
                ex3 = gr.Button("• 2026년 8월 12일 서울의 날씨는 매우 맑고 기온은 28도입니다.", elem_classes=["example-btn"])
                ex4 = gr.Button("• 100달러를 환전하고 3.5km를 걸어서 101호로 갔습니다.", elem_classes=["example-btn"])
            with gr.Column(scale=1):
                ex5 = gr.Button("• 오후 3시 45분 50초에 강남구 테헤란로 123번지에서 만나요.", elem_classes=["example-btn"])
                ex6 = gr.Button("• 제12회 국제학술대회 참가비는 50,000원입니다.", elem_classes=["example-btn"])
                ex7 = gr.Button("• 인공지능 음성합성 기술이 빠르게 발전하고 있습니다.", elem_classes=["example-btn"])

    # Event Handlers
    synth_btn.click(
        fn=synthesize_speech,
        inputs=[text_input, speed_slider],
        outputs=[audio_output, norm_output]
    )

    # Quick Test Case Wiring
    ex1.click(lambda: ("안녕하세요! SNAP과 MeloTTS가 만나 고품질 음성을 생성합니다.", 1.0), outputs=[text_input, speed_slider])
    ex2.click(lambda: ("여기서 3번 버스를 타고 3번 갈아타야 합니다.", 1.0), outputs=[text_input, speed_slider])
    ex3.click(lambda: ("2026년 8월 12일 서울의 날씨는 매우 맑고 기온은 28도입니다.", 1.0), outputs=[text_input, speed_slider])
    ex4.click(lambda: ("100달러를 환전하고 3.5km를 걸어서 101호로 갔습니다.", 1.0), outputs=[text_input, speed_slider])
    ex5.click(lambda: ("오후 3시 45분 50초에 강남구 테헤란로 123번지에서 만나요.", 1.0), outputs=[text_input, speed_slider])
    ex6.click(lambda: ("제12회 국제학술대회 참가비는 50,000원입니다.", 1.0), outputs=[text_input, speed_slider])
    ex7.click(lambda: ("인공지능 음성합성 기술이 빠르게 발전하고 있습니다.", 1.1), outputs=[text_input, speed_slider])

    # Footer
    gr.HTML("""
    <div style="text-align: center; color: #484f58; font-size: 12px; margin-top: 24px;">
        Powered by SNAP C++ Native Engine & MeloTTS &bull; GitHub: <a href="https://github.com/snap-libs/snap_voice" target="_blank" style="color: #58a6ff; text-decoration: none;">snap-libs/snap_voice</a>
    </div>
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
