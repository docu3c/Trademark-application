import io
import base64
import cv2
import json
import requests
import os
from PIL import Image
from typing import List
import numpy as np
import fitz
from utils.ml_utils import process_single_image


def web_law_page(document_path: str) -> List[Image.Image]:
    """
    Return PIL Image objects of the pages where either:
    1. "Web Common Law Summary Page:" appears, or
    2. Both "Web Common Law Overview List" and "Record Nr." appear.
    """
    print(f"Executing web_law_page")
    matching_pages = []  # List to store matching page numbers

    with fitz.open(document_path) as pdf_document:
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            page_text = page.get_text()
            print(page_text)

            # Check for "Web Common Law Summary Page:"
            if "Web Common Law Page:" in page_text:
                matching_pages.append(page_num + 1)

            # Check for "Web Common Law Overview List" and "Record Nr."
            if "WCL-" in page_text:
                matching_pages.append(page_num + 1)
            # if "Web Common Law Overview List" in page_text and "Record Nr." in page_text:
            #     overview_pages = Web_CommonLaw_Overview_List(
            #         page_text, page_num, pdf_document
            #     )
            #     matching_pages.extend(overview_pages)

        # Remove duplicates and sort the page numbers
        matching_pages = sorted(set(matching_pages))

        # Convert matching pages to PIL images
        images = convert_pages_to_pil_images(pdf_document, matching_pages)

    return images


def convert_pages_to_pil_images(
    pdf_document: fitz.Document, page_numbers: List[int]
) -> List[Image.Image]:
    """Convert PDF pages to PIL images."""
    print(f"Executing convert_pages_to_pil_images")
    images = []
    for page_num in page_numbers:
        page = pdf_document.load_page(page_num - 1)
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        images.append(img)
    return images


def extract_web_common_law(
    page_images: List[Image.Image], proposed_name: str
) -> List[dict]:
    """Extract web common law data from images."""
    print(f"Executing extract_web_common_law")
    results = []
    for image in page_images:
        result = process_single_image(image, proposed_name)
        results.append(result)
    return results


def analyze_web_common_law(extracted_data: List[str], proposed_name: str) -> str:
    """
    Comprehensive analysis of web common law trademark data through three specialized stages.
    Returns a professional opinion formatted according to legal standards.
    """
    print(f"Executing analyze_web_common_law")
    # Stage 1: Cited Term Analysis
    cited_term_analysis = section_four_analysis(extracted_data, proposed_name)

    # Stage 2: Component Analysis
    component_analysis = section_five_analysis(extracted_data, proposed_name)

    # Stage 3: Final Risk Assessment
    risk_assessment = section_six_analysis(
        cited_term_analysis, component_analysis, proposed_name
    )

    # Combine all sections into final report
    final_report = f"""
WEB COMMON LAW OPINION: {proposed_name} 

{cited_term_analysis}

{component_analysis}

{risk_assessment}
"""
    return final_report


