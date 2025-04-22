from fastapi import FastAPI, UploadFile

# Create FastAPI App Object
app = FastAPI()

# Main upload function
@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    # Get file contents
    contents = await file.read()
    print(contents)
    return {"filename": file.filename}