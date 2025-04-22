from io import BytesIO

from docx import Document

from typing import Annotated, Final

from pydantic import BaseModel

from fastapi import FastAPI, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from optimize_resume import ResumeOptimizer

# List of allowed origins
ALLOWED_ORIGINS: Final = [
    "https://bradym05.github.io",
]
# Max job description length
JOB_DESCRIPTION_MAX_LENGTH: Final = 2000

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

# Resume file and job description
class UploadFileModel(BaseModel):
    file: UploadFile
    job_description: Annotated[str, Query(max_length=JOB_DESCRIPTION_MAX_LENGTH)] = ""

# Main upload function
@app.post("/uploadfile/")
async def create_upload_file(request_body: UploadFileModel):
    # Get request values
    file = request_body.file
    job_description = request_body.job_description
    # Validate file type
    if file.filename.endswith(".docx"):
        # Validate job description
        if len(job_description) >= 100:
            # Get file contents
            contents = await file.read()
            # Create resume
            resume_object = ResumeOptimizer(Document(BytesIO(contents)), job_description)
            resume_object.compare_keywords()
        else:
            raise HTTPException(status_code=401, detail="Job description is too short (minimum 100 characters)")
    else:
        # Indicate fail due to invalid file type
        raise HTTPException(status_code=400, detail="Invalid file type")
    return {"filename": file.filename}