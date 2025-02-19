import asyncio
import logging
from datetime import datetime
from random import shuffle
from time import time
from uuid import uuid4

import gradio as gr

from app.core.config import config as c
from app.core.loggers import setup_logging
from app.datamodel.chat import ChatQuery
from app.datamodel.feedback import Feedback
from app.datamodel.response import ResponseWithSources
from app.services.chatbot import ChatbotService
from app.services.faq import FAQService

setup_logging(
    log_level=c.LOG_LEVEL,
    use_basic_format=c.LOG_USE_BASIC_FORMAT,
)
_LOGGER = logging.getLogger(__name__)

css = """
#logo {
    display: flex;
    float: left;
    width: 5%;
}
#md-title {
    display: flex;
}
.message-buttons-right {
    display: none;
}
.submit-button {
    background-color: #1c4e1f;
    color: white;
}
button.secondary {
    background-color: #1c4e1f;
    color: white;
}
.block {
    border-color: #1c4e1f;
}
.form {
    border-color: #1c4e1f;
}
"""
    # background-color: #1c4e1f;

chatbot = ChatbotService(
    base_url=c.CHATBOT_URL,
    port=c.CHATBOT_PORT
)
faq_service = FAQService(
    base_url=c.CHATBOT_URL,
    port=c.CHATBOT_PORT
)


def clear_history(request: gr.Request, sessions: gr.State):
    if request.session_hash not in sessions:
        _LOGGER.warning("No sessions found")
        return [], []

    sessions.pop(request.session_hash, None)
    gr.Info("Conversation history is already cleared")
    return [], []


def chat(
    message, history, request: gr.Request, sessions: gr.State,
    persona: str, user_id: str = None, language: str = None
):
    if not user_id:
        raise gr.Error(
            "Silakan pilih RM terlebih dahulu. "
            "Kemudian klik \"Clear Conversation\""
        )
        return

    if request.session_hash not in sessions:
        sessions[request.session_hash] = {
            "interaction_id": str(uuid4()),
            "ai_response_id": [],
        }

    _LOGGER.info("%s is chatting with session: %s (%s)",
                 user_id, request.session_hash,
                 sessions[request.session_hash]["interaction_id"])
    response: ResponseWithSources = chatbot.chat(
        query=ChatQuery(
            query=message,
            user_id=user_id,
            session_id=sessions[request.session_hash]["interaction_id"]
        )
    )
    sessions[request.session_hash]["ai_response_id"].append(response.message_id)
    return response.response


async def chat_with_llm(
    message, history, request: gr.Request, sessions: gr.State,
    persona: str, user_id: str = None, language: str = None
):
    """
    Handles chat interaction with the LLM for Gradio's ChatInterface.
    Args:
        message (str): Current user message
        history (list): List of (user_message, assistant_message) tuples
    Yields:
        str: Streamed response chunks for ChatInterface
    """
    _LOGGER.info("Persona: %s, Language: %s, User: %s",
                 persona, language, user_id)
    if not user_id:
        raise gr.Error(
            "Silakan pilih RM terlebih dahulu. "
            "Kemudian klik \"Clear Conversation\""
        )
        return
    if request.session_hash not in sessions:
        sessions[request.session_hash] = {
            "interaction_id": str(uuid4()),
            "ai_response_id": [],
        }
    _LOGGER.info("%s is chatting with session: %s (%s)",
                 user_id, request.session_hash,
                 sessions[request.session_hash]["interaction_id"])

    response_text = ""
    try:
        _LOGGER.info("Incoming stream response..")
        async for chunk in chatbot.stream_gemini(
            query=ChatQuery(
                query=message,
                session_id=sessions[request.session_hash]["interaction_id"],
                persona=persona,
                user_id=user_id,
                language=language,
            )
        ):
            if isinstance(chunk, tuple):
                session_id, message_id = chunk
                sessions[request.session_hash][
                    "ai_response_id"
                ].append(message_id)
            elif chunk:
                response_text += chunk
                clean_response = response_text.strip()
                yield clean_response
                await asyncio.sleep(0.05)  # Small delay for smoother streaming

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        _LOGGER.exception("Exception occurred: %s", error_msg)
        yield error_msg
        return

    # Handle case where no response was generated
    if not response_text.strip():
        _LOGGER.warning("No response generated")
        yield "No response generated."

    _LOGGER.info("Chat interaction complete")


