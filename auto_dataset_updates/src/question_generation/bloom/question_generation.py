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
    model="gpt-4",
    messages = [{"role": "system", "content": prompt},
                {"role": "user", "content": question}],
    temperature = 0.8,
    max_tokens = 1024
    )
    return response['choices'][0]['message']['content']

@backoff.on_exception(backoff.expo, (openai.error.RateLimitError, openai.error.Timeout, openai.error.APIError, openai.error.ServiceUnavailableError))
def llm_get_answer(prompt, question, answer, follow_up):
    response = openai.ChatCompletion.create(
    model="gpt-4",
    messages = [{"role": "system", "content": prompt},
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer},
                {"role": "user", "content": follow_up}],
    temperature = 0,
    max_tokens = 1024
    )
    return response['choices'][0]['message']['content']
   

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', default = None, type = str, required = None)
    parser.add_argument('--level', type = int, default = 0)
    parser.add_argument('--interrupt', type = int, default = 0)
    args = parser.parse_args()
    level_list = {0: "remember", 1: "apply", 2: "analysis", 3:"evaluation"}
    level  = level_list[args.level]
    seed = "sports_stars"

    file = json.load(open("../../../data/prompt/seed/sports_stars.txt", "r"))
    start_index = args.interrupt
    end_index = len(file)
    bar = tqdm.trange(start_index, end_index, initial = start_index)
    print(f"------------------seed{seed} level{level}----------------------")
    prompt = open("../../../data/prompt/bloom/" + level + ".txt").read()
    for idx, sample in zip(bar, file[args.interrupt:]):
        entity = sample["name"]
        question_sample = entity
        response = llm(prompt, question_sample)
        get_answer = "what is the answer?"
        ref_answer = llm_get_answer(prompt, question_sample, response, get_answer)
        sample_out = {"question": response, "answer": ref_answer}

        with jsonlines.open("../../../data/bloom/" + seed + "_" + level + ".jsonl", 'a') as fw:
            fw.write(sample_out)


  