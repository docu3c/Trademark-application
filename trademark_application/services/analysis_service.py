from typing import Dict, List, Any
import json, re
from config.settings import get_azure_client
from utils.validation import validate_trademark_relevance
from utils.ml_utils import consistency_check, component_consistency_check
from utils.formatting_utils import (
    clean_and_format_opinion,
    format_comprehensive_opinion,
)


def run_trademark_analysis(
    proposed_name, proposed_class, proposed_goods_services, conflicts_data
):
    """
    Run a complete trademark analysis with proper error handling.

    Args:
        proposed_name: Name of the proposed trademark
        proposed_class: Class of the proposed trademark
        proposed_goods_services: Goods and services of the proposed trademark
        conflicts_data: Array of potential conflict trademarks

    Returns:
        A comprehensive trademark opinion
    """
    try:
        if not proposed_name or not proposed_class or not proposed_goods_services:
            return "Error: Missing required trademark information."

        if not conflicts_data:
            return "Error: No conflict data provided for analysis."

        opinion = generate_trademark_opinion(
            conflicts_data, proposed_name, proposed_class, proposed_goods_services
        )
        return opinion

    except Exception as e:
        return f"Error running trademark analysis: {str(e)}"


def section_one_analysis(mark, class_number, goods_services, relevant_conflicts):
    """
    Perform Section I: Comprehensive Trademark Hit Analysis
    """
    client = get_azure_client()

    system_prompt = """
Analyze proposed trademark conflicts using these precise steps:

1. COORDINATED CLASS ANALYSIS:
   - Identify classes related to the proposed goods/services
   - Justify each coordinated class with direct commercial links
   - Consider channels of trade, target consumers, and common industry practices
   - Provide detailed justification for each coordinated class

2. IDENTICAL MARK ANALYSIS:
   - Include here if proposed mark and conflict mark have the exact same name
   - For each identical mark, specify:
     * class_match (True if in same or coordinated class)
     * goods_services_match (True if goods/services are similar/related/overlapping)

3. ONE LETTER DIFFERENCE ANALYSIS:
   - Identify marks with only ONE letter difference (substitution, addition, or deletion)
   - For each mark, specify:
     * class_match (True if in same or coordinated class)
     * goods_services_match (True if goods/services are similar/related/overlapping)
     * Type of letter variation (substitution, addition, deletion)

4. TWO LETTER DIFFERENCE ANALYSIS:
   - Identify marks that differ by exactly TWO letters (substitution, addition, deletion, or a mix)
   - For each mark, specify:
     * class_match (True if in same or coordinated class)
     * goods_services_match (True if goods/services are similar/related/overlapping)
     * Type of letter variation (TWO_SUBSTITUTIONS|TWO_ADDITIONS|TWO_DELETIONS|MIXED)

5. SIMILAR MARK ANALYSIS (CRITICAL ASSESSMENT):
   a) PROMINENT WORD ANALYSIS (FIRST SUBSTEP):
      - For each potentially similar mark, FIRST identify the prominent word(s):
        * The most distinctive or unique word in a multi-word mark

      Examples of prominent word identification:
      * In "Long Live Hair" - "Long Live" is prominent (distinctive phrase)
      * In "Hair Genius" - "Genius" is prominent (more distinctive than "Hair")
      * In "Black Marsmallow" - "Marsmallow" is prominent
      * In "Alpha Brain Smart Gummies" - "Alpha Brain" is prominent (brand element)
      * In "Natural Beauty Cream" - "Beauty" is NOT prominent (descriptive term)
      * In "Organic Food Market" - "Organic" is NOT prominent (generic term)
      * Consider Plural Forms: "Grip" and "Grips" are considered different words

   b) SIMILARITY ANALYSIS (SECOND SUBSTEP):
      - ONLY proceed with similarity analysis if prominent words match between marks
      - If prominent words don't match, mark as NOT similar
      - For matching prominent words, analyze:
        * Phonetic Similarity (Sound):
          - Evaluate how trademarks sound when pronounced naturally
          - Analyze similarities in rhythm, cadence, syllable count/stress
          - Focus on marks sharing dominant or memorable sound patterns
          - Consider variations in word combination (e.g., "COLORGRIP" vs. "COLOR GRIP")
          - Detect phonetic similarity where word structures differ
        
        * Semantic Similarity (Meaning/Concept):
          - Examine inherent meanings, connotations, and commercial impressions
          - Identify marks suggesting same or similar concepts
          - Look for marks creating analogous mental associations
          - Consider combined words (e.g., "COLORGRIP" and "COLOR HOLD" both imply color retention)
          - For multi-word marks, search for ALL essential components

   c) For each similar mark, specify:
      * class_match (True if in same or coordinated class)
      * goods_services_match (True if goods/services are similar/related/overlapping)
      * Similarity type (Phonetic, Semantic, Commercial Impression, or combination)
      * Prominent word match status
      * Detailed reasoning for similarity determination

6. CROWDED FIELD ANALYSIS:
   - Count only marks that passed prominent word analysis
   - Calculate percentage with DIFFERENT owners
   - Determine crowded field status (>50% different owners)
   - Explain practical implications on trademark protection scope

FORMAT RESPONSE IN JSON:
{
  "identified_coordinated_classes": [CLASS NUMBERS],
  "coordinated_classes_explanation": "[BRIEF EXPLANATION]",
  "identical_marks": [
    {
      "mark": "[NAME]",
      "owner": "[OWNER]",
      "goods_services": "[DESCRIPTION]",
      "status": "[STATUS]",
      "class": "[CLASS]",
      "class_match": true|false,
      "goods_services_match": true|false
    }
  ],
  "one_letter_marks": [
    {
      "mark": "[NAME]",
      "owner": "[OWNER]",
      "goods_services": "[DESCRIPTION]",
      "status": "[STATUS]",
      "class": "[CLASS]",
      "class_match": true|false,
      "goods_services_match": true|false,
      "letter_variation": "[SUBSTITUTION|ADDITION|DELETION]"
    }
  ],
  "two_letter_marks": [
    {
      "mark": "[NAME]",
      "owner": "[OWNER]",
      "goods_services": "[DESCRIPTION]",
      "status": "[STATUS]",
      "class": "[CLASS]",
      "class_match": true|false,
      "goods_services_match": true|false,
      "letter_variation": "[TWO_SUBSTITUTIONS|TWO_ADDITIONS|TWO_DELETIONS|MIXED]"
    }
  ],
  "similar_marks": [
    {
      "mark": "[NAME]",
      "prominent_words": ["[WORD1]", "[WORD2]"],
      "prominent_word_match": true|false,
      "similarity_type": "[PHONETIC|SEMANTIC|COMMERCIAL|COMBINATION]",
      "owner": "[OWNER]",
      "goods_services": "[DESCRIPTION]",
      "status": "[STATUS]",
      "class": "[CLASS]",
      "class_match": true|false,
      "goods_services_match": true|false,
      "similarity_reasoning": "[DETAILED EXPLANATION]"
    }
  ],
  "crowded_field": {
    "is_crowded": true|false,
    "percentage": [PERCENTAGE],
    "explanation": "[BRIEF EXPLANATION]",
    "protection_implications": "[EXPLANATION OF IMPACT ON TRADEMARK PROTECTION]"
  }
}
"""

    user_message = f""" 
Proposed Trademark: {mark}
Class: {class_number}
Goods/Services: {goods_services}

Trademark Conflicts:
{json.dumps(relevant_conflicts, indent=2)}

Analyze ONLY Section I: Comprehensive Trademark Hit Analysis. Follow these precise steps:

STEP 1: COORDINATED CLASS ANALYSIS
- Carefully examine the proposed goods/services
- Identify ALL classes related to the primary class "{class_number}"
- Justify each coordinated class with direct commercial links
- Provide a complete list of all relevant classes for conflict analysis

STEP 2: IDENTICAL MARK ANALYSIS
- Find exact character matches to "{mark}" (case-insensitive)
  * Document class and goods/services matching

STEP 3: One Letter Difference Analysis  
    - Identify marks with only ONE letter difference (substitution, addition, or deletion).  
    - For each, determine whether there's a `class_match` and `goods_services_match`.
    
STEP 4: Two Letter Difference Analysis  
    - Identify marks that differ by exactly TWO letters (substitution, addition, deletion, or a mix).  
    - For each, indicate `class_match` and `goods_services_match`.

STEP 5: SIMILAR MARK ANALYSIS
- For each potentially similar mark:
  * FIRST identify prominent words
  * ONLY if prominent words match, then analyze other words
  * If prominent words don't match, mark as NOT similar
  * For matching prominent words, analyze:
    - Phonetic similarity of other words
    - Semantic similarity of other words
    - Functional similarity of other words
  * Document similarity type and matching criteria

STEP 6: CROWDED FIELD ANALYSIS
- Count only marks that passed prominent word analysis
- Calculate percentage with DIFFERENT owners
- Determine if field is "crowded" (>50% different owners)
- Explain trademark protection implications

FORMAT RESPONSE IN JSON as specified in the instructions.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,
        )

        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content

            # Extract JSON data
            json_match = re.search(
                r"```json\s*(.*?)\s*```|({[\s\S]*})", content, re.DOTALL
            )
            if json_match:
                json_str = json_match.group(1) or json_match.group(2)
                try:
                    raw_results = json.loads(json_str)
                    # Apply consistency checking
                    corrected_results = consistency_check(mark, raw_results)
                    return corrected_results
                except json.JSONDecodeError:
                    return {
                        "identified_coordinated_classes": [],
                        "coordinated_classes_explanation": "Unable to identify coordinated classes",
                        "identical_marks": [],
                        "one_letter_marks": [],
                        "two_letter_marks": [],
                        "similar_marks": [],
                        "crowded_field": {
                            "is_crowded": False,
                            "percentage": 0,
                            "explanation": "Unable to determine crowded field status",
                        },
                    }
            else:
                return {
                    "identified_coordinated_classes": [],
                    "coordinated_classes_explanation": "Unable to identify coordinated classes",
                    "identical_marks": [],
                    "one_letter_marks": [],
                    "two_letter_marks": [],
                    "similar_marks": [],
                    "crowded_field": {
                        "is_crowded": False,
                        "percentage": 0,
                        "explanation": "Unable to determine crowded field status",
                    },
                }
        else:
            return {
                "identified_coordinated_classes": [],
                "coordinated_classes_explanation": "Unable to identify coordinated classes",
                "identical_marks": [],
                "one_letter_marks": [],
                "two_letter_marks": [],
                "similar_marks": [],
                "crowded_field": {
                    "is_crowded": False,
                    "percentage": 0,
                    "explanation": "Unable to determine crowded field status",
                },
            }
    except Exception as e:
        print(f"Error in section_one_analysis: {str(e)}")
        return {
            "identified_coordinated_classes": [],
            "coordinated_classes_explanation": "Error occurred during analysis",
            "identical_marks": [],
            "one_letter_marks": [],
            "two_letter_marks": [],
            "similar_marks": [],
            "crowded_field": {
                "is_crowded": False,
                "percentage": 0,
                "explanation": "Error occurred during analysis",
            },
        }


def section_two_analysis(mark, class_number, goods_services, relevant_conflicts):
    """Perform Section II: Component Analysis."""
    client = get_azure_client()

    system_prompt = """
