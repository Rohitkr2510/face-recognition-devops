const select = (selector) => document.querySelector(selector);

const sourcePicker = select("#source-picker");
const workingView = select("#working-view");
const resultView = select("#result-view");
const fileInput = select("#file-input");
const errorMessage = select("#error-message");
const resultImage = select("#result-image");
let previewUrl;

function showView(view) {
  sourcePicker.hidden = view !== "source";
  workingView.hidden = view !== "working";
  resultView.hidden = view !== "result";
}

function showError(message) {
  errorMessage.textContent = message;
  showView("source");
}

async function detectFaces(file) {
  if (!file) return;
  errorMessage.textContent = "";
  showView("working");

  const formData = new FormData();
  formData.append("file", file, file.name || "camera-photo.jpg");

  try {
    const response = await fetch("/api/detect", { method: "POST", body: formData });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "The image could not be processed.");

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(file);
    resultImage.src = previewUrl;
    await resultImage.decode();

    showView("result");
    drawFaceBoxes(result);
    const noun = result.face_count === 1 ? "face" : "faces";
    select("#result-title").textContent = `${result.face_count} ${noun} found`;
    select("#result-detail").textContent = `Processed in ${result.processing_ms} ms · ${result.image.width} × ${result.image.height} px`;
    select("#image-pill").textContent = `${result.face_count} ${noun} detected`;
  } catch (error) {
    showError(error instanceof Error ? error.message : "Something went wrong. Please try again.");
  }
}

function drawFaceBoxes(result) {
  const canvas = select("#face-canvas");
  const displayedWidth = resultImage.clientWidth;
  const displayedHeight = resultImage.clientHeight;
  canvas.width = displayedWidth;
  canvas.height = displayedHeight;
  canvas.style.left = `${resultImage.offsetLeft}px`;
  canvas.style.top = `${resultImage.offsetTop}px`;

  const context = canvas.getContext("2d");
  context.strokeStyle = "#55efb2";
  context.fillStyle = "#55efb2";
  context.lineWidth = Math.max(2, displayedWidth / 300);
  context.font = "600 11px DM Sans";

  const scaleX = displayedWidth / result.image.width;
  const scaleY = displayedHeight / result.image.height;
  result.faces.forEach((face, index) => {
    const x = face.x * scaleX;
    const y = face.y * scaleY;
    const width = face.width * scaleX;
    const height = face.height * scaleY;
    context.strokeRect(x, y, width, height);
    context.fillRect(x, Math.max(0, y - 20), 48, 20);
    context.fillStyle = "#10261e";
    context.fillText(`Face ${index + 1}`, x + 5, Math.max(14, y - 6));
    context.fillStyle = "#55efb2";
  });
}

select("#upload-button").addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => detectFaces(fileInput.files[0]));
select("#reset-button").addEventListener("click", () => {
  fileInput.value = "";
  errorMessage.textContent = "";
  showView("source");
});

const cameraDialog = select("#camera-dialog");
const cameraVideo = select("#camera-video");
let cameraStream;

function closeCamera() {
  cameraStream?.getTracks().forEach((track) => track.stop());
  cameraStream = undefined;
  cameraDialog.close();
}

select("#camera-button").addEventListener("click", async () => {
  if (!navigator.mediaDevices?.getUserMedia) {
    showError("Camera access is not supported by this browser.");
    return;
  }
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
      audio: false,
    });
    cameraVideo.srcObject = cameraStream;
    cameraDialog.showModal();
  } catch {
    showError("Camera access was denied. Allow camera access or upload an image instead.");
  }
});

select("#camera-close").addEventListener("click", closeCamera);
cameraDialog.addEventListener("cancel", (event) => {
  event.preventDefault();
  closeCamera();
});

select("#capture-button").addEventListener("click", () => {
  const canvas = select("#capture-canvas");
  canvas.width = cameraVideo.videoWidth;
  canvas.height = cameraVideo.videoHeight;
  canvas.getContext("2d").drawImage(cameraVideo, 0, 0);
  closeCamera();
  canvas.toBlob((blob) => {
    if (blob) detectFaces(new File([blob], "camera-photo.jpg", { type: "image/jpeg" }));
  }, "image/jpeg", 0.92);
});
