import re

from docx import Document, shared

from typing import Final, Dict, List
from rakun2 import RakunKeyphraseDetector

# Hyperparemeters for rakun2
RAKUN_HYPERPARAMETERS: Final = {
    "num_keywords": 70,
    "merge_threshold": 0.5,
    "alpha": 0.9,
    "token_prune_len": 6
}

# Regex for contact info


class ResumeOptimizer():
    """
    Resume Class - Initialize from a valid python-docx Document object
    """

    # List of possible resume section names
    RESUME_SECTIONS = [
        ["about", "profile", "introduction", "summary", "objective"],
        ["education", "school", "academic"],
        ["qualification", "skill", "credential", "certification"],
        ["experience", "history", "project"],
    ]
    # Regex for contact info (https://uibakery.io/regex-library/)
    CONTACT_REGEX = {
        "phone": "^\\+?\\d{1,4}?[-.\\s]?\\(?\\d{1,3}?\\)?[-.\\s]?\\d{1,4}[-.\\s]?\\d{1,4}[-.\\s]?\\d{1,9}$",
        "email": r"^\S+@\S+\.\S+$"
    }
    URL_REGEX = "^(https?:\\/\\/)?(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"
    # Max length for the title of a section
    MAX_TITLE_LENGTH = 50

    def __init__(self, resume_doc: Document, job_description: str):
        # Set public attributes
        self.resume_doc = resume_doc
        self.job_string = job_description
        self.resume_string = "\n".join([p.text for p in self.resume_doc.paragraphs])
        # Set private attributes
        self.__missing_contact_info = list(ResumeOptimizer.CONTACT_REGEX.keys())
        self.__contact_info = {}
        self.__urls = []
        # Keywords objects
        self.__resume_keywords = RakunKeyphraseDetector(RAKUN_HYPERPARAMETERS)
        self.__job_keywords = RakunKeyphraseDetector(RAKUN_HYPERPARAMETERS)

    # Processing for specific sections (accepts text)
    def __process_header(self, text: str):
        # Check if any contact info is missing
        contact_info_count = len(self.__missing_contact_info)
        if contact_info_count > 0:
            # Iterate over missing info
            for index in range(contact_info_count):
                key = self.__missing_contact_info[index]
                match = re.search(ResumeOptimizer.CONTACT_REGEX[key], text)
                if match:
                    # Update contact info
                    self.__contact_info[key] = match.string
                    self.__missing_contact_info.pop(index)
                    break

    # Update sections dictionary, execute additional operations depending on the section
    def __update_sections(self, text: str, current_section: str, sections: Dict[str, List[str | None]]):
        # Update section
        sections[current_section].append(text)
        # Call process function (if there is one)
        match current_section:
            case "header" | "about":
                self.__process_header(text)
        # Get urls from all text
        url_match = re.search(ResumeOptimizer.URL_REGEX, text)
        if url_match and not re.match(ResumeOptimizer.CONTACT_REGEX["email"], url_match.string):
            self.__urls.append(url_match.string)

    # Getters
    def get_contact_info(self):
        return self.__contact_info
    def get_urls(self):
        return self.__urls
    
    # Seperate resume by sections by finding sections from common words
    def match_parse_resume(self) -> Dict[str, List[str | None]]:
        """
        [RECOMMENDED PARSE FUNCTION]
        Identifies sections, and groups resume content into a dictionary where the keys are the sections
        Checks for section name matches after blank lines, updates section if there is a match
        """
        # Initialize variables
        new_section = True
        current_section = "header"
        sections = {}
        sections[current_section] = []
        # Iterate over paragraphs
        for paragraph in self.resume_doc.paragraphs:
            content_paragraph = True
            # Check for blank line (typically between sections on a resume)
            if not paragraph.text.strip():
                new_section = True
                continue
            elif new_section:
                new_section = False
                # Iterate over section names
                for section_names in ResumeOptimizer.RESUME_SECTIONS:
                    # Check for a match
                    if any(name in paragraph.text.lower() for name in section_names):
                        # Update current section name
                        current_section = section_names[0]
                        sections[current_section] = []
                        content_paragraph = False
                        break
            if content_paragraph:
                # Update current section
                self.__update_sections(paragraph.text, current_section, sections)
        # Return parsed resume
        return sections

    # Seperate resume by sections by finding section names with a different font size
    def font_parse_resume(self) -> Dict[str, List[str | None]]:
        """
        Identifies sections, and groups resume content into a dictionary where the keys are the sections.
        Checks for paragraphs with a font that differs from the rest of the document, or has a style name
        which contains "Heading".
        """
        # Initialize variables
        current_section = "header"
        sections = {}
        sections[current_section] = []
        # Iterate over paragraphs
        for paragraph in self.resume_doc.paragraphs:
            # Check if paragraph text is within max length AND: style name is Heading, font size differs
            if (len(paragraph.text) <= ResumeOptimizer.MAX_TITLE_LENGTH and 
                (paragraph.style.name.startswith("Heading") or 
                 any(run.font.size != None for run in paragraph.runs))):
                # Check if text was 
                # Update section
                current_section = paragraph.text
                sections[current_section] = []
            else:
                # Update current section
                self.__update_sections(paragraph.text, current_section, sections)
        return sections
        
    # Compare the keywords of the resume, and job posting
    def compare_keywords(self):
        # Get keywords
        resume_keywords = self.__resume_keywords.find_keywords(self.resume_string, input_type="string")
        job_keywords = self.__job_keywords.find_keywords(self.job_string, input_type="string")
        # Find matching keywords
        matches = {}
        job_keyword_text = [keyword_tuple[0] for keyword_tuple in job_keywords]
        for keyword_tuple in resume_keywords:
            # Check for match
            if keyword_tuple[0] in job_keyword_text:
                # Get match index
                match_index = job_keyword_text.index(keyword_tuple[0])
                # Set value to false to speed up matching
                job_keyword_text[match_index] = False
                # Set match string to combined value
                matches[keyword_tuple[0]] = keyword_tuple[1] + job_keywords[match_index][1]
        print(matches)