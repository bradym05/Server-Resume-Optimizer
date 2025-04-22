from typing import Final, Annotated
from fastapi import FastAPI, UploadFile, HTTPException, Query

# Constants
MAX_FILE_SIZE: Final = 256

# Create FastAPI App Object
app = FastAPI()

# Main upload function
@app.post("/uploadfile/")
async def create_upload_file(file: Annotated[UploadFile, Query(max_length=MAX_FILE_SIZE)]):
    # Get file contents
    contents = await file.read()
    print(contents)
    return {"filename": file.filename}