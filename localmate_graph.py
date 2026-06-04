from typing import Literal
from pydantic import BaseModel, Field
from categories import CATEGORY_REGISTRY, CategoryHandlerSpec, admin, medical, traffic
from categories.shared import get_llm
from categories.types import CategoryResult

DEFAULT_QUESTION = "외국인등록증을 잃어버렸어요. 어떻게 해야 하나요?"
TOP_LEVEL_CLARIFICATION_QUESTION = (
    "행정, 의료, 교통 중 어떤 도움이 필요한지 조금 더 알려주세요."
)


# 1. RouterSchema (Literal 적용으로 출력값 제한)
class RouterSchema(BaseModel):
    category: Literal["행정", "의료", "교통", "미분류"] = Field(
        description="사용자 질문의 핵심 의도에 맞는 단 하나의 카테고리 선택"
    )
    reason: str = Field(description="이 카테고리로 분류한 명확한 의도 중심의 근거")


# 2. 의도 분류 프롬프트 템플릿
ROUTER_PROMPT_TEMPLATE = """당신은 한국 거주 외국인 지원 서비스(LocalMate)의 핵심 Intent Classifier(의도 분류기)입니다.
사용자 질문의 겉으로 드러난 단어에 절대 낚이지 말고, 문장 전체의 맥락을 분석하여 사용자의 '최종 목적'에 맞는 카테고리로 분류하세요.

[카테고리 분류 가이드라인]
- 행정: 비자, 체류자격, 외국인등록증, 출입국, 정부 민원 및 주택 임대차 계약(계약서, 보증금, 전입신고 등)과 관련된 '행정 절차 및 서류' 관련 질의
- 의료: 병원 이용, 질병/통증/증상, 약국 처방, 야간 응급 상황 등 '신체적 건강 및 의료 서비스 자체'가 목적인 질의
- 교통: 버스/지하철/택시 이용, 실시간 위치, 막차 시간, 길찾기 등 '장소 간 이동 수단 및 이동 방법'에 관한 질의
- 미분류: 위의 세 카테고리에 전혀 해당하지 않는 엉뚱한 질문이거나 해석이 불가능한 경우

[필수 판단 원칙]
1. [Keyword Matching 절대 금지]: 절대로 특정 단어 하나만 보고 분류하지 마세요. 문장 전체의 의미와 사용자의 최종 목적을 분석해야 합니다.
2. [최종 목적 기준 분류]: 여러 카테고리의 단어가 동시에 등장할 경우, 사용자가 최종적으로 얻고자 하는 '정보의 종류'를 기준으로 분류합니다.
3. [이동 중심 판정]: 장소까지 이동하는 방법을 묻는 경우는 목적지가 병원, 관공서, 아파트, 학교 등 그 어디라도 무조건 '교통'으로 분류합니다.
4. [절차 중심 판정]: 주거 공간(아파트, 원룸 등) 단어가 나오더라도, 핵심 의도가 이사나 물리적 이동이 아니라 계약서 작성, 보증금, 전입신고라면 무조건 '행정'으로 분류합니다.

[Few-shot 예시]
- Q: 아파트 가고 싶어요 / 아파트 가는 방법 알려주세요
  A: {{"category": "교통", "reason": "'아파트'라는 단어 내부의 '아파'라는 글자 조각 때문에 의료로 분류하면 안 되며, 문맥상 해당 장소까지의 이동 수단을 묻고 있으므로 교통이 맞습니다."}}

- Q: 병원까지 가는 버스 알려주세요
  A: {{"category": "교통", "reason": "'병원'이라는 의료 단어가 포함되어 있으나, 최종적으로 원하는 정보는 버스 이동 경로이므로 교통으로 분류합니다."}}

- Q: 외국인등록증 주소 변경하려고 주민센터 가는 길 알려주세요
  A: {{"category": "교통", "reason": "행정 기관이 목적지이고 주소 변경이라는 행정 단어가 등장했으나, 최종적으로 원하는 것은 해당 장소까지 이동하는 방법이므로 교통으로 분류합니다."}}

- Q: 새벽에 아파서 병원 가고 싶어요 / 응급실 가야 하나요?
  A: {{"category": "의료", "reason": "'병원 가고 싶다'라는 이동 표현이 포함되어 교통과 혼동될 수 있으나, 본질적인 목적은 야간에 병원에 갈 수 있는지를 묻는 것이므로 의료로 분류합니다."}}

[출력 형식 및 제약 조건]
반드시 아래 지정된 JSON 포맷으로만 응답해야 하며, 다른 여분의 설명이나 마크다운 태그(```json 등)는 절대 붙이지 마세요.

{{
  "category": "행정",
  "reason": "분류 근거를 설명"
}}

사용자 질문:
{user_input}
"""


# 3. 한글 카테고리명을 실제 임포트된 파이썬 모듈 객체와 매핑
CATEGORY_MODULE_MAP = {
    "행정": admin,
    "의료": medical,
    "교통": traffic
}

def route_with_llm_intent(user_input: str) -> CategoryHandlerSpec | None:
    """Gemini LLM을 활용해 사용자 의도를 분류하고, 일치하는 핸들러 스펙을 반환합니다."""
    structured_llm = get_llm().with_structured_output(RouterSchema)
    prompt = ROUTER_PROMPT_TEMPLATE.format(user_input=user_input)
    
    try:
        response = structured_llm.invoke(prompt)
        category = response.category
        reason = response.reason
        
        print(f"\n[AI Intent Router LOG]")
        print(f" - 입력 질문: {user_input}")
        print(f" - 추론 분류: {category}")
        print(f" - 판단 근거: {reason}\n")
        
    except Exception as e:
        print(f"[Router Error] LLM 라우팅 실패로 인한 역질문 유도: {e}")
        return None

    # LLM 문자열 결과에 대응하는 모듈 객체 획득
    target_module = CATEGORY_MODULE_MAP.get(category)
    if target_module is None:
        return None

    for spec in CATEGORY_REGISTRY:
        if spec.module == target_module:
            return spec
            
    return None


def run_localmate_result(user_input: str) -> CategoryResult:
    cleaned_input = user_input.strip()
    if not cleaned_input:
        raise RuntimeError("질문을 입력해주세요.")

    selected_handler = route_with_llm_intent(cleaned_input)
    
    if selected_handler is None:
        return CategoryResult.clarification(TOP_LEVEL_CLARIFICATION_QUESTION)

    return selected_handler.module.run_category(cleaned_input)


def run_localmate(user_input: str) -> str:
    return run_localmate_result(user_input).answer


def main() -> None:
    try:
        user_input = input(
            "질문을 입력해주세요. 빈 입력이면 예시 질문을 사용합니다: "
        ).strip()
    except EOFError:
        user_input = ""

    if not user_input:
        user_input = DEFAULT_QUESTION

    print(run_localmate(user_input))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(exc)
        raise SystemExit(1)