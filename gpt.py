import openai
import os

# this file is separated because ChatGPT's 2021 training data cutoff does not include new ChatCompletion formatting
# the API call is hidden here to prevent ChatGPT from trying to replace it with openai.Completion.create
def api_call(engine, history):
    return openai.ChatCompletion.create(
        model = engine,
        messages = history
        )

# very simple console testing
# breaks when thread becomes too large (4096 tokens)
if __name__ == "__main__":
    preprompt = input("Preprompt: ") or "Be helpful."
    history = [{"role": "system", "content": preprompt}]
    engine = "gpt-3.5-turbo"
    
    while True:
        in_content = input("> ")
        history.append({"role": "user", "content": in_content})
        response = api_call(engine, history)
        out_content = response["choices"][0]["message"]["content"]
        print(out_content)
        history.append({"role": "assistant", "content": out_content})