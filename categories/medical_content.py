from langchain_core.documents import Document

from categories.response_format import (
    format_bullets,
    format_numbered,
)
from categories.medical_rules import (
    NO_DOCS_WARNING,
    SUB_AMBIGUOUS,
    SUB_EMERGENCY,
    SUB_GENERAL_HOSPITAL,
    SUB_HEALTH_INSURANCE_BILL,
    SUB_MEDICAL_COST_INSURANCE,
    SUB_PUBLIC_HEALTH_VACCINATION,
)

PRIMARY_SOURCE_BY_SUBCATEGORY = {
    SUB_GENERAL_HOSPITAL: "medical/medical_general.md",
    SUB_EMERGENCY: "medical/medical_emergency.md",
    SUB_HEALTH_INSURANCE_BILL: "medical/medical_admin.md",
    SUB_PUBLIC_HEALTH_VACCINATION: "medical/medical_admin.md",
    SUB_MEDICAL_COST_INSURANCE: "medical/medical_admin.md",
}

INTRO_BY_SUBCATEGORY = {
    SUB_GENERAL_HOSPITAL: (
        "몸이 아프거나 약이 필요하면 먼저 증상과 방문 가능한 시간을 정리하면 좋아요. "
        "(If you feel sick or need medicine, first organize your symptoms and available visit time.)"
    ),
    SUB_EMERGENCY: (
        "갑자기 심하게 아프면 먼저 119에 전화할 상황인지, 바로 응급실로 갈 상황인지 판단하는 것이 중요해요. "
        "(If you suddenly feel very sick, first decide whether to call 119 or go to an emergency room.)"
    ),
    SUB_HEALTH_INSURANCE_BILL: (
        "건강보험 고지서를 처음 받으면 헷갈릴 수 있어요. 아래 순서대로 금액과 납부 기한부터 확인해보면 됩니다. "
        "(A health insurance bill can be confusing at first. Start by checking the amount and payment deadline in the order below.)"
    ),
    SUB_PUBLIC_HEALTH_VACCINATION: (
        "보건소 예방접종은 지역, 나이, 체류자격, 접종 종류에 따라 대상 여부가 달라질 수 있어요. "
        "(Public health center vaccination eligibility can vary by region, age, visa status, and vaccine type.)"
    ),
    SUB_MEDICAL_COST_INSURANCE: (
        "의료비나 보험 자격이 궁금하면 본인의 자격 상태와 청구 내역을 먼저 확인하면 좋아요. "
        "(If you have questions about medical costs or insurance eligibility, first check your eligibility status and billing details.)"
    ),
    SUB_AMBIGUOUS: (
        "의료 상황이 아직 조금 모호해요. 어떤 도움이 필요한지 먼저 좁혀보면 더 정확히 안내할 수 있어요. "
        "(The medical situation is still a little unclear. Narrowing down what help you need will make the guidance more accurate.)"
    ),
}

EXPRESSION_HEADING_BY_SUBCATEGORY = {
    SUB_GENERAL_HOSPITAL: "병원/약국 직원에게 말하거나 보여줄 문장",
    SUB_EMERGENCY: "응급실 직원이나 119에 말할 문장",
    SUB_HEALTH_INSURANCE_BILL: "국민건강보험공단 직원에게 말하거나 보여줄 문장",
    SUB_PUBLIC_HEALTH_VACCINATION: "보건소 직원에게 말하거나 보여줄 문장",
    SUB_MEDICAL_COST_INSURANCE: "병원 원무과 또는 국민건강보험공단 직원에게 말하거나 보여줄 문장",
    SUB_AMBIGUOUS: "병원/기관 직원에게 말하거나 보여줄 문장",
}

