import os
import json

#search json files
def get_filenames(folder, query):
    results = []
    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            with open(os.path.join(folder, filename), "r") as file:
                data = json.load(file)
                for entry in data:
                    if query.lower() in entry["content"].lower():
                        results.append(filename)
                        break
    return results
