import streamlit as st
import google.generativeai as genai

# 1. 페이지 기본 설정
st.set_page_config(page_title="글로벌 비즈니스 메일 어시스턴트", page_icon="✉️", layout="wide")

st.title("✉️ 글로벌 비즈니스 메일 어시스턴트")
st.markdown("초안부터 답장까지, 핵심 내용만 입력하면 상황과 어조에 맞는 프로페셔널한 비즈니스 이메일을 다국어로 작성해 줍니다.")

# 2. 사이드바: API 키 입력란
with st.sidebar:
    st.header("설정")
    api_key = st.text_input("Gemini API 키를 입력하세요", type="password")
    st.markdown("---")
    st.markdown("ℹ️ 구글 AI Studio에서 발급받은 API 키가 필요합니다.")

# 3. 시스템 프롬프트
system_prompt = """
당신은 빠르고 정확하며 센스 있는 글로벌 '비즈니스 이메일 작성 어시스턴트'입니다.
사용자가 입력한 정보 바탕으로 즉시 발송 가능한 수준의 프로페셔널한 이메일을 작성합니다.

[작성 규칙]
1. 다국어 지원: 사용자가 지정한 언어로 작성하며, 해당 언어권의 비즈니스 매너에 맞게 자연스럽게 윤문합니다.
2. 유형 맞춤: 초안은 목적이 명확하게, 답장은 상대방의 요청에 적절히 응답하며 내용을 녹여냅니다.
3. 톤앤매너: 지정한 어조와 종류에 맞춰 문체와 분위기를 조정합니다.
4. 제목 제안: 목적을 파악할 수 있는 제목 2개를 제안합니다. (답장은 'RE:' 포함)
5. 가독성: 글머리 기호(*, -) 등을 활용하여 읽기 쉽게 구성합니다.
6. 마무리 규칙: 이메일의 마지막은 반드시 사용자가 입력한 '[내 이름] 드림'으로만 끝내십시오. 소속, 직급, 날짜, 시간 등 다른 대괄호 표시([ ]) 형태의 빈칸은 절대 생성하지 마십시오.

[출력 형식]
📌 제목 제안:
- [제안 1]
- [제안 2]

✉️ 이메일 본문:

(작성된 이메일 내용)
"""

# 4. 사용자 입력 폼 구성
col1, col2 = st.columns(2)

with col1:
    email_type = st.radio("작성 유형", ["초안", "답장"], horizontal=True)
    lang = st.selectbox("작성 언어", ["한국어", "영어", "일본어", "중국어"])
    sender_name = st.text_input("내 이름 (발신자)")
    recipient = st.text_input("받는 사람 (예: 협력사 김팀장님)")

with col2:
    tone = st.selectbox("메일 어조", ["정중하게", "친근하게", "간결하고 드라이하게"])
    category = st.selectbox("메일 종류", ["단순 정보 전달", "회신", "제안", "사과 및 양해"])

main_content = st.text_area("주요 내용 (키워드나 개요만 적어도 됩니다)", height=150)

received_email = ""
if email_type == "답장":
    received_email = st.text_area("받은 메일 내용 (여기에 붙여넣어 주세요)", height=150)

# 5. 메일 생성 로직
if st.button("🚀 메일 작성하기", type="primary"):
    if not api_key:
        st.error("좌측 사이드바에 Gemini API 키를 입력해 주세요!")
    elif not sender_name or not recipient or not main_content:
        st.warning("내 이름, 받는 사람, 주요 내용을 모두 입력해 주세요.")
    else:
        try:
            # API 키 설정 및 최신 모델(2.5-flash) 적용
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash", 
                system_instruction=system_prompt
            )
            
            # 사용자 입력을 프롬프트로 구성 (내 이름 포함)
            user_prompt = f"""
            * 작성 유형: {email_type}
            * 작성 언어: {lang}
            * 내 이름: {sender_name}
            * 받는 사람: {recipient}
            * 메일 어조: {tone}
            * 메일 종류: {category}
            * 주요 내용: {main_content}
            """
            
            if email_type == "답장":
                user_prompt += f"\n* 받은 메일:\n{received_email}"

            with st.spinner("AI가 메일을 작성하고 있습니다... ✍️"):
                response = model.generate_content(user_prompt)
                
            st.success("메일 작성이 완료되었습니다!")
            
            # 결과 출력
            st.markdown("### ✨ 완성된 메일")
            st.info(response.text)
            
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")