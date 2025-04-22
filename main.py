from io import BytesIO

from docx import Document

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from optimize_resume import Resume

# List of allowed origins
origins = [
    "https://bradym05.github.io",
]

# Create FastAPI App Object
app = FastAPI()

# Add list of origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Main upload function
@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    # Validate file type
    if file.filename.endswith(".docx"):
        # Get file contents
        contents = await file.read()
        # Create resume
        resume_object = Resume(Document(BytesIO(contents)))
        print(resume_object.get_key_words())
    else:
        # Indicate fail due to invalid file type
        raise HTTPException(status_code=400, detail="Invalid file type")
    return {"filename": file.filename}