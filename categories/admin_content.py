from langchain_core.documents import Document

from categories.response_format import (
    format_bullets,
    format_numbered,
    format_sources,
)
from categories.admin_rules import (
    SUB_ADDRESS_CHANGE,
    SUB_ALIEN_CARD_LOSS,
    SUB_MISC,
    SUB_VISA,
    SUB_VISIT,
)

PRIMARY_SOURCE_BY_SUBCATEGORY = {
    SUB_ALIEN_CARD_LOSS: "admin/admin_alien_card_loss.md",
    SUB_ADDRESS_CHANGE: "admin/admin_address_change.md",
    SUB_VISA: "admin/admin_visa_extension.md",
}

INTRO_BY_SUBCATEGORY = {
    SUB_ALIEN_CARD_LOSS: (
        "외국인등록증을 잃어버렸다면 먼저 분실 여부를 확인하고, 재발급 절차를 확인해야 해요. "
        "아래 순서대로 준비하면 됩니다.\n"
        "(If you lost your Alien Registration Card, first confirm that it is lost and check the reissue process. "
        "You can prepare by following the steps below.)"
    ),
    SUB_ADDRESS_CHANGE: (
        "이사했다면 새 주소를 기준으로 주소 변경 신고가 필요한지 확인해야 해요. "
        "이사 날짜와 새 주소를 먼저 정리해 두면 좋습니다.\n"
        "(If you moved, you may need to report your new address. "
        "It is helpful to prepare your moving date and new address first.)"
    ),
    SUB_VISA: (
        "비자 기간이 곧 끝난다면 만료일을 먼저 확인하고, 체류기간 연장 가능 여부와 신청 절차를 미리 확인하는 것이 좋아요.\n"
        "(If your visa is expiring soon, first check the expiration date and confirm the extension process as soon as possible.)"
    ),
    SUB_VISIT: (
        "기관을 방문해야 할지 헷갈린다면 먼저 방문 목적과 예약 필요 여부를 확인해 주세요.\n"
        "(If you are not sure whether you need to visit an office, first check the purpose of your visit and whether a reservation is required.)"
    ),
    SUB_MISC: (
        "행정 절차는 업무 종류에 따라 준비물이 달라질 수 있어요. 어떤 업무인지 먼저 확인한 뒤 필요한 서류를 정리해 주세요.\n"
        "(Administrative procedures can differ by task. First identify the task, then prepare the required documents.)"
    ),
}

EXPIRED_VISA_INTRO = (
    "비자 기간이 이미 지났다면 괜찮다고 판단하지 말고, 가능한 빨리 관할 출입국외국인청이나 공식 상담 채널에 연락해 본인 상황을 설명해야 합니다.\n"
    "(If your visa period has already expired, it is not safe to assume it is okay. "
    "Contact the immigration office or an official consultation channel as soon as possible and explain your situation.)"
)

