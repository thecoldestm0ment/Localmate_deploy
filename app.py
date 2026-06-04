from pathlib import Path

import streamlit as st

from localmate_graph import run_localmate

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
EXAMPLE_QUESTIONS = [
    "외국인등록증을 잃어버렸어요. 어떻게 해야 해요?",
    "이사했는데 주소 변경 신고를 해야 하나요?",
    "비자 기간이 곧 끝나요. 뭘 해야 해요?",
    "밤늦게 갑자기 아프면 응급실 가야 하나요?",
    "건강 보험 고지서가 나왔어요 어떻게 해야 돼요?",
    "외국인도 보건소에서 무료로 예방접종을 받을 수 있나요?",
    "교통카드는 어디서 충전해요?",
    "버스에서 내릴 때도 카드를 찍어야 해요?",
    "중앙역에서 한양대 ERICA 어떻게 가요?",
    "택시 기사님에게 한양대 ERICA로 가달라고 말하고 싶어요.",
    "막차를 놓쳤어요. 어떻게 해야 해요?",
    "카드를 잃어버렸어요.",
]

def ensure_session_state() -> None:
    st.session_state.setdefault("user_input", "")


def render_example_sidebar() -> None:
    st.sidebar.header("예시 질문")
    for index, example in enumerate(EXAMPLE_QUESTIONS, start=1):
        if st.sidebar.button(
            example,
            key=f"example_{index}",
            use_container_width=True,
        ):
            st.session_state["user_input"] = example


def render_answer() -> None:
    user_input = st.session_state["user_input"].strip()
    if not user_input:
        st.warning(EMPTY_INPUT_MESSAGE)
        return

    with st.spinner(LOADING_MESSAGE):
        try:
            answer = run_localmate(user_input)
        except RuntimeError as exc:
            st.error(str(exc))
        except Exception:
            st.error(GENERATION_ERROR_MESSAGE)
        else:
            st.markdown(answer)


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
    render_answer()
