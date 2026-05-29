from functools import lru_cache
from typing import TypedDict

from langchain_core.documents import Document
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from categories.shared import get_llm, get_vectorstore
from categories.types import CategoryResult

MEDICAL_FILTER = {"category": "medical"}
NO_DOCS_WARNING = "관련 의료 안내 문서를 충분히 찾지 못했습니다. 공식 안내 및 병원 확인이 필요합니다."
GENERATION_ERROR_MESSAGE = "의료 안내를 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도하거나 설정을 확인해주세요."

# 외국인들이 '병원'이라고만 하면 어떤 과(내과/치과 등)인지, 혹은 응급 상황인지 모호할 때 던질 질문
CLARIFY_MEDICAL_QUESTION = (
    "어떤 증상이 있으신가요? 일반 진료(내과, 치과 등)가 필요하신지, 혹은 야간/휴일 응급실 방문이 필요하신지 알려주세요."
)

MEDICAL_KEYWORDS = [
    "병원", "약국", "의사", "치과", "내과", "이비인후과", "산부인과", "약", "처방전",
    "응급", "응급실", "119", "화상", "코피", "부상", "치료", "진료", "보건소", 
    "건강보험", "의료비", "본인부담금", "진료의뢰서"
]

class ActionPlanSchema(BaseModel):
    first_checks: list[str] = Field(default_factory=list)
    todo_steps: list[str] = Field(default_factory=list)
    visit_or_online: list[str] = Field(default_factory=list)
    after_checks: list[str] = Field(default_factory=list)

class KoreanExpressionsSchema(BaseModel):
    office: str  # 원본 코드의 규격을 맞추기 위해 'office'를 '병원/창구'용 표현으로 매핑
    phone: str
    message: str

class MedicalDraftSchema(BaseModel):
    action_plan: ActionPlanSchema
    checklist: list[str] = Field(default_factory=list)
    korean_expressions: KoreanExpressionsSchema

class MedicalState(TypedDict):
    user_input: str
    category: str
    sub_category: str
    needs_clarification: bool
    clarifying_question: str
    retrieved_docs: list[Document]
    action_plan: dict[str, list[str]]
    checklist: list[str]
    korean_expressions: dict[str, str]
    warnings: list[str]
    sources: list[str]
    final_answer: str

def can_handle(user_input: str) -> bool:
    text = normalize_text(user_input)
    if has_any_keyword(text, MEDICAL_KEYWORDS):
        return True
    
    # "아파", "다쳤어" 같은 직관적인 신체 증상 키워드 방어
    symptom_keywords = ["아파", "통증", "다쳤", " 피나", "부러", "걸렸"]
    return has_any_keyword(text, symptom_keywords)

def run_category(user_input: str) -> CategoryResult:
    cleaned_input = user_input.strip()
    if not cleaned_input:
        raise RuntimeError("질문을 입력해주세요.")

    try:
        result = get_graph().invoke(build_initial_state(cleaned_input))
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(GENERATION_ERROR_MESSAGE) from exc

    if result["needs_clarification"]:
        return CategoryResult.clarification(
            result["clarifying_question"],
            category="medical",
        )

    return CategoryResult.success(result["final_answer"], category="medical")

def invoke_structured(prompt: str, schema: type[BaseModel]) -> BaseModel:
    try:
        structured_llm = get_llm().with_structured_output(schema)
        return structured_llm.invoke(prompt)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(GENERATION_ERROR_MESSAGE) from exc

