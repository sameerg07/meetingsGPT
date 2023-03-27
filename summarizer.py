import platform
import os

import openai
from sty import fg, bg, ef, rs
import re
from os.path import splitext, exists

import nltk
# nltk.download('punkt')
from nltk.tokenize import word_tokenize




os.environ["OPENAI_API_KEY"] = '<OPENAIKEY>'
openai.api_type = "azure"
openai.api_base = "<OPENAI BASE URL>"
openai.api_version = "2022-12-01"
openai.api_key = os.getenv("OPENAI_API_KEY")

deployments = openai.Deployment.list()



filepath = "<path to your vtt file>" #abc.vtt
filename = "<path to text file>" ##abc.txt


def clean_webvtt(filepath: str) -> str:
    """Clean up the content of a subtitle file (vtt) to a string

    Args:
        filepath (str): path to vtt file

    Returns:
        str: clean content
    """
    # read file content
    with open(filepath, "r", encoding="utf-8") as fp:
        content = fp.read()

    # remove header & empty lines
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    lines = lines[1:] if lines[0].upper() == "WEBVTT" else lines

    # remove indexes
    lines = [lines[i] for i in range(len(lines)) if not lines[i].isdigit()]

    # remove tcode
    #pattern = re.compile(r'^[0-9:.]{12} --> [0-9:.]{12}')
    pattern = r'[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}\/\d+-\d'
    lines = [lines[i] for i in range(len(lines))
             if not re.match(pattern, lines[i])]

    # remove timestamps
    pattern = r"^\d{2}:\d{2}:\d{2}.\d{3}.*\d{2}:\d{2}:\d{2}.\d{3}$"
    lines = [lines[i] for i in range(len(lines))
             if not re.match(pattern, lines[i])]

    content = " ".join(lines)

    # remove duplicate spaces
    pattern = r"\s+"
    content = re.sub(pattern, r" ", content)

    # add space after punctuation marks if it doesn't exist
    pattern = r"([\.!?])(\w)"
    content = re.sub(pattern, r"\1 \2", content)

    return content


def vtt_to_clean_file(file_in: str, file_out=None, **kwargs) -> str:
    """Save clean content of a subtitle file to text file

    Args:
        file_in (str): path to vtt file
        file_out (None, optional): path to text file
        **kwargs (optional): arguments for other parameters
            - no_message (bool): do not show message of result.
                                 Default is False

    Returns:
        str: path to text file
    """
    # set default values
    print("*"*15)
    print("Processing meeting file: ",file_in)
    print("*"*15)
    no_message = kwargs.get("no_message", False)
    if not file_out:
        filename = splitext(file_in)[0]
        file_out = "%s.txt" % filename
        i = 0
        while exists(file_out):
            i += 1
            file_out = "%s_%s.txt" % (filename, i)

    content = clean_webvtt(file_in)
    with open(file_out, "w+", encoding="utf-8") as fp:
        fp.write(content)

    return file_out




vtt_to_clean_file(filepath)


def count_tokens(filename):
    with open(filename, 'r') as f:
        text = f.read()
    tokens = word_tokenize(text)
    return len(tokens)



token_count = count_tokens(filename)
print(f"Number of tokens: {token_count}")
print("*"*15)


def break_up_file(tokens, chunk_size, overlap_size):
    if len(tokens) <= chunk_size:
        yield tokens
    else:
        chunk = tokens[:chunk_size]
        yield chunk
        yield from break_up_file(tokens[chunk_size-overlap_size:], chunk_size, overlap_size)

def break_up_file_to_chunks(filename, chunk_size=2000, overlap_size=100):
    with open(filename, 'r') as f:
        text = f.read()
    tokens = word_tokenize(text)
    return list(break_up_file(tokens, chunk_size, overlap_size))




chunks = break_up_file_to_chunks(filename)
for i, chunk in enumerate(chunks):
    pass


def convert_to_prompt_text(tokenized_text):
    prompt_text = " ".join(tokenized_text)
    prompt_text = prompt_text.replace(" 's", "'s")
    return prompt_text


prompt_response = []

for i, chunk in enumerate(chunks):
    prompt_request = "Summarize this meeting transcript: " + convert_to_prompt_text(chunks[i])
    messages = [{"role": "system", "content": "This is text summarization."}]    
    messages.append({"role": "user", "content": prompt_request})

    response = openai.Completion.create(
        deployment_id="deployment2",
        model="text-davinci-003",
        prompt=prompt_request,
        temperature=.5,
        max_tokens=250,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    prompt_response.append(response["choices"][0]["text"].strip())

while True:
    question = str(input("You: "))
    prompt_request = "Find the answer for '"+question+"' by cumulating these meeting summaries: " + str(prompt_response)
    response = openai.Completion.create(
            deployment_id="deployment2",
            model="text-davinci-003",
            prompt=prompt_request,
            temperature=.7,
            max_tokens=500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
    meeting_summary = response["choices"][0]["text"].strip()
    print(fg.li_yellow +"meetGPT: ",meeting_summary+fg.rs)
    print("*"*15)