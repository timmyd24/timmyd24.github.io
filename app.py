# Add this constant for the welcome message
WELCOME_MESSAGE = (
    "TRITON is an AI-based secure MTP interpreter project done by ME4 Tan Chee Wei, "
    "ME2 Dean Lee & ME1 Timothy David. TRITON is a tool meant to decode / encode signals "
    "in the MTP using AI and LLM Technology."
)

# Update the main function to include the welcome message
def main():
    # Check if multi-agent settings are defined
    multi_agents = os.environ.get("OPENAI_ASSISTANTS", None)
    single_agent_id = os.environ.get("ASSISTANT_ID", None)
    single_agent_title = os.environ.get("ASSISTANT_TITLE", "Assistants API UI")

    if (
        authentication_required
        and "credentials" in st.secrets
        and authenticator is not None
    ):
        authenticator.login()
        if not st.session_state["authentication_status"]:
            login()
            return
        else:
            authenticator.logout(location="sidebar")

    # Check and add welcome message to chat log if it's empty
    if "chat_log" not in st.session_state or not st.session_state.chat_log:
        st.session_state.chat_log = [{"name": "TRITON", "msg": WELCOME_MESSAGE}]

    if multi_agents:
        assistants_json = json.loads(multi_agents)
        assistants_object = {f'{obj["title"]}': obj for obj in assistants_json}
        selected_assistant = st.sidebar.selectbox(
            "Select an assistant profile?",
            list(assistants_object.keys()),
            index=None,
            placeholder="Select an assistant profile...",
            on_change=reset_chat,  # Call the reset function on change
        )
        if selected_assistant:
            load_chat_screen(
                assistants_object[selected_assistant]["id"],
                assistants_object[selected_assistant]["title"],
            )
    elif single_agent_id:
        load_chat_screen(single_agent_id, single_agent_title)
    else:
        st.error("No assistant configurations defined in environment variables.")