def fallback_bundle(sub_category: str) -> dict[str, object]:
    bundles = {
        "야간/응급": {
            "action_plan": {
                "first_checks": [
                    "환자의 의식 상태와 호흡을 먼저 정확하게 확인하세요.",
                    "즉시 이동 가능한 24시간 응급실이 있는 종합병원을 파악하세요.",
                ],
                "todo_steps": [
                    "위급 상황 시 국번 없이 119로 전화하여 구급차를 요청하세요.",
                    "외국인등록증이나 여권을 챙겨 신속히 응급실로 이동하세요.",
                    "의사의 진단에 따라 응급 처치 및 수속을 진행하세요.",
                ],
                "visit_or_online": [
                    "응급의료정보센터(1339)나 119를 통해 야간 진료 가능 여부를 전화로 확인하세요.",
                ],
                "after_checks": [
                    "응급실 이용 시 추가 부과되는 '응급의료관리료'를 수납 창구에서 확인하세요.",
                ],
            },
            "checklist": ["외국인등록증 또는 여권", "현재 복용 중인 약 (있는 경우)", "상황별 응급 처치 도구"],
            "korean_expressions": {
                "office": "응급실 접수하러 왔습니다. 환자가 갑자기 쓰러졌어요.",
                "phone": "지금 야간 응급실 접수 가능한가요? 당직 의사 선생님 계시나요?",
                "message": "친구가 다쳐서 응급실에 와 있습니다. 도움이 필요합니다.",
            },
        },
        "일반 진료/약국": {
            "action_plan": {
                "first_checks": [
                    "가벼운 감기나 일상적 질환은 큰 병원이 아닌 동네 의원을 먼저 찾으세요.",
                ],
                "todo_steps": [
                    "1단계 의원에서 진료를 받은 후 의사의 '처방전'을 꼭 발급받으세요.",
                    "발급받은 처방전을 지참하여 인근 약국을 방문하세요.",
                ],
                "visit_or_online": [
                    "대학병원(3차) 방문 시 반드시 동네의원 의사의 '진료의뢰서'가 있는지 확인하세요.",
                ],
                "after_checks": [
                    "처방전 없이 약국에서 살 수 있는 약은 일반 의약품으로 제한됨을 유의하세요.",
                ],
            },
            "checklist": ["외국인등록증 또는 여권", "의사 날인이 있는 처방전 (약국 방문 시)", "3차 병원용 진료의뢰서"],
            "korean_expressions": {
                "office": "접수하러 왔습니다. 건강보험 적용 가능한가요?",
                "phone": "오늘 평일 진료 몇 시까지 하시나요? 점심시간은 언제인가요?",
                "message": "병원 진료를 위한 처방전과 영수증을 확인하고 싶습니다.",
            },
        }
    }
    default_bundle = {
        "action_plan": {
            "first_checks": ["의료 관련 공식 안내 및 병원 운영 시간을 먼저 확인하세요."],
            "todo_steps": ["외국인등록증이나 신분증을 지참하여 병의원을 방문하세요."],
            "visit_or_online": ["방문 전 전화나 앱을 통해 진료 예약이 가능한지 확인하세요."],
            "after_checks": ["진료비 수납 시 건강보험 혜택이 정상 적용되었는지 확인하세요."],
        },
        "checklist": ["외국인등록증 또는 여권", "건강보험 자격 확인 증명서"],
        "korean_expressions": {
            "office": "진료 접수를 하고 싶습니다.",
            "phone": "안녕하세요. 외국인 진료 절차와 예약 방법을 문의드립니다.",
            "message": "진료 시간과 필요한 준비물을 안내해 주세요.",
        },
    }
    return bundles.get(sub_category, default_bundle)

def normalize_text(text: str) -> str:
    return text.strip().lower()

def has_any_keyword(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)

def build_initial_state(user_input: str) -> MedicalState:
    return MedicalState(
        user_input=user_input,
        category="의료",
        sub_category="",
        needs_clarification=False,
        clarifying_question="",
        retrieved_docs=[],
        action_plan={"first_checks": [], "todo_steps": [], "visit_or_online": [], "after_checks": []},
        checklist=[],
        korean_expressions={"office": "", "phone": "", "message": ""},
        warnings=[],
        sources=[],
        final_answer="",
    )

def classify_medical_node(state: MedicalState) -> MedicalState:
    text = normalize_text(state["user_input"])
    
    emergency_keywords = ["응급", "응급실", "119", "야간", "휴일", "화상", "부상", "피나", "부러"]
    general_keywords = ["내과", "치과", "이비인후과", "약국", "처방전", "진료의뢰서", "동네의원"]
    admin_insurance_keywords = ["보건소", "건강보험", "보험료", "본인부담금", "수급권자", "체납"]
    generic_hospital_keywords = ["병원", "아파", "치료"]

    if has_any_keyword(text, emergency_keywords):
        sub_category = "야간/응급"
        needs_clarification = False
        clarifying_question = ""
    elif has_any_keyword(text, general_keywords):
        sub_category = "일반 진료/약국"
        needs_clarification = False
        clarifying_question = ""
    elif has_any_keyword(text, admin_insurance_keywords):
        sub_category = "의료 행정/보험"
        needs_clarification = False
        clarifying_question = ""
    elif has_any_keyword(text, generic_hospital_keywords):
        # "나 병원 가야 해", "몸이 아파"처럼 정보가 너무 부족하고 애매할 때 역질문 던지기
        sub_category = "애매함"
        needs_clarification = True
        clarifying_question = CLARIFY_MEDICAL_QUESTION
    else:
        sub_category = "기타 의료"
        needs_clarification = False
        clarifying_question = ""

    return {
        **state,
        "category": "의료",
        "sub_category": sub_category,
        "needs_clarification": needs_clarification,
        "clarifying_question": clarifying_question,
    }

