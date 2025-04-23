from docx import Document, table

from enum import Enum
from typing import Final, Dict, List
from rakun2 import RakunKeyphraseDetector

# Hyperparemeters for rakun2
RAKUN_HYPERPARAMETERS: Final = {
    "num_keywords": 70,
    "merge_threshold": 0.5,
    "alpha": 0.9,
    "token_prune_len": 6
}

class ResumeOptimizer():
    """
    Resume Class - Initialize from a valid python-docx Document object
    """

    # List of possible resume section names
    RESUME_SECTIONS = [
        ["about", "profile", "introduction", "summary", "objective"],
        ["education", "school"],
        ["qualification", "skill", "credential", "certification"],
        ["experience", "history", "project"],
    ]

    # Sections for comparison
    COMPARISON_SECTIONS = ["qualification", "experience", "education"]

    def __init__(self, resume_doc: Document, job_description: str):
        # Set attributes
        self.resume_doc = resume_doc
        self.job_string = job_description
        # Parse resume
        self.__parsed_resume = self.parse_resume()
        # Keywords objects
        self.__resume_keywords = RakunKeyphraseDetector(RAKUN_HYPERPARAMETERS)
        self.__job_keywords = RakunKeyphraseDetector(RAKUN_HYPERPARAMETERS)

    # Seperate resume by sections
    def parse_resume(self) -> Dict[str, List[str | None]]:
        """
        Identifies sections, and groups resume content into a dictionary where the keys are the sections
        Checks for section name matches after blank lines, updates section if there is a match
        """
        # Initialize variables
        new_section = True
        current_section = "header"
        sections = {base_names[0]:[] for base_names in ResumeOptimizer.RESUME_SECTIONS}
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
                        content_paragraph = False
                        break
            if content_paragraph:
                # Add text to current section
                sections[current_section].append(paragraph.text)
        # Return parsed resume
        return sections
    
    # Compare the keywords of the resume, and job posting
    def compare_keywords(self):
        # Create resume string
        resume_string = "\n".join([p.text for p in self.resume_doc.paragraphs])
        # Get keywords
        resume_keywords = self.__resume_keywords.find_keywords(resume_string, input_type="string")
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