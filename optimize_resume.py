from docx import Document
from enum import Enum
from typing import Final, Tuple, Dict
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
    def __init__(self, resume_doc: Document, job_description: str):
        # Set attributes
        self.resume_doc = resume_doc
        self.job_string = job_description
        self.resume_string = "\n".join([p.text for p in self.resume_doc.paragraphs])
        # Keywords objects
        self.resume_keywords = RakunKeyphraseDetector(RAKUN_HYPERPARAMETERS)
        self.job_keywords = RakunKeyphraseDetector(RAKUN_HYPERPARAMETERS)

    def get_keywords(self, rakun_object:RakunKeyphraseDetector, text:str ) -> list[Tuple[str, float]]:
        """
        Get final keywords from rakun2 object with given text
        Use pre-existing results if possible
        """
        if rakun_object.final_keywords:
            return rakun_object.final_keywords
        else:
            return rakun_object.find_keywords(text, input_type="string")
        
    def compare_keywords(self) -> Tuple[Dict[str, Dict[str, float]], list[Tuple[str, float]], float]:
        """
        Compare the scores of resume_text and job_description
        Return values:
            Match Dictionary {
                Keyword: {
                    Difference - Float representing the difference between docs
                    Value - Float representing the keyword's value in the job posting
                }
            }
            Missed Words - List of missed words sorted from highest to lowest value
            Total Difference - Float sum of total difference between docs
        """
        # Get keywords
        job_results = self.get_keywords(self.job_keywords, self.job_string)
        resume_results = self.get_keywords(self.resume_keywords, self.resume_string)
        # Create list of job keywords only
        job_keywords = [keyword_tuple[0] for keyword_tuple in job_results]
        # Results variables
        matches = {}
        missed_words = []
        total_difference = 0
        # Iterate over resume keywords
        for keyword_tuple in resume_results:
            # Check for a match
            resume_keyword = keyword_tuple[0]
            if resume_keyword in job_keywords:
                # Get matched index
                matched_index = job_keywords.index(resume_keyword)
                # Get full tuple
                job_tuple = job_results[matched_index]
                # Record match difference
                difference = job_tuple[1] - keyword_tuple[1]
                total_difference += abs(difference)
                matches[resume_keyword] = {
                    "Difference": difference,
                    "Value": job_tuple[1]
                }
        # Iterate over unmatched keywords from job posting
        for index in range(len(job_keywords)):
            # Check if keyword matched
            keyword = job_keywords[index]
            if keyword in matches.keys():
                continue
            else:
                # Update difference
                total_difference += job_results[index][1]
                missed_words.append(job_results[index])
        # Sort missed words
        missed_words.sort(key=lambda keyword_tuple: keyword_tuple[1], reverse=True)
        print(f"Usage Difference {total_difference}")
        for keyword, info in matches.items():
            print(f'Keyword "{keyword}" value difference: {info["Difference"]}')
        print("Resume Keywords", [keyword_tuple[0] for keyword_tuple in resume_results])
        print("Job Keywords", job_keywords)
        print(missed_words)
        return matches, missed_words, total_difference