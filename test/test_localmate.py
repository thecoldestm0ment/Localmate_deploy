from test_localmate_admin import TEST_CASES as ADMIN_CASES
from test_localmate_medical import TEST_CASES as MEDICAL_CASES
from test_localmate_traffic import TEST_CASES as TRAFFIC_CASES
from test_support import run_localmate_cases

SMOKE_CASES = [
    *ADMIN_CASES,
    *MEDICAL_CASES,
    *TRAFFIC_CASES,
]


def main() -> None:
    run_localmate_cases("localmate_smoke", SMOKE_CASES)


if __name__ == "__main__":
    main()
