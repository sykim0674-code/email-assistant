import streamlit as st
import google.generativeai as genai
import time

# 1. 페이지 기본 설정 (전체 화면 사용)
st.set_page_config(page_title="Mail Assistant", page_icon="✉️", layout="wide", initial_sidebar_state="expanded")

# ==============================================================================
# 🎨 커스텀 CSS 주입
# ==============================================================================
custom_css = """
<style>
/* 폰트 불러오기 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Noto+Sans+KR:wght@400;500;700&display=swap');

/* 라이트 모드 (기본) 색상 변수 */
:root {
    --bg-color: #ffffff;
    --text-color: #111111;
    --text-muted: #666666;
    --input-bg: #f5f5f5;
    --border-color: #e0e0e0;
    --radius: 8px;
    --font-family: 'Inter', 'Noto Sans KR', sans-serif;
}

/* 다크 모드 색상 변수 */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-color: #121212;
        --text-color: #ffffff;
        --text-muted: #a0a0a0;
        --input-bg: #222222;
        --border-color: #333333;
    }
}

/* 전체 폰트 및 배경 적용 */
html, body, [class*="st-"] {
    font-family: var(--font-family) !important;
    color: var(--text-color);
}
.stApp { background-color: var(--bg-color); }

/* 상단 헤더 및 불필요한 기본 UI 숨기기 */
[data-testid="stAppViewBlockContainer"] > div:first-child,
header[data-testid="stHeader"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
#MainMenu, footer, .stDeployButton { 
    display: none !important; 
}

/* 좌측 패널 (Sidebar) 고정 및 스타일링 */
[data-testid="stSidebar"] {
    background-color: var(--bg-color);
    border-right: 0.5px solid var(--border-color);
    min-width: 400px !important;
    max-width: 400px !important;
}
[data-testid="stSidebarNav"] { display: none; }

/* 입력창(Input, TextArea, Selectbox) 플랫 디자인 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background-color: var(--input-bg) !important;
    border: 0.5px solid var(--border-color) !important;
    border-radius: var(--radius) !important;
    box-shadow: none !important;
    color: var(--text-color) !important;
    font-size: 14px !important;
}

/* 포커스 시 테두리 진하게 */
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > div:focus {
    border-color: var(--text-color) !important;
}

/* 메일 작성하기 메인 버튼 (강제 검정 배경 + 흰 글씨) */
.stButton > button[kind="primary"] {
    background-color: #000000 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: var(--radius) !important;
    width: 100% !important;
    height: 48px;
    font-weight: 600;
    box-shadow: none !important;
    margin-top: 10px;
}

/* 라디오 버튼(토글 형태) 스타일링 */
div[role="radiogroup"] {
    gap: 0px;
    background: var(--input-bg);
    padding: 4px;
    border-radius: var(--radius);
    border: 0.5px solid var(--border-color);
}
div[role="radiogroup"] label {
    padding: 6px 12px;
    border-radius: 6px;
    margin: 0;
}

/* 상태 뱃지 잘림 방지 추가 */
.status-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 16px;
    font-size: 13px;
    font-weight: 600;
    background-color: var(--input-bg);
    border: 0.5px solid var(--border-color);
    color: var(--text-color);
    white-space: nowrap;
    width: fit-content;
    margin-bottom: 16px;
}

/* 스켈레톤 로딩 애니메이션 */
@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}
.skeleton {
    animation: shimmer 2s infinite linear;
    background: linear-gradient(to right, var(--input-bg) 4%, var(--border-color) 25%, var(--input-bg) 36%);
    background-size: 1000px 100%;
    border-radius: var(--radius);
    margin-bottom: 16px;
}
.sk-title { height: 40px; width: 60%; margin-top: 20px;}
.sk-meta { height: 48px; width: 100%; margin-bottom: 40px; }
.sk-line { height: 20px; width: 100%; margin-bottom: 12px; }
.sk-line-short { height: 20px; width: 80%; margin-bottom: 12px; }

/* 메인 영역 여백 조정 */
.block-container {
    padding-top: 2rem !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    max-width: 1200px !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
# ==============================================================================

# 2. 세션 상태 초기화 (이모지 제거)
if "status" not in st.session_state:
    st.session_state.status = "Waiting"
if "result_subject" not in st.session_state:
    st.session_state.result_subject = ""
if "result_body" not in st.session_state:
    st.session_state.result_body = ""

# 3. 좌측 패널 (Sidebar)
with st.sidebar:
    st.markdown("<h2 style='margin-top:0;'>✉️ Mail Assistant</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: var(--text-muted); font-size: 13px; margin-bottom: 24px;'>초안부터 답장까지, 핵심 내용만 입력하면 상황에 맞는 메일을 작성해 줍니다.</p>", unsafe_allow_html=True)
    
    email_type = st.radio("Type", ["Draft", "Reply"], horizontal=True)
    lang = st.selectbox("Language", ["한국어", "English", "日本語", "中文"])
    tone = st.selectbox("Tone", ["정중하게", "공식적으로", "친근하게", "간결하게", "설득력 있게"])
    category = st.selectbox("Category", ["단순 정보 전달", "미팅 요청", "제안/영업", "사과/해명", "감사 표현", "일정 조율", "보고/공유"])
    
    sender_name = st.text_input("Sender")
    recipient = st.text_input("Recipient", placeholder="협력사 김팀장님")
    main_content = st.text_area("Key points", placeholder="Keywords or Brief outline", height=100)
    
    received_email = ""
    # "Reply" 선택 시에만 이전 메일 입력창 표시
    if email_type == "Reply":
        received_email = st.text_area("Previous email", placeholder="Paste the previous email here", height=100)
    
    # Generate 버튼
    submit_btn = st.button("🚀 Generate", type="primary", use_container_width=True)

# 4. 우측 패널 (상단 툴바 버튼 제거, 뱃지만 표시)
st.markdown(f"<div class='status-badge'>{st.session_state.status}</div>", unsafe_allow_html=True)

# 5. 메일 생성 로직
if submit_btn:
    if not sender_name or not recipient or not main_content:
        st.sidebar.warning("Sender, Recipient, Key points 항목을 모두 입력해 주세요.")
    else:
        st.session_state.status = "Generating"
        st.rerun() 

elif st.session_state.status == "Generating":
    placeholder = st.empty()
    placeholder.markdown("""
        <div class="skeleton sk-title"></div>
        <div class="skeleton sk-meta"></div>
        <div class="skeleton sk-line"></div>
        <div class="skeleton sk-line"></div>
        <div class="skeleton sk-line-short"></div>
        <div style="margin-top:20px;" class="skeleton sk-line"></div>
        <div class="skeleton sk-line-short"></div>
    """, unsafe_allow_html=True)
    
    time.sleep(1.2)
    
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        system_prompt = """
        당신은 글로벌 비즈니스 이메일 전문 AI 어시스턴트입니다.
        주어진 정보를 바탕으로 해당 언어권의 비즈니스 매너에 맞는 완벽한 이메일을 작성하세요.
        메일 종류(제안, 사과, 미팅 등)에 따라 본문의 템플릿과 구조를 다르게 적용하세요.
        
        [출력 형식]
        제목: [직관적이고 명확한 메일 제목]
        ---
        [이메일 본문]
        - 마지막은 반드시 '[내 이름] 드림' 또는 해당 언어권에 맞는 맺음말로 끝내세요.
        - [ ] 형태의 빈칸은 절대 만들지 마세요.
        """
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_prompt)
        
        user_prompt = f"""
        * 작성 유형: {email_type}
        * 작성 언어: {lang}
        * 메일 어조: {tone}
        * 메일 종류: {category}
        * 내 이름: {sender_name}
        * 받는 사람: {recipient}
        * 주요 내용: {main_content}
        * 이전 메일 내용: {received_email}
        """
        
        response = model.generate_content(user_prompt)
        text = response.text
        
        subject, body = "", text
        if "제목:" in text and "---" in text:
            parts = text.split("---")
            subject = parts[0].replace("제목:", "").strip()
            body = parts[1].strip()
        elif "제목:" in text:
            lines = text.split("\n")
            subject = lines[0].replace("제목:", "").strip()
            body = "\n".join(lines[1:]).strip()

        st.session_state.result_subject = subject
        st.session_state.result_body = body
        st.session_state.status = "Complete"
        
        placeholder.empty() 
        st.rerun()

    except Exception as e:
        placeholder.empty()
        st.error(f"오류가 발생했습니다: {e}")
        st.session_state.status = "Waiting"

# 6. 기본 상태 및 완료 상태 화면 출력
if st.session_state.status == "Waiting":
    st.markdown("""
        <div style='display:flex; flex-direction:column; align-items:center; justify-content:center; height: 60vh; color: var(--border-color);'>
            <h1 style='font-size: 48px; margin-bottom: 16px;'>✉️</h1>
            <h3 style='color: var(--text-muted); font-weight: 500;'>Please fill out the form on the left to generate an email</h3>
        </div>
    """, unsafe_allow_html=True)

elif st.session_state.status == "Complete":
    st.markdown(f"<h1 style='font-size: 32px; font-weight: 700; margin-top: 16px; margin-bottom: 24px;'>{st.session_state.result_subject}</h1>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; background: var(--input-bg); padding: 16px; border-radius: 8px; border: 0.5px solid var(--border-color); margin-bottom: 32px; font-size: 14px;'>
            <div><span style='color: var(--text-muted); font-size: 12px; display: block;'>보내는 이</span><b>{sender_name}</b></div>
            <div><span style='color: var(--text-muted); font-size: 12px; display: block;'>받는 이</span><b>{recipient}</b></div>
            <div><span style='color: var(--text-muted); font-size: 12px; display: block;'>어조 및 언어</span><b>{tone} · {lang}</b></div>
            <div><span style='color: var(--text-muted); font-size: 12px; display: block;'>분류</span><b>{category}</b></div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style='white-space: pre-wrap; line-height: 1.8; font-size: 16px; color: var(--text-color);'>
{st.session_state.result_body}
        </div>
    """, unsafe_allow_html=True)