You are a trademark attorney and expert in trademark opinion writing. Your task is to conduct **Section II: Component Analysis** for a proposed trademark. Please follow these structured steps and format your entire response in JSON.

🔍 COMPONENT ANALYSIS REQUIREMENTS:

(a) Break the proposed trademark into individual components (if compound).  
(b) For each component, identify relevant conflict marks that incorporate that component.  
(c) For each conflict, provide the following details:  
    - Full mark  
    - Owner name  
    - Goods/services (FULL description)  
    - Class number  
    - Registration status (REGISTERED or PENDING)  
    - Flags for:  
        * `class_match`: True if in the same or coordinated class  
        * `goods_services_match`: True if similar or overlapping goods/services  
(d) Evaluate the distinctiveness of each component:  
    - Use one of: `GENERIC`, `DESCRIPTIVE`, `SUGGESTIVE`, `ARBITRARY`, `FANCIFUL`

📘 COORDINATED CLASS ANALYSIS (CRITICAL):

You **must** identify not only exact class matches but also any coordinated or related classes. Use trademark practice and industry standards to determine which classes relate to the proposed goods/services. 

✅ Example coordinated class groupings (not exhaustive):  
- **Food & Beverage**: 29, 30, 31, 32, 35, 43  
- **Furniture/Home Goods**: 20, 35, 42  
- **Fashion**: 18, 25, 35  
- **Technology/Software**: 9, 38, 42  
- **Health/Beauty**: 3, 5, 44  
- **Entertainment**: 9, 41, 42

