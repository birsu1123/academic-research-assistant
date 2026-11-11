from llm.model import get_model

model = get_model()

response = model.invoke(
    "Explain what a literature review is in one sentence."
)

print(response.content)