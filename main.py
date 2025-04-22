from io import BytesIO
from uuid import uuid1

from docx import Document

from typing import Annotated, Final

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from optimize_resume import ResumeOptimizer

# List of allowed origins
ALLOWED_ORIGINS: Final = [
    "https://bradym05.github.io",
]
# Max job description length
JOB_DESCRIPTION_MAX_LENGTH: Final = 2000

# Resume storage
resume_storage = {}

# Create FastAPI App Object
app = FastAPI()

# Add list of origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Main upload function
@app.post("/uploadfile/")
async def create_upload_file(file: Annotated[UploadFile, File()], job_description: Annotated[str, Form(max_length=JOB_DESCRIPTION_MAX_LENGTH)]):
    # Initialize file id
    file_id = ""
    if file.filename.endswith(".docx"):
        # Validate job description
        if len(job_description) >= 100:
            # Get file contents
            contents = await file.read()
            # Create resume
            resume_object = ResumeOptimizer(Document(BytesIO(contents)), job_description)
            resume_object.compare_keywords()
            # Create UUID
            file_id = uuid1()
            # Reference file
            resume_storage[file_id] = resume_object
        else:
            raise HTTPException(status_code=401, detail="Job description is too short (minimum 100 characters)")
    else:
        # Indicate fail due to invalid file type
        raise HTTPException(status_code=400, detail="Invalid file type")
    return {"file_id": file_id}