You are expected to go **beyond** this list and apply expert reasoning based on the proposed trademark's actual goods/services. Clearly explain **why** the identified classes are relevant.

⚠️ KEY REMINDERS:
- If ANY component appears in ANY other class—even outside the exact class—it must be flagged.
- Do not overlook conflicts in **related/coordinated classes**—mark `class_match = true` for all those.
- Include full goods/services text. Avoid summarizing.

📊 CROWDED FIELD ANALYSIS:

Provide a statistical overview:
- Count the total number of relevant marks identified across components  
- Calculate the percentage owned by distinct owners  
- Determine if the field is "crowded" (typically over 50% from different owners)  
- Explain how a crowded field may reduce trademark risk

🧾 OUTPUT FORMAT (REQUIRED: JSON ONLY):

{
  "identified_coordinated_classes": [LIST OF CLASS NUMBERS],
  "coordinated_classes_explanation": "[DETAILED EXPLANATION]",
  "components": [
    {
      "component": "[COMPONENT NAME]",
      "marks": [
        {
          "mark": "[CONFLICTING TRADEMARK]",
          "owner": "[OWNER NAME]",
          "goods_services": "[FULL GOODS/SERVICES DESCRIPTION]",
          "status": "[REGISTERED/PENDING]",
          "class": "[CLASS NUMBER]",
          "class_match": true|false,
          "goods_services_match": true|false
        }
      ],
      "distinctiveness": "[GENERIC|DESCRIPTIVE|SUGGESTIVE|ARBITRARY|FANCIFUL]"
    }
  ],
  "crowded_field": {
    "total_hits": [NUMBER],
    "distinct_owner_percentage": [PERCENTAGE],
    "is_crowded": true|false,
    "explanation": "[EXPLAIN IMPACT OF A CROWDED FIELD ON RISK]"
  }
}
⭐ IMPORTANT: Sort all identified conflicting marks alphabetically by mark name under each component.
"""

    user_message = f"""