FALLBACK_BUNDLES: dict[str, dict[str, object]] = {
    SUB_ALIEN_CARD_LOSS: {
        "action_plan": {
            "first_checks": [
                "마지막으로 본 장소와 시간을 정리하세요.  \n   (Write down where and when you last saw it.)",
                "단순 분실인지, 도난 가능성이 있는지 먼저 확인하세요.  \n   (Check whether it seems simply lost or possibly stolen.)",
            ],
            "todo_steps": [
                "출입국외국인청 또는 공식 안내에서 재발급 절차를 확인하세요.  \n   (Check the reissue process through the immigration office or official guidance.)",
                "방문 예약이 필요한지 확인하세요.  \n   (Check whether you need to make a visit reservation.)",
                "여권, 사진, 체류 관련 정보를 준비하세요.  \n   (Prepare your passport, photo, and stay-related information.)",
            ],
            "visit_or_online": [
                "온라인 신청이 가능한지 확인하세요.  \n   (Check whether online application is available.)",
                "방문이 필요한 경우 예약 여부를 확인하세요.  \n   (If you need to visit, check whether a reservation is required.)",
            ],
            "after_checks": [
                "접수 후 등록증 수령 방법을 확인하세요.  \n   (After applying, check how you will receive the card.)",
                "기관에서 추가로 요청할 수 있는 서류가 있는지 확인하세요.  \n   (Check whether the office may ask for additional documents.)",
            ],
        },
        "checklist": ["여권 (Passport)", "증명사진 (ID photo)", "외국인등록번호 또는 체류 관련 정보 (Alien registration number or stay-related information)", "분실 경위 메모 (Memo about when and where you lost it)", "방문 예약 확인 내역 (Visit reservation confirmation)"],
        "korean_expressions": {
            "office": "외국인등록증을 잃어버렸어요. 재발급 절차를 안내해 주세요.  \n  (I lost my Alien Registration Card. Please tell me the reissue process.)",
            "phone": "방문 예약이 필요한가요?  \n  (Do I need to make a visit reservation?)",
            "message": "준비해야 하는 서류와 접수 방법을 알려 주세요.  \n  (Please tell me the required documents and how to apply.)",
        },
    },
    SUB_ADDRESS_CHANGE: {
        "action_plan": {
            "first_checks": [
                "이사 날짜와 새 주소를 정확하게 정리하세요.  \n   (Write down your moving date and new address accurately.)",
                "주소 변경 신고 대상인지 먼저 확인하세요.  \n   (Check whether you need to report the address change.)",
            ],
            "todo_steps": [
                "신고 기한이 있는지 확인하세요.  \n   (Check whether there is a reporting deadline.)",
                "온라인 신고 또는 방문 신고가 가능한지 확인하세요.  \n   (Check whether you can report online or need to visit.)",
                "거주지 확인 서류를 준비하세요.  \n   (Prepare documents proving your residence.)",
            ],
            "visit_or_online": [
                "온라인 신고가 가능한지 확인하세요.  \n   (Check whether online reporting is available.)",
                "방문이 필요한 경우 예약이 필요한지 확인하세요.  \n   (If you need to visit, check whether a reservation is required.)",
            ],
            "after_checks": [
                "새 주소가 정상 반영되었는지 확인하세요.  \n   (Check whether your new address was updated correctly.)",
                "기관에서 추가로 요청할 수 있는 서류가 있는지 확인하세요.  \n   (Check whether the office may ask for additional documents.)",
            ],
        },
        "checklist": ["여권 (Passport)", "외국인등록증 또는 체류 관련 신분 확인 자료 (Alien Registration Card or stay-related ID information)", "새 주소 확인 서류 (Proof of new address)", "거주 확인 자료 (Residence confirmation document)", "방문 예약 확인 내역 (Visit reservation confirmation)"],
        "korean_expressions": {
            "office": "이사해서 주소 변경 신고가 필요한지 확인하고 싶어요.  \n  (I moved and would like to check whether I need to report my address change.)",
            "phone": "주소 변경 신고 방법과 필요한 서류를 알려 주세요.  \n  (Please tell me how to report an address change and what documents are required.)",
            "message": "이사 날짜와 새 주소를 기준으로 어떻게 신고하면 되나요?  \n  (How should I report based on my moving date and new address?)",
        },
    },
    SUB_VISA: {
        "action_plan": {
            "first_checks": [
                "현재 비자/체류자격 정보와 만료일을 확인하세요.  \n   (Check your current visa/status of stay and expiration date.)",
                "체류기간 연장 신청 가능 시기와 필요한 서류를 확인하세요.  \n   (Check when you can apply for an extension and what documents are required.)",
            ],
            "todo_steps": [
                "공식 안내에서 체류기간 연장 또는 비자 관련 절차를 확인하세요.  \n   (Check the extension or visa process through official guidance.)",
                "방문 예약이 필요한지 확인하세요.  \n   (Check whether you need to make a visit reservation.)",
                "여권과 체류 관련 서류를 준비하세요.  \n   (Prepare your passport and stay-related documents.)",
            ],
            "visit_or_online": [
                "온라인 신청이 가능한지 확인하세요.  \n   (Check whether online application is available.)",
                "방문이 필요한 경우 관할 기관과 예약 가능 여부를 확인하세요.  \n   (If you need to visit, check the responsible office and reservation availability.)",
            ],
            "after_checks": [
                "접수 상태와 추가 서류 요청 여부를 확인하세요.  \n   (Check your application status and whether additional documents are requested.)",
                "처리 일정은 공식 안내에서 다시 확인하세요.  \n   (Confirm processing timelines through official guidance.)",
            ],
        },
        "checklist": ["여권 (Passport)", "외국인등록증 또는 체류 관련 정보 (Alien Registration Card or stay-related information)", "현재 비자/체류자격 정보 (Current visa/status of stay information)", "체류기간 만료일 확인 자료 (Document showing your stay period expiration date)", "기관에서 추가로 요청할 수 있는 서류 (Documents the office may additionally request)", "방문 예약 확인 내역 (Visit reservation confirmation)"],
        "korean_expressions": {
            "office": "비자 기간이 곧 끝나서 체류기간 연장 방법을 확인하고 싶어요.  \n  (My visa period is ending soon, and I would like to check how to extend my stay.)",
            "phone": "제 체류자격에 필요한 서류가 무엇인지 알고 싶어요.  \n  (I would like to know what documents are required for my status of stay.)",
            "message": "방문 예약이 필요한지 확인해 주세요.  \n  (Please check whether I need to make a visit reservation.)",
        },
    },
    SUB_VISIT: {
        "action_plan": {
            "first_checks": [
                "어떤 기관에 어떤 목적으로 방문해야 하는지 먼저 확인하세요.  \n   (First check which office you need to visit and why.)",
                "예약이 필요한 업무인지 확인하세요.  \n   (Check whether the task requires an appointment.)",
            ],
            "todo_steps": [
                "방문 목적에 맞는 기관을 확인하세요.  \n   (Confirm the correct office for your purpose.)",
                "예약 방법과 준비물을 확인하세요.  \n   (Check how to reserve and what to prepare.)",
            ],
            "visit_or_online": [
                "온라인 예약이 가능한지 확인하세요.  \n   (Check whether online reservation is available.)",
            ],
            "after_checks": [
                "예약 내용과 방문 시간을 다시 확인하세요.  \n   (Confirm your appointment details and visit time.)",
            ],
        },
        "checklist": ["여권 (Passport)", "방문 목적 관련 안내 내용 (Information related to your visit purpose)", "예약 확인 내역 (Appointment confirmation)", "본인 확인 자료 (Identity document)"],
        "korean_expressions": {
            "office": "이 업무는 방문 예약이 필요한가요?  \n  (Does this task require a visit reservation?)",
            "phone": "방문 예약 방법과 준비물을 알려 주세요.  \n  (Please tell me how to make a visit reservation and what to prepare.)",
            "message": "제가 방문해야 하는 기관이 맞는지 확인해 주세요.  \n  (Please check whether this is the right office for me to visit.)",
        },
    },
    SUB_MISC: {
        "action_plan": {
            "first_checks": [
                "어떤 행정 업무인지 먼저 확인하세요.  \n   (First identify which administrative task you need help with.)",
            ],
            "todo_steps": [
                "업무에 맞는 기관과 절차를 확인하세요.  \n   (Check the correct office and procedure for the task.)",
                "본인 상황에 맞는 준비물을 정리하세요.  \n   (Prepare documents that match your situation.)",
            ],
            "visit_or_online": [
                "방문 또는 온라인 처리 가능 여부를 확인하세요.  \n   (Check whether it can be handled online or requires a visit.)",
            ],
            "after_checks": [
                "처리 후 추가 확인이 필요한지 다시 살펴보세요.  \n   (After processing, check whether any follow-up is needed.)",
            ],
        },
        "checklist": ["여권 (Passport)", "본인 확인 자료 (Identity document)", "방문 또는 신청 관련 안내 내용 (Information about the visit or application)"],
        "korean_expressions": {
            "office": "이 업무는 어떤 절차로 진행하면 되나요?  \n  (What procedure should I follow for this task?)",
            "phone": "필요한 준비물과 방문 여부를 알려 주세요.  \n  (Please tell me what to prepare and whether I need to visit.)",
            "message": "제 상황에서 어떤 기관에 문의해야 하나요?  \n  (Which office should I contact for my situation?)",
        },
    },
}

