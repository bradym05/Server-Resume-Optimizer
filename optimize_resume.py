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

class CompareResume():
    """
    Compare Resume

    ...

    Attributes
    ----------
    resume_string : str
        String resume
    job_string : str
        String job description

    Methods
    -------
    compare():
        Compare keywords and update attributes
    get_matches():
        Returns match dictionary {keyword: match value} from compare()
    get_match_points():
        Returns total points accumulated from compare()
    get_match_percentage():
        Returns match_points/max_points from compare()
    get_missed_keywords():
        Returns a dictionary {missed keyword: match value} of keywords from the job posting which were not in the resume from compare()
    """
    def __init__(self, resume_string: str, job_string: str):
        """
        Construct a new CompareResume object

        Parameters
        ----------
        resume_string : str
            String resume
        job_string : str
            String job description

        """
        # Set private attributes
        self.__matches = {}
        self.__misses = {}
        self.__match_points = 0
        self.__max_points = 0
        # Create Rakun Keywords objects
        self.__resume_keywords = RakunKeyphraseDetector(RAKUN_HYPERPARAMETERS)
        self.__job_keywords = RakunKeyphraseDetector(RAKUN_HYPERPARAMETERS)
        # Set public attributes
        self.resume_string = resume_string
        self.job_string = job_string
    
    # Getters
    def get_matches(self) -> Dict[str, float]:
        """
        Get matches from compare() results
        """
        return self.__matches
    def get_match_points(self) -> float:
        """
        Get match_points from compare() results
        """
        return self.__match_points
    def get_match_percentage(self) -> float:
        """
        Get match_points/max_points
        """
        return self.__match_points/self.__max_points
    def get_missed_keywords(self) -> Dict[str, float]:
        """
        Get keywords from the job posting which were not in the resume, and their values
        """
        missed_keywords = {}
        resume_keywords = [keyword_tuple[0] for keyword_tuple in self.__resume_keywords.final_keywords]
        # Iterate over job keywords
        for keyword_tuple in self.__job_keywords.final_keywords:
            keyword_string = keyword_tuple[0]
            if keyword_string in resume_keywords:
                continue
            else:
                missed_keywords[keyword_string] = keyword_tuple[1]
        return missed_keywords

    # Compare keywords
    def compare(self):
        """
        Main comparison method\n
        1. Finds keywords with Rakun2
        2. Finds resume keywords that match with job keywords
        3. Calculates score per keyword by adding the values from Rakun2
        """
        # Get keywords
        resume_keywords = self.__resume_keywords.find_keywords(self.resume_string, input_type="string")
        job_keywords = self.__job_keywords.find_keywords(self.job_string, input_type="string")
        # Initialize results
        matches = {}
        match_points = 0
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
                match_points += match_value
        # Update attributes
        self.__match_points = match_points
        self.__max_points = max_points
        self.__matches = matches

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
    
    Methods
    -------
    match_parse_resume():
        [RECOMMENDED] Parses resume by finding words that match predefined section names
    font_parse_resume():
        Parses resume by finding headings or font styles that differ from the base font style
    get_contact_info():
        Returns dictionary of contact info from resume after parsing
    get_urls():
        Returns list of URLs from resume after parsing
    get_compare_string():
        Returns joined resume sections (except header) after parsing
    """

    # List of possible resume section names
    RESUME_SECTIONS: List[List[str]] = [
        ["about", "profile", "introduction", "summary", "objective"],
        ["education", "school", "academic"],
        ["qualification", "skill", "credential", "certification", "certificate"],
        ["experience", "history", "project", "work"],
    ]
    # Regex for contact info
    CONTACT_REGEX: Dict[str, str] = {
        "phone": r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]',
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,3}" #https://www.reddit.com/r/Python/comments/16jj0x9/
    }
    # URL Regex from https://regex101.com/r/03VgN5/5/
    URL_REGEX: str = r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b"
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
            found_keys = []
            for index in range(contact_info_count):
                key = self.__missing_contact_info[index]
                matches = re.findall(ResumeOptimizer.CONTACT_REGEX[key], text)
                if matches:
                    match_string = matches[0]
                    # Update contact info
                    self.__contact_info[key] = match_string
                    # Remove from text
                    text = text.replace(match_string, "")
                    # Update array of found keys
                    found_keys.append(key)
            # Remove found keys from missing contact info
            for key in found_keys:
                self.__missing_contact_info.remove(key)
            # Check if more info was found
            if len(self.__contact_info) > 0 and len(found_keys) == 0:
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
    def get_compare_string(self, parsed_resume : Dict[str, List[str]]) -> str:
        """
        Compile string from Resume, primarily used for compare_keywords() method
        """
        compare_string = ""
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
    
    def optimize(self):
        """
        Main optimization method\n
        1. Parses resume with match_parse_resume()
        2. Compares resume with CompareResume object
        """
        # Parse and compile compare string
        sections = self.match_parse_resume()
        compare_string = self.get_compare_string(sections)
        # Create comparison object, and compare
        comparison_object = CompareResume(compare_string, self.job_string)
        comparison_object.compare()
        # Get comparison percentage
        match_percentage = comparison_object.get_match_percentage()