def send_feedback(
    feedback: gr.LikeData, request: gr.Request, message: list[list[str]],
    user_id: str, sessions: gr.State,
):
    response = ""
    input_query = ""
    for interaction_idx, interaction in enumerate(message):
        if interaction_idx == feedback.index[0]:
            if feedback.index[1] == 1:
                response = interaction[1]
            ai_response_id = sessions[request.session_hash][
                "ai_response_id"
            ][interaction_idx]
            input_query = interaction[0]

    if not user_id:
        raise gr.Error(
            "Silakan pilih RM terlebih dahulu. "
            "Kemudian klik \"Clear Conversation\""
        )
        return

    _LOGGER.info("%s give feedback (%s): %s",
                 user_id, ai_response_id, feedback.liked)

    data = Feedback(
        user_id=user_id,
        session_id=request.session_hash,
        interaction_id=sessions[request.session_hash]["interaction_id"],
        ai_response_id=ai_response_id,
        use_case="cbrm",
        rating=feedback.liked,
        input_query=input_query,
        response=response,
    )

    if feedback.liked:
        gr.Info("Terima kasih telah memberikan penilaian.")
    else:
        gr.Info("Maaf untuk ketidaknyamanannya. "
                "Terima kasih sudah memberikan penilaian.")

    chatbot.send_feedback(data)
    _LOGGER.info("Done sending feedback")
    return feedback


def refresh_qa():
    t0 = time()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    faq = faq_service.generate()
    shuffle(faq.faq)
    qa_containers = [
        gr.Markdown(
            f"""
            <h1 align="center">FAQ</h1>
            <p align="right"><i>Generated at: {now}</i></p>
            """,
            elem_id="md-title"
        )
    ]
    for qa in faq.faq:
        qa_containers.extend([
            qa.question,
            qa.answer,
        ])
    _LOGGER.info("Done refreshing FAQ in %.2fs", time() - t0)
    return qa_containers


with gr.Blocks(title="CBRM", css=css) as demo:
    state = gr.State({})
    with gr.Tab("Chat"):
        gr.Markdown(
            """
            <h1 align="center">Generative AI Chatbot</h1>
            """
        )
        with gr.Row():
            persona = gr.Dropdown(
                ["Relationship Manager", "Resource Manager"],
                label="Select persona",
                value="Resource Manager",
            )
            language = gr.Textbox(
                placeholder="Language of the response..",
                label="Response language",
            )
            rm = gr.Dropdown(
                ["USER003", "USER002", "USER001"],
                label="Select User",
                value="USER001",
            )

        bot = gr.Chatbot(height=400)
        chat = gr.ChatInterface(
            chat_with_llm,
            chatbot=bot,
            theme="soft",
            submit_btn="Send",
            show_progress="minimal",
            additional_inputs=[state, persona, rm, language],
        )

        # Add change handlers to clear conversation
        persona.change(
            clear_history,
            inputs=[state],
            outputs=[chat.chatbot, chat.chatbot_state],
        )
        language.change(
            clear_history,
            inputs=[state],
            outputs=[chat.chatbot, chat.chatbot_state],
        )
        rm.change(
            clear_history,
            inputs=[state],
            outputs=[chat.chatbot, chat.chatbot_state],
        )

        # handlers to clear conversation whenever either persona, language, or
        # rm change values

        clear_btn = gr.ClearButton(
            value="Clear Conversation",
        )
        clear_btn.click(
            clear_history,
            inputs=[state],
            outputs=[chat.chatbot, chat.chatbot_state],
        )

        bot.like(send_feedback, inputs=[chat.chatbot, rm, state])

    with gr.Tab("FAQ"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        faq = faq_service.generate()

        header_md = gr.Markdown(
            f"""
            <h1 align="center">FAQ</h1>
            <p align="right"><i>Generated at: {now}</i></p>
            """
        )

        with gr.Row():
            refresh_btn = gr.Button("Refresh FAQ", scale=0)


        qa_containers = [header_md]
        for qa in faq.faq:
            question_md = gr.Markdown(f"**{qa.question}**")
            with gr.Accordion("Lihat jawaban", open=False):
                answer_md = gr.Markdown(qa.answer)
            qa_containers.extend([question_md, answer_md])

        refresh_btn.click(
            fn=refresh_qa,
            outputs=qa_containers,
        )


if __name__ == "__main__":
    _LOGGER.info("Starting UI")
    demo.queue(
        default_concurrency_limit=c.CONCURRENCY_LIMIT,
        max_size=c.MAX_QUEUE_SIZE
    )
    demo.launch()
