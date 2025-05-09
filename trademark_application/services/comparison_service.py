from typing import Dict, List, Union
import json
from utils.ml_utils import (
    is_semantically_equivalent,
    is_phonetically_equivalent,
    first_words_phonetically_equivalent,
)
from utils.validation import is_similar_goods_services
from utils.text_processing import normalize_text

import re
from sentence_transformers import SentenceTransformer, util
from fuzzywuzzy import fuzz

# Load semantic model once at module level for efficiency
semantic_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def compare_trademarks(
    existing_trademark: Dict[str, Union[str, List[int]]],
    proposed_name: str,
    proposed_class: str,
    proposed_goods_services: str,
) -> Dict[str, Union[str, int]]:
    # Convert proposed classes to a list of integers
    proposed_classes = [int(c.strip()) for c in proposed_class.split(",")]

    # Condition 1A: Exact character-for-character match
    condition_1A_satisfied = (
        existing_trademark["trademark_name"].strip().lower()
        == proposed_name.strip().lower()
    )

    # Condition 1B: Semantically equivalent
    condition_1B_satisfied = is_semantically_equivalent(
        existing_trademark["trademark_name"], proposed_name
    )

    # Condition 1C: Phonetically equivalent
    condition_1C_satisfied = is_phonetically_equivalent(
        existing_trademark["trademark_name"], proposed_name
    )

    # Condition 1D: First two or more words are phonetically equivalent
    condition_1D_satisfied = first_words_phonetically_equivalent(
        existing_trademark["trademark_name"], proposed_name
    )

    # Condition 1E: Proposed name is the first word of the existing trademark
    condition_1E_satisfied = (
        existing_trademark["trademark_name"].lower().startswith(proposed_name.lower())
    )

    # Check if any Condition 1 is satisfied
    condition_1_satisfied = any(
        [
            condition_1A_satisfied,
            condition_1B_satisfied,
            condition_1C_satisfied,
            condition_1D_satisfied,
            condition_1E_satisfied,
        ]
    )

    # Condition 2: Overlap in International Class Numbers
    condition_2_satisfied = bool(
        set(existing_trademark["international_class_number"]) & set(proposed_classes)
    )

    from nltk.stem import WordNetLemmatizer

    # Condition 3: Target market and goods/services overlap
    def target_market_and_goods_overlap(existing_gs, proposed_gs, threshold=0.65):

        existing_normalized = normalize_text(existing_gs)
        proposed_normalized = normalize_text(proposed_gs)

        embeddings1 = semantic_model.encode(existing_normalized, convert_to_tensor=True)
        embeddings2 = semantic_model.encode(proposed_normalized, convert_to_tensor=True)
        similarity_score = util.cos_sim(embeddings1, embeddings2).item()
        # st.write("Semantic Similarity Score:", similarity_score)
        if similarity_score >= threshold:
            return True

        # Split into words and lemmatize
        lemmatizer = WordNetLemmatizer()
        existing_words = {
            lemmatizer.lemmatize(word) for word in existing_normalized.split()
        }
        proposed_words = {
            lemmatizer.lemmatize(word) for word in proposed_normalized.split()
        }

        # Check for common words
        common_words = existing_words.intersection(proposed_words)
        # st.write("Common Words:", existing_gs , common_words)
        return bool(common_words)

    condition_3_satisfied = target_market_and_goods_overlap(
        existing_trademark["goods_services"], proposed_goods_services
    )

    # Clean and standardize the trademark status
    status = existing_trademark["status"].strip().lower()

    # Check for 'Cancelled' or 'Abandoned' status
    if any(keyword in status for keyword in ["cancelled", "abandoned", "expired"]):
        conflict_grade = "Low"
        reasoning = "The existing trademark status is 'Cancelled' or 'Abandoned.'"
    else:
        points = sum(
            [
                condition_1_satisfied,  # 1 point if any Condition 1 is satisfied
                condition_2_satisfied,  # 1 point if Condition 2 is satisfied
                condition_3_satisfied,  # 1 point if Condition 3 is satisfied
            ]
        )

        # Determine conflict grade based on points
        if points == 3:
            conflict_grade = "High"
        elif points == 2:
            conflict_grade = "Moderate"
        elif points == 1:
            conflict_grade = "Low"
        else:
            conflict_grade = "None"

        if condition_1_satisfied:
            condition_1_details = []
            if condition_1A_satisfied:
                condition_1_details.append("Exact character-for-character match")
            if condition_1B_satisfied:
                condition_1_details.append("Semantically equivalent")
            if condition_1C_satisfied:
                condition_1_details.append("Phonetically equivalent")
            if condition_1D_satisfied:
                condition_1_details.append(
                    "First two or more words are phonetically equivalent"
                )
            if condition_1E_satisfied:
                condition_1_details.append(
                    "Proposed name is the first word of the existing trademark"
                )

        # Generate detailed reasoning for Condition 1
        if condition_1_satisfied:
            condition_1_reasoning = (
                f"Condition 1: Satisfied - {', '.join(condition_1_details)}."
            )
        else:
            condition_1_reasoning = "Condition 1: Not Satisfied."

        # Reasoning
        reasoning = (
            f"{condition_1_reasoning} \n"
            f"Condition 2: {'Satisfied' if condition_2_satisfied else 'Not Satisfied'} - Overlap in class numbers.\n"
            f"Condition 3: {'Satisfied' if condition_3_satisfied else 'Not Satisfied'} - Overlap in goods/services and target market."
        )

    if existing_trademark["design_phrase"] == "No Design phrase presented in document":
        design_label = "Word"
    else:
        design_label = "Design"

    if condition_1_satisfied and condition_2_satisfied and condition_3_satisfied:
        return {
            "Trademark Name , Class Number": f"{existing_trademark['trademark_name']} , {existing_trademark['international_class_number']}",
            "Trademark name": existing_trademark["trademark_name"],
            "Trademark Status": existing_trademark["status"],
            "Trademark Owner": existing_trademark["owner"],
            "Trademark class Number": existing_trademark["international_class_number"],
            "Trademark serial number": existing_trademark["serial_number"],
            "Serial / Registration Number": f"{existing_trademark['serial_number']} / {existing_trademark['registration_number']}",
            "Trademark registration number": existing_trademark["registration_number"],
            "Trademark design phrase": existing_trademark["design_phrase"],
            "Word/Design": design_label,
            "conflict_grade": conflict_grade,
            "reasoning": reasoning,
            "Mark": "   ✔️",
            "Class": "   ✔️",
            "Goods/Services": "   ✔️",
            "Direct Hit": " ",
        }

    elif condition_1_satisfied and condition_2_satisfied:
        return {
            "Trademark Name , Class Number": f"{existing_trademark['trademark_name']} , {existing_trademark['international_class_number']}",
            "Trademark name": existing_trademark["trademark_name"],
            "Trademark Status": existing_trademark["status"],
            "Trademark Owner": existing_trademark["owner"],
            "Trademark class Number": existing_trademark["international_class_number"],
            "Trademark serial number": existing_trademark["serial_number"],
            "Serial / Registration Number": f"{existing_trademark['serial_number']} / {existing_trademark['registration_number']}",
            "Trademark registration number": existing_trademark["registration_number"],
            "Trademark design phrase": existing_trademark["design_phrase"],
            "Word/Design": design_label,
            "conflict_grade": conflict_grade,
            "reasoning": reasoning,
            "Mark": "   ✔️",
            "Class": "   ✔️",
            "Goods/Services": "  ",
            "Direct Hit": " ",
        }

    elif condition_2_satisfied and condition_3_satisfied:
        return {
            "Trademark Name , Class Number": f"{existing_trademark['trademark_name']} , {existing_trademark['international_class_number']}",
            "Trademark name": existing_trademark["trademark_name"],
            "Trademark Status": existing_trademark["status"],
            "Trademark Owner": existing_trademark["owner"],
            "Trademark class Number": existing_trademark["international_class_number"],
            "Trademark serial number": existing_trademark["serial_number"],
            "Serial / Registration Number": f"{existing_trademark['serial_number']} / {existing_trademark['registration_number']}",
            "Trademark registration number": existing_trademark["registration_number"],
            "Trademark design phrase": existing_trademark["design_phrase"],
            "Word/Design": design_label,
            "conflict_grade": conflict_grade,
            "reasoning": reasoning,
            "Mark": " ",
            "Class": "   ✔️",
            "Goods/Services": "   ✔️",
            "Direct Hit": " ",
        }

    else:
        return {
            "Trademark Name , Class Number": f"{existing_trademark['trademark_name']} , {existing_trademark['international_class_number']}",
            "Trademark name": existing_trademark["trademark_name"],
            "Trademark Status": existing_trademark["status"],
            "Trademark Owner": existing_trademark["owner"],
            "Trademark class Number": existing_trademark["international_class_number"],
            "Trademark serial number": existing_trademark["serial_number"],
            "Serial / Registration Number": f"{existing_trademark['serial_number']} / {existing_trademark['registration_number']}",
            "Trademark registration number": existing_trademark["registration_number"],
            "Trademark design phrase": existing_trademark["design_phrase"],
            "Word/Design": design_label,
            "conflict_grade": conflict_grade,
            "reasoning": reasoning,
            "Mark": " ",
            "Class": "   ✔️",
            "Goods/Services": " ",
            "Direct Hit": " ",
        }


