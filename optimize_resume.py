import re
import numpy
import functools
import itertools

from docx.document import Document
from docx.table import Table

from typing import Final, Dict, List, Tuple, Optional
from rakun2 import RakunKeyphraseDetector

# Hyperparameters for rakun2
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
    to_count(keywords_dict):
        Converts given dictionary of keyword-float values into keyword-int values
    """

    # Extract words with regular expression
    WORD_REGEX: Final = r'\b\w+\b'

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
        self.__match_points = 0
        self.__max_points = 0
        # Create Rakun Keywords objects
        self.__resume_keywords = RakunKeyphraseDetector(RAKUN_HYPERPARAMETERS)
        self.__job_keywords = RakunKeyphraseDetector(RAKUN_HYPERPARAMETERS)
        # Set public attributes
        self.resume_string = resume_string
        self.job_string = job_string
    
    # Getters
    @property
    def matches(self) -> Dict[str, float]:
        """
        Dictionary of matched word to value from compare() results
        """
        return self.__matches
    @property
    def match_points(self) -> float:
        """
        Total sum of points from compare() results
        """
        return self.__match_points
    @property
    def max_points(self) -> float:
        """
        Maximum points possible from compare() results
        """
        return self.__max_points
    @property
    @functools.cache
    def match_percentage(self) -> float:
        """
        match_points/max_points
        """
        return self.__match_points/self.__max_points
        
    @property
    @functools.cache
    def missed_keywords(self) -> Dict[str, float]:
        """
        Keywords from the job posting which were not in the resume, and their values
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
    
    @property
    @functools.cache
    def job_matches(self) -> List[Tuple[str, float]]:
        """
        Dictionary of matched keywords to their value in the job description
        """
        job_matches = {}
        for keyword_tuple in self.__job_keywords.final_keywords:
            if keyword_tuple[0] in self.matches.keys():
                job_matches[keyword_tuple[0]] = keyword_tuple[1]
        return job_matches
    
    @property
    @functools.cache
    def resume_matches(self) -> Dict[str, float]:
        """
        Dictionary of matched keywords to their value in the resume
        """
        resume_matches = {}
        for keyword_tuple in self.__resume_keywords.final_keywords:
            if keyword_tuple[0] in self.matches.keys():
                resume_matches[keyword_tuple[0]] = keyword_tuple[1]
        return resume_matches
    
    @property
    @functools.cache
    def low_keywords(self) -> Dict[str, float]:
        """
        Matched keywords which appeared less on the resume, and more on the job posting
        Dictionary of keywords to the difference in value (job - resume)
        """
        low_keywords = {}
        for keyword, resume_value in self.resume_matches.items():
            job_value = self.job_matches[keyword]
            if job_value > resume_value:
                low_keywords[keyword] = job_value - resume_value
        return low_keywords
    
    # Convert given Rakun2 keyword dictionary into a word count dictionary
    def to_count(self, keywords_dict: Dict[str, float]) -> Dict[str, int]:
        """
        Pass a Rakun2 keyword dictionary (keyword - float) and convert to (keyword - int)
        1. Calculates word-count ratio (job_string/resume_string)
        2. Iterates over all keywords in given dictionary
            - Counts keyword appearances in resume string
            - Adjusts count (count * ratio)
            - Counts keyword appearances in job string
            - Calculates difference (job_count - resume_count)
            - Records (keyword - difference) in dict if difference > 0
        3. Returns final keyword count dictionary
        """
        # Lower strings
        job_words = self.job_string.lower()
        resume_words = self.resume_string.lower()
        # Calculate resume/job word count ratio
        ratio = len(re.findall(CompareResume.WORD_REGEX, job_words))/len(re.findall(CompareResume.WORD_REGEX, resume_words))
        # Initialize dictionary
        keyword_counts = {}
        # Iterate over all matches
        for keyword in keywords_dict.keys():
            # Get resume count and adjust
            resume_count = resume_words.count(keyword) * ratio
            # Get job count and difference
            job_count = job_words.count(keyword)
            difference = round(job_count - resume_count)
            # Check if underused, reference
            if difference > 0:
                keyword_counts[keyword] = difference
        # Return final dictionary
        return keyword_counts
    
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
            max_points += keyword_tuple[1]
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
                # Update max points
                max_points += keyword_tuple[1]
        # Update attributes
        self.__match_points = match_points
        self.__max_points = max_points/2
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
    match_parse(parse_string: str, is_resume: bool):
        Parses text by finding words that match predefined section names
    get_compare_string(parse_results, keys):
        Returns joined sections (from given keys) from parse results
    apply_weights(sections: Dict[str, List[str | None]], keyword_values: Dict[str, float]):
        Apply SECTION_WEIGHTS to given keyword dict
    analyze():
        Parses and compares the resume and job description
        Returns JSON dictionary of results from comparison
        
    """

    # List of possible resume section names
    SECTION_IDENTIFIERS: List[List[str]] = [
        ["about", "profile", "introduction", "summary", "objective"],
        ["education", "school", "academic"],
        ["qualification", "skill", "credential", "certification", "certificate"],
        ["experience", "history", "project", "work"],
    ]
    # Weight of each section (applied to job description keywords)
    SECTION_WEIGHTS: Dict[str, float] = {
        "header": 1,
        "education": 1,
        "about": 2,
        "qualification": 4,
        "experience": 4,
    }
    # Regex for contact info
    CONTACT_REGEX: Dict[str, str] = {
        "phone": r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]',
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,3}" #https://www.reddit.com/r/Python/comments/16jj0x9/
    }
    # URL Regex from https://regex101.com/r/03VgN5/5/
    URL_REGEX: str = r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b"
    DATES_REGEX: str = r"((\d:[0-9]{2}/)?\d{2}/\d{4})"
    # Max length for the title of a section
    MAX_TITLE_LENGTH: int = 50
    # Threshold (of match points) for showing missed keywords instead of underused keywords
    MISSED_THRESHOLD: float = 0.7
    # Maximum number of underused words to return
    MAX_UNDERUSED: int = 20

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
        self.resume_string = ""
        # Create resume string
        for inner_content in self.resume_doc.iter_inner_content():
            # Check content type
            if type(inner_content) == Table:
                # Get paragraphs from content cells
                for column in inner_content.columns:
                    for cell in column.cells:
                        self.resume_string += "\n".join(p.text for p in cell.paragraphs)
            else:
                self.resume_string += f"\n{inner_content.text}"

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
    
    # Extract URLs from the given string, append them to private url list
    def __extract_urls(self, text: str) -> str:
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
        return text

    # Update sections dictionary, execute additional operations depending on the section
    def __update_sections(self, text, current_section: str, sections: Dict[str, List[str | None]]) -> str:
        # Call process function (if there is one)
        matched_section = None
        match current_section:
            case "header":
                text, new_section = self.__process_header(text)
                # Check for new section, match if possible
                if new_section:
                    matched_section = self.__match_section(text, sections)
            case "about":
                text, new_section = self.__process_header(text)
        # Extract urls
        text = self.__extract_urls(text)
        # Check if a new section was matched
        if matched_section:
            current_section = matched_section
        else:
            sections[current_section].append(text)
        return current_section
    
    def __match_section(self, text, sections) -> str | None:
        # Iterate over section names
        matched_section = None
        for section_names in ResumeOptimizer.SECTION_IDENTIFIERS:
            if not section_names[0] in sections.keys():
                # Check for a match
                if any(name in text.lower() for name in section_names):
                    # Update current section name
                    matched_section = section_names[0]
                    sections[matched_section] = []
                    break
        return matched_section

    # Getters
    @property
    def contact_info(self) -> Dict[str, str]:
        """Dictionary of contact info from parsing"""
        return self.__contact_info
    @property
    def urls(self) -> List[str]:
        """List of all URLs found from parsing"""
        return self.__urls
    def get_compare_string(self, parse_results: Dict[str, List[str]], keys: Optional[List[str]]=None) -> str:
        """
        Compile string from parse results, primarily used for compare_keywords() method
        1. Iterate over each section that was given in keys
        2. Append text to compare string, start new line
        3. Return final compare string
        """
        compare_string = ""
        keys = keys if keys else list(parse_results.keys())
        # Iterate over sections in parse results and append all text to the compare string
        for section_name in keys:
            for text in parse_results[section_name]:
                compare_string += text + "\n"
        # Return final compare string
        return compare_string

    # Seperate string by finding sections from common words
    def match_parse(self, parse_string: str, is_resume: bool = False) -> Dict[str, List[str | None]]:
        """
        Identifies sections, and groups content into a dictionary where the keys are the sections
        Checks for section name matches after blank lines, updates section if there is a match.

        Parameters
        ----------
        parse_string : str
            String which will be parsed
        is_resume : bool
            If True, additional content will be extracted and stored for analysis
        """
        # Initialize variables
        new_section = True
        current_section = "header"
        sections = {current_section : []}
        # Iterate over lines
        for line in parse_string.splitlines():
            body_paragraph = True
            # Check for blank line (typically between sections on a resume)
            if not line.strip():
                new_section = True
                continue
            elif new_section:
                new_section = False
                # Check for a match
                matched_section = self.__match_section(line, sections)
                if matched_section:
                    # Update current section name
                    current_section = matched_section
                    body_paragraph = False
            if body_paragraph:
                # Check if this is a resume, update accordingly
                if is_resume:
                    current_section = self.__update_sections(line, current_section, sections)
                else:
                    sections[current_section].append(line)
        # Return parsed resume
        return sections
    
    def apply_weights(self, sections: Dict[str, List[str | None]], keyword_values: Dict[str, float]) -> Dict[str, float]:
        """
        Apply SECTION_WEIGHTS to given keywords dictionary from the provided sections dictionary
        1. Get compare string (all sections combined)
        2. Add weights
            - Get section string by joining list
            - Iterate over all keywords
                - Cache/get cached total count (count of keyword in compare string)
                - Get count weight (#word in section/#word in all sections)
                - Add final weight ((Rakun2 value * section weight) * count weight)
            - Add section weight to total weight
        3. Divide weights
            - Iterate over each keyword - weight value
            - Divide by total weight
        4. Return final weighted dictionary
        """
        # Initialize variables
        total_weight = 0
        weighted_dict = keyword_values.copy()
        compare_string = self.get_compare_string(sections).lower()
        total_counts = {}
        # Iterate over each section
        for section_name, section_list in sections.items():
            # Check if section has any content
            if len(section_list) > 0:
                # Get section string
                section_string = "\n".join(section_list).lower()
                # Get section weight
                section_weight = ResumeOptimizer.SECTION_WEIGHTS[section_name]
                applied = False
                # Iterate over keywords
                for keyword, value in keyword_values.items():
                    # Check cache, count and cache if not cached already
                    if not keyword in total_counts.keys():
                        total_counts[keyword] = compare_string.count(keyword)
                    # Get section count
                    section_count = section_string.count(keyword)
                    # Check if keyword is in this section
                    if section_count > 0:
                        # Update applied
                        applied = True
                        # Calculate and add weight
                        count_weight = section_count/total_counts[keyword]
                        weighted_dict[keyword] += section_weight * value * count_weight
                # Check if section had any keywords
                if applied == True:
                    # Update total weight
                    total_weight += section_weight
            else:
                continue
        # Iterate over each keyword, divide weight
        for keyword in weighted_dict.keys():
            weighted_dict[keyword] /= total_weight
        # Return final weighted dictionary
        return weighted_dict
    
    # Get parsing results for given parse dictionary
    def parsing_results(self, parsed_dict: Dict[str, List[str | None]]) -> Dict[str, float | dict]:
        """
        1. Create list of successfully parsed sections
        2. Iterate over all possible sections
        3. Calculate total value of parsed sections
        4. Get score from total/max values
        Return dictionary: A dictionary with parse results
                    - "max_score":float',
                    - "parsing_score":float',
                    - "missed_sections":dict
                        - "value":float,
                        - "identifiers":list(str),
                    - "found_sections":dict
                        - "value":float,
                        - "identifiers":list(str),
        """
        # Create list of parsed sections
        parsed_sections = list(section_name for section_name, section_list in parsed_dict.items() if len(section_list) > 0)
        # Initialize variables
        max_score = 0
        parsing_score = 0
        missed_sections = {}
        found_sections = {}
        # Iterate over section names
        for section_ids in ResumeOptimizer.SECTION_IDENTIFIERS:
            section = section_ids[0]
            # Get section weight
            section_weight = ResumeOptimizer.SECTION_WEIGHTS[section]
            # Increment max score
            max_score += section_weight
            # Check if parsed
            if section in parsed_sections:
                # Increment parsing score
                parsing_score += section_weight
                # Record value in parsed sections
                found_sections[section] = {
                    "value": section_weight,
                    "identifiers": section_ids
                }
            else:
                # Record value in missed sections
                missed_sections[section] = {
                    "value": section_weight,
                    "identifiers": section_ids
                }
        # Return results
        return {
            "max_score":max_score,
            "parsing_score":parsing_score,
            "missed_sections":missed_sections,
            "found_sections":found_sections
        }
                
    @functools.cache
    def analyze(self) -> str:
        """
        Main analysis method
        1. Parses resume and job description with match_parse()
        2. Gets parsing results with parsing_results()
        3. Compares resume with CompareResume object
        4. Finds missed or underused keywords depending on match points 
            - (missed keywords are probably not meaningful if most keywords are matched)
        5. Create and return results as JSON ready dictionary
        """
        # Parse resume and job posting
        resume_sections = self.match_parse(self.resume_string, True)
        job_sections = self.match_parse(self.job_string)

        # Get parsing results
        parsing_results = self.parsing_results(resume_sections)
        
        # Compare job description and resume
        comparison_object = CompareResume(
                self.get_compare_string(resume_sections, list(resume_sections.keys())[1:]), # without header
                self.get_compare_string(job_sections)
            )
        comparison_object.compare()

        # Get weighted matches and missed keywords
        matched_weighted = self.apply_weights(job_sections, comparison_object.matches)
        missed_weighted = self.apply_weights(job_sections, comparison_object.missed_keywords)

        # Calculate scores
        matched_total = sum(matched_weighted.values())
        missed_total = sum(missed_weighted.values())
        net = missed_total + matched_total
        # Calculate final score
        if missed_total > matched_total:
            match_percentage = matched_total/missed_total
        elif net > 0:
            match_percentage = matched_total/(missed_total + matched_total)
        else:
            match_percentage = 0
        # Check match points
        if match_percentage >= ResumeOptimizer.MISSED_THRESHOLD:
            # Return underused keywords
            underused = comparison_object.to_count(matched_weighted)
        else:
            # Return missed keywords
            underused = comparison_object.to_count(missed_weighted)
        # Sort underused from high-low
        underused = dict(sorted(underused.items(), key=lambda item: item[1], reverse=True))

        # Return final results
        return {
            "match_percentage": float(match_percentage),
            "underused":dict(itertools.islice(underused.items(), min(len(underused), ResumeOptimizer.MAX_UNDERUSED))),
            "contact_info":self.contact_info,
            "parsing_results":parsing_results
        }