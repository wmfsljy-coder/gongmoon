import streamlit as st
import google.generativeai as genai
from streamlit_paste_button import paste_image_button 

# =========================================================
# 1. 보안 설정 및 모델 초기화 (일관성 및 속도 최적화)
# =========================================================
try:
    GENAI_API_KEY = st.secrets["GENAI_API_KEY"]
    genai.configure(api_key=GENAI_API_KEY)
except Exception as e:
    st.error("금고(Secrets)에 API 키가 설정되지 않았습니다.")

# 핵심 포인트 1: 일관성(Consistency) 확보
# temperature를 0.0으로 설정하여 매번 동일한 결과를 출력하도록 통제합니다.
model = genai.GenerativeModel(
    model_name='gemini-3.1-flash-lite',
    generation_config={
        "temperature": 0.0,  
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }
)

# =========================================================
# 2. 웹 페이지 UI 설정
# =========================================================
st.set_page_config(page_title="공문서 교정기", layout="wide")

st.title("📄 공문서 교정기")
st.caption("선생님의 업무 경감을 위한 프로그램입니다.")

# =========================================================
# 3. 메인 로직 (입력부와 출력부 분리)
# =========================================================
col1, col2 = st.columns(2)

# --- [왼쪽 열: 입력부] ---
with col1:
    st.subheader("📥 검토할 내용")
    input_type = st.radio("입력 방식 선택", ["글자로 입력", "이미지 붙여넣기"])
    
    if input_type == "글자로 입력":
        user_content = st.text_area("내용 입력", height=500, placeholder="공문 내용을 여기에 붙여넣으세요.")
    else:
        paste_result = paste_image_button(label="📋 공문 캡처 후 클릭하여 붙여넣기")
        if paste_result and paste_result.image_data is not None:
            user_content = paste_result.image_data
            st.image(user_content, caption="붙여넣은 이미지", use_container_width=True)
        else:
            user_content = None

# --- [오른쪽 열: 출력부] ---
with col2:
    st.subheader("✅ 전문가 교정 결과")
    
    if st.button("전문가 정밀 검토 시작", type="primary", use_container_width=True):
        if user_content:
            placeholder = st.empty()
            full_text = "" 
            
            with st.spinner("행정 지침 대조 및 교정 중..."):
                try:
                    # 핵심 포인트 2: 프롬프트 간결화 (들여쓰기를 왼쪽으로 밀착하여 AI 인식률 향상)
                    prompt = """
당신은 엄격한 행정 감사관입니다. 제시된 지침 외에 어떠한 문구 수정이나 창의적인 해석도 배제하고, 오직 규정된 형식으로만 출력하십시오.
결과물에나 [ ] 기호는 절대로 출력하지 마십시오.

**[항목 체계 및 강제 줄 바꿈 규정]**
1. **항목 1번과 2번 사이**: 줄 바꿈은 하되, 사이에 빈 줄(Enter 2번)을 절대 두지 마십시오. (1번 바로 다음 줄에 2번이 와야 합니다.)
2. **항목별 단독 줄 원칙 (가장 중요)**: 본문 시작은 반드시 "2. 주제를 다음과 같이~" 형태로 숫자 2를 포함하여 기재하십시오. '가.', '나.', '다.' 등 모든 하위 항목은 반드시 새로운 줄에서 시작하십시오.
3. **붙임(첨부물) 수직 정렬**: 붙임이 2개 이상일 경우, 1번과 2번 파일명은 반드시 서로 다른 줄에 기재하십시오. 2번 이후의 항목은 1번 항목의 첫 글자 위치에 수직으로 맞추십시오 (앞에 공백 6칸).
4. **기호 제거**: 2번 항목의 주제어에 대괄호 [ ]를 절대 사용하지 마십시오.
5. **들여쓰기 및 마감**: 2단계(가.): 2칸 공백 / 3단계(1)): 4칸 공백. 본문 끝과 '붙임' 사이만 빈 줄 2개를 둡니다. 마지막 글자 뒤 2칸 띄우고 '끝.' 기재.

**[규정 2. 8단계 들여쓰기 (물리적 공백)]**
- 1단계(1., 2.): 0칸 공백
- 2단계(가., 나.): 왼쪽에서 2칸 공백
- 3단계(1), 2)): 왼쪽에서 4칸 공백
- 4단계(가), 나)): 왼쪽에서 6칸 공백
- 항목 부호와 내용 사이는 반드시 공백 1칸을 둡니다.

**[규정 3. 날짜, 시간, 금액 표기법]**
- 날짜: 숫자 뒤 온점(.)을 찍고 반드시 한 칸 띄웁니다. (예: 2026. 5. 12.)
- 시간: 24시각제로 표기하며 쌍점(:) 앞뒤는 띄우지 않습니다. (예: 15:30)
- 금액: 아라비아 숫자 뒤에 괄호를 하고 한글을 붙여 씁니다. (예: 금15,790원(금일만오천칠백구십원))

**[규정 4. 붙임(첨부물) 정렬 가이드]**
- 첨부 1개: '붙임' 뒤에 공백 2칸을 두고 파일명을 씁니다. 번호(1.)는 생략합니다.
- 첨부 2개 이상: '붙임' 뒤에 공백 2칸 후 '1. 파일명 1부.'를 쓰고, 둘째 줄 이후: 물리적 공백 6칸 + '2. 파일명 1부.'

**[규정 5. '끝.' 표시 마감 규칙]**
- 첨부물 없을 때: 본문 마지막 글자에서 공백 2칸 후 '끝.' 기재.
- 첨부물 있을 때: 마지막 붙임 수량(1부.) 뒤에서 공백 2칸 후 '끝.' 기재. 
- 표로 끝날 때: 표의 마지막 칸까지 채워졌다면 다음 줄 왼쪽 기본선에서 공백 2칸 후 '끝.' 기재. 

**[규정 6. 행정용어 순화 및 문장 부호]**
- 일본식 한자어/어려운 용어는 쉬운 우리말로 바꿉니다. (본 -> 이/해당/우리, 상기 -> 위, 당해 -> 해당, 필하다 -> 마치다, 인편 -> 직접, 일체 -> 모두)
- 법률/규정은 홀낫표(「 」), 책 제목은 겹낫표(『 』)를 사용하십시오.
- 쌍점(:)은 앞말에 붙여 쓰고 뒷말과는 한 칸 띄웁니다.

---
**[출력 예시 - 이 형식을 그대로 따르십시오]**
1. 관련: 우리 학교-123(2026. 5. 13.)
2. 교원 연수비 지원을 다음과 같이 보고합니다.
  가. 지원 내역: 진로결정코칭 연수
  나. 지원 금액: 금3,150,000원(금삼백일십오만원)

붙임  1. 세부 내역 1부.
      2. 증빙 서류 1부.  끝.
"""
                    # 핵심 포인트 3: 스트리밍을 통한 빠른 체감 속도 제공
                    content_list = [prompt, user_content] if not isinstance(user_content, str) else [prompt + "\n\n" + user_content]
                    
                    response = model.generate_content(content_list, stream=True)
                    
                    for chunk in response:
                        if chunk.text:
                            full_text += chunk.text
                            placeholder.text(full_text)
                            
                except Exception as e:
                    st.error(f"⚠️ 실행 중 오류가 발생했습니다: {e}")
                    if "429" in str(e):
                        st.warning("현재 서버 요청 한도를 초과했습니다. 1분 뒤에 다시 시도해 주세요.")
        else:
            st.warning("검토할 내용을 입력하거나 이미지를 붙여넣어 주세요.")
