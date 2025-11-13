// app.js
document.getElementById('uploadBtn').addEventListener('click', async () => {
  const fromLang = document.getElementById('fromLang').value;
  const toLang = document.getElementById('toLang').value;
  const fileInput = document.getElementById('fileInput');
  const statusEl = document.getElementById('status');
  const downloadLink = document.getElementById('downloadLink');

  if (!fileInput.files.length) {
    statusEl.innerText = "Please select a PDF file.";
    return;
  }

  statusEl.innerText = "Requesting upload URL...";

  try {
    // 1 Generate pre-signed URL
    const res = await fetch(`${CONFIG.API_BASE_URL}/generate?fromLang=${fromLang}&toLang=${toLang}`);
    const data = await res.json();
    console.log("Presigned URL:", data.url);

    // 2 Upload PDF to S3
    const pdfFile = fileInput.files[0];
    statusEl.innerText = "Uploading PDF...";
    const uploadRes = await fetch(data.url, {
      method: 'PUT',
      body: pdfFile,
      headers: { 'Content-Type': 'application/pdf' }
    });

    if (!uploadRes.ok) throw new Error(`Upload failed: ${uploadRes.status}`);

    statusEl.innerText = "Upload complete! PDF is being processed.";
    console.log("Upload complete:", data.request_id);

    // 3 Poll for translation status
    const requestId = data.request_id;
    let completed = false;

    while (!completed) {
      await new Promise(r => setTimeout(r, 3000));
      const statusRes = await fetch(`${CONFIG.API_BASE_URL}/status?requestId=${requestId}`);
      const statusData = await statusRes.json();
      console.log(`Status: ${statusData.status}`);

      if (statusData.status === "COMPLETED") {
        statusEl.innerText = " Translation completed!";

        // Fix download link formatting (convert s3:// to https://)
        let downloadUrl = statusData.download_url;
        if (downloadUrl && downloadUrl.startsWith("s3://")) {
          const parts = downloadUrl.replace("s3://", "").split("/");
          const bucket = parts.shift();
          const key = parts.join("/");
          downloadUrl = `https://${bucket}.s3.${CONFIG.REGION}.amazonaws.com/${key}`;
        }

        downloadLink.href = downloadUrl;
        downloadLink.textContent = "Download translated text";
        downloadLink.style.display = "inline-block";

        completed = true;
      } else if (statusData.status === "FAILED") {
        statusEl.innerText = " Translation failed.";
        completed = true;
      } else {
        console.log("Still processing:", statusData.status);
      }
    }
  } catch (err) {
    console.error("Error:", err);
    statusEl.innerText = "Error: " + err.message;
  }
});

