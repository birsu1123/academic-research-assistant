from langchain_ollama import ChatOllama


def get_model():
    return ChatOllama(
        model="qwen3:8b",
        temperature=0,
        num_ctx=8192,
        reasoning=False,
    )