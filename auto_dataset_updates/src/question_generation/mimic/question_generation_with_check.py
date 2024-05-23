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
os.chdir("../../../")

@backoff.on_exception(backoff.expo, (openai.error.RateLimitError, openai.error.Timeout, openai.error.APIError, openai.error.ServiceUnavailableError))
def llm(prompt):
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages = [{"role": "system", "content": prompt}],
      temperature = 0.8,
      max_tokens = 1024
      )
    return response['choices'][0]['message']['content']

@backoff.on_exception(backoff.expo, (openai.error.RateLimitError, openai.error.Timeout, openai.error.APIError, openai.error.ServiceUnavailableError))
def llm_check_answer(prompt, answer, follow_up):
    response = openai.ChatCompletion.create(
    model="gpt-4-1106-preview",
    messages = [{"role": "system", "content": prompt},
                {"role": "assistant", "content": answer},
                {"role": "user", "content": follow_up}],
    temperature = 0,
    max_tokens = 1024
    )
    return response['choices'][0]['message']['content']

@backoff.on_exception(backoff.expo, (openai.error.RateLimitError, openai.error.Timeout, openai.error.APIError, openai.error.ServiceUnavailableError))
def llm_get_new_sample(prompt, answer, follow_up, answer_check, new_sample):
    response = openai.ChatCompletion.create(
    model="gpt-4-1106-preview",
    messages = [{"role": "system", "content": prompt},
                {"role": "assistant", "content": answer},
                {"role": "user", "content": follow_up},
                {"role": "assistant", "content": answer_check},
                {"role": "user", "content": new_sample}],
    temperature = 0,
    max_tokens = 1024
    )
    return response['choices'][0]['message']['content']
    

parser = argparse.ArgumentParser(description = 'argparse')
parser.add_argument('--dataset', type = str, required = True)
parser.add_argument('--interrupt', type = int, default = 0)
args = parser.parse_args()


if __name__ == '__main__':
    file = json.load(open("data/" + args.dataset +  ".json","r"))
    prompt = open("data/prompt/question_generation/" + args.dataset + ".txt").read()
    start_index = args.interrupt
    end_index = len(file)
    bar = tqdm.trange(start_index, end_index, initial = start_index)
    mimic_dataset = []
    for idx, sample in zip(bar, file[args.interrupt:]):
        new_sample = copy.deepcopy(sample)
        sys_prompt = prompt  +  "\n\n" + json.dumps(sample)
        new_question = llm(sys_prompt)
        new_sample["new_question"] = new_question
        follow_up = "Is the answer correct?"
        answer_check = llm_check_answer(sys_prompt, new_question, follow_up)
        new_sample["answer_check"] = answer_check
        new_sample_ask = '''if not correct return the correct one in JSON object else return "None"'''
        correct_new_sample = llm_get_new_sample(sys_prompt, new_question, follow_up, answer_check, new_sample_ask)
        if "```json" in correct_new_sample: correct_new_sample =  correct_new_sample[8:-3]
        new_sample["correct_new_sample"] = correct_new_sample
        outdir = "data/mimic/" + args.dataset + ".jsonl"
        os.makedirs(os.path.dirname(outdir), exist_ok=True)
        with jsonlines.open(outdir, 'a') as fw:
          fw.write(new_sample)