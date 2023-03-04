import openai

def GPT(engine, history):
    return openai.ChatCompletion.create(
        model = engine,
        messages = history
        )
