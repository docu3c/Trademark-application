from typing import Tuple
from sentence_transformers import SentenceTransformer, util
from fuzzywuzzy import fuzz
import torch
from utils.text_processing import levenshtein_distance
import cv2
import numpy as np
import base64
import requests
import os
from PIL import Image
import json
from config.settings import (
    SEMANTIC_SIMILARITY_THRESHOLD,
    SEMANTIC_HIGH,
    SEMANTIC_LOW,
    PHONETIC_SIMILARITY_THRESHOLD,
    PHONETIC_HIGH,
    PHONETIC_LOW,
)

# Load the semantic similarity model with device specified during initialization
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
semantic_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2", device=device
)


def ml_semantic_match(name1: str, name2: str) -> Tuple[float, bool, str]:
    """
    Perform semantic matching between two trademark names using ML
    Returns a tuple of (similarity_score, is_match, confidence)
    """
    embeddings1 = semantic_model.encode(name1, convert_to_tensor=True)
    embeddings2 = semantic_model.encode(name2, convert_to_tensor=True)
    similarity_score = util.cos_sim(embeddings1, embeddings2).item()
    print(f"Name1: {name1} and Name2: {name2} : Semantic Score: {similarity_score}\n")

    # Determine match based on thresholds
    if similarity_score >= SEMANTIC_HIGH:
        return similarity_score, True, "high"
    if similarity_score < SEMANTIC_LOW:
        return similarity_score, False, "low"

    # Borderline case
    return similarity_score, False, "medium"


def ml_phonetic_match(name1: str, name2: str) -> Tuple[float, bool, str]:
    """
    Perform phonetic matching between two trademark names using ML
    Returns a tuple of (similarity_score, is_match, confidence)
    """
    ratio = fuzz.ratio(name1.lower(), name2.lower())
    normalized_ratio = ratio / 100.0

    # Determine match based on thresholds
    print(f"Name1: {name1} and Name2: {name2} : Phonetic Ratio: {ratio}\n")
    if ratio >= PHONETIC_HIGH:
        return normalized_ratio, True, "high"
    if ratio < PHONETIC_LOW:
        return normalized_ratio, False, "low"

    # Borderline case
    return normalized_ratio, False, "medium"


# Helper function for semantic equivalence
def is_semantically_equivalent(name1, name2, threshold=SEMANTIC_SIMILARITY_THRESHOLD):
    embeddings1 = semantic_model.encode(name1, convert_to_tensor=True)
    embeddings2 = semantic_model.encode(name2, convert_to_tensor=True)
    similarity_score = util.cos_sim(embeddings1, embeddings2).item()
    print(f"Name1: {name1} and Name2: {name2} : Semantic Score: {similarity_score}\n")
    return similarity_score >= threshold


def is_phonetically_equivalent(name1, name2, threshold=PHONETIC_SIMILARITY_THRESHOLD):
    print(f"Executing is_phonetically_equivalent")
    ratio = fuzz.ratio(name1.lower(), name2.lower())
    print(f"Name1: {name1} and Name2: {name2} : Phonetic Ratio: {ratio}\n")
    return ratio >= threshold


def first_words_phonetically_equivalent(
    existing_name, proposed_name, threshold=PHONETIC_SIMILARITY_THRESHOLD
):
    existing_words = existing_name.lower().split()
    proposed_words = proposed_name.lower().split()
    if len(existing_words) < 2 or len(proposed_words) < 2:
        return False
    return (
        fuzz.ratio(" ".join(existing_words[:2]), " ".join(proposed_words[:2]))
        >= threshold
    )


def is_phonetic_partial_match(name1: str, name2: str, threshold: float = 55) -> bool:
    """
    Check if there is a partial phonetic match between two names
    """
    return fuzz.partial_ratio(name1.lower(), name2.lower()) >= threshold


def consistency_check(proposed_mark: str, classification: dict) -> dict:
    """Reclassify marks based on Levenshtein distance."""
    corrected = {
        "identical_marks": [],
        "one_letter_marks": [],
        "two_letter_marks": [],
        "similar_marks": classification.get("similar_marks", [])[
            :
        ],  # Copy similar marks as is
    }

    # Process marks from the 'identical_marks' bucket.
    for entry in classification.get("identical_marks", []):
        candidate = entry.get("mark", "")
        diff = levenshtein_distance(proposed_mark, candidate)
        if diff == 0:
            corrected["identical_marks"].append(entry)
        elif diff == 1:
            corrected["one_letter_marks"].append(entry)
        elif diff == 2:
            corrected["two_letter_marks"].append(entry)
        else:
            corrected["similar_marks"].append(entry)

    # Process marks from the 'one_two_letter_marks' bucket.
    for entry in classification.get("one_two_letter_marks", []):
        candidate = entry.get("mark", "")
        diff = levenshtein_distance(proposed_mark, candidate)
        if diff == 0:
            corrected["identical_marks"].append(entry)
        elif diff == 1:
            corrected["one_letter_marks"].append(entry)
        elif diff == 2:
            corrected["two_letter_marks"].append(entry)
        else:
            corrected["similar_marks"].append(entry)

    return corrected