WARNING_BY_SUBCATEGORY = {
    SUB_GENERAL_HOSPITAL: [
        "이 안내는 의사의 진단이나 처방을 대신할 수 없습니다. (This guidance cannot replace a doctor's diagnosis or prescription.)",
        "방문 전 진료 시간과 예약 필요 여부를 전화로 확인하세요. (Call before visiting to check opening hours and whether an appointment is needed.)",
    ],
    SUB_EMERGENCY: [
        "의식이 없거나 숨쉬기 어렵거나 통증이 매우 심하면 지체하지 말고 119에 전화하세요. (If the person is unconscious, has trouble breathing, or has severe pain, call 119 without delay.)",
        "응급 여부는 증상과 상태에 따라 달라지므로 현장 의료진의 안내를 따르세요. (Emergency decisions depend on symptoms and condition, so follow medical staff guidance.)",
    ],
    SUB_HEALTH_INSURANCE_BILL: [
        "보험료 금액과 납부 기한은 고지서와 공단 안내 기준으로 확인하세요. (Check the premium amount and payment deadline based on the bill and NHIS guidance.)",
        "본인 명의가 아니거나 금액이 이상하면 납부 전 국민건강보험공단에 문의하세요. (If the bill is not in your name or the amount seems wrong, contact NHIS before paying.)",
    ],
    SUB_PUBLIC_HEALTH_VACCINATION: [
        "무료 여부는 지역, 나이, 체류자격, 접종 종류에 따라 달라질 수 있습니다. (Free eligibility can vary by region, age, visa status, and vaccine type.)",
        "방문 전 보건소에 대상 여부와 준비물을 확인하세요. (Before visiting, ask the public health center about eligibility and required documents.)",
    ],
    SUB_MEDICAL_COST_INSURANCE: [
        "의료비와 보험 적용 여부는 병원, 진료 항목, 보험 자격에 따라 달라질 수 있습니다. (Medical costs and coverage can vary by hospital, treatment item, and insurance eligibility.)",
        "수납 전 원무과에 본인부담금과 보험 적용 여부를 확인하세요. (Before paying, ask the billing desk about your out-of-pocket cost and coverage.)",
    ],
    SUB_AMBIGUOUS: [
        "증상이 심하거나 갑자기 악화되면 119 또는 응급실에 먼저 문의하세요. (If symptoms are severe or suddenly worsen, contact 119 or an emergency room first.)",
    ],
}