WARNING_BY_SUBCATEGORY = {
    SUB_ALIEN_CARD_LOSS: [
        "외국인등록증은 신분 확인에 필요할 수 있으므로, 분실이 확실하다면 재발급 절차를 미루지 않는 것이 좋습니다.  \n  (Your Alien Registration Card may be needed for identification, so if it is lost, it is better not to delay the reissue process.)",
        "필요 서류, 수수료, 처리 기간은 개인 상황에 따라 달라질 수 있으므로 방문 전 확인하세요.  \n  (Required documents, fees, and processing time may differ depending on your situation, so check before visiting.)",
    ],
    SUB_ADDRESS_CHANGE: [
        "주소 변경 신고에는 기한이 있을 수 있으므로 이사 날짜를 기준으로 미리 확인하세요.  \n  (There may be a deadline for reporting an address change, so check as soon as possible based on your moving date.)",
        "거주지 확인 서류는 계약 형태나 거주 상황에 따라 달라질 수 있습니다.  \n  (Documents proving your residence may differ depending on your housing contract or living situation.)",
    ],
    SUB_VISA: [
        "체류기간 만료 전에 신청 가능 시기와 필요 서류를 확인하는 것이 중요합니다.  \n  (It is important to check the application period and required documents before your stay period expires.)",
        "체류자격마다 필요한 서류가 다를 수 있습니다.  \n  (Required documents may differ depending on your status of stay.)",
    ],
    SUB_VISIT: [
        "방문 예약 가능 시간과 준비물은 기관과 업무에 따라 달라질 수 있습니다.  \n  (Reservation times and required items may differ depending on the office and task.)",
    ],
    SUB_MISC: [
        "업무 종류와 개인 상황에 따라 필요한 서류와 절차가 달라질 수 있습니다.  \n  (Required documents and procedures may differ depending on the task and your personal situation.)",
    ],
}

