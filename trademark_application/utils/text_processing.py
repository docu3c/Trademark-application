import re
import nltk
from typing import List
from openai import AzureOpenAI
import os
import json
import ast

nltk.download("wordnet")
nltk.download("omw-1.4")


def preprocess_text(text: str) -> str:
    """Clean and standardize text"""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[\u2013\u2014]", "-", text)
    return text


def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    # Replace special hyphen-like characters with a standard hyphen
    text = re.sub(r"[−–—]", "-", text)
    # Remove punctuation except hyphens and spaces
    text = re.sub(r"[^\w\s-]", " ", text)
    # Convert to lowercase
    text = text.lower()
    # Remove specific words and numbers
    text = re.sub(r"\b\d+\b", "", text)
    words_to_remove = [
        "class",
        "care",
        "in",
        "and",
        "the",
        "for",
        "with",
        "from",
        "to",
        "under",
        "using",
        "of",
        "no",
        "include",
        "ex",
        "example",
        "classes",
        "search",
        "scope",
        "shower",
        "products",
        "shampoos",
    ]
    for word in words_to_remove:
        text = re.sub(r"\b" + word + r"\b", "", text)

    # Replace specific words
    text = re.sub(r"\bshampoos\b", "hair", text)

    # Standardize whitespace
    return " ".join(text.split())


def replace_disallowed_words(text: str) -> str:
    """Replace disallowed words with placeholders"""
    disallowed_words = {
        "sexual": "xxxxxx",
        "sex": "xxx",
    }
    for word, replacement in disallowed_words.items():
        text = text.replace(word, replacement)
    # Ensure single paragraph output
    text = " ".join(text.split())
    return text


def levenshtein_distance(a: str, b: str) -> int:
    if len(a) < len(b):
        return levenshtein_distance(b, a)
    if len(b) == 0:
        return len(a)

    previous_row = range(len(b) + 1)
    for i, c1 in enumerate(a):
        current_row = [i + 1]
        for j, c2 in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def parse_international_class_numbers(class_numbers: str) -> List[int]:
    """Parse class numbers from string"""
    try:
        # Remove any non-numeric characters except commas
        cleaned = re.sub(r"[^\d,]", "", class_numbers)
        # Split by comma and convert to integers
        return [int(num.strip()) for num in cleaned.split(",") if num.strip()]
    except Exception:
        return []


def list_conversion(proposed_class: str) -> List[int]:
    """Convert class string to list of integers using GPT"""
    try:
        azure_endpoint = os.getenv("AZURE_ENDPOINT")
        api_key = os.getenv("AZURE_API_KEY")

        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version="2024-10-01-preview",
        )

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant for converting the class number string into python list of numbers.\n Respond only with python list. Example : [18,35]",
            },
            {
                "role": "user",
                "content": f"The class number are: {proposed_class}. convert the string into python list of numbers.",
            },
        ]

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0,
            max_tokens=150,
        )

        lst_class = response.choices[0].message.content
        return ast.literal_eval(lst_class)
    except Exception:
        return []


def find_class_numbers(goods_services: str) -> List[int]:
    """Find class numbers in goods/services description using GPT"""
    try:
        azure_endpoint = os.getenv("AZURE_ENDPOINT")
        api_key = os.getenv("AZURE_API_KEY")

        client = AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=api_key,
            api_version="2024-10-01-preview",
        )

        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant for finding the International class number of provided Goods & Services.",
            },
            {
                "role": "user",
                "content": f"The goods/services are: {goods_services}. Find the international class numbers.",
            },
        ]

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.5,
            max_tokens=150,
        )

        class_numbers_str = response.choices[0].message.content
        class_numbers = re.findall(r"(?<!\d)\d{2}(?!\d)", class_numbers_str)
        return [int(num) for num in set(class_numbers)]
    except Exception:
        return []
