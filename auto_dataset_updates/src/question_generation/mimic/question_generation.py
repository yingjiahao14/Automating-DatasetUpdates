import os
import openai
import json
import sys
import random
import time
import torch 
import numpy as np
import argparse
import tqdm
import backoff 
import jsonlines

# Changing the current directory to three levels up in the directory hierarchy.
os.chdir("../../../")

# Applying a backoff strategy to handle exceptions related to OpenAI API calls.
@backoff.on_exception(backoff.expo, (openai.error.RateLimitError, openai.error.Timeout, openai.error.APIError, openai.error.ServiceUnavailableError))
def llm(prompt):
    try:
      # Making a request to the OpenAI API to generate a completion based on the input prompt.
      response = openai.ChatCompletion.create(
        model="",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.8,
        max_tokens=1024
      )
      # Parsing the JSON response.
      return json.loads(response['choices'][0]['message']['content'])
    except json.JSONDecodeError:
      # Handling cases where the response is not in valid JSON format.
      if "```json" in response['choices'][0]['message']['content']:
         context = response['choices'][0]['message']['content'][8:-3]
         return json.loads(context)
      return {"error": "Response is not in JSON format"}

# Setting up argument parsing.
parser = argparse.ArgumentParser(description='argparse')
parser.add_argument('--dataset', type=str, required=True)
parser.add_argument('--interrupt', type=int, default=0)
args = parser.parse_args()

if __name__ == '__main__':
    # Loading the dataset from a specified JSON file.
    file = json.load(open(f"data/orig/{args.dataset}/{args.dataset}.json", "r"))
    # Reading a text file that contains prompts.
    prompt = open("data/prompt/question_generation/" + args.dataset + ".txt").read()
    start_index = args.interrupt
    end_index = len(file)
    # Initializing a progress bar for the process.
    bar = tqdm.trange(start_index, end_index, initial=start_index)
    print(f"-------{len(file)}----------")
    mimic_dataset = []
    for idx, sample in zip(bar, file[args.interrupt:]):
        # Generating a system prompt by appending the JSON sample to the base prompt.
        sys_prompt = prompt + "\n\n" + json.dumps(sample) + "\n Provide your response as a JSON object.{}"
        new_sample = llm(sys_prompt)
        mimic_dataset.append(new_sample)
        # Setting the output directory and ensuring it exists.
        outdir = "data/mimic/" + args.dataset + ".jsonl"
        os.makedirs(os.path.dirname(outdir), exist_ok=True)
        # Writing the generated samples to a .jsonl file.
        with jsonlines.open(outdir, 'a') as fw:
          fw.write(new_sample)
