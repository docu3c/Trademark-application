import fitz
from typing import List
from PIL import Image
from config.settings import MAX_TOKENS_PER_CHUNK, EXCLUDE_HEADER_FOOTER


def read_pdf(
    file_path: str, exclude_header_footer: bool = EXCLUDE_HEADER_FOOTER
) -> str:
    """
    Read a PDF file and return its text content
    """
    doc = fitz.open(file_path)
    text = ""

    for page in doc:
        if exclude_header_footer:
            # Get page dimensions
            page_rect = page.rect
            # Define header and footer regions (adjust these values as needed)
            header_height = 50
            footer_height = 50
            # Create a rectangle for the main content
            content_rect = fitz.Rect(
                page_rect.x0,
                page_rect.y0 + header_height,
                page_rect.x1,
                page_rect.y1 - footer_height,
            )
            text += page.get_text("text", clip=content_rect)
        else:
            text += page.get_text("text")

    doc.close()
    return text


def split_text(text: str, max_tokens: int = MAX_TOKENS_PER_CHUNK) -> List[str]:
    """
    Split text into chunks of maximum token size
    """
    # Simple splitting by sentences for now
    sentences = text.split(". ")
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence.split())
        if current_length + sentence_length > max_tokens:
            chunks.append(". ".join(current_chunk) + ".")
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length

    if current_chunk:
        chunks.append(". ".join(current_chunk) + ".")

    return chunks


def convert_pages_to_pil_images(
    pdf_document: fitz.Document, page_numbers: List[int]
) -> List[Image.Image]:
    """
    Convert PDF pages to PIL Images
    """
    images = []
    for page_num in page_numbers:
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    return images


def Web_CommonLaw_Overview_List(
    document: str, start_page: int, pdf_document: fitz.Document
) -> List[int]:
    """
    Extract the page numbers for the 'Web Common Law Overview List' section.
    """
    pages_with_overview = []
    for i in range(start_page, min(start_page + 2, pdf_document.page_count)):
        page = pdf_document.load_page(i)
        page_text = page.get_text()
        if "Record Nr." in page_text:  # Check for "Record Nr." in the text
            pages_with_overview.append(i + 1)  # Use 1-based indexing for page numbers
    return pages_with_overview
