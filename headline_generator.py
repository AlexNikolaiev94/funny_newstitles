import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from random import choice

EOS = [".", ]


def read_csv(_file):
    with _file:
        reader = csv.DictReader(_file)
        result = [row["headline"] for row in reader]
    return result


def read_json(_file):
    with _file:
        data = json.load(_file)
        result = [headline for headline in data["headlines"]]
    return result


def generate_word_pool(headlines):
    pool = []
    for h in headlines:
        h += '.'
        h_corpus = h.split()
        pool.extend(h_corpus)
    return pool


def generate_dictionary(words):
    word_dict = {}
    for i, word in enumerate(words):
        try:
            first, second, third = words[i], words[i + 1], words[i + 2]
        except IndexError:
            break
        key = (first, second)
        if key not in word_dict:
            word_dict[key] = []
        word_dict[key].append(third)
    return word_dict


def generate_headline(word_dict, headline_length):
    word_list = [k for k in word_dict.keys() if k[0][0].isupper()]
    try:
        key = choice(word_list)
    except IndexError:
        pass
    else:
        word_list = []
        first, second = key
        if first[-1] in EOS or second[-1] in EOS:
            pass
        else:
            word_list.append(first)
            word_list.append(second)
            for x in range(headline_length):
                try:
                    third = choice(word_dict[key])
                except KeyError:
                    break
                word_list.append(third)
                if third[-1] in EOS:
                    break
                key = (second, third)
                first, second = key
            headline = " ".join(word_list)
            return headline[:-1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", nargs=1, required=True)
    parser.add_argument("-l", "--length", nargs=1, required=True)
    args = parser.parse_args()
    input_file = args.input[0]
    headline_length = int(args.length[0])
    # Create or find the output file if exists
    output_file = "output.csv"
    if os.path.exists(Path(output_file)):
        access_flag = "a"
    else:
        access_flag = "w"
    # Get file extension and use the corresponding reader
    _, ext = os.path.splitext(Path(input_file))
    # Make sure the file exists; Exit gracefully otherwise.
    try:
        _file = open(input_file, mode="r", encoding="utf-8")
    except FileNotFoundError:
        print("The specified input file is not found. Exiting now.")
        sys.exit(2)
    else:
        if ext == ".csv":
            input_headlines = read_csv(_file)
        elif ext == ".json":
            input_headlines = read_json(_file)
        else:
            print("Unsupported input file type.")
            print("Supported formats are CSV and JSON.")
            _file.close()
            sys.exit(2)
    # Transform all the headings into one word pool
    word_pool = generate_word_pool(input_headlines)
    word_dict = generate_dictionary(word_pool)
    result = []
    for x in range(len(input_headlines)):
        headline = generate_headline(word_dict, headline_length)
        if not headline:
            break
        if headline in input_headlines:
            break
        if len(headline) < headline_length / 3:
            break
        result.append(headline)
    # TODO: select only the most realistic headlines for output
    if len(result) == 0:
        print("No unique or realistic headlines generated.")
        sys.exit(0)
    # Write out output to a CSV file
    with open(output_file, access_flag, newline="", encoding="utf-8") as _file:
        field_names = ["date", "headline", ]
        writer = csv.DictWriter(_file, field_names)
        writer.writeheader()
        for h in result:
            writer.writerow({
                "date": datetime.now().strftime("%Y%m%d%H%M%S"),
                "headline": h
            })
        sys.exit(0)


if __name__ == "__main__":
    main()
