"""Streamlit interface for ACG Ideal Matchmaker."""
import html
import json
import os

import numpy as np
import streamlit as st
from pipeline import (
    get_api_key, CHAR_DATA_PATH, EMBEDDINGS_PATH, load_character_data, load_embeddings,
    extract_traits, embed_text_ollama, generate_final_report,
)

from retrieval import CosineIndex

st.set_page_config(page_title="ACG • 理想型研究室", page_icon="✦", layout="wide")
st.markdown("""
<style>
:root { --ink:#23344d; --accent:#5162d6; }
.stApp { background:#f4f7fc; color:var(--ink); }
.block-container { max-width:1160px; padding-top:2.5rem; }
h1,h2,h3 { font-family:'Trebuchet MS','Microsoft JhengHei',sans-serif; letter-spacing:-.035em; }
.hero { padding:2.4rem; border-radius:24px; background:#e5ebff; border:1px solid #cbd5f7; margin-bottom:1.7rem; }
.eyebrow { color:#5162d6; font:700 .78rem monospace; letter-spacing:.16em; }
.hero h1 { font-size:clamp(2rem,5vw,3.4rem); margin:.6rem 0; }
.hero p { max-width:620px; color:#516078; line-height:1.8; }
.card { min-height:180px; background:#fff; padding:1.5rem; border:1px solid #dce3f0; border-radius:18px; margin:.6rem 0; }
.card .rank { color:#5162d6; font:700 .8rem monospace; }
.card h3 { margin:.7rem 0; }
.chip { display:inline-block; background:#edf0ff; color:#4051ad; border-radius:20px; padding:.25rem .65rem; margin:.2rem; font-size:.85rem; }
.stButton button:focus-visible { outline:3px solid #5162d6; outline-offset:3px; }
@media(max-width:640px) { .hero { padding:1.4rem; } .block-container { padding-top:1rem; } }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_catalog():
    characters = load_character_data(CHAR_DATA_PATH)
    embeddings = load_embeddings(EMBEDDINGS_PATH)
    if len(characters) != len(embeddings):
        raise ValueError("角色資料與向量數量不一致，請重新產生資料。")
    if not characters or any(not isinstance(c.get('name'), str) or not c['name'].strip() for c in characters):
        raise ValueError("角色資料缺少有效名稱。")
    if embeddings.ndim != 2 or not np.isfinite(embeddings).all():
        raise ValueError("角色向量格式無效。")
    return characters, embeddings

@st.cache_resource
def load_index():
    _, vectors = load_catalog()
    return CosineIndex(vectors)

try:
    characters, embeddings = load_catalog()
    search_index = load_index()
except (OSError, ValueError) as exc:
    st.error(f"無法載入角色檔案：{exc}")
    st.stop()

st.markdown('''<div class="hero"><div class="eyebrow">ACG / CHARACTER DISCOVERY</div>
<h1>你的理想型，<br>會是哪位角色？</h1>
<p>從性格、相處方式到讓你心動的小細節，把喜歡的特質寫下來，探索與你偏好接近的二次元角色。</p></div>''', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ✦ 理想型研究室")
    st.caption(f"角色檔案 · {len(characters)} 位")
    st.markdown("描述偏好 → 分析特質 → 探索角色")
    st.divider()
    ready = bool(get_api_key())
    if ready:
        st.success("AI 金鑰已設定")
    else:
        st.warning("設定 OPENAI_API_KEY 即可開始 AI 匹配。")
    st.caption("匹配需要本機 Ollama 與 bge-m3 模型。你的描述與候選角色特質會傳送至 OpenAI。")
    with st.expander("如何啟動服務"):
        st.code("ollama pull bge-m3\nollama serve", language="shell")
        st.caption("可在專案 .env 設定 OPENAI_API_KEY，修改後重新啟動應用。")

left, right = st.columns([1.35, 1], gap="large")
with left:
    st.subheader("描述讓你心動的特質")
    examples = {"自行描述":"", "冷靜但溫柔":"我喜歡外表冷靜、內心溫柔的人，會默默照顧朋友，偶爾害羞，有反差萌。", "可靠的夥伴":"我喜歡可靠、有正義感、有幽默感的夥伴，遇到困難會勇敢站出來。", "元氣與好奇心":"我喜歡開朗有活力、好奇心旺盛的人，有自己的熱愛，也願意一起嘗試新事物。"}
    choice = st.selectbox("從靈感開始", list(examples))
    with st.form("match_form"):
        description = st.text_area("你的理想型", value=examples[choice], height=155, max_chars=2000, placeholder="例如：有點毒舌，但總在關鍵時刻默默照顧別人……", key=f"description_{choice}")
        count = st.slider("想探索幾位角色？", 3, min(10, len(characters)), 5)
        submitted = st.form_submit_button("尋找我的理想型 →", type="primary", use_container_width=True)
with right:
    st.subheader("讓描述更有方向")
    st.markdown("**性格**　冷靜、開朗、溫柔、毒舌\n\n**相處方式**　默默照顧、一起冒險、互相吐槽\n\n**反差與細節**　看似強勢卻容易害羞、認真又愛甜食")
    st.caption("描述越具體，越容易找到有辨識度的特質。結果取決於現有角色檔案，適合用來探索偏好。")

if submitted:
    if not description.strip():
        st.warning("先寫下你喜歡的性格或相處方式。")
    elif not ready:
        st.error("請先設定 OPENAI_API_KEY，再重新啟動應用。")
    else:
        try:
            with st.status("正在探索你的理想型…", expanded=True) as status:
                st.write("分析偏好中的核心特質")
                traits = extract_traits(description.strip())
                st.write("比對角色檔案")
                scores = search_index.search(embed_text_ollama('; '.join(traits)), count)
                matches = [(idx, score, characters[idx]) for idx, score in scores]
                st.session_state.result = dict(description=description.strip(), traits=traits, matches=matches, report="")
                st.write("整理匹配解讀")
                try:
                    st.session_state.result['report'] = generate_final_report(description.strip(), traits, matches)
                except RuntimeError:
                    st.warning("匹配結果已保留。AI 解讀暫時無法產生，請稍後重試。")
                status.update(label="探索完成", state="complete", expanded=False)
        except (RuntimeError, ValueError) as exc:
            st.error(str(exc))

result = st.session_state.get('result')
st.divider()
if result:
    st.subheader("你的角色 shortlist")
    st.caption(f"本次偏好：{result['description']}")
    st.markdown(''.join(f'<span class="chip">{html.escape(t)}</span>' for t in result['traits']), unsafe_allow_html=True)
    st.caption("相對匹配分數：本次候選中最高為 100、最低為 0；全部同分時為 50。不是喜歡的機率，也不能跨次比較。")
    for offset in range(0, len(result['matches']), 3):
        columns = st.columns(3)
        for column, (rank, (_, score, character)) in zip(columns, enumerate(result['matches'][offset:offset+3], start=offset+1)):
            with column:
                tags = ''.join(f'<span class="chip">{html.escape(str(t))}</span>' for t in character.get('moe_traits', [])[:5])
                st.markdown(f'<div class="card"><div class="rank">MATCH / {rank:02d} · {score:.1f}</div><h3>{html.escape(character["name"])}</h3>{tags}</div>', unsafe_allow_html=True)
    if result['report']:
        st.subheader("為什麼是他們？")
        st.markdown(result['report'])
    payload = {**result, 'matches':[{'rank':i+1, 'score':score, 'character':char} for i, (_,score,char) in enumerate(result['matches'])]}
    st.download_button("下載這次探索結果", json.dumps(payload, ensure_ascii=False, indent=2), file_name="acg-matches.json", mime="application/json")
else:
    st.subheader("先認識幾位角色")
    st.caption("以下是角色檔案預覽，尚未進行個人化匹配。")
    for column, character in zip(st.columns(3), characters[:3]):
        with column:
            tags = ''.join(f'<span class="chip">{html.escape(str(t))}</span>' for t in character.get('moe_traits', [])[:5])
            st.markdown(f'<div class="card"><div class="rank">CHARACTER FILE</div><h3>{html.escape(character["name"])}</h3>{tags}</div>', unsafe_allow_html=True)
