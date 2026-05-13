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

# 모델 설정 (Gemini 1.5 Flash)
model = genai.GenerativeModel(model_name='gemini-1.5-flash')

# 웹 페이지 설정
st.set_page_config(page_title="공문서 교정기", layout="wide")

st.title("📄 공문서 교정기")
st.caption("선생님의 업무 경감을 위한 프로그램입니다.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 검토할 내용")
    input_type = st.radio("입력 방식 선택", ["글자로 입력", "이미지 붙여넣기"])
    user_content = st.text_area("내용 입력", height=500, placeholder="공문 내용을 여기에 붙여넣으세요.") if input_type == "글자로 입력" else None
    if input_type == "이미지 붙여넣기":
        paste_result = paste_image_button(label="📋 공문 캡처 후 클릭하여 붙여넣기")
        if paste_result and paste_result.image_data is not None:
            user_content = paste_result.image_data
            st.image(user_content, caption="붙여넣은 이미지", use_container_width=True)

with col2:
    st.subheader("✅ 전문가 교정 결과")
    if st.button("전문가 정밀 검토 시작", type="primary", use_container_width=True):
        if user_content:
            prompt = """
            당신은 대한민국 행정 전문가입니다. 아래 지침에 따라 공문을 정교하게 교정하십시오. 
            [중요 지침] 답변 내용에와 같은 출처 표시를 절대로 포함하지 마십시오. 
            오직 최종 교정된 공문서 내용만 출력하십시오.
            ---
            **[항목 체계 및 서식 규정]**
           **[규정 1. 항목 체계 및 제목]**
            - **제목**: 핵심내용을 적을 것. 
            - **항목 1번 (근거/관련)**: 반드시 1. 관련: 기관명-번호(연. 월. 일., "제목") 형식을 최상단에 배치하십시오.
            - **항목 2번 (본문 시작)**: 핵심 내용을 `2. [주제]을 다음과 같이 건의하고자 합니다.`(또는 보고합니다)로 시작하십시오. [cite: 72, 88]

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

            ---
            **[답변 출력 형식]**
            [교정된 제목]
            ```text
            (제목 기재)
            ```
            [교정된 본문]
            ```text
            (위 규정이 적용된 본문 전체)
            ```
            [수정 이유]
            (간결한 설명)
            """
            with st.spinner("전문가 정밀 교정 중..."):
                try:
                    response = model.generate_content([prompt, user_content] if not isinstance(user_content, str) else prompt + "\n\n" + user_content)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"실행 오류: {e}")
