import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from localmate_graph import run_localmate_result

DB_DIR = Path("chroma_db")

@dataclass(frozen=True)
class TestCase:
    name: str
    query: str
    category: str
    sub_category: str
    needs_clarification: bool
    contains: tuple[str, ...]


TEST_CASES = [
    TestCase(
        name="admin_alien_card_loss",
        query="외국인등록증을 잃어버렸어요. 어떻게 해야 하나요?",
        category="admin",
        sub_category="외국인등록증 분실",
        needs_clarification=False,
        contains=(
            "행정 / 외국인등록증 분실",
            "준비물 체크리스트",
            "기관에서 사용할 한국어",
            "admin/admin_alien_card_loss.md",
        ),
    ),
    TestCase(
        name="admin_card_ambiguous",
        query="카드를 잃어버렸어요.",
        category="admin",
        sub_category="애매함",
        needs_clarification=True,
        contains=(
            "어떤 카드를 잃어버리셨나요?",
            "1. 외국인등록증",
            "3. 교통카드/티머니",
        ),
    ),
    TestCase(
        name="traffic_transport_card",
        query="교통카드는 어디서 충전해요?",
        category="traffic",
        sub_category="교통카드/결제",
        needs_clarification=False,
        contains=(
            "교통 / 교통카드/결제",
            "교통카드 충전하고 싶어요.",
            "traffic/transport_card.md",
        ),
    ),
    TestCase(
        name="traffic_bus_transfer",
        query="버스에서 내릴 때도 카드를 찍어야 해요?",
        category="traffic",
        sub_category="버스 이용/환승",
        needs_clarification=False,
        contains=(
            "교통 / 버스 이용/환승",
            "하차 태그",
            "traffic/bus_transfer.md",
        ),
    ),
    TestCase(
        name="traffic_taxi_usage",
        query="택시 기사님에게 한양대 ERICA로 가달라고 말하고 싶어요.",
        category="traffic",
        sub_category="택시 이용",
        needs_clarification=False,
        contains=(
            "교통 / 택시 이용",
            "한양대 ERICA 정문으로 가주세요.",
            "카드 결제 가능해요?",
            "traffic/taxi_usage.md",
        ),
    ),
    TestCase(
        name="traffic_fixed_place_route",
        query="중앙역에서 한양대 ERICA 어떻게 가요?",
        category="traffic",
        sub_category="고정 장소 이동",
        needs_clarification=False,
        contains=(
            "교통 / 고정 장소 이동",
            "출발지: 중앙역",
            "목적지: 한양대 ERICA",
            "지도 앱 또는 정류장 안내기",
            "traffic/ansan_fixed_places_guide.md",
        ),
    ),
    TestCase(
        name="traffic_missing_origin",
        query="한양대 ERICA 가고 싶어요.",
        category="traffic",
        sub_category="고정 장소 이동",
        needs_clarification=True,
        contains=(
            "출발지가 어디인가요?",
            "중앙역, 한대앞역, 한양대 ERICA 중에서 알려주세요.",
        ),
    ),
    TestCase(
        name="traffic_realtime_arrival",
        query="지금 버스 몇 분 뒤에 와요?",
        category="traffic",
        sub_category="버스 이용/환승",
        needs_clarification=True,
        contains=(
            "실시간 버스 도착 시간",
            "정류장 안내기나 지도 앱",
            "이 버스 언제 와요?",
        ),
    ),
    TestCase(
        name="traffic_over_medical",
        query="병원에 버스로 어떻게 가요?",
        category="traffic",
        sub_category="버스 이용/환승",
        needs_clarification=True,
        contains=("출발지와 목적지가 어디인가요?",),
    ),
    TestCase(
        name="medical_general",
        query="기침이 있고 열이 나요.",
        category="medical",
        sub_category="일반 진료/약국",
        needs_clarification=False,
        contains=("의료 / 일반 진료/약국", "약국은 어디에 있나요?"),
    ),
]


def ensure_ready() -> None:
    load_dotenv()

    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(".env 파일에 GOOGLE_API_KEY를 설정해주세요.")

    if not DB_DIR.exists():
        raise RuntimeError("먼저 python build_vector_db.py를 실행해주세요.")


def validate_case(case: TestCase) -> list[str]:
    result = run_localmate_result(case.query)
    failures: list[str] = []

    if result.category != case.category:
        failures.append(f"category expected={case.category} actual={result.category}")

    if result.sub_category != case.sub_category:
        failures.append(
            f"sub_category expected={case.sub_category} actual={result.sub_category}"
        )

    if result.needs_clarification != case.needs_clarification:
        failures.append(
            "needs_clarification "
            f"expected={case.needs_clarification} actual={result.needs_clarification}"
        )

    answer = result.answer
    for expected_text in case.contains:
        if expected_text not in answer:
            failures.append(f"missing text: {expected_text}")

    return failures


def main() -> None:
    ensure_ready()

    passed = 0
    total = len(TEST_CASES)

    for case in TEST_CASES:
        failures = validate_case(case)
        if failures:
            print(f"[FAIL] {case.name}")
            for failure in failures:
                print(f"  - {failure}")
            print(f"  query: {case.query}")
            print()
            continue

        passed += 1
        print(f"[PASS] {case.name}")

    print()
    print(f"summary: {passed}/{total} passed")

    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(exc)
        raise SystemExit(1)
    except Exception:
        print("LocalMate 답변 테스트 중 오류가 발생했습니다. 설정과 chroma_db 상태를 확인해주세요.")
        raise SystemExit(1)
