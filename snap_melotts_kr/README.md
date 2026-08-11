# snap_melotts_kr (Korean Module for SNAP C++ SDK & MeloTTS)

Submodule for Korean text-to-speech synthesis within the **`snap_melotts`** repository.

---

## 1. Quick Start

```bash
# 1. Clone repository and enter Korean submodule directory
git clone https://github.com/snap-libs/snap_melotts.git
cd snap_melotts/snap_melotts_kr

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize model resources (SNAP_HOME=.)
snap init . --lang ko

# 4. Run audio synthesis
python infer_demo.py --text "여기서 3번버스를 타고 3번 갈아타야합니다" --output output_kr.wav
```

---

## 2. Technical Characteristics

1. **Direct BERT Tensor Export**: Consumes raw 768-dimensional hidden state tensors directly exported from SNAP C++ SDK ONNX sessions (`snap_get_bert_features`).
2. **Text Normalization**: Delegates Sino/Native Korean numeral disambiguation to the C++ engine (`snap_process`).
3. **Portable Directory Hierarchy**: Functions using `SNAP_HOME=.` as the top-level anchor for relative path resolution (`models/ko/`).
