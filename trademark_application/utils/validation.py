from typing import List, Dict, Union
from sentence_transformers import SentenceTransformer, util
from nltk.stem import WordNetLemmatizer
import re
import json


def is_correct_format_code1(page_text: str) -> bool:
    print(f"Executing is_correct_format_code1")
    required_fields = ["Status:", "Goods/Services:"]
    return all(field in page_text for field in required_fields)


def is_correct_format_code2(page_text: str) -> bool:
    print(f"Executing is_correct_format_code2")
    required_fields = ["Register", "Nice Classes", "Goods & Services"]
    return all(field in page_text for field in required_fields)


def is_substring_match(name1: str, name2: str) -> bool:
    """
    Check if one name is a substring of another
    """
    print(f"Executing is_substring_match")
    name1_lower = name1.lower()
    name2_lower = name2.lower()
    return name1_lower in name2_lower or name2_lower in name1_lower


def has_shared_word(name1: str, name2: str) -> bool:
    """
    Check if two names share any words
    """
    print(f"Executing has_shared_word")
    words1 = set(name1.lower().split())
    words2 = set(name2.lower().split())
    return not words1.isdisjoint(words2)


def is_similar_goods_services(
    existing_goods: str, proposed_goods: str, threshold: float = 0.65
) -> bool:
    """
    Check if goods/services descriptions are similar using semantic similarity
    """
    print(f"Executing is_similar_goods_services")
    # Initialize the model (consider moving this to a global scope or singleton)
    semantic_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def normalize_text(text: str) -> str:
        # Replace special characters
        text = re.sub(r"[−–—]", "-", text)
        # Remove punctuation except hyphens
        text = re.sub(r"[^\w\s-]", " ", text)
        # Convert to lowercase
        text = text.lower()
        # Remove numbers
        text = re.sub(r"\b\d+\b", "", text)
        # Remove common words
        common_words = [
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
        ]
        for word in common_words:
            text = re.sub(r"\b" + word + r"\b", "", text)
        # Replace specific terms
        text = re.sub(r"\bshampoos\b", "hair", text)
        # Standardize whitespace
        return " ".join(text.split())

    # Normalize both texts
    existing_normalized = normalize_text(existing_goods)
    proposed_normalized = normalize_text(proposed_goods)

    # Get embeddings and calculate similarity
    embeddings1 = semantic_model.encode(existing_normalized, convert_to_tensor=True)
    embeddings2 = semantic_model.encode(proposed_normalized, convert_to_tensor=True)
    similarity_score = util.cos_sim(embeddings1, embeddings2).item()

    if similarity_score >= threshold:
        return True

    # Additional check using lemmatization
    lemmatizer = WordNetLemmatizer()
    existing_words = {
        lemmatizer.lemmatize(word) for word in existing_normalized.split()
    }
    proposed_words = {
        lemmatizer.lemmatize(word) for word in proposed_normalized.split()
    }

    # Check for common words
    common_words = existing_words.intersection(proposed_words)
    return bool(common_words)


def validate_trademark_relevance(conflicts_array, proposed_goods_services):
    """
    Pre-filter trademarks that don't have similar or identical goods/services
    This function is implemented in code rather than relying on GPT

    Args:
        conflicts_array: List of trademark conflicts
        proposed_goods_services: Goods/services of the proposed trademark

    Returns:
        filtered_conflicts: List of relevant trademark conflicts
        excluded_count: Number of trademarks excluded
    """
    print(f"Executing validate_trademark_relevance")
    # Parse conflicts_array if it's a string (assuming JSON format)
    if isinstance(conflicts_array, str):
        try:
            conflicts = json.loads(conflicts_array)
        except json.JSONDecodeError:
            # If it's not valid JSON, try to parse it as a list of dictionaries
            conflicts = (
                eval(conflicts_array) if conflicts_array.strip().startswith("[") else []
            )
    else:
        conflicts = conflicts_array

    # Initialize lists for relevant and excluded trademarks
    relevant_conflicts = []
    excluded_count = 0

    # Define a function to check similarity between goods/services
    def is_similar_goods_services(existing_goods, proposed_goods):
        # Convert to lowercase for case-insensitive comparison
        existing_lower = existing_goods.lower()
        proposed_lower = proposed_goods.lower()

        # Check for exact match
        if existing_lower == proposed_lower:
            return True

        # Check if one contains the other
        if existing_lower in proposed_lower or proposed_lower in existing_lower:
            return True

        # Check for overlapping keywords
        # Extract significant keywords from both descriptions
        existing_keywords = set(re.findall(r"\b\w+\b", existing_lower))
        proposed_keywords = set(re.findall(r"\b\w+\b", proposed_lower))

        # Remove common stop words
        stop_words = {
            "and",
            "or",
            "the",
            "a",
            "an",
            "in",
            "on",
            "for",
            "of",
            "to",
            "with",
        }
        existing_keywords = existing_keywords - stop_words
        proposed_keywords = proposed_keywords - stop_words

        # Calculate keyword overlap
        if len(existing_keywords) > 0 and len(proposed_keywords) > 0:
            overlap = len(existing_keywords.intersection(proposed_keywords))
            overlap_ratio = overlap / min(
                len(existing_keywords), len(proposed_keywords)
            )

            # If significant overlap (more than 30%), consider them similar
            if overlap_ratio > 0.3:
                return True

        return False

    # Process each conflict
    for conflict in conflicts:
        # Ensure conflict has goods/services field
        if "goods_services" in conflict:
            if is_similar_goods_services(
                conflict["goods_services"], proposed_goods_services
            ):
                relevant_conflicts.append(conflict)
            else:
                excluded_count += 1
        else:
            # If no goods/services field, include it for safety
            relevant_conflicts.append(conflict)

    print(f"relevant_conflicts:\n {(len(relevant_conflicts))}")

    return relevant_conflicts, excluded_count