EXPIRED_VISA_WARNINGS = [
    "체류기간이 지난 상태는 개인 상황에 따라 불이익이 생길 수 있으므로, 괜찮다고 판단하지 않는 것이 안전합니다.  \n  (If your stay period has already expired, there may be disadvantages depending on your situation, so it is not safe to assume it is okay.)",
    "가능한 빨리 관할 출입국외국인청 또는 공식 상담 채널에 문의하세요.  \n  (Contact the immigration office or an official consultation channel as soon as possible.)",
    "문의할 때 본인의 체류자격과 만료일을 정확히 설명하세요.  \n  (When contacting them, explain your status of stay and expiration date clearly.)",
]


def get_fallback_bundle(sub_category: str) -> dict[str, object]:
    return FALLBACK_BUNDLES.get(sub_category, FALLBACK_BUNDLES[SUB_MISC])


def get_primary_source(sub_category: str) -> str | None:
    return PRIMARY_SOURCE_BY_SUBCATEGORY.get(sub_category)


def format_context(docs: list[Document]) -> str:
    if not docs:
        return (
            "관련 문서를 찾지 못했습니다. 절차를 단정하지 말고, 공식 안내 확인이 필요하다는 점을 "
            "자연스럽게 안내해 주세요."
        )

    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        sub_category = doc.metadata.get("sub_category", "unknown")
        parts.append(
            f"[source={source} | sub_category={sub_category}]\n{doc.page_content}"
        )
    return "\n\n".join(parts)


