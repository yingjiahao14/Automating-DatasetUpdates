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
import time
import copy
import jsonlines


@backoff.on_exception(backoff.expo, (openai.error.RateLimitError, openai.error.Timeout, openai.error.APIError, openai.error.ServiceUnavailableError))
def llm(prompt, question):
    response = openai.ChatCompletion.create(
    model="gpt-4-1106-preview",
    messages = [{"role": "system", "content": prompt},
                {"role": "user", "content": question}],
    temperature = 0,
    max_tokens = 1024
    )
    return response['choices'][0]['message']['content']
   

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', default=None, type=str, required=True)
    parser.add_argument('--tag', type = str, default = "mimic")
    parser.add_argument('--interrupt', type = int, default = 0)
    args = parser.parse_args()

    file = []
    if args.tag == "mimic":
        file = json.load(open("../../data/mimic/" + args.dataset  + "/" + args.dataset +  ".json","r"))
    else:
        file = json.load(open("../../data/orig/" + args.dataset  + "/" + args.dataset +  ".json","r"))
    prompt = open("../../data/prompt/question_answer/" + args.dataset + ".txt").read()
    start_index = args.interrupt
    end_index = len(file)
    print(f"<----------------dataset:{args.dataset}---------->")
    bar = tqdm.trange(start_index, end_index, initial = start_index)
    response = []
    for idx, sample in zip(bar, file[args.interrupt:]):
        question_sample = ""
        if args.dataset == "task_cs":
            question_sample = "string1: " + sample['input']['str1'] + "\n"  \
                              + "string2: " + sample['input']['str2'] 
        elif args.dataset == "task_phy":
            question = sample["input"]
            answers = sample["target_scores"]
            question_sample = question + "\n"
            options = ['A', 'B', 'C', 'D', 'E', "F" , "G", "H", "I"]
            index = 0
            for (answer, _) in answers.items():
                question_sample += f"{options[index]}: {answer}\n"
                index += 1
        elif args.dataset == "task_math":
            question = sample["input"]
            answers = sample["target_scores"]
            question_sample = question + "\n"
            options = ['A', 'B', 'C', 'D', 'E', "F" , "G", "H", "I"]
            index = 0
            for (answer, _) in answers.items():
                question_sample += f"{options[index]}: {answer}\n"
                index += 1
        else:
            question_sample = sample["input"]

        response = llm(prompt, question_sample)
        if args.dataset != "task_math":
            sample = {"input": sample["input"], "target_scores": sample["target_scores"], "response": response}
        else:
            sample = {"input": sample["input"], "hint": sample["hint"], \
                      "target_scores": sample["target_scores"], "response": response}
   
 
  