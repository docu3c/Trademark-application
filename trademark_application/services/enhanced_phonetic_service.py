import os
import re
from typing import Literal, Dict, Optional
from rapidfuzz import fuzz
import phonetics
from openai import AzureOpenAI


def detect_prominent_component_with_llm(
    mark: str,
    model_name: str = "gpt-4.1",
    azure_endpoint: str = None,
    api_key: str = None,
) -> str:
    """
    Ask the LLM to pick out the 'prominent' (legally distinctive) component
    of a compound trademark. Returns a single word or short phrase in lowercase.
    """
    print(f"Executing detect_prominent_component_with_llm")
    azure_endpoint = azure_endpoint or os.getenv("AZURE_ENDPOINT")
    api_key = api_key or os.getenv("AZURE_API_KEY")

    if not azure_endpoint or not api_key:
        return ""

    client = AzureOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        api_version="2024-02-15-preview",
    )

    system = (
        "You are a trademark attorney. "
        "When given a compound trademark name, "
        "identify the single most distinctive (legally prominent) element. "
        "Answer with that word or phrase only."
    )
    user = f'Trademark: "{mark}"\nWhich part is the prominent/distinctive element?'

    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
            max_tokens=20,
        )

        choice = resp.choices[0].message.content.strip()
        # return first line, stripped, lowercase
        return choice.split("\n")[0].strip().strip('"').lower()
    except Exception as e:
        print(f"LLM Error: {str(e)}")
        return ""


def get_prominent_element(
    mark: str, strategy: Literal["last", "first", "longest"] = "last"
) -> str:
    """
    Simple fallback heuristic if LLM fails:
    - 'last': last whitespace token
    - 'first': first token
    - 'longest': the longest token
    """
    print(f"Executing get_prominent_element")
    tokens = re.findall(r"\w+", mark)
    if not tokens:
        return mark.lower()
    if strategy == "first":
        return tokens[0].lower()
    if strategy == "longest":
        return max(tokens, key=len).lower()
    return tokens[-1].lower()


def get_phonetic_key(token: str) -> str:
    """
    Return a Metaphone code for the token.
    """
    return phonetics.metaphone(token)


def is_prominent_phonetic_match(
    name1: str,
    name2: str,
    threshold: int = 90,
    strategy: Literal["last", "first", "longest"] = "last",
) -> Dict[str, any]:
    """
    Heuristic phonetic match: isolate prominent token by 'strategy',
    compare Metaphone codes exactly or fuzzily.
    Returns a dictionary with match result and analysis details.
    """
    tok1 = get_prominent_element(name1, strategy)
    tok2 = get_prominent_element(name2, strategy)
    code1 = get_phonetic_key(tok1)
    code2 = get_phonetic_key(tok2)

    exact_match = code1 and code1 == code2
    fuzzy_score = fuzz.ratio(code1 or tok1, code2 or tok2)
    is_match = exact_match or fuzzy_score >= threshold

    return {
        "is_match": is_match,
        "prominent_element1": tok1,
        "prominent_element2": tok2,
        "phonetic_code1": code1,
        "phonetic_code2": code2,
        "exact_match": exact_match,
        "fuzzy_score": fuzzy_score,
        "threshold": threshold,
    }


def is_llm_prominent_phonetic_match(
    name1: str,
    name2: str,
    threshold: int = 90,
    llm_model: str = "gpt-4.1",
    fallback_strategy: Literal["last", "first", "longest"] = "last",
) -> Dict[str, any]:
    """
    LLM + phonetic match:
    1) ask the LLM for the prominent component of each mark
    2) if LLM fails, fall back to `fallback_strategy`
    3) compare Metaphone codes exactly or fuzzily
    Returns a dictionary with match result and analysis details.
    """
    try:
        key1 = detect_prominent_component_with_llm(name1, model_name=llm_model)
        key2 = detect_prominent_component_with_llm(name2, model_name=llm_model)
    except Exception as e:
        print(f"LLM Error: {str(e)}")
        key1 = key2 = ""

    if not key1:
        key1 = get_prominent_element(name1, fallback_strategy)
    if not key2:
        key2 = get_prominent_element(name2, fallback_strategy)

    code1 = get_phonetic_key(key1)
    code2 = get_phonetic_key(key2)

    exact_match = code1 and code1 == code2
    fuzzy_score = fuzz.ratio(code1 or key1, code2 or key2)
    is_match = exact_match or fuzzy_score >= threshold

    return {
        "is_match": is_match,
        "prominent_element1": key1,
        "prominent_element2": key2,
        "phonetic_code1": code1,
        "phonetic_code2": code2,
        "exact_match": exact_match,
        "fuzzy_score": fuzzy_score,
        "threshold": threshold,
        "used_llm": bool(key1 and key2),
    }
