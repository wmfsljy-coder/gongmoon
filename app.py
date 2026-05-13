import streamlit as st
import google.generativeai as genai
from PIL import Image
# 에러의 원인: 아래 줄이 반드시 있어야 이미지 붙여넣기 기능이 작동합니다!
from streamlit_paste_button import paste_image_button 

# =========================================================
# 1. 보안 금고(Secrets)에서 API 키 안전하게 가져오기
# =========================================================
try:
    GENAI_API_KEY = st.secrets["GENAI_API_KEY"]
    genai.configure(api_key=GENAI_API_KEY)
except Exception as e:
    st.error("금고(Secrets) 설정을 확인해주세요.")

# 모델 설정 (Gemini 3.1 Flash-lite)
model = genai.GenerativeModel(
    model_name='gemini-3.1-flash-lite',
    generation_config={
        "temperature": 0.0,  # 0에 가까울수록 매번 동일한 결과를 출력합니다.
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }
)

# 웹 페이지 설정
st.set_page_config(page_title="공문서 교정기", layout="wide")

st.title("📄 공문서 교정기")
st.caption("선생님의 업무 경감을 위한 프로그램입니다.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 검토할 내용")
    input_type = st.radio("입력 방식 선택", ["글자로 입력", "이미지 붙여넣기"])
    
    # 입력 방식에 따른 데이터 처리
    if input_type == "글자로 입력":
        user_content = st.text_area("내용 입력", height=500, placeholder="공문 내용을 여기에 붙여넣으세요.")
    else:
        paste_result = paste_image_button(label="📋 공문 캡처 후 클릭하여 붙여넣기")
        if paste_result and paste_result.image_data is not None:
            user_content = paste_result.image_data
            st.image(user_content, caption="붙여넣은 이미지", use_container_width=True)
        else:
            user_content = None
with col2:
    st.subheader("✅ 전문가 교정 결과")
    
    # 버튼 클릭 시 실행
    if st.button("전문가 정밀 검토 시작", type="primary", use_container_width=True):
        if user_content:
            # 1. 텍스트를 실시간으로 채워넣을 변수와 공간 미리 확보 (에러 방지)
            placeholder = st.empty()
            full_text = "" 
            
            with st.spinner("웅천고 행정 지침 대조 및 교정 중..."):
                try:
                    # 선생님의 프롬프트 설정
                    prompt = """
                    당신은 엄격한 행정 감사관입니다. 제시된 지침 외에 어떠한 문구 수정이나 창의적인 해석도 배제하고, 오직 규정된 형식으로만 출력하십시오.
                    [규정] 항목 1, 2번 사이 빈 줄 금지 / 본문과 붙임 사이 빈 줄 2개 / 8단계 들여쓰기 준수 / '끝.' 마감 처리 필수.
                    """
                    
                    # 2. 이미지와 텍스트 입력을 모두 처리
                    content_list = [prompt, user_content] if not isinstance(user_content, str) else [prompt + "\n\n" + user_content]
                    
                    # 3. 실시간 스트리밍 호출
                    response = model.generate_content(content_list, stream=True)
                    
                    # 4. 글자가 생성되는 대로 화면에 즉시 출력
                    for chunk in response:
                        if chunk.text:
                            full_text += chunk.text
                            placeholder.markdown(full_text)
                            
                except Exception as e:
                    st.error(f"⚠️ 실행 중 오류가 발생했습니다: {e}")
                    if "429" in str(e):
                        st.warning("현재 구글 서버의 요청 한도를 초과했습니다. 1분 뒤에 다시 시도해 주세요.")
        else:
            st.warning("검토할 내용을 입력하거나 이미지를 붙여넣어 주세요.")

# --- 코드 끝 ---
