from docx import Document, table

from enum import Enum
from typing import Final, Dict, List
from rakun2 import RakunKeyphraseDetector

# Hyperparemeters for rakun2
RAKUN_HYPERPARAMETERS: Final = {
    "num_keywords": 20,
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
        for content in self.resume_doc.iter_inner_content():
            # Check content type
            if type(content) == table.Table:
                # Append all text from all table cells
                for column in content.columns:
                    for cell in column.cells:
                        for paragraph in cell.paragraphs:
                            # Check if paragraph has content
                            if paragraph.text.strip():
                                sections[current_section].append(paragraph.text)
            else:
                # Check for blank line (typically between sections on a resume)
                if not content.text.strip():
                    new_section = True
                    continue
                elif new_section:
                    new_section = False
                    # Iterate over section names
                    for section_names in ResumeOptimizer.RESUME_SECTIONS:
                        # Check for a match
                        if any(name in content.text.lower() for name in section_names):
                            # Update current section name
                            current_section = section_names[0]
                            break
                # Add text to current section
                sections[current_section].append(content.text)
        # Return parsed resume
        return sections
    
    # Compare the keywords of the resume, and job posting
    def compare_keywords(self):
        # Get job posting keywords first
        job_keywords = self.__job_keywords.find_keywords(self.job_string, input_type="string")
        # Create resume string
        resume_string = ""
        for section_name in ResumeOptimizer.COMPARISON_SECTIONS:
            resume_string += " ".join(self.__parsed_resume[section_name])
        # Compare keywords using job keywords as priors
        resume_keywords = self.__resume_keywords.find_keywords(resume_string, input_type="string")
        print(resume_string)
        print(resume_keywords)