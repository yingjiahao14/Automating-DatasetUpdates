import os
import openai
import json
import sys
import random
import time
import re
from thefuzz import process
import torch 
import numpy as np
import argparse
import tqdm
import backoff 
import jsonlines
import time
import copy
import jsonlines

@backoff.on_exception(backoff.expo, (openai.error.RateLimitError, openai.error.Timeout, openai.error.APIError, openai.error.ServiceUnavailableError))
def llm(prompt, question):
    response = openai.ChatCompletion.create(
    model="",
    messages = [{"role": "system", "content": prompt},
                {"role": "user", "content": question}],
    temperature = 0,
    max_tokens = 1024
    )
    return response['choices'][0]['message']['content']
   

choices = ["A", "B", "C", "D"]
def get_input_sample(sample):
    prompt = "The following is a multiple-choice question. Please choose the most suitable one among A, B, C and D as the answer to this question.\n\n"
    question_sample = sample["question"] + "\n"
    for choice in choices:
        question_sample += f'{choice}. {sample[f"{choice}"]}\n'
    return prompt, question_sample

def extract_choice(gen, choice_list):
    # answer is A | choice is A | choose A
    res = re.search(
        r"(?:(?:[Cc]hoose)|(?:(?:[Aa]nswer|[Cc]hoice)(?![^ABCD]{0,20}?(?:n't|not))[^ABCD]{0,10}?\b(?:|is|:|be))\b)[^ABCD]{0,20}?\b(A|B|C|D)\b",
        gen,
    )

    # A is correct | A is right
    if res is None:
        res = re.search(
            r"\b(A|B|C|D)\b(?![^ABCD]{0,8}?(?:n't|not)[^ABCD]{0,5}?(?:correct|right))[^ABCD]{0,10}?\b(?:correct|right)\b",
            gen,
        )

    # straight answer: A
    if res is None:
        res = re.search(r"^(A|B|C|D)(?:\.|,|:|$)", gen)

    # simply extract the first appearred letter
    if res is None:
        res = re.search(r"(?<![a-zA-Z])(A|B|C|D)(?![a-zA-Z=])", gen)

    if res is None:
        return choices[choice_list.index(process.extractOne(gen, choice_list)[0])]
    return res.group(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', default=None, type=str)
    parser.add_argument('--tag', type = str, default = "mimic")
    parser.add_argument('--interrupt', type = int, default = 0)
    args = parser.parse_args()
    task_list = ["task_medicine"]
    data_source_list = ["orig", "mimic"]
    for task in task_list:
        for source in data_source_list:
            acc = 0
            file = []
            file = json.load(open("../../data/" + source  + "/"  + task + "/"  + task + ".json","r", encoding='utf-8'))
            start_index = args.interrupt
            end_index = len(file)
            bar = tqdm.trange(start_index, end_index, initial = start_index)
            for idx, sample in zip(bar, file[args.interrupt:]):
                prompt, question = get_input_sample(sample)
                response = llm(prompt, question)
                new_sample = copy.deepcopy(sample)
                new_sample["response"] = response
                pred = extract_choice(response, [new_sample[choice] for choice in choices])
                if pred == new_sample["answer"]:
                    acc += 1 
            print(f"<------------------model:gpt4-task:{task} --source{source}---acc:{acc/len(file)}---------->")

  
    
    