import os
import requests
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from io import BytesIO
from PIL import Image

app = FastAPI()

# Set up the static and template directories
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global variable to track progress
download_progress = {"progress": 0}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/download/")
async def download_asset(url: str = Form(...)):
    global download_progress
    download_progress["progress"] = 0  # Reset progress at the start

    # Get the file extension
    file_extension = os.path.splitext(url)[-1].lower()

    downloaded = 0  # Initialize downloaded variable
    total_size = 0  # Initialize total_size variable

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise HTTPError for bad responses

        total_size = int(response.headers.get('content-length', 0))

        if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            img_data = BytesIO()

            for data in response.iter_content(chunk_size=1024):
                img_data.write(data)
                downloaded += len(data)
                download_progress["progress"] = int((downloaded / total_size) * 100)

            img_data.seek(0)  # Reset stream position for reading
            img = Image.open(img_data)
            img_path = "temp_image" + file_extension
            
            # Create a StreamingResponse to send the image
            return StreamingResponse(BytesIO(img.tobytes()), media_type="image/jpeg", headers={"Content-Disposition": f"attachment; filename={os.path.basename(img_path)}"})

        elif file_extension in ['.mp4', '.mov', '.avi']:
            video_path = "temp_video" + file_extension
            
            # Create a StreamingResponse to send the video
            return StreamingResponse(response.iter_content(chunk_size=8192), media_type="video/mp4", headers={"Content-Disposition": f"attachment; filename={os.path.basename(video_path)}"})

        else:
            return JSONResponse({"error": "Unsupported file type."}, status_code=400)

    except requests.HTTPError as http_err:
        download_progress["progress"] = 0  # Reset progress on failure
        return JSONResponse({"error": f"HTTP error occurred: {str(http_err)}"}, status_code=response.status_code)
    except requests.ConnectionError:
        download_progress["progress"] = 0  # Reset progress on failure
        return JSONResponse({"error": "Connection error occurred. Please check your internet connection."}, status_code=500)
    except requests.Timeout:
        download_progress["progress"] = 0  # Reset progress on failure
        return JSONResponse({"error": "Request timed out. Please try again later."}, status_code=500)
    except Exception as e:
        download_progress["progress"] = 0  # Reset progress on failure
        return JSONResponse({"error": f"An unexpected error occurred: {str(e)}"}, status_code=500)
    finally:
        # Reset progress if download was completed successfully
        if downloaded == total_size and total_size > 0:
            download_progress["progress"] = 100

@app.get("/progress/")
async def get_progress():
    """API endpoint to get the download progress."""
    return JSONResponse(download_progress)
