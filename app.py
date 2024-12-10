import os
import base64
import re
import json

import streamlit as st
import openai
from openai import AssistantEventHandler
from tools import TOOL_MAP
from typing_extensions import override
from dotenv import load_dotenv
import streamlit_authenticator as stauth

load_dotenv()


def str_to_bool(str_input):
    if not isinstance(str_input, str):
        return False
    return str_input.lower() == "true"


# Load environment variables
openai_api_key = os.environ.get("OPENAI_API_KEY")
instructions = os.environ.get("RUN_INSTRUCTIONS", "")
enabled_file_upload_message = os.environ.get(
    "ENABLED_FILE_UPLOAD_MESSAGE", "Upload a file"
)
azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
azure_openai_key = os.environ.get("AZURE_OPENAI_KEY")
authentication_required = str_to_bool(os.environ.get("AUTHENTICATION_REQUIRED", False))

# Load authentication configuration
if authentication_required:
    if "credentials" in st.secrets:
        authenticator = stauth.Authenticate(
            st.secrets["credentials"].to_dict(),
            st.secrets["cookie"]["name"],
            st.secrets["cookie"]["key"],
            st.secrets["cookie"]["expiry_days"],
        )
    else:
        authenticator = None  # No authentication should be performed

client = None
if azure_openai_endpoint and azure_openai_key:
    client = openai.AzureOpenAI(
        api_key=azure_openai_key,
        api_version="2024-05-01-preview",
        azure_endpoint=azure_openai_endpoint,
    )
else:
    client = openai.OpenAI(api_key=openai_api_key)


class EventHandler(AssistantEventHandler):
    @override
    def on_event(self, event):
        pass

    @override
    def on_text_created(self, text):
        st.session_state.current_message = ""
        with st.chat_message("Assistant"):
            st.session_state.current_markdown = st.empty()

    @override
    def on_text_delta(self, delta, snapshot):
        if snapshot.value:
            text_value = re.sub(
                r"\[(.*?)\]\s*\(\s*(.*?)\s*\)", "Download Link", snapshot.value
            )
            st.session_state.current_message = text_value
            st.session_state.current_markdown.markdown(
                st.session_state.current_message, True
            )

    @override
    def on_text_done(self, text):
        format_text = format_annotation(text)
        st.session_state.current_markdown.markdown(format_text, True)
        st.session_state.chat_log.append({"name": "assistant", "msg": format_text})

    @override
    def on_tool_call_created(self, tool_call):
        if tool_call.type == "code_interpreter":
            st.session_state.current_tool_input = ""
            with st.chat_message("Assistant"):
                st.session_state.current_tool_input_markdown = st.empty()

    @override
    def on_tool_call_done(self, tool_call):
        st.session_state.tool_calls.append(tool_call)


def create_thread(content, file):
    return client.beta.threads.create()


def create_message(thread, content, file):
    attachments = []
    if file is not None:
        attachments.append(
            {"file_id": file.id, "tools": [{"type": "code_interpreter"}, {"type": "file_search"}]}
        )
    client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=content, attachments=attachments
    )


def handle_uploaded_file(uploaded_file):
    file = client.files.create(file=uploaded_file, purpose="assistants")
    return file


def format_annotation(text):
    citations = []
    text_value = text.value
    for index, annotation in enumerate(text.annotations):
        text_value = text_value.replace(annotation.text, f" [{index}]")

        if file_citation := getattr(annotation, "file_citation", None):
            cited_file = client.files.retrieve(file_citation.file_id)
            citations.append(
                f"[{index}] {file_citation.quote} from {cited_file.filename}"
            )
    text_value += "\n\n" + "\n".join(citations)
    return text_value


# Dynamic welcome messages
WELCOME_MESSAGES = {
    "TRITON": (
        "TRITON is a trial prototype designed to translate plain intentions into coded tactical signals using MTP. "
        "It is also envisioned as a learning tool to aid personnel in learning how to use MTP for tactical signals. "
        "Additionally, TRITON is capable of encoding and decoding MTP signals, making it an invaluable tool for tactical communication. "
        "Joint project by Timothy David, Dean Lee & Tan Chee Wei."
    ),
    "GENERAL ASSISTANT (UNCLASSIFIED)": (
        "Welcome to the General Assistant. This assistant is equipped to handle a variety of tasks, "
        "ranging from answering questions to helping with research and day-to-day inquiries. "
        "Feel free to ask anything!"
    ),
}


def render_chat(selected_assistant):
    # Determine the welcome message based on the selected assistant
    welcome_message = WELCOME_MESSAGES.get(selected_assistant, "Welcome! How can I assist you today?")

    if not st.session_state.chat_log:
        st.session_state.chat_log.append({"name": selected_assistant, "msg": welcome_message})

    for chat in st.session_state.chat_log:
        with st.chat_message(chat["name"]):
            st.markdown(chat["msg"], True)


def run_stream(user_input, file, selected_assistant_id):
    if "thread" not in st.session_state:
        st.session_state.thread = create_thread(user_input, file)
    create_message(st.session_state.thread, user_input, file)
    with client.beta.threads.runs.stream(
        thread_id=st.session_state.thread.id,
        assistant_id=selected_assistant_id,
        event_handler=EventHandler(),
    ) as stream:
        stream.until_done()


def reset_chat():
    st.session_state.chat_log = []
    st.session_state.in_progress = False


def load_chat_screen(assistant_id, assistant_title):
    uploaded_file = st.sidebar.file_uploader(
        enabled_file_upload_message,
        type=["txt", "pdf", "csv", "json", "geojson", "xlsx", "xls"],
    )

    st.title(assistant_title if assistant_title else "")
    user_msg = st.chat_input("Message", on_submit=reset_chat)

    render_chat(assistant_title)

    if user_msg:
        with st.chat_message("user"):
            st.markdown(user_msg, True)
        st.session_state.chat_log.append({"name": "user", "msg": user_msg})

        file = None
        if uploaded_file is not None:
            file = handle_uploaded_file(uploaded_file)
        run_stream(user_msg, file, assistant_id)
        st.rerun()


def main():
    multi_agents = os.environ.get("OPENAI_ASSISTANTS", None)

    if multi_agents:
        assistants_json = json.loads(multi_agents)
        assistants_object = {obj["title"]: obj for obj in assistants_json}

        selected_assistant = st.sidebar.selectbox(
            "Select an assistant profile",
            list(assistants_object.keys()),
            index=None,
            on_change=reset_chat,
        )

        if selected_assistant:
            load_chat_screen(
                assistants_object[selected_assistant]["id"],
                assistants_object[selected_assistant]["title"],
            )


if __name__ == "__main__":
    main()