def validate_trademark_relevance(conflicts_array, proposed_goods_services):
    """Pre-filter trademarks that don't have similar or identical goods/services"""
    # Parse conflicts_array if it's a string
    if isinstance(conflicts_array, str):
        try:
            conflicts = json.loads(conflicts_array)
        except json.JSONDecodeError:
            conflicts = (
                eval(conflicts_array) if conflicts_array.strip().startswith("[") else []
            )
    else:
        conflicts = conflicts_array

    relevant_conflicts = []
    excluded_count = 0

    for conflict in conflicts:
        if "goods_services" in conflict:
            if is_similar_goods_services(
                conflict["goods_services"], proposed_goods_services
            ):
                relevant_conflicts.append(conflict)
            else:
                excluded_count += 1
        else:
            relevant_conflicts.append(conflict)

    return relevant_conflicts, excluded_count


def filter_by_gpt_response(conflicts, gpt_json):
    """Remove trademarks that GPT flagged as lacking goods/services overlap"""
    if isinstance(gpt_json, str):
        try:
            gpt_json = json.loads(gpt_json)
        except json.JSONDecodeError:
            return conflicts

    gpt_results = gpt_json.get("results", [])
    overlapping_marks = {
        result["mark"] for result in gpt_results if result.get("overlap") is True
    }
    filtered_conflicts = [c for c in conflicts if c.get("mark") in overlapping_marks]

    return filtered_conflicts


