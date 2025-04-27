import re

from docx import Document
from docx.table import Table

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
    Resume Optimizer

    ...

    Attributes
    ----------
    resume_doc : Document
        Resume document
    job_string : str
        String job description
    matches : Dict[str, float]
        Keyword to value of keyword from compare_keywords()

    Methods
    -------
    match_parse_resume():
        [RECOMMENDED] Parses resume by finding words that match predefined section names
    font_parse_resume():
        Parses resume by finding headings or font styles that differ from the base font style
    get_compare_string():
        Joins resume sections except the header and returns the final string
    """

    # List of possible resume section names
    RESUME_SECTIONS: List[List[str]] = [
        ["about", "profile", "introduction", "summary", "objective"],
        ["education", "school", "academic"],
        ["qualification", "skill", "credential", "certification", "certificate"],
        ["experience", "history", "project", "work"],
    ]
    # Regex for contact info (https://uibakery.io/regex-library/)
    CONTACT_REGEX: Dict[str, str] = {
        "phone": "^\\+?\\d{1,4}?[-.\\s]?\\(?\\d{1,3}?\\)?[-.\\s]?\\d{1,4}[-.\\s]?\\d{1,4}[-.\\s]?\\d{1,9}$",
        "email": r"^\S+@\S+\.\S+$"
    }
    URL_REGEX: str = r"(?:https?:\/\/)?(?:www\.)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)"
    # Max length for the title of a section
    MAX_TITLE_LENGTH: int = 50

    def __init__(self, resume_doc: Document, job_string: str):
        """
        Construct a new ResumeOptimizer object

        Parameters
        ----------
        resume_doc : Document
            Resume document
        job_string : str
            String job description

        """
        # Set private attributes
        self.__missing_contact_info = list(ResumeOptimizer.CONTACT_REGEX.keys())
        self.__contact_info = {}
        self.__urls = []
        # Create Rakun Keywords objects
        self.__resume_keywords = RakunKeyphraseDetector(RAKUN_HYPERPARAMETERS)
        self.__job_keywords = RakunKeyphraseDetector(RAKUN_HYPERPARAMETERS)
        # Set public attributes
        self.resume_doc = resume_doc
        self.job_string = job_string

    # Processing for specific sections (modifies text)
    def __process_header(self, text: str) -> tuple[str, bool]:
        # Check if any contact info is missing
        contact_info_count = len(self.__missing_contact_info)
        new_section = False
        if contact_info_count > 0:
            # Iterate over missing info
            new_info = False
            for index in range(contact_info_count):
                key = self.__missing_contact_info[index]
                match = re.search(ResumeOptimizer.CONTACT_REGEX[key], text)
                if match:
                    # Update contact info
                    self.__contact_info[key] = match.string
                    self.__missing_contact_info.pop(index)
                    # Remove from text
                    text = text.replace(match.string, "")
                    # Indicate new info was found
                    new_info = True
                    break
            # Check if more info was found
            if len(self.__contact_info) > 0 and new_info == False:
                new_section = True
        else:
            new_section = True
        return text, new_section

    # Update sections dictionary, execute additional operations depending on the section
    def __update_sections(self, paragraph, current_section: str, sections: Dict[str, List[str | None]]) -> str:
        # Call process function (if there is one)
        text = paragraph.text
        matched_section = None
        match current_section:
            case "header":
                text, new_section = self.__process_header(text)
                # Check for new section, match if possible
                if new_section:
                    matched_section = self.__match_section(text, sections)
            case "about":
                text, new_section = self.__process_header(text)
        # Get urls from all text
        url_matches = re.findall(ResumeOptimizer.URL_REGEX, text)
        # Check for matches
        if url_matches:
            # Iterate over all URLs
            for url_match in url_matches:
                # Check if URL is an email, make sure URL is not already in the url_match list
                if not re.match(ResumeOptimizer.CONTACT_REGEX["email"], url_match) and not url_match in self.__urls:
                    self.__urls.append(url_match)
                    text = text.replace(url_match, "")
        # Check if a new section was matched
        if matched_section:
            current_section = matched_section
        else:
            sections[current_section].append(text)
        return current_section
    
    def __match_section(self, text, sections) -> str | None:
        # Iterate over section names
        matched_section = None
        for section_names in ResumeOptimizer.RESUME_SECTIONS:
            if not section_names[0] in sections.keys():
                # Check for a match
                if any(name in text.lower() for name in section_names):
                    # Update current section name
                    matched_section = section_names[0]
                    sections[matched_section] = []
                    break
        return matched_section

    # Getters
    def get_contact_info(self) -> Dict[str, str]:
        """Get contact info"""
        return self.__contact_info
    def get_urls(self) -> List[str]:
        """Get URLs"""
        return self.__urls
    def get_compare_string(self) -> str:
        """
        Compile string from Resume, primarily used for compare_keywords() method
        """
        compare_string = ""
        parsed_resume = self.match_parse_resume()
        # Iterate over sections in parsed resume
        for section_name, section_text_list in parsed_resume.items():
            # Skip the header
            if section_name == "header":
                continue
            else:
                for text in section_text_list:
                    compare_string += text + "\n"
        # Return final compare string
        return compare_string

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
        sections = {current_section : []}
        # Iterate over paragraphs
        for inner_content in self.resume_doc.iter_inner_content():
            inner_paragraphs = []
            # Check content type
            if type(inner_content) == Table:
                # Get paragraphs from content cells
                for column in inner_content.columns:
                    for cell in column.cells:
                        inner_paragraphs.extend(cell.paragraphs)
            else:
                inner_paragraphs = [inner_content]
            # Iterate over paragraphs
            for paragraph in inner_paragraphs:
                body_paragraph = True
                # Check for blank line (typically between sections on a resume)
                if not paragraph.text.strip():
                    new_section = True
                    continue
                elif new_section:
                    new_section = False
                    # Check for a match
                    matched_section = self.__match_section(paragraph.text, sections)
                    if matched_section:
                        # Update current section name
                        current_section = matched_section
                        body_paragraph = False
                if body_paragraph:
                    # Update current section
                    current_section = self.__update_sections(paragraph, current_section, sections)
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
                # Update section
                current_section = paragraph.text
                sections[current_section] = []
            else:
                # Update current section
                current_section = self.__update_sections(paragraph, current_section, sections)
        # Return parsed resume
        return sections
        
    # Compare the keywords of the resume, and job posting
    def compare_keywords(self) -> Dict[str, float]:
        # Get keywords
        resume_string = self.get_compare_string()
        resume_keywords = self.__resume_keywords.find_keywords(resume_string, input_type="string")
        job_keywords = self.__job_keywords.find_keywords(self.job_string, input_type="string")
        # Initialize results
        matches = {}
        total_points = 0
        max_points = 0
        job_keyword_text = []
        # Iterate over job keywords
        for keyword_tuple in job_keywords:
            # Update keyword list and max points
            job_keyword_text.append(keyword_tuple[0])
            max_points += keyword_tuple[1] * 2
        # Find matches
        for keyword_tuple in resume_keywords:
            # Check for match
            if keyword_tuple[0] in job_keyword_text:
                # Get match index
                match_index = job_keyword_text.index(keyword_tuple[0])
                # Set value to false to speed up matching
                job_keyword_text[match_index] = False
                # Set match string to combined value
                match_value = keyword_tuple[1] + job_keywords[match_index][1]
                matches[keyword_tuple[0]] = match_value
                total_points += match_value
        return matches