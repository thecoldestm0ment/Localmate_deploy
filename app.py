from pathlib import Path

import streamlit as st

from localmate_graph import run_localmate_result

DB_DIR = Path("chroma_db")
PAGE_TITLE = "LocalMate"
PAGE_ICON = "🏠"
APP_TITLE = "🏠 LocalMate"
APP_DESCRIPTION = "외국인 주민을 위한 생활 적응 AI Agent"
INPUT_LABEL = "상황을 입력해주세요."
INPUT_PLACEHOLDER = "예: 중앙역에서 한양대 ERICA 어떻게 가요?"
LOADING_MESSAGE = "LocalMate가 안내를 준비하고 있습니다..."
MISSING_DB_MESSAGE = "먼저 python build_vector_db.py를 실행해주세요."
EMPTY_INPUT_MESSAGE = "질문을 입력해주세요."
GENERATION_ERROR_MESSAGE = "안내를 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
HISTORY_LIMIT = 20
EXAMPLE_GROUPS = {
    "행정": [
        "외국인등록증을 잃어버렸어요. 어떻게 해야 해요?",
        "이사했는데 주소 변경 신고를 해야 하나요?",
        "비자 기간이 곧 끝나요. 뭘 해야 해요?",
    ],
    "의료": [
        "밤늦게 갑자기 아프면 응급실 가야 하나요?",
        "건강 보험 고지서가 나왔어요 어떻게 해야 돼요?",
        "외국인도 보건소에서 무료로 예방접종을 받을 수 있나요?",
    ],
    "교통": [
        "교통카드는 어디서 충전해요?",
        "버스에서 내릴 때도 카드를 찍어야 해요?",
        "중앙역에서 한양대 ERICA 어떻게 가요?",
        "택시 기사님에게 한양대 ERICA로 가달라고 말하고 싶어요.",
        "막차를 놓쳤어요. 어떻게 해야 해요?",
    ],
    "애매한 질문": [
        "카드를 잃어버렸어요.",
    ],
}


def build_history_item(user_input: str, result) -> dict:
    return {
        "query": user_input,
        "answer": result.answer,
        "category": result.category,
        "sub_category": result.sub_category,
        "needs_clarification": result.needs_clarification,
        "clarifying_question": result.clarifying_question,
        "sources": result.sources,
        "warnings": result.warnings,
        "error": None,
    }


def build_error_item(user_input: str, error_message: str) -> dict:
    return {
        "query": user_input,
        "answer": "",
        "category": None,
        "sub_category": None,
        "needs_clarification": False,
        "clarifying_question": None,
        "sources": (),
        "warnings": (),
        "error": error_message,
    }


def add_history_item(item: dict) -> None:
    st.session_state["history"].insert(0, item)
    del st.session_state["history"][HISTORY_LIMIT:]


def ensure_session_state() -> None:
    st.session_state.setdefault("user_input", "")
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("submit_requested", False)


def render_example_sidebar() -> None:
    st.sidebar.header("예시 질문")
    for group_name, examples in EXAMPLE_GROUPS.items():
        st.sidebar.subheader(group_name)
        for index, example in enumerate(examples, start=1):
            if st.sidebar.button(
                example,
                key=f"example_{group_name}_{index}",
                use_container_width=True,
            ):
                st.session_state["user_input"] = example
                st.session_state["submit_requested"] = True


def submit_current_input() -> None:
    user_input = st.session_state["user_input"].strip()
    if not user_input:
        st.warning(EMPTY_INPUT_MESSAGE)
        return

    with st.spinner(LOADING_MESSAGE):
        try:
            result = run_localmate_result(user_input)
        except RuntimeError as exc:
            add_history_item(build_error_item(user_input, str(exc)))
        except Exception:
            add_history_item(build_error_item(user_input, GENERATION_ERROR_MESSAGE))
        else:
            add_history_item(build_history_item(user_input, result))


def render_result_meta(item: dict) -> None:
    category = item.get("category") or "미분류"
    sub_category = item.get("sub_category") or "-"
    status = "확인 질문" if item.get("needs_clarification") else "답변"
    st.caption(f"{status} · {category} / {sub_category}")


def render_history() -> None:
    if not st.session_state["history"]:
        return

    st.divider()
    st.subheader("답변 히스토리")
    for index, item in enumerate(st.session_state["history"], start=1):
        with st.container():
            st.markdown(f"**질문 {index}.** {item['query']}")
            render_result_meta(item)
            if item.get("error"):
                st.error(item["error"])
            else:
                st.markdown(item["answer"])
        if index < len(st.session_state["history"]):
            st.divider()


st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON)
ensure_session_state()

st.title(APP_TITLE)
st.write(APP_DESCRIPTION)

render_example_sidebar()

if not DB_DIR.exists():
    st.info(MISSING_DB_MESSAGE)

st.text_area(
    INPUT_LABEL,
    key="user_input",
    height=180,
    placeholder=INPUT_PLACEHOLDER,
)

if st.button("안내 받기", use_container_width=True):
    submit_current_input()

if st.session_state["submit_requested"]:
    st.session_state["submit_requested"] = False
    submit_current_input()

render_history()