Proposed Trademark: {mark}
Class: {class_number}
Goods/Services: {goods_services}

Trademark Conflicts:
{json.dumps(relevant_conflicts, indent=2)}

Analyze ONLY Section II: Component Analysis.

IMPORTANT REMINDERS:

- Break the proposed trademark into components (if compound) and analyze conflicts that contain each component.
- For each conflicting mark:
  * Include the full mark, owner name, class, status (REGISTERED/PENDING), and FULL goods/services description.
  * Set `class_match = True` if:
      - The conflicting mark is in the same class as "{class_number}", OR
      - The conflicting mark is in a related or coordinated class based on the proposed goods/services "{goods_services}"
  * Set `goods_services_match = True` if the conflicting mark covers similar or overlapping goods/services to "{goods_services}"

- For coordinated class analysis:
  * Identify ALL classes that are related or coordinated to the proposed class.
  * Provide reasoning for why each class is coordinated, based on standard groupings and your analysis of "{goods_services}"

- Crowded Field Analysis:
  1. Show the total number of compound mark hits involving ANY component of the proposed trademark.
  2. Count how many distinct owners are represented among those marks.
  3. Calculate the percentage of marks owned by different parties.
  4. If more than 50% of the marks have different owners, set `is_crowded = true` and explain how this reduces potential risk.

