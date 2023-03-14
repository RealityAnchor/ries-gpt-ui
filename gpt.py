import openai
import os

def api_call(engine, history):
    return openai.ChatCompletion.create(
        model = engine,
        messages = history
        )

if __name__ == "__main__":
    print(openai.api_key)
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
