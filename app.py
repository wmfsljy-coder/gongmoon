import streamlit as st
import google.generativeai as genai
from streamlit_paste_button import paste_image_button 
import re  

# =========================================================
# 1. 보안 설정 및 API 키 초기화
# =========================================================
st.set_page_config(page_title="공문서 교정기", layout="wide")

try:
    GENAI_API_KEY = st.secrets["GENAI_API_KEY"]
    genai.configure(api_key=GENAI_API_KEY)
except Exception as e:
    st.error("금고(Secrets)에 API 키가 설정되지 않았습니다.")

# =========================================================
# 2. 웹 페이지 UI 설정
# =========================================================
st.title("📄 공문서 교정기")
st.caption("선생님의 업무 경감을 위한 프로그램입니다. 수정사항은 wmfsljy@gmail.com 으로 교정 화면을 캡쳐해서 보내주세요")

col1, col2 = st.columns(2)

# --- [왼쪽: 입력부] ---
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

# --- [오른쪽: 출력부 및 핵심 로직] ---
with col2:
    st.subheader("✅ 전문가 교정 결과")
    
    if st.button("전문가 정밀 검토 시작", type="primary", use_container_width=True):
        if user_content:
            placeholder = st.empty()
            full_text = "" 
            
            with st.spinner("최적의 엔진을 찾아 교정을 시작합니다..."):
                
                # 선생님의 초정밀 행정 지침 프롬프트
                prompt = """
당신은 엄격하고 센스 있는 행정 감사관입니다. 원본 문서의 문맥을 완벽히 파악하여, 오직 규정된 형식으로만 출력하십시오.

**[출력 형식 (매우 중요)]**
결과물을 반드시 아래의 세 가지 구분자로 감싸서 출력하십시오. 다른 안내 멘트는 절대 금지.
[제목시작]
(교정된 제목 1줄)
[제목끝]
[본문시작]
(교정에 맞춘 본문 전체 내용)
[본문끝]
[이유시작]
(무엇을 어떤 규정에 따라 수정했는지 간결하게 개조식으로 작성)
[이유끝]

**[규정 1. 문맥 파악 및 도입부 작성 (가장 중요)]**
1. **단일 목적 통합**: 원본 문서의 목적(지출 건의, 결과 보고 등)을 종합하여 도입부 문장을 **단 하나**로 깔끔하게 작성하십시오. 
   - (절대 금지) 1. ~지출을 건의합니다. 2. ~내역을 보고합니다. (이렇게 문장을 억지로 두 개로 쪼개지 마십시오.)
   - (올바른 예) 1. 2026학년도 교육실습 협의회비(2차)를 다음과 같이 지출하고자 합니다.
2. **'관련' 항목 유연성**
   - 원본 문서에 '관련(근거)' 내용이 없다면 출력 예시와 같은 '1. 관련: 웅천고등학교-0000(2026. 5. 13., "관련문서 제목")'의 유형을 만들고, 본문 주제를 '2.'로 시작하십시오. (이 경우 세부 내역은 '가., 나., 다.'로 이어집니다.)
   - **(주의) 관련 문서가 2개 이상일 경우**: 한 줄에 길게 이어서 쓰지 말고, **반드시 줄 바꿈(\n)**을 하여 각각 새로운 줄에 기재하십시오. (예: 1. 관련: 가. 문서1 \n 나. 문서2)
   - 관련(근거) 문서는 반드시 `기관명-번호(연. 월. 일., "문서 제목")` 형태를 지켜야 합니다. 원본에 제목이 누락되었더라도 문맥을 파악해 반드시 큰따옴표(" ") 안에 적절한 제목을 기재하십시오.
   [작성 예시 - 2개 이상일 때]
     1. 관련:
       가. 웅천고등학교-1541(2023. 2. 21., "장학금 지급 계획")
       나. 웅천고등학교-1934(2024. 2. 28., "장학생 선정 결과")
3. **상황 인지**: 첨부물에 '결과 보고서'가 있다면 이미 협의가 완료된 사안이므로, 문맥에 맞게 지출 '건의'나 '보고'로 자연스럽게 마감하십시오.

**[규정 2. 항목 체계 및 강제 줄 바꿈 규정]**
1. **항목 1번과 2번 사이 (존재할 경우)**: 빈 줄(Enter 2번)을 절대 두지 마십시오.
2. **항목별 단독 줄 원칙**: '가.', '나.', '다.' 등 모든 하위 항목은 반드시 새로운 줄에서 시작하십시오. (한 줄에 이어서 쓰는 것 엄격히 금지). 모든 항목 부호 앞에는 줄 바꿈(\n) 필수.
3. **붙임 수직 정렬**: 붙임이 2개 이상일 경우, 1번과 2번 파일명은 반드시 서로 다른 줄에 기재. 2번 이후 항목은 1번 항목의 첫 글자 위치에 수직 정렬 (앞에 공백 6칸).

**[규정 3. 8단계 들여쓰기 (물리적 공백)]**
- 1단계(1., 2.): 0칸 공백
- 2단계(가., 나.): 왼쪽에서 2칸 공백
- 3단계(1), 2)): 왼쪽에서 4칸 공백
- 본문 끝과 '붙임' 사이만 빈 줄 1개를 둡니다.

**[규정 4. 날짜, 시간, 금액 표기법]**
- 날짜: 숫자 뒤 온점(.)을 찍고 한 칸 띄웁니다. (예: 2026. 5. 14.)
- 시간: 24시각제로 표기 (예: 11:30~13:30)
- 금액: 숫자 뒤에 괄호를 하고 한글을 붙여 씁니다. (예: 금120,000원(금십이만원))

**[규정 5. 붙임 정렬 가이드]**
- **첨부 1개일 때**: '붙임' 글자 뒤 스페이스바 2번 후 파일명을 바로 기재. **(절대 금지: 파일이 1개뿐일 때는 '1.' 이라는 번호를 절대 쓰지 마십시오.)**
- 첨부 2개 이상: 둘째 줄 부터의 번호 시작위치는 첫째 줄 1. 의 시작위치와 동일해야 한다.
  [첫째 줄] '붙임' + 스페이스바 2번 + '1. 파일명 1부.'
  [둘째 줄] 스페이스바 6번 + '2. 파일명 1부.'

**[규정 6. 행정용어 순화 및 마감]**
- 일본식 한자어 순화 (본 -> 이/해당/우리, 필하다 -> 마치다, 일체 -> 모두 등)
- 마지막 글자 뒤 2칸 띄우고 '끝.' 기재.

---
**[출력 예시]**
[제목시작]
2026학년도 교육실습 협의회비(2차) 지출 건의
[제목끝]
[본문시작]
1. 관련: 웅천고등학교-0000(2026. 5. 13.) "관련문서 제목"
2. 2026학년도 교육실습 협의회비(2차) 지출을 다음과 같이 건의합니다.
  가. 일시: 2026. 5. 14. 11:30~13:30
  나. 장소: 관내 식당

붙임  1. 협의 결과 보고서 1부.
      2. 지출 증빙 서류 1부.  끝.
[본문끝]
[이유시작]
- 항목 간의 줄 바꿈 및 들여쓰기 규정을 적용하였습니다.
- 붙임 파일의 수직 정렬 규정을 적용하였습니다.
[이유끝]
"""
                # 순차적 적용을 위한 모델 리스트
                model_list = ['gemini-3.1-flash-lite', 'gemini-2.5-flash-lite', 'gemini-2.0-flash-lite']
                success = False
                
                content_list = [prompt, user_content] if not isinstance(user_content, str) else [prompt + "\n\n" + user_content]

                # 모델 순차 시도 (Fallback 로직)
                for model_name in model_list:
                    try:
                        current_model = genai.GenerativeModel(
                            model_name=model_name,
                            generation_config={"temperature": 0.0, "max_output_tokens": 8192}
                        )
                        
                        response = current_model.generate_content(content_list, stream=True)
                        
                        # 1단계: 실시간 스트리밍 (원시 텍스트 출력)
                        for chunk in response:
                            if chunk.text:
                                full_text += chunk.text
                                placeholder.text(full_text)
                        
                        success = True
                        break # 성공 시 루프 탈출
                        
                    except Exception as e:
                        # 에러 발생 시 다음 모델로 전환
                        st.warning(f"⚠️ {model_name} 엔진 혼잡. 다음 엔진으로 전환합니다...")
                        full_text = "" # 텍스트가 섞이지 않도록 초기화
                        continue 

                # 2단계: 모든 처리가 끝난 후 화면 가공 및 출력
                if success:
                    placeholder.empty()
                    
                    title_match = re.search(r'\[제목시작\](.*?)\[제목끝\]', full_text, re.DOTALL)
                    body_match = re.search(r'\[본문시작\](.*?)\[본문끝\]', full_text, re.DOTALL)
                    reason_match = re.search(r'\[이유시작\](.*?)\[이유끝\]', full_text, re.DOTALL)
                    
                    title_text = title_match.group(1).strip() if title_match else "제목을 추출하지 못했습니다."
                    body_text = body_match.group(1).strip() if body_match else full_text
                    reason_text = reason_match.group(1).strip() if reason_match else "수정 이유를 생성하지 못했습니다."
                    
                    # 최종 출력 (복사 버튼 포함)
                    if title_match and body_match:
                        st.markdown("### 📌 교정된 제목")
                        st.code(title_text, language="text")
                        
                        st.markdown("### 📝 교정된 본문")
                        st.code(body_text, language="text")
                        
                        st.markdown("### 💡 주요 수정 내역 및 사유")
                        st.info(reason_text)
                    else:
                        st.warning("규격대로 추출되지 않았습니다. 원문을 표시합니다.")
                        st.text(full_text)
                        
                else:
                    st.error("❌ 모든 예비 엔진이 현재 혼잡합니다. 잠시 후 다시 시도해 주세요.")
        else:
            st.warning("검토할 내용을 입력하거나 이미지를 붙여넣어 주세요.")