FALLBACK_BUNDLES: dict[str, dict[str, object]] = {
    SUB_GENERAL_HOSPITAL: {
        "action_plan": {
            "first_checks": [
                "증상과 시작 시간을 짧게 정리해 병원이나 약국 직원에게 알려주세요. (Briefly explain your symptoms and when they started to hospital or pharmacy staff.)",
                "오늘 방문 가능한 병원이나 약국의 운영 시간을 확인하세요. (Check the opening hours of a clinic or pharmacy you can visit today.)",
            ],
            "todo_steps": [
                "신분증과 건강보험 자격 확인 자료를 챙기세요. (Bring your ID and health insurance eligibility information.)",
                "접수할 때 증상과 아픈 부위를 짧게 설명하세요. (At registration, briefly explain your symptoms and the painful area.)",
                "진료 후 처방전이 있으면 가까운 약국으로 가세요. (After the visit, take the prescription to a nearby pharmacy if you receive one.)",
            ],
            "visit_or_online": [
                "병원에 전화해 예약이 필요한지 확인하세요. (Call the clinic to ask whether an appointment is needed.)",
                "약국에서는 복용 횟수와 식전/식후 복용 여부를 확인하세요. (At the pharmacy, ask how often to take the medicine and whether to take it before or after meals.)",
            ],
            "after_checks": [
                "약 복용 방법과 주의사항을 다시 확인하세요. (Check the medication instructions and precautions again.)",
                "증상이 악화되면 다시 병원이나 응급실에 문의하세요. (If symptoms get worse, contact a clinic or emergency room again.)",
            ],
        },
        "checklist": [
            "외국인등록증 또는 여권 (Alien registration card or passport)",
            "건강보험 자격 확인 자료 (Health insurance eligibility information)",
            "증상 메모 (Symptom notes)",
            "복용 중인 약 목록 (List of current medications)",
        ],
        "korean_expressions": {
            "office": "진료 접수를 하고 싶습니다. 처음 왔습니다. (I would like to register for treatment. This is my first visit.)",
            "phone": "오늘 진료가 가능한 시간과 예약 필요 여부를 알고 싶습니다. (I would like to know today's available hours and whether I need an appointment.)",
            "message": "진료 시간과 필요한 준비물을 안내해주세요. (Please tell me the clinic hours and what I need to bring.)",
        },
    },
    SUB_EMERGENCY: {
        "action_plan": {
            "first_checks": [
                "증상이 심하거나 숨쉬기 어렵거나 움직이기 힘들면 먼저 119에 연락하거나 응급실로 가세요. (If symptoms are severe, breathing is difficult, or moving is hard, call 119 or go to the emergency room first.)",
                "혼자 움직이기 어렵다면 주변 사람에게 도움을 요청하세요. (If it is hard to move alone, ask someone nearby for help.)",
            ],
            "todo_steps": [
                "119 상담원에게 현재 위치와 증상을 짧게 말하세요. (Tell the 119 operator your current location and symptoms briefly.)",
                "상태가 심하지 않지만 걱정되면 가까운 응급실에 전화해 방문 필요 여부를 물어보세요. (If it is not severe but you are worried, call a nearby emergency room and ask whether you should visit.)",
                "여권 또는 외국인등록증과 복용 중인 약 정보를 챙기세요. (Bring your passport or alien registration card and information about current medications.)",
            ],
            "visit_or_online": [
                "응급실에 도착하면 증상이 언제 시작됐는지 먼저 말하세요. (When you arrive at the emergency room, first say when the symptoms started.)",
                "혼자 설명하기 어렵다면 한국어 문장을 직원에게 보여주세요. (If it is hard to explain alone, show the Korean sentences to staff.)",
            ],
            "after_checks": [
                "진료 후 다음 진료가 필요한지 확인하세요. (After treatment, ask whether follow-up care is needed.)",
                "처방약이 있으면 복용 방법을 약국에서 다시 확인하세요. (If you receive medicine, confirm how to take it at the pharmacy.)",
            ],
        },
        "checklist": [
            "현재 위치 메모 (Current location note)",
            "외국인등록증 또는 여권 (Alien registration card or passport)",
            "복용 중인 약 정보 (Current medication information)",
            "보호자 또는 비상 연락처 (Guardian or emergency contact)",
        ],
        "korean_expressions": {
            "office": "갑자기 심하게 아파서 응급 진료가 필요합니다. (I suddenly feel very sick and need emergency care.)",
            "phone": "지금 119가 필요할지 응급실에 가야 할지 알고 싶습니다. (I want to know whether I need 119 or should go to the emergency room.)",
            "message": "환자가 갑자기 아파서 응급실 방문이 필요한지 확인하고 싶습니다. (The patient suddenly became sick, and I want to check whether an emergency room visit is needed.)",
        },
    },
    SUB_HEALTH_INSURANCE_BILL: {
        "action_plan": {
            "first_checks": [
                "고지서에 적힌 납부 금액을 확인하세요. (Check the payment amount on the bill.)",
                "고지서의 납부 기한을 확인하세요. (Check the payment deadline on the bill.)",
                "본인 명의 고지서인지 확인하세요. (Check whether the bill is in your name.)",
            ],
            "todo_steps": [
                "고지서에 적힌 납부 방법을 확인하세요. (Check the payment methods written on the bill.)",
                "금액, 명의, 기한이 헷갈리면 국민건강보험공단에 문의하세요. (If the amount, name, or deadline is confusing, contact the National Health Insurance Service.)",
                "납부 후에는 영수증이나 납부 완료 내역을 확인하세요. (After paying, check the receipt or payment completion record.)",
            ],
            "visit_or_online": [
                "국민건강보험공단 고객센터나 지사에 고지서 내용을 문의하세요. (Ask the NHIS call center or branch about the bill details.)",
                "온라인 또는 앱에서 납부 내역을 확인할 수 있는지 확인하세요. (Check whether you can view payment history online or in an app.)",
            ],
            "after_checks": [
                "납부 후 처리 여부를 확인하세요. (Check whether the payment was processed after you pay.)",
                "다음 달에도 같은 방식으로 고지서가 나오는지 확인하세요. (Check whether the bill is issued the same way next month.)",
            ],
        },
        "checklist": [
            "건강보험 고지서 원본 (Original health insurance bill)",
            "외국인등록증 또는 여권 (Alien registration card or passport)",
            "납부할 금액과 기한 메모 (Payment amount and deadline note)",
            "납부 영수증 또는 납부 내역 (Receipt or payment record)",
        ],
        "korean_expressions": {
            "office": "건강보험 고지서 금액과 납부 기한을 확인하고 싶습니다. (I would like to check the health insurance bill amount and payment deadline.)",
            "phone": "고지서가 제 명의인지, 어떻게 납부해야 하는지 알고 싶습니다. (I want to know whether the bill is in my name and how I should pay it.)",
            "message": "건강보험 고지서 납부 방법과 납부 후 확인 방법을 안내해주세요. (Please tell me how to pay the health insurance bill and how to confirm payment afterward.)",
        },
    },
    SUB_PUBLIC_HEALTH_VACCINATION: {
        "action_plan": {
            "first_checks": [
                "받고 싶은 예방접종 종류를 확인하세요. (Check which vaccination you want to receive.)",
                "본인의 나이, 체류자격, 거주 지역을 정리하세요. (Organize your age, visa status, and residence area.)",
            ],
            "todo_steps": [
                "관할 보건소에 전화해 외국인도 대상인지 확인하세요. (Call your local public health center to ask whether foreigners are eligible.)",
                "무료 여부는 지역, 나이, 체류자격, 접종 종류에 따라 다를 수 있어요. (Free eligibility can vary by region, age, visa status, and vaccine type.)",
                "보건소에 대상 여부를 먼저 확인하세요. (Ask the public health center to check your eligibility first.)",
                "예약이 필요한지와 가져갈 서류를 확인하세요. (Ask whether an appointment is needed and what documents to bring.)",
            ],
            "visit_or_online": [
                "보건소 홈페이지나 전화로 접종 가능 날짜를 확인하세요. (Check available vaccination dates on the public health center website or by phone.)",
                "방문 전 신분증과 예방접종 기록이 필요한지 확인하세요. (Before visiting, ask whether ID and vaccination records are needed.)",
            ],
            "after_checks": [
                "접종 후 이상 반응 안내를 확인하세요. (After vaccination, check the guidance for possible side effects.)",
                "다음 접종 일정이 필요한지 확인하세요. (Ask whether another vaccination date is needed.)",
            ],
        },
        "checklist": [
            "외국인등록증 또는 여권 (Alien registration card or passport)",
            "거주지 정보 (Residence information)",
            "기존 예방접종 기록 (Previous vaccination record)",
            "문의할 접종 이름 (Name of the vaccine to ask about)",
        ],
        "korean_expressions": {
            "office": "외국인도 이 예방접종 대상자인지 확인하고 싶습니다. (I would like to check whether foreigners are eligible for this vaccination.)",
            "phone": "무료 접종 대상인지, 예약이 필요한지 알고 싶습니다. (I want to know whether I am eligible for a free vaccination and whether I need an appointment.)",
            "message": "예방접종 대상 조건과 준비물을 안내해주세요. (Please tell me the vaccination eligibility conditions and required documents.)",
        },
    },
    SUB_MEDICAL_COST_INSURANCE: {
        "action_plan": {
            "first_checks": [
                "진료비 내역서와 영수증을 확인하세요. (Check the itemized medical bill and receipt.)",
                "건강보험 자격이 적용됐는지 확인하세요. (Check whether your health insurance eligibility was applied.)",
            ],
            "todo_steps": [
                "병원 원무과에 보험 적용 여부와 본인부담금을 물어보세요. (Ask the hospital billing desk about coverage and your out-of-pocket cost.)",
                "건강보험 자격이 헷갈리면 국민건강보험공단에 문의하세요. (If your insurance eligibility is unclear, contact NHIS.)",
                "환급 가능성이 있으면 필요한 서류를 확인하세요. (If a refund may be possible, check the required documents.)",
            ],
            "visit_or_online": [
                "병원 원무과에서 진료비 세부 내역서를 요청하세요. (Ask the hospital billing desk for an itemized bill.)",
                "공단 홈페이지나 고객센터에서 자격 상태를 확인하세요. (Check your eligibility through the NHIS website or call center.)",
            ],
            "after_checks": [
                "납부 후 영수증을 보관하세요. (Keep the receipt after payment.)",
                "보험 자격이 수정되면 병원 비용이 다시 계산되는지 확인하세요. (If your insurance eligibility changes, ask whether the hospital cost can be recalculated.)",
            ],
        },
        "checklist": [
            "진료비 영수증 또는 청구서 (Medical receipt or bill)",
            "외국인등록증 또는 여권 (Alien registration card or passport)",
            "건강보험 자격 확인 자료 (Health insurance eligibility information)",
            "환급 문의에 필요한 계좌 정보 (Bank account information for refund inquiries)",
        ],
        "korean_expressions": {
            "office": "이 진료비에 건강보험이 적용되었는지 확인하고 싶습니다. (I would like to check whether health insurance was applied to this medical bill.)",
            "phone": "제 건강보험 자격이 현재 유효한지 알고 싶습니다. (I want to know whether my health insurance eligibility is currently valid.)",
            "message": "의료비 본인부담금과 보험 적용 여부를 안내해주세요. (Please tell me the out-of-pocket cost and whether insurance applies.)",
        },
    },
    SUB_AMBIGUOUS: {
        "action_plan": {
            "first_checks": [
                "아픈 부위와 필요한 도움을 한 문장으로 정리해보세요. (Try to summarize the painful area and the help you need in one sentence.)",
            ],
            "todo_steps": [
                "증상이 있으면 병원/약국 안내를 선택하세요. (If you have symptoms, choose clinic/pharmacy guidance.)",
                "고지서나 보험료 문제라면 건강보험 안내를 선택하세요. (If it is about a bill or premium, choose health insurance guidance.)",
                "예방접종이나 보건소 서비스라면 보건소 안내를 선택하세요. (If it is about vaccination or public health center services, choose public health center guidance.)",
            ],
            "visit_or_online": [
                "질문을 조금 더 구체적으로 다시 입력해보세요. (Try entering the question again with more detail.)",
            ],
            "after_checks": [
                "위급한 증상이 있으면 119 또는 응급실에 먼저 문의하세요. (If there are urgent symptoms, contact 119 or an emergency room first.)",
            ],
        },
        "checklist": [
            "증상 또는 문의 목적 (Symptoms or inquiry purpose)",
            "신분증 (ID)",
            "관련 문서 또는 고지서 (Related document or bill)",
        ],
        "korean_expressions": {
            "office": "어떤 의료 안내를 받아야 할지 잘 모르겠습니다. (I am not sure what kind of medical guidance I need.)",
            "phone": "제 상황을 설명하면 어디에 문의해야 하는지 알려주실 수 있나요? (If I explain my situation, can you tell me where I should ask?)",
            "message": "제 상황에 맞는 문의처를 안내해주세요. (Please tell me the right place to contact for my situation.)",
        },
    },
}