def route_after_classify(state: MedicalState) -> str:
    return "final_node" if state["needs_clarification"] else "retrieve_node"

def retrieve_node(state: MedicalState) -> MedicalState:
    if state["needs_clarification"]:
        return state

    try:
        docs = get_vectorstore().similarity_search(
            state["user_input"],
            k=3,
            filter=MEDICAL_FILTER,
        )
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(GENERATION_ERROR_MESSAGE) from exc

    warnings = list(state["warnings"])
    if not docs:
        warnings.append(NO_DOCS_WARNING)

    sources: list[str] = []
    for doc in docs:
        source = doc.metadata.get("source")
        if source and source not in sources:
            sources.append(source)

    return {
        **state,
        "retrieved_docs": docs,
        "warnings": warnings,
        "sources": sources,
    }

def format_context(docs: list[Document]) -> str:
    if not docs:
        return "관련 의학 및 의료 행정 문서를 찾지 못했습니다. 공식 안내 및 의료기관 확인이 필요하다는 점을 안내하세요."

    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        sub_category = doc.metadata.get("sub_category", "unknown")
        parts.append(f"[source={source} | sub_category={sub_category}]\n{doc.page_content}")
    return "\n\n".join(parts)

def plan_node(state: MedicalState) -> MedicalState:
    context = format_context(state["retrieved_docs"])
    prompt = f"""
당신은 외국인 주민을 위한 의료 시스템 및 병의원 이용 안내 도우미입니다.
아래 사용자 질문과 의료 FAQ 문맥을 바탕으로 쉬운 한국어 행동 안내, 준비물 체크리스트, 의료기관/전화에서 쓸 표현을 작성하세요.

중요 규칙:
- 문서에 언급되지 않은 구체적인 비급여 진료비, 실시간 대기시간, 특정 병원명을 단정하지 마세요.
- 전문적인 의학적 진단이나 처방(예: 특정 전문 의약품 추천 등)을 내리지 마세요. 법률/의료 조언이 아님을 명시하세요.
- 한국의 독특한 의약분업(병원 진료 후 약국 이동) 및 1, 2, 3차 병원 단계별 특성(진료의뢰서)을 반영하세요.
- 각 항목은 짧고 바로 행동할 수 있게 작성하세요.
- checklist는 3개 이상 6개 이하로 작성하세요.
- JSON 스키마에 맞게 작성하세요.

사용자 질문:
{state["user_input"]}

상황 분류:
의료 / {state["sub_category"]}

문맥:
{context}
""".strip()

    try:
        result = invoke_structured(prompt, MedicalDraftSchema)
        bundle = {
            "action_plan": {
                "first_checks": result.action_plan.first_checks or [],
                "todo_steps": result.action_plan.todo_steps or [],
                "visit_or_online": result.action_plan.visit_or_online or [],
                "after_checks": result.action_plan.after_checks or [],
            },
            "checklist": [item.strip() for item in result.checklist if item.strip()],
            "korean_expressions": {
                "office": result.korean_expressions.office.strip(),
                "phone": result.korean_expressions.phone.strip(),
                "message": result.korean_expressions.message.strip(),
            },
        }
    except RuntimeError as exc:
        if str(exc) != GENERATION_ERROR_MESSAGE:
            raise
        bundle = fallback_bundle(state["sub_category"])

    return {
        **state,
        "action_plan": bundle["action_plan"],
        "checklist": bundle["checklist"][:6],
        "korean_expressions": bundle["korean_expressions"],
    }