def section_four_analysis(extracted_data: List[str], proposed_name: str) -> str:
    """
    Perform Section IV: Comprehensive Cited Term Analysis
    """
    print(f"Executing section_four_analysis")
    azure_endpoint = os.getenv(
        "AZURE_ENDPOINT",
    )
    api_key = os.getenv(
        "AZURE_API_KEY",
    )
    model = "gpt-4o"

    extracted_text = "\n".join([str(item) for item in extracted_data])

    prompt = f"""You are a trademark attorney analyzing web common law trademark data.
Perform Section IV analysis (Comprehensive Cited Term Analysis) with these subsections:

1. Identical Cited Terms
2. One Letter and Two Letter Differences
3. Phonetically/Semantically/Functionally Similar Terms

Analyze this web common law data against proposed trademark: {proposed_name}

Extracted Data:
{extracted_text}

Perform comprehensive analysis:
1. Check for identical cited terms
2. Analyze one/two letter differences
3. Identify similar terms (phonetic/semantic/functional)
4. For each, determine if goods/services are similar

Return results in EXACTLY this format:

Section IV: Comprehensive Cited Term Analysis

(a) Identical Cited Terms:
| Cited Term | Owner | Goods & Services | Goods & Services Match |
|------------|-------|------------------|------------------------|
| [Term 1]   | [Owner]| [Goods/Services] | [True/False]           |

(b) One Letter and Two Letter Analysis:
| Cited Term | Owner | Goods & Services | Difference Type | Goods & Services Match |
|------------|-------|------------------|-----------------|------------------------|
| [Term 1]   | [Owner]| [Goods/Services] | [One/Two Letter] | [True/False]           |

(c) Phonetically, Semantically & Functionally Similar Analysis:
| Cited Term | Owner | Goods & Services | Similarity Type | Goods & Services Match |
|------------|-------|------------------|-----------------|------------------------|
| [Term 1]   | [Owner]| [Goods/Services] | [Phonetic/Semantic/Functional] | [True/False] |

Evaluation Guidelines:
- Goods/services match if they overlap with proposed trademark's intended use
- One letter difference = exactly one character changed/added/removed
- Two letter difference = exactly two characters changed/added/removed
- Phonetic similarity = sounds similar when spoken
- Semantic similarity = similar meaning
- Functional similarity = similar purpose/use
- State "None" when no results are found
- Filter out rows where both match criteria are False
- Always include complete goods/services text
"""

    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a trademark attorney specializing in comprehensive trademark analysis. Provide precise, professional analysis in the exact requested format.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "max_tokens": 2000,
        "temperature": 0.1,
    }

    headers = {"Content-Type": "application/json", "api-key": api_key}
    response = requests.post(
        f"{azure_endpoint}/openai/deployments/{model}/chat/completions?api-version=2024-10-01-preview",
        headers=headers,
        data=json.dumps(data),
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    return "Failed to generate cited term analysis"


def section_five_analysis(extracted_data: List[str], proposed_name: str) -> str:
    """
    Perform Section V: Component Analysis and Crowded Field Assessment
    (Skips entire section if identical hits exist in cited term analysis)
    """
    print(f"Executing section_five_analysis")
    azure_endpoint = os.getenv("AZURE_ENDPOINT")
    api_key = os.getenv(
        "AZURE_API_KEY",
    )
    model = "gpt-4o"

    extracted_text = "\n".join([str(item) for item in extracted_data])

    prompt = f"""You are a trademark attorney analyzing web common law components.
First check if there are any identical cited terms to '{proposed_name}' in this data:

Extracted Data:
{extracted_text}

IF IDENTICAL TERMS EXIST:
- Skip entire Section V analysis
- Return this exact text:
  "Section V omitted due to identical cited terms"

IF NO IDENTICAL TERMS EXIST:
Perform Section V analysis (Component Analysis) with these subsections:
1. Component Breakdown
2. Crowded Field Analysis

Return results in EXACTLY this format:

Section V: Component Analysis

Component 1: [First Component]
| Cited Term | Owner | Goods & Services | Goods & Services Match |
|------------|-------|------------------|------------------------|
| [Term 1]   | [Owner]| [Goods/Services] | [True/False]           |

(b) Crowded Field Analysis:
- **Total component hits found**: [NUMBER]
- **Terms with different owners**: [NUMBER] ([PERCENTAGE]%)
- **Crowded Field Status**: [YES/NO]
- **Analysis**: 
  [DETAILED EXPLANATION OF FINDINGS]

IMPORTANT:
1. First check for identical terms before any analysis
2. If identical terms exist, skip entire Section V
3. Only perform component and crowded field analysis if NO identical terms exist
4. Never show any analysis if identical terms are found
"""

    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a trademark attorney who FIRST checks for identical terms before deciding whether to perform any Section V analysis.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "max_tokens": 2000,
        "temperature": 0.1,  # Low temperature for strict rule following
    }

    headers = {"Content-Type": "application/json", "api-key": api_key}
    response = requests.post(
        f"{azure_endpoint}/openai/deployments/{model}/chat/completions?api-version=2024-10-01-preview",
        headers=headers,
        data=json.dumps(data),
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    return "Failed to generate component analysis"


def section_six_analysis(
    cited_term_analysis: str, component_analysis: str, proposed_name: str
) -> str:
    """
    Perform Section VI: Final Risk Assessment with strict rules:
    - Skip crowded field analysis if identical hits exist
    - Risk levels only MEDIUM-HIGH or MEDIUM-LOW
    """
    print(f"Executing section_six_analysis")
    azure_endpoint = os.getenv("AZURE_ENDPOINT")
    api_key = os.getenv(
        "AZURE_API_KEY",
    )
    model = "gpt-4o"

    prompt = f"""You are a senior trademark attorney preparing a final risk assessment for {proposed_name}.

**STRICT RULES TO FOLLOW:**
1. **Identical Hits Take Precedence**:
   - If ANY identical cited terms exist in Section IV(a), IMMEDIATELY set risk to MEDIUM-HIGH
   - SKIP ENTIRELY any crowded field analysis in this case
   - Include note: "Crowded field analysis omitted due to identical cited terms"

2. **Crowded Field Analysis ONLY When**:
   - NO identical cited terms exist
   - Then analyze crowded field from Section V(b)
   - If crowded field exists (>50% different owners), set risk to MEDIUM-LOW

3. **Risk Level Restrictions**:
   - Maximum risk: MEDIUM-HIGH (never HIGH)
   - Minimum risk: MEDIUM-LOW (never LOW)
   - Only these two possible outcomes

**Analysis Sections:**
Cited Term Analysis:
{cited_term_analysis}

Component Analysis:
{component_analysis}

**Required Output Format:**

Section VI: Web Common Law Risk Assessment

Market Presence:
- [Brief market overview based on findings]

Enforcement Patterns:
- [List any concerning enforcement patterns if found]

Risk Category for Use:
- **[MEDIUM-HIGH or MEDIUM-LOW]**
- [Clear justification based on strict rules above]

III. COMBINED RISK ASSESSMENT

Overall Risk Category:
- **[MEDIUM-HIGH or MEDIUM-LOW]**
- [Detailed explanation following these guidelines:
   - If identical terms: "Identical cited term(s) found, elevating risk to MEDIUM-HIGH. Crowded field analysis not performed."
   - If crowded field: "No identical terms found. Crowded field (X% different owners) reduces risk to MEDIUM-LOW."
   - If neither: "No identical terms and no crowded field, maintaining MEDIUM-LOW risk."]

**Critical Instructions:**
1. NEVER show crowded field analysis if identical terms exist
2. ALWAYS use specified risk level terminology
3. Keep explanations concise but legally precise
4. Maintain strict adherence to the rules above
"""

    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a trademark risk assessment expert who STRICTLY follows rules about identical hits and crowded fields. Never deviate from the specified risk levels.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "max_tokens": 1500,
        "temperature": 0.1,  # Low temperature for consistent rule-following
    }

    headers = {"Content-Type": "application/json", "api-key": api_key}
    response = requests.post(
        f"{azure_endpoint}/openai/deployments/{model}/chat/completions?api-version=2024-10-01-preview",
        headers=headers,
        data=json.dumps(data),
    )

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    return "Failed to generate risk assessment"
