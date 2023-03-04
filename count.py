import json
import os
import tiktoken

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

folder_path = f'{os.getcwd()}/history'
token_counts = []

# Loop through each file in the folder
for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        with open(os.path.join(folder_path, filename), "r") as f:
            data = json.load(f)
            for message in data:
                if message["role"] == "assistant":
                    content = message["content"]
                    num_tokens = len(encoding.encode(content))
                    token_counts.append(num_tokens)

if token_counts:
    print(sorted(token_counts))
    print(f'\nThe largest token count is {max(token_counts)}.')
    print(f'The smallest token count is {min(token_counts)}.')
    print(f'The mean token count is {sum(token_counts) / len(token_counts):.2f}.')
else:
    print('No JSON files found.')