def checklist_node(state: MedicalState) -> MedicalState:
    items = list(state["checklist"])
    if not items:
        items = fallback_bundle(state["sub_category"])["checklist"]
    return {**state, "checklist": items[:6]}

def expression_node(state: MedicalState) -> MedicalState:
    expressions = dict(state["korean_expressions"])
    if not all(expressions.values()):
        expressions = fallback_bundle(state["sub_category"])["korean_expressions"]
    return {**state, "korean_expressions": expressions}

def warning_node(state: MedicalState) -> MedicalState:
    warnings = [
        "체류자격, 건강보험 가입 여부에 따라 의료비 본인부담금 비율이 크게 달라질 수 있습니다.",
        "3차 대학병원 방문 전에는 반드시 1단계 의원의 '진료의뢰서'를 지참해야 보험 혜택을 받습니다.",
        "이 안내는 공식 의료 조언이 아니므로, 급박한 증상이 있거나 응급 상황 시 즉시 119에 문의하십시오.",
    ]
    for warning in state["warnings"]:
        if warning not in warnings:
            warnings.append(warning)
    return {**state, "warnings": warnings}

def format_bullets(items: list[str]) -> str:
    if not items:
        return "- 확인이 필요한 의료 정보가 있습니다."
    return "\n".join(f"- {item}" for item in items)

def format_numbered(items: list[str]) -> str:
    if not items:
        return "1. 공식 안내 및 의료기관을 먼저 확인해주세요."
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))

def format_checkboxes(items: list[str]) -> str:
    if not items:
        return "□ 필요한 신분증 및 의료 서류를 다시 확인해주세요."
    return "\n".join(f"□ {item}" for item in items)

def format_sources(sources: list[str]) -> str:
    if not sources:
        return "- 관련 의료 문서를 찾지 못했습니다."
    return "\n".join(f"- {source}" for source in sources)

def final_node(state: MedicalState) -> MedicalState:
    if state["needs_clarification"]:
        return {**state, "final_answer": state["clarifying_question"]}

    action_plan = state["action_plan"]
    final_answer = "\n".join(
        [
            "## 상황 분류",
            f"의료 / {state['sub_category']}",
            "",
            "## 먼저 확인할 것",
            format_bullets(action_plan.get("first_checks", [])),
            "",
            "## 해야 할 일",
            format_numbered(action_plan.get("todo_steps", [])),
            "",
            "## 방문/온라인 확인",
            format_bullets(action_plan.get("visit_or_online", [])),
            "",
            "## 처리 후 확인할 것",
            format_bullets(action_plan.get("after_checks", [])),
            "",
            "## 준비물 체크리스트",
            format_checkboxes(state["checklist"]),
            "",
            "## 기관에서 사용할 한국어",
            f'- 병의원/창구에서 말할 문장:\n  "{state["korean_expressions"].get("office", "")}"',
            f'- 전화로 물어볼 문장:\n  "{state["korean_expressions"].get("phone", "")}"',
            f'- 문자/이메일 문장:\n  "{state["korean_expressions"].get("message", "")}"',
            "",
            "## 주의사항",
            format_bullets(state["warnings"]),
            "",
            "## 참고 문서",
            format_sources(state["sources"]),
        ]
    )
    return {**state, "final_answer": final_answer}

def build_graph():
    graph = StateGraph(MedicalState)
    graph.add_node("classify_medical_node", classify_medical_node)
    graph.add_node("retrieve_node", retrieve_node)
    graph.add_node("plan_node", plan_node)
    graph.add_node("checklist_node", checklist_node)
    graph.add_node("expression_node", expression_node)
    graph.add_node("warning_node", warning_node)
    graph.add_node("final_node", final_node)

    graph.set_entry_point("classify_medical_node")
    graph.add_conditional_edges(
        "classify_medical_node",
        route_after_classify,
        {
            "retrieve_node": "retrieve_node",
            "final_node": "final_node",
        },
    )
    graph.add_edge("retrieve_node", "plan_node")
    graph.add_edge("plan_node", "checklist_node")
    graph.add_edge("checklist_node", "expression_node")
    graph.add_edge("expression_node", "warning_node")
    graph.add_edge("warning_node", "final_node")
    graph.add_edge("final_node", END)
    return graph.compile()

@lru_cache(maxsize=1)
def get_graph():
    return build_graph()