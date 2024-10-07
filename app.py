import os
import requests
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from io import BytesIO
from PIL import Image
from pathlib import Path

app = FastAPI()

# Set up the static and template directories
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global variable to track progress
download_progress = {"progress": 0}

# Get user's Downloads folder path
downloads_folder = str(Path.home() / "Downloads")

def download_image(url, save_path):
    """
    Download an image from a URL and save it to the specified path.
    """
    try:
        response = requests.get(url, timeout=10)  # Set a timeout for the request
        response.raise_for_status()  # Raise an error for bad status codes

        with open(save_path, 'wb') as file:
            file.write(response.content)

        print(f"Downloaded: {save_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
    except OSError as e:
        print(f"Error saving {save_path}: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/download/")
async def download_asset(url: str = Form(...)):
    global download_progress
    download_progress["progress"] = 0  # Reset progress at the start

    # Get the file extension
    file_extension = os.path.splitext(url)[-1].lower()

    # Construct the save path in the Downloads folder
    file_name = f"downloaded_image{file_extension}"
    save_path = os.path.join(downloads_folder, file_name)

    try:
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            # Call the download_image function to download and save the image
            download_image(url, save_path)

            # Return the image file as a download
            return FileResponse(save_path, media_type="image/jpeg", filename=file_name)

        else:
            return JSONResponse({"error": "Unsupported file type."}, status_code=400)

    except Exception as e:
        download_progress["progress"] = 0  # Reset progress on failure
        return JSONResponse({"error": f"An unexpected error occurred: {str(e)}"}, status_code=500)

@app.get("/progress/")
async def get_progress():
    """API endpoint to get the download progress."""
    return JSONResponse(download_progress)
