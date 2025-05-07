from typing import Dict, List, Union
import json
from ..utils.ml_utils import (
    is_semantically_equivalent,
    is_phonetically_equivalent,
    first_words_phonetically_equivalent,
)
from ..utils.validation import is_similar_goods_services
from ..utils.text_processing import normalize_text


def compare_trademarks(
    existing_trademark: Dict[str, Union[str, List[int]]],
    proposed_name: str,
    proposed_class: str,
    proposed_goods_services: str,
) -> Dict[str, Union[str, int]]:
    """Compare existing trademark with proposed trademark"""
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

    # Condition 3: Target market and goods/services overlap
    condition_3_satisfied = is_similar_goods_services(
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

        # Generate detailed reasoning
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
            condition_1_reasoning = (
                f"Condition 1: Satisfied - {', '.join(condition_1_details)}."
            )
        else:
            condition_1_reasoning = "Condition 1: Not Satisfied."

        reasoning = (
            f"{condition_1_reasoning} \n"
            f"Condition 2: {'Satisfied' if condition_2_satisfied else 'Not Satisfied'} - Overlap in class numbers.\n"
            f"Condition 3: {'Satisfied' if condition_3_satisfied else 'Not Satisfied'} - Overlap in goods/services and target market."
        )

    # Determine if it's a word or design mark
    if existing_trademark["design_phrase"] == "No Design phrase presented in document":
        design_label = "Word"
    else:
        design_label = "Design"

    # Prepare the result dictionary
    result = {
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
        "Mark": "   ✔️" if condition_1_satisfied else " ",
        "Class": "   ✔️" if condition_2_satisfied else " ",
        "Goods/Services": "   ✔️" if condition_3_satisfied else " ",
        "Direct Hit": " ",
    }

    return result


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
