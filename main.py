from io import BytesIO
from uuid import uuid4, UUID

from docx import Document

from typing import Annotated, Final, Dict

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from optimize_resume import ResumeOptimizer

# List of allowed origins
ALLOWED_ORIGINS: Final = [
    "https://bradym05.github.io",
    "http://localhost:8080"
]
# Max job description length
JOB_DESCRIPTION_MAX_LENGTH: Final = 3000
JOB_DESCRIPTION_MIN_LENGTH: Final = 100
# Max resume size (bytes)
RESUME_MAX_SIZE: Final = 2e6
# MIME for docx files
DOCX_MIME: Final = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

# Resume storage
resume_storage: Dict[str, ResumeOptimizer] = {}

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
async def create_upload_file(file: Annotated[UploadFile, File()], job_description: Annotated[str, Form(max_length=JOB_DESCRIPTION_MAX_LENGTH, min_length=JOB_DESCRIPTION_MIN_LENGTH)]):
    # Initialize file id
    file_id = ""
    # Validate file type
    if file.content_type == DOCX_MIME:
        # Validate file size
        if file.size <= RESUME_MAX_SIZE:
            # Get file contents
            contents = await file.read(int(RESUME_MAX_SIZE))
            # Create resume
            resume_object = ResumeOptimizer(Document(BytesIO(contents)), job_description)
            # Create UUID, store as hex
            file_id = uuid4()
            # Reference file
            resume_storage[file_id] = resume_object
        else:
            raise HTTPException(status_code=403, detail="Resume file is too large (maximum 2mb)")
    else:
        # Indicate fail due to invalid file type
        raise HTTPException(status_code=403, detail="Invalid file type")
    return {"file_id": file_id}

# Optimize function
@app.get("/optimize/{file_id}")
async def optimize_resume(file_id: UUID):
    # Catch key error (resume not found)
    try:
        # Get resume object, remove from storage
        resume_object = resume_storage.pop(file_id)
        # Analyze and return results
        return resume_object.analyze()
    except KeyError:
        raise HTTPException(status_code=404, detail="Resume has not been uploaded")