- Output must be detailed, thorough, and clearly structured. Ensure that all logic is explicitly shown and justified.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,
        )

        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content

            # Extract JSON data
            json_match = re.search(
                r"```json\s*(.*?)\s*```|({[\s\S]*})", content, re.DOTALL
            )
            if json_match:
                json_str = json_match.group(1) or json_match.group(2)
                try:
                    raw_results = json.loads(json_str)
                    # Apply consistency checking
                    corrected_results = component_consistency_check(mark, raw_results)
                    return corrected_results
                except json.JSONDecodeError:
                    return {
                        "identified_coordinated_classes": [],
                        "coordinated_classes_explanation": "Unable to identify coordinated classes",
                        "components": [],
                        "crowded_field": {
                            "total_hits": 0,
                            "distinct_owner_percentage": 0,
                            "is_crowded": False,
                            "explanation": "Unable to determine crowded field status.",
                        },
                    }
            else:
                return {
                    "identified_coordinated_classes": [],
                    "coordinated_classes_explanation": "Unable to identify coordinated classes",
                    "components": [],
                    "crowded_field": {
                        "total_hits": 0,
                        "distinct_owner_percentage": 0,
                        "is_crowded": False,
                        "explanation": "Unable to determine crowded field status.",
                    },
                }
        else:
            return {
                "identified_coordinated_classes": [],
                "coordinated_classes_explanation": "Unable to identify coordinated classes",
                "components": [],
                "crowded_field": {
                    "total_hits": 0,
                    "distinct_owner_percentage": 0,
                    "is_crowded": False,
                    "explanation": "Unable to determine crowded field status.",
                },
            }
    except Exception as e:
        print(f"Error in section_two_analysis: {str(e)}")
        return {
            "identified_coordinated_classes": [],
            "coordinated_classes_explanation": "Error occurred during analysis",
            "components": [],
            "crowded_field": {
                "total_hits": 0,
                "distinct_owner_percentage": 0,
                "explanation": "Unable to determine crowded field status.",
            },
        }


