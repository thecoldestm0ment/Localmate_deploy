from pathlib import Path

import streamlit as st

from localmate_graph import run_localmate

DB_DIR = Path("chroma_db")
EXAMPLE_QUESTIONS = [
    "외국인등록증을 잃어버렸어요. 어떻게 해야 해요?",
    "이사했는데 주소 변경 신고를 해야 하나요?",
    "비자 기간이 곧 끝나요. 뭘 해야 해요?",
    "카드를 잃어버렸어요.",
]

st.set_page_config(page_title="LocalMate", page_icon="🏠")

if "user_input" not in st.session_state:
    st.session_state["user_input"] = ""

st.title("🏠 LocalMate")
st.write("외국인 주민을 위한 행정 생활 적응 AI Agent")

st.sidebar.header("예시 질문")
for index, example in enumerate(EXAMPLE_QUESTIONS, start=1):
    if st.sidebar.button(example, key=f"example_{index}", use_container_width=True):
        st.session_state["user_input"] = example

if not DB_DIR.exists():
    st.info("먼저 python build_vector_db.py를 실행해주세요.")

st.text_area(
    "행정 상황을 입력해주세요.",
    key="user_input",
    height=160,
    placeholder="예: 외국인등록증을 잃어버렸어요. 어떻게 해야 하나요?",
)

if st.button("안내 받기", use_container_width=True):
    if not st.session_state["user_input"].strip():
        st.warning("질문을 입력해주세요.")
    else:
        with st.spinner("LocalMate가 안내를 준비하고 있습니다..."):
            try:
                answer = run_localmate(st.session_state["user_input"])
            except RuntimeError as exc:
                st.error(str(exc))
            except Exception:
                st.error("안내를 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
            else:
                st.markdown(answer)