def merge_admin_warnings(extra_warnings: list[str]) -> list[str]:
    warnings: list[str] = []
    for warning in extra_warnings:
        if warning not in warnings:
            warnings.append(warning)
    return warnings


def build_final_answer(
    sub_category: str,
    is_expired_visa: bool,
    action_plan: dict[str, list[str]],
    checklist: list[str],
    korean_expressions: dict[str, str],
    warnings: list[str],
    sources: list[str],
) -> str:
    bundle = get_fallback_bundle(sub_category)
    curated_plan = bundle["action_plan"]
    curated_checklist = bundle["checklist"]
    curated_expressions = bundle["korean_expressions"]
    intro = EXPIRED_VISA_INTRO if is_expired_visa else INTRO_BY_SUBCATEGORY.get(
        sub_category,
        INTRO_BY_SUBCATEGORY[SUB_MISC],
    )
    final_warnings = build_warnings(sub_category, is_expired_visa, warnings)
    final_sources = prioritize_sources(sub_category, sources)
    checklist_section = format_admin_checkboxes(curated_checklist or checklist)

    sections = [
        intro,
        "## 상황 분류\n"
        f"행정 / {sub_category}",
        "## 지금 해야 할 일\n"
        f"{format_numbered(curated_plan.get('todo_steps', action_plan.get('todo_steps', [])))}",
    ]

    if checklist_section:
        sections.append(
            "## 준비물 체크리스트\n"
            f"{checklist_section}"
        )

    sections.extend(
        [
            "## 기관 직원에게 말하거나 보여줄 문장\n"
            "아래 문장은 출입국외국인청, 주민센터, 상담 창구 직원에게 직접 말하거나 보여주면 됩니다.  \n"
            "(You can say or show the following sentences to staff at the immigration office, community center, or consultation desk.)\n\n"
            f"{format_bullets(list((curated_expressions or korean_expressions).values()))}",
            "## 방문/온라인 확인\n"
            f"{format_bullets(curated_plan.get('visit_or_online', action_plan.get('visit_or_online', [])))}",
            "## 처리 후 확인할 것\n"
            f"{format_bullets(curated_plan.get('after_checks', action_plan.get('after_checks', [])))}",
            "## 주의사항\n"
            f"{format_bullets(final_warnings)}",
            "## 참고 문서\n"
            f"{format_sources(final_sources)}",
        ]
    )

    return "\n\n".join(sections).strip()


def build_warnings(
    sub_category: str,
    is_expired_visa: bool,
    extra_warnings: list[str],
) -> list[str]:
    warnings = (
        list(EXPIRED_VISA_WARNINGS)
        if is_expired_visa
        else list(WARNING_BY_SUBCATEGORY.get(sub_category, WARNING_BY_SUBCATEGORY[SUB_MISC]))
    )
    for warning in extra_warnings:
        if warning and warning not in warnings and "관련 문서를 충분히 찾지 못했습니다" not in warning:
            warnings.append(warning)
    return warnings


def format_admin_checkboxes(items: list[str]) -> str:
    if not items:
        return ""
    return "  \n".join(f"□ {item}" for item in items)


def prioritize_sources(sub_category: str, sources: list[str]) -> list[str]:
    primary_source = get_primary_source(sub_category)
    prioritized: list[str] = []
    if primary_source:
        prioritized.append(primary_source)

    for source in sources:
        if source == primary_source:
            continue
        if not is_relevant_source(sub_category, source):
            continue
        if source not in prioritized:
            prioritized.append(source)
        if len(prioritized) >= 2:
            break

    return prioritized


def is_relevant_source(sub_category: str, source: str) -> bool:
    expected = get_primary_source(sub_category)
    if expected:
        return source == expected
    return source.startswith("admin/")