def component_consistency_check(mark, results):
    """
    Verify component analysis results for consistency and correctness.

    Args:
        mark: The proposed trademark
        results: Raw component analysis results

    Returns:
        Validated and corrected component analysis results
    """
    print(f"Executing component_consistency_check")
    corrected_results = results.copy()

    # Ensure coordinated classes exist
    if "identified_coordinated_classes" not in corrected_results:
        corrected_results["identified_coordinated_classes"] = []

    if "coordinated_classes_explanation" not in corrected_results:
        corrected_results["coordinated_classes_explanation"] = (
            "No coordinated classes identified"
        )

    # Check components field
    if "components" not in corrected_results:
        corrected_results["components"] = []

    # Validate each component and its marks
    for i, component in enumerate(corrected_results.get("components", [])):
        # Ensure component has name and marks fields
        if "component" not in component:
            component["component"] = f"Component {i+1}"

        if "marks" not in component:
            component["marks"] = []

        # Ensure component distinctiveness
        if "distinctiveness" not in component:
            # Default to descriptive if not specified
            component["distinctiveness"] = "DESCRIPTIVE"

        # Check each mark in the component
        for j, mark_entry in enumerate(component.get("marks", [])):
            # Ensure all required fields exist
            required_fields = [
                "mark",
                "owner",
                "goods_services",
                "status",
                "class",
                "class_match",
                "goods_services_match",
            ]
            for field in required_fields:
                if field not in mark_entry:
                    if field == "class_match" or field == "goods_services_match":
                        corrected_results["components"][i]["marks"][j][field] = False
                    else:
                        corrected_results["components"][i]["marks"][j][
                            field
                        ] = "Unknown"

    # Validate crowded field analysis
    if "crowded_field" not in corrected_results:
        corrected_results["crowded_field"] = {
            "total_hits": 0,
            "distinct_owner_percentage": 0,
            "is_crowded": False,
            "explanation": "Unable to determine crowded field status",
        }
    else:
        # Ensure all required crowded field fields exist
        if "total_hits" not in corrected_results["crowded_field"]:
            corrected_results["crowded_field"]["total_hits"] = 0

        if "distinct_owner_percentage" not in corrected_results["crowded_field"]:
            corrected_results["crowded_field"]["distinct_owner_percentage"] = 0

        if "is_crowded" not in corrected_results["crowded_field"]:
            corrected_results["crowded_field"]["is_crowded"] = False

        if "explanation" not in corrected_results["crowded_field"]:
            corrected_results["crowded_field"][
                "explanation"
            ] = "Unable to determine crowded field status"

    return corrected_results


def encode_image(image: Image.Image) -> str:
    """Encode a PIL Image as Base64 string using OpenCV."""
    print(f"Executing encode_image")
    image_np = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    buffered = cv2.imencode(".jpg", image_np)[1]
    return base64.b64encode(buffered).decode("utf-8")


def process_single_image(image: Image.Image, proposed_name: str) -> dict:
    """Process a single image using Azure OpenAI API."""
    azure_endpoint = os.getenv("AZURE_ENDPOINT")
    api_key = os.getenv("AZURE_API_KEY")
    model = "gpt-4.1"

    base64_image = encode_image(image)

    prompt = f"""Extract the following details from the given image: Cited term, Owner name, Goods & services.\n\n
    
                Cited Term:\n
                - This is the snippet in the product/site text that *fully or partially matches* the physically highlighted or searched trademark name: {proposed_name}.
                - You must prioritize any match that closely resembles '{proposed_name}' — e.g., 'ColorGrip', 'COLORGRIP', 'Color self Grip' , 'Grip Colour', 'color-grip', 'Grip' , or minor variations in spacing/punctuation.

                Owner Name (Brand):\n
                - Identify the name of the individual or entity that owns or manufactures the product.
                - Look for indicators like "Owner:," "Brand:," "by:," or "Manufacturer:."
                - If none are found, return "Not specified."
                
                Goods & Services:\n
                - Extract the core goods and services associated with the trademark or product.  
                - Provide relevant detail (e.g., "permanent hair color," "nail care polish," "hair accessories," or "hair styling tools").
    
                Return output only in the exact below-mentioned format:  
                Example output format:  
                    Cited_term: ColourGrip,\n  
                    Owner_name: Matrix, \n 
                    Goods_&_services: Hair color products,\n    
"""

    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant for extracting Meta Data based on the given Images [Note: Only return the required extracted data in the exact format mentioned].",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                ],
            },
        ],
        "max_tokens": 200,
        "temperature": 0,
    }

    headers = {"Content-Type": "application/json", "api-key": api_key}
    response = requests.post(
        f"{azure_endpoint}/openai/deployments/{model}/chat/completions?api-version=2024-10-01-preview",
        headers=headers,
        data=json.dumps(data),
    )

    if response.status_code == 200:
        extracted_data = response.json()["choices"][0]["message"]["content"]
    else:
        extracted_data = "Failed to extract data"

    return {extracted_data.strip()}
