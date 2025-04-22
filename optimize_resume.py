from docx import Document
from typing import Final
from rakun2 import RakunKeyphraseDetector

# Hyperparemeters for rakun2
RAKUN_HYPERPARAMETERS: Final = {
    "num_keywords": 20,
    "merge_threshold": 1.1,
    "alpha": 0.3,
    "token_prune_len": 3
}

class Resume():
    """
    Resume Class - Initialize from a valid python-docx Document object
    """
    def __init__(self, resume_doc: Document):
        self.resume_doc = resume_doc
        self.resume_text = "\n".join([p.text for p in self.resume_doc.paragraphs])
        self.__keyword_detector = RakunKeyphraseDetector(RAKUN_HYPERPARAMETERS)

    def get_key_words(self) -> list:
        """
        Extract keywords with rakun2
        """
        return self.__keyword_detector.find_keywords(self.resume_text, input_type="string")