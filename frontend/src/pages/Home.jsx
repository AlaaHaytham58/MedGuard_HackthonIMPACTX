import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import TopNav from "../components/TopNav.jsx";
import { useHistory } from "../state/HistoryContext.jsx";
import { analyzePhotos } from "../api/client.js";
import {
  UploadCloudIcon,
  CameraIcon,
  SearchIcon,
  InfoIcon,
  SpinnerIcon,
  TrashIcon,
  AlertIcon,
} from "../components/icons.jsx";
import "./Home.css";

export default function Home() {
  const navigate = useNavigate();
  const { recordCheck } = useHistory();
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const [photo, setPhoto] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [searchError, setSearchError] = useState("");
  const [requestError, setRequestError] = useState("");
  const [submitting, setSubmitting] = useState(null); // null | "photo" | "search"

  function handleFiles(fileList) {
    const files = Array.from(fileList || []).slice(0, 4);
    if (!files.length) return;
    setPhoto({ files, name: files.map((file) => file.name).join(", "), url: URL.createObjectURL(files[0]) });
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    handleFiles(event.dataTransfer.files);
  }

  async function handleCheckPhoto() {
    if (!photo || submitting) return;
    setSubmitting("photo");
    setRequestError("");
    try {
      const report = await analyzePhotos(photo.files);
      const id = recordCheck(report);
      navigate(`/results/${id}`);
    } catch (error) {
      setRequestError(error.message || "Could not analyze the photo.");
      setSubmitting(null);
    }
  }

  function handleSearchSubmit(event) {
    event.preventDefault();
    if (submitting) return;
    if (!searchText.trim()) {
      setSearchError("Type a medicine name to continue.");
      return;
    }
    setSearchError("");
    setSearchError("Search integration is not connected yet. Upload a photo to check medicines.");
  }

  const busy = Boolean(submitting);

  return (
    <div className="page">
      <TopNav />

      <main className="home">
        <div className="home__intro">
          <h1>Check if your medicines are safe to take together</h1>
          <p className="home__lede">
            Upload a photo of a medicine box, or search by name. MedGuard reads the
            medicines and checks them against a verified medical database.
          </p>
        </div>

        <div className="disclaimer" role="note">
          <InfoIcon className="disclaimer__icon" />
          <p>
            MedGuard helps read and match medicine names. It doesn't decide whether a
            combination is safe — that answer always comes from verified medical
            data, never from AI guessing. It doesn't replace your doctor or
            pharmacist.
          </p>
        </div>

        <section className="panel panel--primary" aria-labelledby="upload-heading">
          <h2 id="upload-heading" className="panel__heading">
            Upload a photo
          </h2>

          {!photo ? (
            <div
              className={"dropzone" + (isDragging ? " dropzone--active" : "")}
              onDragOver={(event) => {
                event.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
            >
              <UploadCloudIcon className="dropzone__icon" />
              <p className="dropzone__title">Drag a photo here</p>
              <p className="dropzone__hint">or choose one below · JPG or PNG, up to 10MB</p>

              <div className="dropzone__actions">
                <button
                  type="button"
                  className="btn btn--secondary"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={busy}
                >
                  Choose photo
                </button>
                <button
                  type="button"
                  className="btn btn--ghost"
                  onClick={() => cameraInputRef.current?.click()}
                  disabled={busy}
                >
                  <CameraIcon /> Take a photo
                </button>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                className="visually-hidden"
                onChange={(event) => handleFiles(event.target.files)}
              />
              <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                multiple
                className="visually-hidden"
                onChange={(event) => handleFiles(event.target.files)}
              />
            </div>
          ) : (
            <div className="photo-chip">
              <img src={photo.url} alt="" className="photo-chip__thumb" />
              <div className="photo-chip__meta">
                <p className="photo-chip__name">{photo.name}</p>
                <p className="photo-chip__status">Ready to check</p>
              </div>
              <button
                type="button"
                className="icon-btn"
                onClick={() => setPhoto(null)}
                disabled={busy}
                aria-label="Remove photo"
              >
                <TrashIcon />
              </button>
            </div>
          )}

          {photo && (
            <button
              type="button"
              className="btn btn--primary btn--block"
              onClick={handleCheckPhoto}
              disabled={busy}
            >
              {submitting === "photo" ? (
                <>
                  <SpinnerIcon size={18} /> Reading your medicine…
                </>
              ) : (
                "Check interactions"
              )}
            </button>
          )}
        </section>

        <div className="divider">
          <span>or</span>
        </div>

        <section className="panel" aria-labelledby="search-heading">
          <h2 id="search-heading" className="panel__heading panel__heading--muted">
            Search by name instead
          </h2>
          <form className="search-form" onSubmit={handleSearchSubmit} noValidate>
            <div className="search-form__field">
              <SearchIcon className="search-form__icon" />
              <input
                type="text"
                value={searchText}
                onChange={(event) => {
                  setSearchText(event.target.value);
                  if (searchError) setSearchError("");
                }}
                placeholder="e.g. Panadol Extra"
                aria-label="Medicine name"
                aria-invalid={Boolean(searchError)}
                aria-describedby={searchError ? "search-error" : undefined}
                disabled={busy}
              />
            </div>
            <button type="submit" className="btn btn--outline" disabled={busy}>
              {submitting === "search" ? (
                <>
                  <SpinnerIcon size={18} /> Looking that up…
                </>
              ) : (
                "Check interactions"
              )}
            </button>
          </form>
          {searchError && (
            <p id="search-error" className="field-error">
              <AlertIcon width={16} height={16} />
              {searchError}
            </p>
          )}
          {requestError && <p className="field-error">{requestError}</p>}
        </section>
      </main>
    </div>
  );
}
