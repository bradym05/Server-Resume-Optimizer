from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware

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
    # Get file contents
    contents = await file.read()
    print(contents)
    return {"filename": file.filename}