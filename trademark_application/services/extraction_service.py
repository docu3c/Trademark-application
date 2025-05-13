import fitz
from typing import Dict, List, Union
import re
from utils.text_processing import preprocess_text, find_class_numbers
from config.settings import get_azure_client


def extract_trademark_details_code1(
    document_chunk: str,
) -> Dict[str, Union[str, List[int]]]:
    """Extract trademark details using format code 1"""
    print(f"Executing extract_trademark_details_code1")
    try:
        client = get_azure_client()
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant for extracting Meta Data from the Trademark Document.",
            },
            {
                "role": "user",
                "content": f"""
                Extract the following details from the trademark document: trademark name, status.\n\nDocument:\n{document_chunk}
                Don't extract the same trademark details more than once; extract them only once. 
                 
                Return output only in the below mentioned format:
                Example-1 output format: 
                    Trademark Name: SLIK\n 
                    Status: PENDING\n
                Example-2 output format: 
                    Trademark Name: HUMOR US GOODS\n 
                    Status: REGISTERED\n
                Example-3 output format: 
                    Trademark Name: #WASONUO %& PIC\n 
                    Status: REGISTERED\n
                Example-4 output format: 
                    Trademark Name: AT Present, WE'VE GOT YOUR-BACK(SIDE)\n 
                    Status: PUBLISHED\n\n
                    
                Note: The trademark name length can also be 1 or 2 characters. (Example: Trademark Name: PI), (Example: Trademark Name: PII) \n""",
            },
        ]

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0,
            max_tokens=300,
        )
        extracted_text = response.choices[0].message.content

        details = {}
        for line in extracted_text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                details[key.strip().lower().replace(" ", "_")] = value.strip()

        return details

    except Exception as e:
        print(f"An error occurred: {e}")
        return {}


def extract_trademark_details_code2(page_text: str) -> Dict[str, Union[str, List[int]]]:
    details = {}

    trademark_name_match = re.search(
        r"\d+\s*/\s*\d+\s*\n\s*\n\s*([A-Za-z0-9'&!,\-. ]+)\s*\n", page_text
    )
    if trademark_name_match:
        details["trademark_name"] = trademark_name_match.group(1).strip()
    else:
        trademark_name_match = re.search(
            r"(?<=\n)([A-Za-z0-9'&!,\-. ]+)(?=\n)", page_text
        )
        details["trademark_name"] = (
            trademark_name_match.group(1).strip() if trademark_name_match else ""
        )

    status_match = re.search(
        r"Status\s*(?:\n|:\s*)([A-Za-z]+)", page_text, re.IGNORECASE
    )
    details["status"] = status_match.group(1).strip() if status_match else ""

    owner_match = re.search(r"Holder\s*(?:\n|:\s*)(.*)", page_text, re.IGNORECASE)
    if owner_match:
        details["owner"] = owner_match.group(1).strip()
    else:
        owner_match = re.search(r"Owner\s*(?:\n|:\s*)(.*)", page_text, re.IGNORECASE)
        details["owner"] = owner_match.group(1).strip() if owner_match else ""

    nice_classes_match = re.search(
        r"Nice Classes\s*[\s:]*\n((?:\d+(?:,\s*\d+)*)\b)", page_text, re.IGNORECASE
    )
    if nice_classes_match:
        nice_classes_text = nice_classes_match.group(1)
        nice_classes = [int(cls.strip()) for cls in nice_classes_text.split(",")]
        details["international_class_number"] = nice_classes
    else:
        details["international_class_number"] = []

    serial_number_match = re.search(r"Application#\s*(.*)", page_text, re.IGNORECASE)
    details["serial_number"] = (
        serial_number_match.group(1).strip() if serial_number_match else ""
    )

    goods_services_match = re.search(
        r"Goods & Services\s*(.*?)(?=\s*G&S translation|$)",
        page_text,
        re.IGNORECASE | re.DOTALL,
    )
    details["goods_services"] = (
        goods_services_match.group(1).strip() if goods_services_match else ""
    )

    registration_number_match = re.search(
        r"Registration#\s*(.*)", page_text, re.IGNORECASE
    )
    details["registration_number"] = (
        registration_number_match.group(1).strip() if registration_number_match else ""
    )

    # Description
    design_phrase = re.search(
        r"Description\s*(.*?)(?=\s*Applicant|Owner|Holder|$)",
        page_text,
        re.IGNORECASE | re.DOTALL,
    )
    details["design_phrase"] = (
        design_phrase.group(1).strip()
        if design_phrase
        else "No Design phrase presented in document"
    )

    return details


def extract_serial_number(
    document: str, start_page: int, pdf_document: fitz.Document
) -> str:
    """Extract serial number from document"""
    combined_texts = ""
    for i in range(start_page, min(start_page + 13, pdf_document.page_count)):
        page = pdf_document.load_page(i)
        page_text = page.get_text()
        combined_texts += page_text
        if "Serial Number:" in page_text or "Ownership Details:" in page_text:
            break

    pattern = r"Chronology:.*?Serial Number:\s*([\d,-−]+)"
    match = re.search(pattern, combined_texts, re.DOTALL)
    if match:
        return match.group(1).strip()
    return "No serial number presented in document"


def extract_ownership(
    document: str, start_page: int, proposed_name: str, pdf_document: fitz.Document
) -> str:
    """Extract ownership details from document"""
    combined_texts = ""
    for i in range(start_page, min(start_page + 13, pdf_document.page_count)):
        page = pdf_document.load_page(i)
        page_text = page.get_text()
        combined_texts += page_text
        if "Last Reported Owner:" in page_text or "Ownership Details:" in page_text:
            break

    pattern = r"Last Reported Owner:\s*(.*?)\n\s*(.*?)\n"
    match = re.search(pattern, combined_texts, re.DOTALL)
    if match:
        owner_name = match.group(1).strip()
        owner_type = match.group(2).strip()
        if owner_type == proposed_name:
            return owner_name
        else:
            return f"{owner_name} {owner_type}"
    return "Not available in the provided document."


