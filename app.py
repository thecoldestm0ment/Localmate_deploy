from pathlib import Path

import streamlit as st

from localmate_graph import run_localmate_result

DB_DIR = Path("chroma_db")
PAGE_TITLE = "LocalMate"
PAGE_ICON = "🏠"
APP_TITLE = "🏠 LocalMate"
APP_DESCRIPTION = "외국인 주민을 위한 행정·의료·교통 생활 적응 AI Agent"

MISSING_DB_MESSAGE = "먼저 python build_vector_db.py를 실행해주세요."
EMPTY_INPUT_MESSAGE = "질문을 입력해주세요."
LOADING_MESSAGE = "LocalMate가 안내를 준비하고 있어요..."
GENERATION_ERROR_MESSAGE = (
    "안내를 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도하거나 설정을 확인해주세요."
)

CHAT_HISTORY_LIMIT = 12
QUESTION_MODE_NEW = "new"
QUESTION_MODE_FOLLOW_UP = "follow_up"
QUESTION_MODE_LABELS = {
    "새 질문": QUESTION_MODE_NEW,
    "후속 질문": QUESTION_MODE_FOLLOW_UP,
}
QUESTION_MODE_LABEL_BY_VALUE = {
    value: label for label, value in QUESTION_MODE_LABELS.items()
}
EXAMPLE_GROUPS = {
    "행정": [
        "외국인등록증을 잃어버렸어요. 어떻게 해야 해요?",
        "이사했는데 주소 변경 신고를 해야 하나요?",
        "비자 기간이 곧 끝나요. 뭘 해야 해요?",
    ],
    "의료": [
        "배가 갑자기 아프면 응급실에 가야 하나요?",
        "건강보험 고지서가 어려워요. 어떻게 해야 해요?",
        "외국인도 보건소에서 예방접종을 받을 수 있나요?",
    ],
    "교통": [
        "교통카드는 어디서 충전해요?",
        "버스에서 내릴 때도 카드를 찍어야 해요?",
        "중앙역에서 한양대 ERICA 어떻게 가요?",
        "택시 기사님에게 한양대 ERICA로 가달라고 말하고 싶어요.",
        "막차를 놓쳤어요. 어떻게 해야 해요?",
    ],
    "후속 질문": [
        "준비물만 다시 알려줘",
        "짧게 알려줘",
        "기관에 뭐라고 말해?",
        "카드를 잃어버렸어요.",
    ],
}


def ensure_session_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("previous_category", None)
    st.session_state.setdefault("previous_sub_category", None)
    st.session_state.setdefault("previous_answer_summary", None)
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("chat_prompt", "")
    st.session_state.setdefault("selected_question_mode", QUESTION_MODE_NEW)
    st.session_state.setdefault(
        "question_mode_label",
        QUESTION_MODE_LABEL_BY_VALUE[QUESTION_MODE_NEW],
    )
    st.session_state.setdefault("last_question_mode", QUESTION_MODE_NEW)


def build_context(question_mode: str) -> dict:
    if question_mode == QUESTION_MODE_NEW:
        previous_category = None
        previous_sub_category = None
        previous_answer_summary = None
    else:
        previous_category = st.session_state["previous_category"]
        previous_sub_category = st.session_state["previous_sub_category"]
        previous_answer_summary = st.session_state["previous_answer_summary"]

    return {
        "previous_category": previous_category,
        "previous_sub_category": previous_sub_category,
        "previous_answer_summary": previous_answer_summary,
        "chat_history": st.session_state["chat_history"][-6:],
        "question_mode": question_mode,
    }


def fill_example_prompt(example: str, mode: str) -> None:
    st.session_state["chat_prompt"] = example
    st.session_state["selected_question_mode"] = mode
    st.session_state["question_mode_label"] = QUESTION_MODE_LABEL_BY_VALUE[mode]


def render_example_sidebar() -> None:
    st.sidebar.header("예시 질문")
    for group_name, examples in EXAMPLE_GROUPS.items():
        st.sidebar.subheader(group_name)
        for index, example in enumerate(examples, start=1):
            mode = (
                QUESTION_MODE_FOLLOW_UP
                if group_name == "후속 질문"
                else QUESTION_MODE_NEW
            )
            st.sidebar.button(
                example,
                key=f"example_{group_name}_{index}",
                use_container_width=True,
                on_click=fill_example_prompt,
                args=(example, mode),
            )

    st.sidebar.divider()
    if st.sidebar.button("대화 초기화", use_container_width=True):
        reset_chat()
        st.rerun()


def reset_chat() -> None:
    st.session_state["messages"] = []
    st.session_state["previous_category"] = None
    st.session_state["previous_sub_category"] = None
    st.session_state["previous_answer_summary"] = None
    st.session_state["chat_history"] = []
    st.session_state["chat_prompt"] = ""
    st.session_state["selected_question_mode"] = QUESTION_MODE_NEW
    st.session_state["question_mode_label"] = (
        QUESTION_MODE_LABEL_BY_VALUE[QUESTION_MODE_NEW]
    )
    st.session_state["last_question_mode"] = QUESTION_MODE_NEW