def get_fallback_bundle(sub_category: str) -> dict[str, object]:
    return FALLBACK_BUNDLES.get(sub_category, FALLBACK_BUNDLES[SUB_AMBIGUOUS])


def get_primary_source(sub_category: str) -> str | None:
    return PRIMARY_SOURCE_BY_SUBCATEGORY.get(sub_category)


def format_context(docs: list[Document]) -> str:
    if not docs:
        return (
            "관련 문서를 찾지 못했습니다. 공식 안내를 확인해야 한다는 전제로만 "
            "조심스럽게 안내해주세요."
        )

    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        sub_category = doc.metadata.get("sub_category", "unknown")
        parts.append(
            f"[source={source} | sub_category={sub_category}]\n{doc.page_content}"
        )
    return "\n\n".join(parts)


def merge_medical_warnings(
    extra_warnings: list[str],
    sub_category: str,
    user_input: str,
) -> list[str]:
    warnings = list(WARNING_BY_SUBCATEGORY.get(sub_category, WARNING_BY_SUBCATEGORY[SUB_AMBIGUOUS]))
    for warning in extra_warnings:
        if not warning or is_no_docs_warning(warning):
            continue
        if warning not in warnings:
            warnings.append(warning)
    return warnings


def is_no_docs_warning(warning: str) -> bool:
    return warning == NO_DOCS_WARNING or "관련 문서를 충분히 찾지 못했습니다" in warning