def extract_registration_number(
    document: str, start_page: int, pdf_document: fitz.Document
) -> str:
    """Extract registration number from document"""
    combined_texts = ""
    for i in range(start_page, min(start_page + 8, pdf_document.page_count)):
        page = pdf_document.load_page(i)
        page_text = page.get_text()
        combined_texts += page_text
        if "Registration Number:" in page_text or "Ownership Details:" in page_text:
            break

    pattern = r"Last ReportedOwner:.*?Registration Number:\s*([\d,]+)"
    match = re.search(pattern, combined_texts, re.DOTALL)
    if match:
        return match.group(1).strip()
    return "NA"


def extract_international_class_numbers_and_goods_services(
    document: str, start_page: int, pdf_document: fitz.Document
) -> Dict[str, Union[List[int], str]]:
    """Extract international class numbers and goods/services"""
    class_numbers = []
    goods_services = []
    combined_text = ""

    for i in range(start_page, min(start_page + 10, pdf_document.page_count)):
        page = pdf_document.load_page(i)
        page_text = page.get_text()
        combined_text += page_text
        if "Last Reported Owner:" in page_text:
            break

    pattern = r"International Class (\d+): (.*?)(?=\nInternational Class \d+:|\n[A-Z][a-z]+:|\nLast Reported Owner:|Disclaimers:|\Z)"
    matches = re.findall(pattern, combined_text, re.DOTALL)

    for match in matches:
        class_number = int(match[0])
        class_numbers.append(class_number)
        goods_services.append(f"Class {class_number}: {match[1].strip()}")

    return {
        "international_class_numbers": class_numbers,
        "goods_services": "\n".join(goods_services),
    }


def extract_design_phrase(
    document: str, start_page: int, pdf_document: fitz.Document
) -> str:
    """Extract design phrase from document"""
    print(f"Executing extract_design_phrase")
    combined_texts = ""
    for i in range(start_page, min(start_page + 10, pdf_document.page_count)):
        page = pdf_document.load_page(i)
        page_text = page.get_text()
        combined_texts += page_text
        if "Design Phrase:" in page_text or "Filing Correspondent:" in page_text:
            break

    pattern = r"Design Phrase:\s*(.*?)(?=Other U\.S\. Registrations:|Filing Correspondent:|Group:|USPTO Page:|$)"
    match = re.search(pattern, combined_texts, re.DOTALL)
    if match:
        design_phrase = match.group(1).strip()
        # Remove any newline characters within the design phrase
        design_phrase = " ".join(design_phrase.split())
        return design_phrase
    return "No Design phrase presented in document"


def extract_proposed_trademark_details(
    file_path: str,
) -> Dict[str, Union[str, List[int]]]:
    """Extract proposed trademark details from input format"""
    proposed_details = {}
    with fitz.open(file_path) as pdf_document:
        if pdf_document.page_count > 0:
            page = pdf_document.load_page(0)
            page_text = preprocess_text(page.get_text())
            if "Mark Searched:" not in page_text:
                page = pdf_document.load_page(1)
                page_text = preprocess_text(page.get_text())

    name_match = re.search(
        r"Mark Searched:\s*(.*?)(?=\s*Client Name:)",
        page_text,
        re.IGNORECASE | re.DOTALL,
    )
    if name_match:
        proposed_details["proposed_trademark_name"] = name_match.group(1).strip()

    if "Goods/Services:" in page_text:
        goods_services_match = re.search(
            r"Goods/Services:\s*(.*?)(?=\s*Trademark Research Report)",
            page_text,
            re.IGNORECASE | re.DOTALL,
        )
    else:
        goods_services_match = re.search(
            r"Goods and Services:\s*(.*?)(?=\s*Order Info)",
            page_text,
            re.IGNORECASE | re.DOTALL,
        )

    if goods_services_match:
        proposed_details["proposed_goods_services"] = goods_services_match.group(
            1
        ).strip()

    # Use LLM to find the international class number based on goods & services
    if "proposed_goods_services" in proposed_details:
        goods_services = proposed_details["proposed_goods_services"]
        class_numbers = find_class_numbers(goods_services)
        proposed_details["proposed_nice_classes_number"] = class_numbers

    return proposed_details


def extract_proposed_trademark_details2(
    file_path: str,
) -> Dict[str, Union[str, List[int]]]:
    """Extract proposed trademark details from first page"""
    proposed_details = {}
    with fitz.open(file_path) as pdf_document:
        if pdf_document.page_count > 0:
            page = pdf_document.load_page(0)
            page_text = preprocess_text(page.get_text())

            name_match = re.search(r"Name:\s*(.*?)(?=\s*Nice Classes:)", page_text)
            if name_match:
                proposed_details["proposed_trademark_name"] = name_match.group(
                    1
                ).strip()

            nice_classes_match = re.search(
                r"Nice Classes:\s*(\d+(?:,\s*\d+)*)", page_text
            )
            if nice_classes_match:
                proposed_details["proposed_nice_classes_number"] = (
                    nice_classes_match.group(1).strip()
                )

            goods_services_match = re.search(
                r"Goods & Services:\s*(.*?)(?=\s*Registers|$)",
                page_text,
                re.IGNORECASE | re.DOTALL,
            )
            if goods_services_match:
                proposed_details["proposed_goods_services"] = (
                    goods_services_match.group(1).strip()
                )

    return proposed_details