def assess_conflict(
    existing_trademark: List[Dict[str, Union[str, List[int]]]],
    proposed_name: str,
    proposed_class: str,
    proposed_goods_services: str,
) -> List[Dict[str, int]]:

    import phonetics
    from sentence_transformers import util
    from rapidfuzz import fuzz

    def normalize_text_name(text):
        """Normalize text by converting to lowercase, removing special characters, and standardizing whitespace."""
        # Remove punctuation except hyphens and spaces
        # text = re.sub(r"[^\w\s-’]", "", text)
        # Convert to lowercase
        text = re.sub(r"’", " ", text)
        text = text.lower()
        # Standardize whitespace
        return " ".join(text.split())

    # Clean and standardize the trademark status
    status = existing_trademark["status"].strip().lower()
    # Check for 'Cancelled' or 'Abandoned' status
    if any(keyword in status for keyword in ["cancelled", "abandoned", "expired"]):
        conflict_grade = "Low"
        reasoning = "The existing trademark status is 'Cancelled' or 'Abandoned.'"
    else:

        existing_trademark_name = normalize_text_name(
            existing_trademark["trademark_name"]
        )
        proposed_name = normalize_text_name(proposed_name)

        # Phonetic Comparison
        existing_phonetic = phonetics.metaphone(existing_trademark_name)
        proposed_phonetic = phonetics.metaphone(proposed_name)
        phonetic_match = existing_phonetic == proposed_phonetic

        # Semantic Similarity
        existing_embedding = semantic_model.encode(
            existing_trademark_name, convert_to_tensor=True
        )
        proposed_embedding = semantic_model.encode(
            proposed_name, convert_to_tensor=True
        )
        semantic_similarity = util.cos_sim(
            existing_embedding, proposed_embedding
        ).item()

        # String Similarity
        string_similarity = fuzz.ratio(existing_trademark_name, proposed_name)

        def is_substring_match(name1, name2):
            return name1.lower() in name2.lower() or name2.lower() in name1.lower()

        substring_match = is_substring_match(existing_trademark_name, proposed_name)

        def has_shared_word(name1, name2):
            words1 = set(name1.lower().split())
            words2 = set(name2.lower().split())
            return not words1.isdisjoint(words2)

        shared_word = has_shared_word(existing_trademark_name, proposed_name)

        from fuzzywuzzy import fuzz

        def is_phonetic_partial_match(name1, name2, threshold=55):
            return fuzz.partial_ratio(name1.lower(), name2.lower()) >= threshold

        phonetic_partial_match = is_phonetic_partial_match(
            existing_trademark_name, proposed_name
        )

        # st.write(f"Shared word : {existing_trademark_name} : {shared_word}")
        # st.write(f"Phonetic partial match : {existing_trademark_name} : {phonetic_partial_match}")
        # st.write(f"Substring match : {existing_trademark_name} : {substring_match}")

        # Decision Logic
        if (
            phonetic_match
            or substring_match
            or shared_word
            or semantic_similarity >= 0.5
            or string_similarity >= 55
            or phonetic_partial_match >= 55
        ):
            conflict_grade = "Name-Match"
        else:
            conflict_grade = "Low"

        semantic_similarity = semantic_similarity * 100

        # Reasoning
        reasoning = (
            f"Condition 1: {'Satisfied' if phonetic_match else 'Not Satisfied'} - Phonetic match found.\n"
            f"Condition 2: {'Satisfied' if substring_match else 'Not Satisfied'} - Substring match found.\n"
            f"Condition 3: {'Satisfied' if shared_word else 'Not Satisfied'} - Substring match found.\n"
            f"Condition 4: {'Satisfied' if phonetic_partial_match >= 55 else 'Not Satisfied'} - String similarity is ({round(phonetic_partial_match)}%).\n"
            f"Condition 5: {'Satisfied' if semantic_similarity >= 50 else 'Not Satisfied'} - Semantic similarity is ({round(semantic_similarity)}%).\n"
            f"Condition 6: {'Satisfied' if string_similarity >= 55 else 'Not Satisfied'} - String similarity is ({round(string_similarity)}%).\n"
        )

    if existing_trademark["design_phrase"] == "No Design phrase presented in document":
        design_label = "Word"
    else:
        design_label = "Design"

    return {
        "Trademark Name , Class Number": f"{existing_trademark['trademark_name']} , {existing_trademark['international_class_number']}",
        "Trademark name": existing_trademark["trademark_name"],
        "Trademark Status": existing_trademark["status"],
        "Trademark Owner": existing_trademark["owner"],
        "Trademark class Number": existing_trademark["international_class_number"],
        "Trademark serial number": existing_trademark["serial_number"],
        "Serial / Registration Number": f"{existing_trademark['serial_number']} / {existing_trademark['registration_number']}",
        "Trademark registration number": existing_trademark["registration_number"],
        "Trademark design phrase": existing_trademark["design_phrase"],
        "Word/Design": design_label,
        "conflict_grade": conflict_grade,
        "reasoning": reasoning,
        "Mark": " ",
        "Class": " ",
        "Goods/Services": " ",
        "Direct Hit": "   ✔️",
    }
