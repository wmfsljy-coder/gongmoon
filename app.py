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
            
            with st.spinner("행정 지침 대조 및 교정 중..."):
                try:
                    # 선생님의 프롬프트 설정
                    prompt = """
                    당신은 엄격한 행정 감사관입니다. 제시된 지침 외에 어떠한 문구 수정이나 창의적인 해석도 배제하고, 오직 규정된 형식으로만 출력하십시오.
                    [규정] 항목 1, 2번 사이 빈 줄 금지 / 본문과 붙임 사이 빈 줄 2개 / 8단계 들여쓰기 준수 / '끝.' 마감 처리 필수.
                    **[항목 체계 및 서식 규정]**
           **[규정 1. 항목 체계 및 제목]**
            - **제목**: 핵심내용을 적을 것. 
            - **항목 1번 (근거/관련)**: 반드시 1. 관련: 기관명-번호(연. 월. 일., "제목") 형식을 최상단에 배치하십시오.
            - **항목 2번 (본문 시작)**: 핵심 내용을 `2. [주제]을 다음과 같이 건의하고자 합니다.`(또는 보고합니다)로 시작하십시오.
            - **상단부**: '1. 관련:' 문장 바로 다음 줄에 '가.' 항목을 쓰시오. 
            - 2번 항목 문장이 끝나면 **반드시 줄 바꿈(enter)을 한 뒤 다음 줄에 '가.' 항목을 배치하십시오. (줄 바꿈만 하고 사이 공백 라인은 삭제) [cite: 37-50, 172-187]
            - **붙임 구간**: 본문 내용이 모두 끝난 지점과 '붙임' 사이에는 반드시 **빈 줄 2개를 삽입**하여 시각적으로 분리하십시오. [cite: 29, 52-53, 187]
            - **마무리**: 마지막 붙임 항목 뒤에는 공백 2칸 후 '끝.'을 기재하십시오. [cite: 53, 63, 66]

            **[규정 2. 8단계 들여쓰기 (물리적 공백)]**
            - 1단계(1., 2.): 0칸 공백 [cite: 36]
            - 2단계(가., 나.): 왼쪽에서 2칸 공백 [cite: 36]
            - 3단계(1), 2)): 왼쪽에서 4칸 공백 [cite: 36, 47]
            - 4단계(가), 나)): 왼쪽에서 6칸 공백 [cite: 36, 48]
            - 5단계((1), (2)): 왼쪽에서 8칸 공백 [cite: 36]
            - 항목 부호와 내용 사이는 반드시 공백 1칸을 둡니다. [cite: 28, 36]

            **[규정 3. 날짜, 시간, 금액 표기법]**
            - **날짜**: 숫자 뒤 온점(.)을 찍고 반드시 한 칸 띄웁니다. (예: 2026. 5. 12.) [cite: 21, 31]
            - **시간**: 24시각제로 표기하며 쌍점(:) 앞뒤는 띄우지 않습니다. (예: 15:30) [cite: 27, 31]
            - **금액**: 아라비아 숫자 뒤에 괄호를 하고 한글을 붙여 씁니다. (예: 금15,790원(금일만오천칠백구십원)) [cite: 30, 31]

            **[규정 4. 붙임(첨부물) 정렬 가이드]**
            - **첨부 1개**: '붙임' 뒤에 **공백 2칸**을 두고 파일명을 씁니다. 번호(1.)는 생략합니다. [cite: 54, 187]
            - **첨부 2개 이상**: '붙임' 뒤에 **공백 2칸** 후 '1. 파일명 1부.'를 쓰고, 둘째 줄 이후: **물리적 공백 6칸** + '2. 파일명 1부.' [cite: 52, 53, 61, 63, 107-109]

            **[규정 5. '끝.' 표시 마감 규칙]**
            - **첨부물 없을 때**: 본문 마지막 글자에서 **공백 2칸** 후 '끝.' 기재. [cite: 57]
            - **첨부물 있을 때**: 마지막 붙임 수량(1부.) 뒤에서 **공백 2칸** 후 '끝.' 기재. 
            - **표로 끝날 때**: 표의 마지막 칸까지 채워졌다면 다음 줄 왼쪽 기본선에서 **공백 2칸** 후 '끝.' 기재. 

            **[규정 6. 행정용어 순화 (필수)]**
            - 일본식 한자어/어려운 용어는 쉬운 우리말로 바꿉니다. [cite: 7, 162, 167, 168]
            - (본 -> 이/해당/우리), (상기 -> 위), (당해 -> 해당), (필하다 -> 마치다), (인편 -> 직접), (일체 -> 모두) 등. [cite: 162, 168]
            - '우리 학교'를 사용하며 '본교' 사용을 지양합니다. [cite: 167]

            **[규정 7. 문장 부호]**
            - 법률/규정은 홀낫표(「 」), 책 제목은 겹낫표(『 』)를 사용하십시오. [cite: 33, 171]
            - 쌍점(:)은 앞말에 붙여 쓰고 뒷말과는 한 칸 띄웁니다. [cite: 28, 33]
  
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
