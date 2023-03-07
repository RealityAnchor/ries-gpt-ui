import openai

def call(engine, history):
    return openai.ChatCompletion.create(
        model = engine,
        messages = history
        )