def append_user_message(content: str) -> None:
    mode_label = QUESTION_MODE_LABEL_BY_VALUE.get(
        st.session_state["last_question_mode"],
        "새 질문",
    )
    st.session_state["messages"].append(
        {
            "role": "user",
            "content": content,
            "question_mode": st.session_state["last_question_mode"],
            "mode_label": mode_label,
        }
    )


def append_assistant_message(result) -> None:
    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": result.answer,
            "category": result.category,
            "sub_category": result.sub_category,
            "sources": result.sources,
            "warnings": result.warnings,
            "answer_mode": result.answer_mode,
            "needs_clarification": result.needs_clarification,
        }
    )


def append_error_message(message: str) -> None:
    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": message,
            "error": True,
            "sources": (),
        }
    )


def update_context_memory(user_input: str, result) -> None:
    if result.category:
        st.session_state["previous_category"] = result.category
    if result.sub_category:
        st.session_state["previous_sub_category"] = result.sub_category
    if result.answer_summary:
        st.session_state["previous_answer_summary"] = result.answer_summary

    st.session_state["chat_history"].append(
        {
            "user": user_input,
            "assistant": result.answer,
            "answer_summary": result.answer_summary,
            "category": result.category,
            "sub_category": result.sub_category,
            "answer_mode": result.answer_mode,
            "question_mode": st.session_state["last_question_mode"],
        }
    )
    del st.session_state["chat_history"][:-CHAT_HISTORY_LIMIT]


def clear_routing_context() -> None:
    st.session_state["previous_category"] = None
    st.session_state["previous_sub_category"] = None
    st.session_state["previous_answer_summary"] = None


def handle_prompt(prompt: str, question_mode: str) -> None:
    user_input = prompt.strip()
    if not user_input:
        st.warning(EMPTY_INPUT_MESSAGE)
        return

    st.session_state["last_question_mode"] = question_mode
    if question_mode == QUESTION_MODE_NEW:
        clear_routing_context()

    append_user_message(user_input)

    if not DB_DIR.exists():
        append_error_message(MISSING_DB_MESSAGE)
        return

    with st.spinner(LOADING_MESSAGE):
        try:
            result = run_localmate_result(
                user_input,
                context=build_context(question_mode),
            )
        except RuntimeError as exc:
            append_error_message(str(exc))
        except Exception:
            append_error_message(GENERATION_ERROR_MESSAGE)
        else:
            append_assistant_message(result)
            update_context_memory(user_input, result)


def render_messages() -> None:
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            if message["role"] == "user" and message.get("mode_label"):
                st.caption(message["mode_label"])
            if message.get("error"):
                st.error(message["content"])
            else:
                st.markdown(message["content"])
                render_message_meta(message)


def render_message_meta(message: dict) -> None:
    if message["role"] != "assistant":
        return

    category = message.get("category")
    sub_category = message.get("sub_category")
    answer_mode = message.get("answer_mode")
    if category or sub_category:
        st.caption(f"{category or '미분류'} / {sub_category or '-'} · {answer_mode}")

    sources = tuple(message.get("sources") or ())
    if sources:
        with st.expander("참고한 문서 보기"):
            for source in sources:
                st.markdown(f"- `{source}`")


def render_context_status() -> None:
    category = st.session_state["previous_category"]
    sub_category = st.session_state["previous_sub_category"]
    if category and sub_category:
        st.caption(f"현재 이어가는 맥락: {category} / {sub_category}")
    else:
        st.caption("현재 이어가는 맥락: 없음")


st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON)


def render_question_mode_selector() -> str:
    st.write(
        "새로운 상황이면 **새 질문**, 이전 답변에 이어 묻는다면 **후속 질문**을 선택하세요."
    )
    selected_label = st.radio(
        "질문 유형을 선택하세요.",
        options=list(QUESTION_MODE_LABELS.keys()),
        key="question_mode_label",
        horizontal=True,
        label_visibility="collapsed",
    )
    selected_mode = QUESTION_MODE_LABELS[selected_label]
    st.session_state["selected_question_mode"] = selected_mode
    if selected_mode == QUESTION_MODE_NEW:
        st.caption("새 주제로 분류하고 답변합니다.")
    else:
        st.caption("이전 대화 맥락을 유지해서 짧게 답변합니다.")
    return selected_mode


ensure_session_state()

st.title(APP_TITLE)
st.write(APP_DESCRIPTION)

render_example_sidebar()

if not DB_DIR.exists():
    st.info(MISSING_DB_MESSAGE)

render_context_status()
question_mode = render_question_mode_selector()
render_messages()

chat_prompt = st.chat_input(
    "상황을 입력해주세요. 예: 중앙역에서 한양대 ERICA 어떻게 가요?",
    key="chat_prompt",
)
if chat_prompt:
    handle_prompt(chat_prompt, question_mode)
    st.rerun()
