from test.test_retriever_admin import TEST_CASES as ADMIN_CASES
from test.test_retriever_traffic import TEST_CASES as TRAFFIC_CASES
from test.test_support import run_retriever_cases

SMOKE_CASES = [
    *ADMIN_CASES,
    *TRAFFIC_CASES,
]


def main() -> None:
    run_retriever_cases("retriever_smoke", SMOKE_CASES)


if __name__ == "__main__":
    main()