def format_medical_checklist(items: list[str]) -> str:
    normalized_items = [str(item).strip() for item in items if str(item).strip()]
    return "  \n".join(f"□ {item}" for item in normalized_items)


def build_final_answer(
    sub_category: str,
    action_plan: dict[str, list[str]],
    checklist: list[str],
    korean_expressions: dict[str, str],
    warnings: list[str],
    sources: list[str],
) -> str:
    del sources  # Sources stay in CategoryResult, but final_answer does not print them.

    checklist_section = format_medical_checklist(checklist)
    expression_heading = EXPRESSION_HEADING_BY_SUBCATEGORY.get(
        sub_category,
        EXPRESSION_HEADING_BY_SUBCATEGORY[SUB_AMBIGUOUS],
    )

    sections = [
        INTRO_BY_SUBCATEGORY.get(sub_category, INTRO_BY_SUBCATEGORY[SUB_AMBIGUOUS]),
        "",
        "## 상황 분류",
        f"의료 / {sub_category}",
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
    ]

    if checklist_section:
        sections.extend(
            [
                "## 준비물 체크리스트",
                checklist_section,
                "",
            ]
        )

    sections.extend(
        [
            f"## {expression_heading}",
            "아래 문장은 현장에서 직원에게 직접 말하거나 보여주면 됩니다. (You can say or show the sentences below to staff on site.)",
            f'- 기관에서 말할 문장:\n  "{korean_expressions.get("office", "")}"',
            f'- 전화로 물어볼 문장:\n  "{korean_expressions.get("phone", "")}"',
            f'- 문자/이메일 문장:\n  "{korean_expressions.get("message", "")}"',
            "",
            "## 주의사항",
            format_bullets(warnings),
        ]
    )

    return "\n".join(sections)
