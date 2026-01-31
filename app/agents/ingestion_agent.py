from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import pytesseract


class IngestionAgent:

    def extract_text(self, file_path: str, file_type: str) -> str:
        # Route extraction based on file type
        if file_type == "pdf":
            return self._extract_pdf(file_path)
        elif file_type == "image":
            return self._extract_image(file_path)
        else:
            # Reject unsupported formats
            raise ValueError(f"Unsupported file type: {file_type}")

    def _extract_pdf(self, file_path: str) -> str:
        # Extract text from all PDF pages
        text_parts = []
        doc = fitz.open(file_path)

        for page in doc:
            # Read page text
            page_text = page.get_text()
            if page_text:
                text_parts.append(page_text)

        # Normalize extracted content
        return self._clean_text("\n".join(text_parts))

    def _extract_image(self, file_path: str) -> str:
        # Perform OCR on image file
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return self._clean_text(text)

    def _clean_text(self, text: str) -> str:
        """
        Aggressive text cleaning for better chunking and display
        """
        import re

        # Remove null characters
        text = text.replace("\x00", " ")

        # Fix hyphenated words broken across lines: "convers-\nation" → "conversation"
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

        # Join lines within paragraphs: "word1\nword2" → "word1 word2"
        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

        # Replace multiple newlines (paragraph breaks) with double newline
        text = re.sub(r"\n{2,}", "\n\n", text)

        # Replace tabs with spaces
        text = text.replace("\t", " ")

        # Normalize multiple spaces to single space
        text = re.sub(r" {2,}", " ", text)

        # Fix common PDF artifacts (soft hyphens)
        text = re.sub(r"[­\u00ad]", "", text)

        return text.strip()
