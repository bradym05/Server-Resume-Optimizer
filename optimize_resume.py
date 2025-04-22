from docx import Document
from enum import Enum
from typing import Final, Tuple
from rakun2 import RakunKeyphraseDetector

# Hyperparemeters for rakun2
RAKUN_HYPERPARAMETERS: Final = {
    "num_keywords": 20,
    "merge_threshold": 1.1,
    "alpha": 0.3,
    "token_prune_len": 3
}

class ResumeOptimizer():
    """
    Resume Class - Initialize from a valid python-docx Document object
    """
    def __init__(self, resume_doc: Document, job_description: str):
        self.resume_doc = resume_doc
        self.resume_text = "\n".join([p.text for p in self.resume_doc.paragraphs])
        self.job_description = job_description
        self.__keyword_detector = RakunKeyphraseDetector(RAKUN_HYPERPARAMETERS)
        self.__keyword_cache = {}

    def get_keywords(self, attribute) -> list[Tuple[str, float]]:
        """
        Extract keywords of given attribute (doc name) with rakun2, cache results
        Args:
        attribute - ("resume_text" or "job_description")
        """
        # Get attribute
        keyword_text = getattr(self, attribute, False)
        if keyword_text and len(keyword_text) > 0:
            # Check cache
            if not AttributeError in self.__keyword_cache.keys():
                # Find keywords and update cache
                self.__keyword_cache[attribute] = self.__keyword_detector.find_keywords(keyword_text, input_type="string")
            # Return cached keywords
            return self.__keyword_cache[attribute]
        
    def compare_keywords(self):
        """
        Compare the scores of resume_text and job_description
        """
        # Get keywords
        job_results = self.get_keywords("job_description")
        resume_results = self.get_keywords("resume_text")
        # Create list of job keywords only
        job_keywords = [keyword_tuple[0] for keyword_tuple in job_results]
        # Results variables
        total_matches = 0
        total_difference = 0
        match_differences = {}
        # Iterate over resume keywords
        for keyword_tuple in resume_results:
            # Check for a match
            resume_keyword = keyword_tuple[0]
            if resume_keyword in job_keywords:
                # Get matched index
                matched_index = job_keywords.index(resume_keyword)
                job_keywords.pop(matched_index)
                # Get full tuple
                job_tuple = job_results[matched_index + total_matches]
                # Record match difference
                difference = job_tuple[1] - keyword_tuple[1]
                total_difference += abs(difference)
                match_differences[resume_keyword] = difference
                # Update total matches
                total_matches += 1
        print(f"Keyword Matches: {total_matches}")
        print(f"Usage Difference {total_difference}")
        for keyword, difference in match_differences.items():
            print(f'Keyword "{keyword}" value difference: {difference}')
