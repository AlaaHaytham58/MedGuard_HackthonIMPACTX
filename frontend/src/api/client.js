const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

export async function analyzePhotos(files) {
  const body = new FormData();
  for (const file of files) {
    body.append("images", file);
  }

  const response = await fetch(`${API_BASE_URL}/pipeline`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    throw new Error(`Photo analysis failed (${response.status})`);
  }
  return response.json();
}