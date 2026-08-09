const $ = (selector) => document.querySelector(selector);
const dropzone = $("#dropzone");
const input = $("#file-input");
const uploadState = $("#upload-state");
const loadingState = $("#loading-state");
const previewState = $("#preview-state");
const errorMessage = $("#error-message");
let objectUrl;

function showState(state) {
  uploadState.hidden = state !== "upload";
  loadingState.hidden = state !== "loading";
  previewState.hidden = state !== "preview";
}

async function processFile(file) {
  if (!file) return;
  errorMessage.textContent = "";
  showState("loading");
  const formData = new FormData();
  formData.append("file", file, file.name || "camera-capture.jpg");
  try {
    const response = await fetch("/api/detect", { method: "POST", body: formData });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Detection failed");
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(file);
    const image = $("#preview-image");
    image.src = objectUrl;
    await image.decode();
    drawFaces(image, data);
    $("#result-title").textContent = `${data.face_count} face${data.face_count === 1 ? "" : "s"} detected`;
    $("#result-detail").textContent = `Processed securely in ${data.processing_ms} ms`;
    showState("preview");
    await refreshActivity();
  } catch (error) {
    showState("upload");
    errorMessage.textContent = error.message;
  }
}

function drawFaces(image, data) {
  const canvas = $("#face-canvas");
  canvas.width = image.clientWidth;
  canvas.height = image.clientHeight;
  canvas.style.left = `${image.offsetLeft}px`;
  canvas.style.width = `${image.clientWidth}px`;
  const context = canvas.getContext("2d");
  const scaleX = canvas.width / data.image.width;
  const scaleY = canvas.height / data.image.height;
  context.strokeStyle = "#35e0a1";
  context.lineWidth = 3;
  data.faces.forEach((face) => context.strokeRect(face.x * scaleX, face.y * scaleY, face.width * scaleX, face.height * scaleY));
}

async function refreshActivity() {
  const response = await fetch("/api/activity");
  const data = await response.json();
  $("#detection-total").textContent = data.total;
  $("#faces-total").textContent = data.items.reduce((sum, item) => sum + item.faces, 0);
  const average = data.items.length ? data.items.reduce((sum, item) => sum + item.processing_ms, 0) / data.items.length : 0;
  $("#latency-average").textContent = average ? `${average.toFixed(0)} ms` : "—";
  $("#activity-list").innerHTML = data.items.length ? data.items.map((item) => `
    <div class="activity-item"><span class="file-icon">▧</span><div><strong>${escapeHtml(item.filename)}</strong><small>${item.faces} face${item.faces === 1 ? "" : "s"} found</small></div><time>${item.processing_ms} ms</time></div>`).join("") :
    '<div class="empty-state"><span>⌁</span><h3>No detections yet</h3><p>Your processed images will appear here.</p></div>';
}

function escapeHtml(value) { const node = document.createElement("div"); node.textContent = value; return node.innerHTML; }

$("#browse-button").addEventListener("click", (event) => { event.stopPropagation(); input.click(); });
dropzone.addEventListener("click", () => { if (!previewState.hidden) return; input.click(); });
dropzone.addEventListener("keydown", (event) => { if (["Enter", " "].includes(event.key)) input.click(); });
input.addEventListener("change", () => processFile(input.files[0]));
["dragenter", "dragover"].forEach((name) => dropzone.addEventListener(name, (event) => { event.preventDefault(); dropzone.classList.add("dragging"); }));
["dragleave", "drop"].forEach((name) => dropzone.addEventListener(name, (event) => { event.preventDefault(); dropzone.classList.remove("dragging"); }));
dropzone.addEventListener("drop", (event) => processFile(event.dataTransfer.files[0]));
$("#reset-button").addEventListener("click", (event) => { event.stopPropagation(); input.value = ""; showState("upload"); });
$("#refresh-button").addEventListener("click", refreshActivity);

const dialog = $("#camera-dialog");
const video = $("#camera-video");
let stream;
$("#camera-button").addEventListener("click", async () => {
  try { stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false }); video.srcObject = stream; dialog.showModal(); }
  catch { errorMessage.textContent = "Camera access is unavailable. Check your browser permissions."; }
});
function closeCamera() { if (stream) stream.getTracks().forEach((track) => track.stop()); dialog.close(); }
$("#camera-close").addEventListener("click", closeCamera);
$("#capture-button").addEventListener("click", () => {
  const canvas = $("#capture-canvas"); canvas.width = video.videoWidth; canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0); closeCamera();
  canvas.toBlob((blob) => processFile(new File([blob], "camera-capture.jpg", { type: "image/jpeg" })), "image/jpeg", .9);
});

refreshActivity();