def section_three_analysis(
    mark, class_number, goods_services, section_one_results, section_two_results=None
):
    """
    Perform Section III: Risk Assessment and Summary

    Args:
        mark: The proposed trademark
        class_number: The class of the proposed trademark
        goods_services: The goods and services of the proposed trademark
        section_one_results: Results from Section I
        section_two_results: Results from Section II (may be None if Section II was skipped)

    Returns:
        A structured risk assessment and summary
    """
    client = get_azure_client()

    # Check if we should skip Section Two analysis and directly set risk to medium-high
    skip_section_two = False
    skip_reason = ""

    # Check for phonetic or semantic marks with class match and goods/services match
    for mark_entry in section_one_results.get("similar_marks", []):
        if mark_entry.get("similarity_type") in ["Phonetic", "Semantic"]:
            if mark_entry.get("class_match") and mark_entry.get("goods_services_match"):
                skip_section_two = True
                skip_reason = "Found a Phonetic or Semantic similar mark with both class match and goods/services match"
                break
            elif mark_entry.get("class_match"):
                skip_section_two = True
                skip_reason = "Found a Phonetic or Semantic similar mark with coordinated class match"
                break

    system_prompt = """
You are a trademark expert attorney specializing in trademark opinion writing.

Please analyze the results from Sections I and II to create Section III: Risk Assessment and Summary. Your analysis should address the following elements in detail:

1. Likelihood of Confusion:
   • Evaluate potential consumer confusion between the proposed trademark and any conflicting marks.
   • Take into account both exact class matches and coordinated/related class conflicts.
   • Discuss phonetic, visual, or conceptual similarities, and overlapping goods/services.

2. Descriptiveness:
   • Analyze whether the proposed trademark is descriptive in light of the goods/services and compared to existing conflicts.
   • Note whether any conflicts suggest a common industry term or generic language.

3. Aggressive Enforcement and Litigious Behavior:
   • Identify any conflicting mark owners with a history of enforcement or litigation.
   • Extract and summarize patterns such as frequent oppositions, cease-and-desist actions, or broad trademark portfolios.

4. Overall Risk Rating:
   • Provide risk ratings for Registration and Use separately:
     - For Registration: MEDIUM-HIGH when identical marks are present
     - For Use: MEDIUM-HIGH when identical marks are present
     - When no identical marks exist but similar marks are found:
       * Start with MEDIUM-HIGH risk level
       * If crowded field exists (>50% different owners), reduce risk by one level:
         - MEDIUM-HIGH → MEDIUM-LOW
         - MEDIUM → LOW (but never go below MEDIUM-LOW)
   • Justify the rating using findings from:
     - Class and goods/services overlap (including coordinated class logic)
     - Crowded field metrics (e.g., distinct owner percentage)
     - Descriptiveness and enforceability of components
     - History of enforcement activity

IMPORTANT:
- When determining likelihood of confusion, incorporate coordinated class analysis.
- Crowded field data from Section II must be factored into risk mitigation. If >50% of conflicting marks are owned by unrelated entities, that reduces enforceability and legal risk by one level.
- For identical marks, ALWAYS rate risk as MEDIUM-HIGH for Registration and MEDIUM-HIGH for Use, regardless of crowded field percentage.
- When no identical marks exist but similar marks are found in a crowded field (>50% different owners), reduce risk by one level.
- Do NOT increase risk to HIGH even when identical marks are present.
- Do NOT reduce risk level below MEDIUM-LOW.

Your output MUST be returned in the following JSON format:

{
  "likelihood_of_confusion": [
    "[KEY POINT ABOUT LIKELIHOOD OF CONFUSION]",
    "[ADDITIONAL POINT ABOUT LIKELIHOOD OF CONFUSION]"
  ],
  "descriptiveness": [
    "[KEY POINT ABOUT DESCRIPTIVENESS]"
  ],
  "aggressive_enforcement": {
    "owners": [
      {
        "name": "[OWNER NAME]",
        "enforcement_patterns": [
          "[PATTERN 1]",
          "[PATTERN 2]"
        ]
      }
    ],
    "enforcement_landscape": [
      "[KEY POINT ABOUT ENFORCEMENT LANDSCAPE]",
      "[ADDITIONAL POINT ABOUT ENFORCEMENT LANDSCAPE]"
    ]
  },
  "overall_risk": {
    "level_registration": "MEDIUM-HIGH",
    "explanation_registration": "[EXPLANATION OF RISK LEVEL WITH FOCUS ON IDENTICAL MARKS]",
    "level_use": "MEDIUM-HIGH",
    "explanation_use": "[EXPLANATION OF RISK LEVEL]",
    "crowded_field_percentage": [PERCENTAGE],
    "crowded_field_impact": "[EXPLANATION OF HOW CROWDED FIELD AFFECTED RISK LEVEL]"
  }
}
"""

    # Prepare the user message based on whether Section II was skipped
    if skip_section_two:
        user_message = f"""
Proposed Trademark: {mark}
Class: {class_number}
Goods and Services: {goods_services}

Section I Results:
{json.dumps(section_one_results, indent=2)}

SPECIAL INSTRUCTION: Section II analysis was skipped because: {skip_reason}. According to our risk assessment rules, when a Phonetic or Semantic mark is identified with a class match (and either goods/services match or coordinated class match), the risk level is automatically set to MEDIUM-HIGH for both Registration and Use.

Create Section III: Risk Assessment and Summary.

IMPORTANT REMINDERS:
- SET the risk level to MEDIUM-HIGH for both Registration and Use
- Include an explanation that this risk level is due to the presence of a Phonetic or Semantic similar mark with class match
- Focus the risk discussion on the similar marks identified in Section I
- For aggressive enforcement analysis, examine the owners of similar marks
- Specifically analyze coordinated class conflicts
"""
    else:
        user_message = f"""
Proposed Trademark: {mark}
Class: {class_number}
Goods and Services: {goods_services}

Section I Results:
{json.dumps(section_one_results, indent=2)}

Section II Results:
{json.dumps(section_two_results, indent=2)}

Create Section III: Risk Assessment and Summary.

IMPORTANT REMINDERS:
- Focus the risk discussion on crowded field analysis and identical marks
- Include the percentage of overlapping marks from crowded field analysis
- For identical marks specifically, ALWAYS set risk level to:
  * MEDIUM-HIGH for Registration
  * MEDIUM-HIGH for Use
- When no identical marks exist but similar marks are found:
  * Start with MEDIUM-HIGH risk level
  * If crowded field exists (>50% different owners), reduce risk by one level:
    - MEDIUM-HIGH → MEDIUM-LOW
    - MEDIUM → LOW (but never go below MEDIUM-LOW)
- Never increase risk to HIGH even with identical marks present
- For aggressive enforcement analysis, examine the owners of similar marks
- Specifically analyze coordinated class conflicts
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,
        )

        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content

            # Extract JSON data
            json_match = re.search(
                r"```json\s*(.*?)\s*```|({[\s\S]*})", content, re.DOTALL
            )
            if json_match:
                json_str = json_match.group(1) or json_match.group(2)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    return {
                        "likelihood_of_confusion": [
                            "Unable to determine likelihood of confusion."
                        ],
                        "descriptiveness": ["Unable to determine descriptiveness."],
                        "aggressive_enforcement": {
                            "owners": [],
                            "enforcement_landscape": [
                                "Unable to determine enforcement patterns."
                            ],
                        },
                        "overall_risk": {
                            "level_registration": (
                                "MEDIUM-HIGH" if skip_section_two else "MEDIUM-LOW"
                            ),
                            "explanation_registration": (
                                f"Risk level set to MEDIUM-HIGH due to {skip_reason}"
                                if skip_section_two
                                else "Unable to determine precise risk level."
                            ),
                            "level_use": (
                                "MEDIUM-HIGH" if skip_section_two else "MEDIUM-LOW"
                            ),
                            "explanation_use": (
                                f"Risk level set to MEDIUM-HIGH due to {skip_reason}"
                                if skip_section_two
                                else "Unable to determine precise risk level."
                            ),
                            "crowded_field_percentage": 0,
                            "crowded_field_impact": (
                                "Section II analysis was skipped due to high-risk marks in Section I"
                                if skip_section_two
                                else "Unable to determine crowded field impact"
                            ),
                        },
                    }
            else:
                return {
                    "likelihood_of_confusion": [
                        "Unable to determine likelihood of confusion."
                    ],
                    "descriptiveness": ["Unable to determine descriptiveness."],
                    "aggressive_enforcement": {
                        "owners": [],
                        "enforcement_landscape": [
                            "Unable to determine enforcement patterns."
                        ],
                    },
                    "overall_risk": {
                        "level_registration": (
                            "MEDIUM-HIGH" if skip_section_two else "MEDIUM-LOW"
                        ),
                        "explanation_registration": (
                            f"Risk level set to MEDIUM-HIGH due to {skip_reason}"
                            if skip_section_two
                            else "Unable to determine precise risk level."
                        ),
                        "level_use": (
                            "MEDIUM-HIGH" if skip_section_two else "MEDIUM-LOW"
                        ),
                        "explanation_use": (
                            f"Risk level set to MEDIUM-HIGH due to {skip_reason}"
                            if skip_section_two
                            else "Unable to determine precise risk level."
                        ),
                        "crowded_field_percentage": 0,
                        "crowded_field_impact": (
                            "Section II analysis was skipped due to high-risk marks in Section I"
                            if skip_section_two
                            else "Unable to determine crowded field impact"
                        ),
                    },
                }
        else:
            return {
                "likelihood_of_confusion": [
                    "Unable to determine likelihood of confusion."
                ],
                "descriptiveness": ["Unable to determine descriptiveness."],
                "aggressive_enforcement": {
                    "owners": [],
                    "enforcement_landscape": [
                        "Unable to determine enforcement patterns."
                    ],
                },
                "overall_risk": {
                    "level_registration": (
                        "MEDIUM-HIGH" if skip_section_two else "MEDIUM-LOW"
                    ),
                    "explanation_registration": (
                        f"Risk level set to MEDIUM-HIGH due to {skip_reason}"
                        if skip_section_two
                        else "Unable to determine precise risk level."
                    ),
                    "level_use": "MEDIUM-HIGH" if skip_section_two else "MEDIUM-LOW",
                    "explanation_use": (
                        f"Risk level set to MEDIUM-HIGH due to {skip_reason}"
                        if skip_section_two
                        else "Unable to determine precise risk level."
                    ),
                    "crowded_field_percentage": 0,
                    "crowded_field_impact": (
                        "Section II analysis was skipped due to high-risk marks in Section I"
                        if skip_section_two
                        else "Unable to determine crowded field impact"
                    ),
                },
            }
    except Exception as e:
        print(f"Error in section_three_analysis: {str(e)}")
        return {
            "likelihood_of_confusion": ["Unable to determine likelihood of confusion."],
            "descriptiveness": ["Unable to determine descriptiveness."],
            "aggressive_enforcement": {
                "owners": [],
                "enforcement_landscape": ["Unable to determine enforcement patterns."],
            },
            "overall_risk": {
                "level_registration": (
                    "MEDIUM-HIGH" if skip_section_two else "MEDIUM-LOW"
                ),
                "explanation_registration": (
                    f"Risk level set to MEDIUM-HIGH due to {skip_reason}"
                    if skip_section_two
                    else "Unable to determine precise risk level."
                ),
                "level_use": "MEDIUM-HIGH" if skip_section_two else "MEDIUM-LOW",
                "explanation_use": (
                    f"Risk level set to MEDIUM-HIGH due to {skip_reason}"
                    if skip_section_two
                    else "Unable to determine precise risk level."
                ),
                "crowded_field_percentage": 0,
                "crowded_field_impact": (
                    "Section II analysis was skipped due to high-risk marks in Section I"
                    if skip_section_two
                    else "Unable to determine crowded field impact"
                ),
            },
        }


def generate_trademark_opinion(
    conflicts_array: List[Dict[str, Any]],
    proposed_name: str,
    proposed_class: str,
    proposed_goods_services: str,
) -> str:
    """
    Generate a comprehensive trademark opinion
    """
    # Pre-filter trademarks
    relevant_conflicts, excluded_count = validate_trademark_relevance(
        conflicts_array, proposed_goods_services
    )

    # Perform analyses
    section_one_results = section_one_analysis(
        proposed_name, proposed_class, proposed_goods_services, relevant_conflicts
    )

    section_two_results = section_two_analysis(
        proposed_name, proposed_class, proposed_goods_services, relevant_conflicts
    )

    section_three_results = section_three_analysis(
        proposed_name,
        proposed_class,
        proposed_goods_services,
        section_one_results,
        section_two_results,
    )

    # Create comprehensive opinion structure
    opinion_structure = {
        "proposed_name": proposed_name,
        "proposed_class": proposed_class,
        "proposed_goods_services": proposed_goods_services,
        "excluded_count": excluded_count,
        "section_one": section_one_results,
        "section_two": section_two_results,
        "section_three": section_three_results,
    }

    # Format the opinion
    comprehensive_opinion = format_comprehensive_opinion(opinion_structure)
    return clean_and_format_opinion(comprehensive_opinion, opinion_structure)
