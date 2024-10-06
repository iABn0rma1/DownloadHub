const urlInput = document.getElementById("urlInput");
const previewContainer = document.getElementById("previewContainer");
const form = document.getElementById("downloadForm");
const progressBar = document.getElementById("progressBar");
const progressText = document.getElementById("progressText");
const progressLine = document.getElementById("progressLine");
const statusMessage = document.getElementById("statusMessage");
const downloadButton = document.getElementById("downloadButton");
let rateLimitTimer = null;
let progressInterval = null; // Variable to hold the progress interval

urlInput.addEventListener("input", function () {
	const url = urlInput.value;
	if (isValidUrl(url)) {
		fetchPreview(url);
	} else {
		clearPreview(); // Clear preview if the URL is invalid
	}
});

function isValidUrl(url) {
	// Basic URL validation
	return (
		url.endsWith(".jpg") ||
		url.endsWith(".jpeg") ||
		url.endsWith(".png") ||
		url.endsWith(".gif") ||
		url.endsWith(".bmp") ||
		url.endsWith(".mp4") ||
		url.endsWith(".mov") ||
		url.endsWith(".avi")
	);
}

function fetchPreview(url) {
	fetch(url)
		.then((response) => {
			if (!response.ok) throw new Error("Failed to fetch the asset.");
			return response.blob();
		})
		.then((blob) => {
			const objectURL = URL.createObjectURL(blob);
			renderPreview(objectURL, url);
		})
		.catch((error) => {
			console.error(error);
			clearPreview(); // Clear preview on error
		});
}

function renderPreview(objectURL, url) {
	clearPreview(); // Clear any existing previews
	const fileExtension = url.split(".").pop().toLowerCase();

	if (["jpg", "jpeg", "png", "gif", "bmp"].includes(fileExtension)) {
		const img = document.createElement("img");
		img.src = objectURL;
		img.alt = "Image Preview";
		img.style.maxWidth = "100%"; // Responsive image
		img.style.height = "auto";
		previewContainer.appendChild(img);
	} else if (["mp4", "mov", "avi"].includes(fileExtension)) {
		const video = document.createElement("video");
		video.src = objectURL;
		video.controls = true; // Show controls for video
		video.style.maxWidth = "100%"; // Responsive video
		video.style.height = "auto";
		previewContainer.appendChild(video);
	}
}

function clearPreview() {
	previewContainer.innerHTML = ""; // Clear existing previews
}

form.addEventListener("submit", function (e) {
	e.preventDefault();
	const url = urlInput.value;
	resetStatus(); // Reset status message
	startDownload(url);
});

function startDownload(url) {
	// Send the download request
	const formData = new FormData();
	formData.append("url", url);

	fetch("/download/", {
		method: "POST",
		body: formData,
	})
		.then((response) => {
			if (response.ok) {
				return response.blob();
			} else {
				throw new Error("Download failed");
			}
		})
		.then((blob) => {
			const downloadUrl = window.URL.createObjectURL(blob);
			const a = document.createElement("a");
			a.href = downloadUrl;
			a.download = url.split("/").pop(); // Extract filename from URL
			document.body.appendChild(a);
			a.click();
			a.remove();
			showSuccess(); // Show success status
			applyRateLimit(); // Apply rate limit after success
		})
		.catch((error) => {
			showError(); // Show error status
			clearInterval(progressInterval); // Stop progress updates on error
		});

	// Start polling for progress
	updateProgress();
}

function updateProgress() {
	progressInterval = setInterval(function () {
		fetch("/progress/")
			.then((response) => response.json())
			.then((data) => {
				progressBar.style.width = data.progress + "%";
				progressText.textContent = `Progress: ${data.progress}%`;
				progressLine.style.width = data.progress + "%"; // Update progress line below navbar
				if (data.progress >= 100) {
					clearInterval(progressInterval);
				}
			});
	}, 500); // Poll every 500ms
}

function resetStatus() {
	statusMessage.textContent = "";
}

function showSuccess() {
	statusMessage.textContent = "Download completed successfully!";
	statusMessage.style.color = "#28a745"; // Green for success
}

function showError() {
	statusMessage.textContent = "Download failed. Please try again.";
	statusMessage.style.color = "#dc3545"; // Red for error
}

function applyRateLimit() {
	downloadButton.disabled = true; // Disable the button
	let timeLeft = 15;
	statusMessage.textContent = `Please wait ${timeLeft} seconds before the next download.`;
	statusMessage.style.color = "#ffcc00"; // Yellow color for rate limit message

	rateLimitTimer = setInterval(function () {
		timeLeft -= 1;
		statusMessage.textContent = `Please wait ${timeLeft} seconds before the next download.`;
		if (timeLeft <= 0) {
			clearInterval(rateLimitTimer);
			downloadButton.disabled = false; // Re-enable the button after 15 seconds
			resetStatus();
		}
	}, 1000); // Update every second
}
