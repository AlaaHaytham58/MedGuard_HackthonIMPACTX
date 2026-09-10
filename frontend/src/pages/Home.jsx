import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import TopNav from "../components/TopNav.jsx";
import ConditionSelector from "../components/ConditionSelector.jsx";
import { useHistory } from "../state/HistoryContext.jsx";
import { useLanguage } from "../state/LanguageContext.jsx";
import { boxes } from "../data/boxes.js";
import { checkMedications, findAlternatives, runPipeline } from "../api/client.js";
import { reportFromCheck, reportFromPipeline } from "../api/report.js";
import {
  ScanFrameIcon,
  SearchIcon,
  InfoIcon,
  SpinnerIcon,
  TrashIcon,
  AlertIcon,
  ArrowRightIcon,
  PrinterIcon,
  ShieldMark,
} from "../components/icons.jsx";
import "./Home.css";

// Mirrors the reference template's scroll reveal: elements marked [data-reveal]
// stay hidden until they enter the viewport, then animate once.
function useScrollReveal() {
  const rootRef = useRef(null);

  useEffect(() => {
    const targets = rootRef.current.querySelectorAll("[data-reveal]");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-revealed");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );

    targets.forEach((target) => observer.observe(target));
    return () => observer.disconnect();
  }, []);

  return rootRef;
}

export default function Home() {
  const navigate = useNavigate();
  const { recordCheck } = useHistory();
  const fileInputRef = useRef(null);
  const revealRoot = useScrollReveal();
  const { t, isArabic } = useLanguage();

  const MAX_PHOTOS = 4;

  const [photos, setPhotos] = useState([]);
  const [selectedConditions, setSelectedConditions] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);
  const [searchMedicines, setSearchMedicines] = useState([""]);
  const [activeSearchMedicine, setActiveSearchMedicine] = useState(0);
  const [searchError, setSearchError] = useState("");
  const [submitting, setSubmitting] = useState(null);
  const [failure, setFailure] = useState("");

  const busy = Boolean(submitting);
  const chosen = boxes.filter((box) => selectedIds.includes(box.id));
  const canCheckBoxes = chosen.length >= 2;
  const currentSearchText = searchMedicines[activeSearchMedicine] ?? "";

  function handleFiles(fileList) {
    const incoming = Array.from(fileList ?? []);
    if (incoming.length === 0) return;
    setFailure("");
    setPhotos((previous) =>
      [...previous, ...incoming.map((file) => ({ file, url: URL.createObjectURL(file) }))].slice(
        0,
        MAX_PHOTOS
      )
    );
  }

  function removePhoto(index) {
    setPhotos((previous) => {
      URL.revokeObjectURL(previous[index].url);
      return previous.filter((_, position) => position !== index);
    });
  }

  function handleDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    handleFiles(event.dataTransfer.files);
  }

  function toggleBox(id) {
    setFailure("");
    setSelectedIds((previous) =>
      previous.includes(id) ? previous.filter((entry) => entry !== id) : [...previous, id]
    );
  }

  async function handleCheckPhotos() {
    if (photos.length === 0 || busy) return;
    setSubmitting("photo");
    setFailure("");
    try {
      const data = await runPipeline(photos.map((photo) => photo.file), selectedConditions);
      const report = reportFromPipeline(data);
      if (report.medications.length === 0) {
        setFailure(
          "We could not read a medicine name from those photos. Try a clearer, closer shot of the box front."
        );
        return;
      }
      navigate(`/results/${recordCheck(report)}`);
    } catch (error) {
      setFailure(error.message);
    } finally {
      setSubmitting(null);
    }
  }

  async function handleCheckBoxes() {
    if (!canCheckBoxes || busy) return;
    setSubmitting("boxes");
    setFailure("");

    const medications = chosen.map((box) => ({
      input_name: box.brand,
      generic_name: box.ingredient,
      dosage_mg: box.dosageMg ?? null,
      match_method: "picker",
      match_confidence: 1,
    }));

    try {
      const [check, ...alternatives] = await Promise.all([
        checkMedications(medications),
        ...chosen.map((box) =>
          findAlternatives(box.brand, box.dosageMg).catch(() => null)
        ),
      ]);

      const report = reportFromCheck(check, {
        medications: chosen.map((box) => ({
          inputName: box.brand,
          ingredient: box.ingredient,
          dosageMg: box.dosageMg ?? null,
          image: box.image,
          matchMethod: "picker",
        })),
        alternatives: alternatives.filter(Boolean),
      });

      navigate(`/results/${recordCheck(report)}`);
    } catch (error) {
      setFailure(error.message);
    } finally {
      setSubmitting(null);
    }
  }

  async function handleSearchSubmit(event) {
    event.preventDefault();
    if (busy) return;

    const typedMedicines = searchMedicines.map((medicine) => medicine.trim()).filter(Boolean);
    const uniqueMedicines = [...new Set(typedMedicines)];
    if (uniqueMedicines.length === 0) {
      setSearchError("Type a medicine name to continue.");
      return;
    }

    setSearchError("");
    setSubmitting("search");
    setFailure("");
    try {
      const data = await runPipeline([], selectedConditions, "", uniqueMedicines);
      const report = reportFromPipeline(data);
      if (report.medications.length === 0) {
        setSearchError("That medicine is not in the catalogue. Try the brand name on the box.");
        return;
      }
      navigate(`/results/${recordCheck(report)}`);
    } catch (error) {
      setSearchError(error.message);
    } finally {
      setSubmitting(null);
    }
  }

  return (
    <div className="page" ref={revealRoot}>
      <TopNav />

      <main>
        {/* ---------- Hero: the tool itself is the offer ---------- */}
        <section className="hero">
          <div className="hero__inner">
            <div className="hero__copy" data-reveal>
              <p className="kicker kicker--onDark">{t("Built for Egyptian medicine boxes")}</p>
              <h1 className="hero__title">{t("Know if your medicines are safe together")}</h1>
              <p className="hero__lede">
                {t("Photograph the boxes you have at home. MedGuard reads the active ingredient off each one and checks the combination against a verified medical database.")}
              </p>
              <div className="hero__note">
                <span className="hero__rule" />
                <p>{t("No account. No cost. Works with brand names.")}</p>
              </div>
            </div>
          </div>
        </section>

        {/* ---------- The trust boundary, in the most prominent slot ---------- */}
        <section className="pipeline">
          <div className="shell">
            <ol className="pipeline__grid">
              <li className="step step--navy" data-reveal>
                <div className="step__top">
                  <span className="step__num">1</span>
                  <span className="step__rule" />
                </div>
                <h3 className="step__title">{t("You photograph the boxes")}</h3>
                <p className="step__body">
                  {t("Egyptian brand names are fine — Brufen, Concor, Marevan. You never need to know the generic name.")}
                </p>
              </li>

              <li className="step step--cyan" data-reveal style={{ transitionDelay: "0.12s" }}>
                <div className="step__top">
                  <span className="step__num">2</span>
                  <span className="step__rule" />
                </div>
                <h3 className="step__title">{t("AI reads the ingredient")}</h3>
                <p className="step__body">
                  {t("Vision pulls the brand name off the packaging and maps it to its active ingredient. That is all the AI does.")}
                </p>
              </li>

              <li className="step step--outline" data-reveal style={{ transitionDelay: "0.24s" }}>
                <div className="step__top">
                  <span className="step__num">3</span>
                  <span className="step__rule" />
                </div>
                <h3 className="step__title">{t("A database gives the verdict")}</h3>
                <p className="step__body">
                  {t("DDInter 2.0 decides whether the combination is dangerous. Never the AI — that boundary is the whole point.")}
                </p>
              </li>
            </ol>
          </div>
        </section>

        {/* ---------- Upload: the primary way in ---------- */}
        <section className="starter" id="start">
          <div className="shell">
            <div className="upload-card" data-reveal>
              <h2 className="upload-card__heading">{t("Start your check")}</h2>

              <ConditionSelector
                selectedConditions={selectedConditions}
                onChange={setSelectedConditions}
                disabled={busy}
              />

              <div
                className={"dropzone" + (isDragging ? " dropzone--active" : "")}
                onDragOver={(event) => {
                  event.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
              >
                <span className="dropzone__sweep" aria-hidden="true" />
                <ScanFrameIcon className="dropzone__icon" />
                <p className="dropzone__title">{t("Drag your medicine photos here")}</p>
                <p className="dropzone__hint">
                  Up to {MAX_PHOTOS} boxes — add them all, then check them in one go
                </p>
              </div>

              {photos.length > 0 && (
                <ul className="photo-list">
                  {photos.map((photo, index) => (
                    <li key={photo.url} className="photo-chip">
                      <img src={photo.url} alt="" className="photo-chip__thumb" />
                      <div className="photo-chip__meta">
                        <p className="photo-chip__name">{photo.file.name}</p>
                        <p className="photo-chip__status">{t("Ready to check")}</p>
                      </div>
                      <button
                        type="button"
                        className="icon-btn"
                        onClick={() => removePhoto(index)}
                        disabled={busy}
                        aria-label={`Remove ${photo.file.name}`}
                      >
                        <TrashIcon />
                      </button>
                    </li>
                  ))}
                </ul>
              )}

              <div className="upload-card__actions">
                {photos.length > 0 && (
                  <button
                    type="button"
                    className="mg-btn mg-btn--solid mg-btn--block"
                    onClick={handleCheckPhotos}
                    disabled={busy}
                  >
                    {submitting === "photo" ? (
                      <>
                        <SpinnerIcon size={18} /> Reading your medicines
                      </>
                    ) : (
                      `Check ${photos.length} ${photos.length === 1 ? "photo" : "photos"}`
                    )}
                  </button>
                )}

                <button
                  type="button"
                  className={
                    "mg-btn mg-btn--block " +
                    (photos.length > 0 ? "mg-btn--outline" : "mg-btn--solid")
                  }
                  onClick={() => fileInputRef.current?.click()}
                  disabled={busy || photos.length >= MAX_PHOTOS}
                >
                  {photos.length === 0
                    ? t("Choose photos")
                    : photos.length >= MAX_PHOTOS
                      ? `Maximum ${MAX_PHOTOS} photos`
                      : t("Add another photo")}
                </button>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                className="visually-hidden"
                onChange={(event) => {
                  handleFiles(event.target.files);
                  event.target.value = "";
                }}
              />

              {failure && (
                <p className="field-error" role="alert">
                  <AlertIcon width={16} height={16} />
                  {failure}
                </p>
              )}

              <p className="upload-card__alt">
                {isArabic ? "لا تملك العبوة؟" : "Don't have the box handy?"} <a href="#search">{t("Search by name")}</a>
              </p>
            </div>
          </div>
        </section>

        {/* ---------- Pick by packaging, not by generic name ---------- */}
        <section className="picker">
          <div className="shell">
            <header className="section-head" data-reveal>
              <h2 className="section-head__title">{t("Pick the boxes you have")}</h2>
              <p className="section-head__lede">
                {t("Recognise your medicine by its packaging, not by a generic name you were never told. Tap a box to add it to the check.")}
              </p>
            </header>

            <ul className="box-grid">
              {boxes.map((box, index) => {
                const isSelected = selectedIds.includes(box.id);
                return (
                  <li key={box.id} data-reveal style={{ transitionDelay: `${index * 0.08}s` }}>
                    <button
                      type="button"
                      className={"box-card" + (isSelected ? " box-card--on" : "")}
                      onClick={() => toggleBox(box.id)}
                      disabled={busy}
                      aria-pressed={isSelected}
                    >
                      {isSelected && <span className="box-card__tag">{isArabic ? "تمت الإضافة" : "Added"}</span>}
                      <span className="box-card__frame">
                        <img src={box.image} alt="" className="box-card__img" />
                      </span>
                      <span className="box-card__meta">
                        <span className="box-card__brand">{box.brand}</span>
                        <span className="box-card__ingredient">{box.ingredient}</span>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>

            <p className="picker__fallback">
              {t("Your box not here?")} <a href="#search">{t("Photograph it instead")}</a> — {t("that is what MedGuard is built for.")}
            </p>
          </div>
        </section>

        {/* ---------- Brand to generic, made visible ---------- */}
        <section className="checking">
          <div className="shell">
            <header className="section-head" data-reveal>
              <h2 className="section-head__title">{t("What we are actually checking")}</h2>
            </header>

            <div className="checking__card" data-reveal>
              {chosen.length === 0 ? (
                <p className="checking__empty">
                  {t("Nothing picked yet — tap a box above and we will show you the active ingredients we would look up.")}
                </p>
              ) : (
                <div className="checking__flow">
                  <ul className="ingredient-cards">
                    {chosen.map((box) => (
                      <li key={box.id} className="ingredient-card">
                        <img src={box.image} alt="" />
                        <div>
                          <p className="ingredient-card__brand">{box.brand}</p>
                          <p className="ingredient-card__name">{box.ingredient}</p>
                        </div>
                      </li>
                    ))}
                  </ul>

                  <div className="checking__arrow" aria-hidden="true">
                    <ArrowRightIcon />
                    <span>DDInter 2.0</span>
                  </div>

                  <div className="checking__verdict">
                    <div className="preview preview--quiet">
                      <InfoIcon />
                      <p>
                        {canCheckBoxes
                          ? (isArabic
                            ? `يتم فحص كل زوج من الأزواج المحتملة وعددها ${(chosen.length * (chosen.length - 1)) / 2} مقابل قاعدة البيانات.`
                            : `Every one of the ${(chosen.length * (chosen.length - 1)) / 2} possible pairs gets checked against the database.`)
                          : t("Add one more box — a combination needs at least two medicines.")}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {failure && (
                <p className="field-error" role="alert">
                  <AlertIcon width={16} height={16} />
                  {failure}
                </p>
              )}

              <div className="checking__cta">
                <button
                  type="button"
                  className="mg-btn mg-btn--solid"
                  onClick={handleCheckBoxes}
                  disabled={busy || !canCheckBoxes}
                >
                  {submitting === "boxes" ? (
                    <>
                      <SpinnerIcon size={18} /> Checking
                    </>
                  ) : (
                    canCheckBoxes
                      ? (isArabic ? `افحص هذه الأدوية (${chosen.length})` : `Check these ${chosen.length} medicines`)
                      : t("Check my medicines")
                  )}
                </button>
                <p className="checking__hint">
                  {canCheckBoxes
                    ? t("The verdict comes from the DDInter catalogue, not the AI.")
                    : t("Pick at least two boxes to check a combination.")}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ---------- Search fallback ---------- */}
        <section className="search-band" id="search">
          <div className="shell shell--narrow">
            <header className="section-head" data-reveal>
              <h2 className="section-head__title">{t("Or type the name instead")}</h2>
            </header>

            <ConditionSelector
              selectedConditions={selectedConditions}
              onChange={setSelectedConditions}
              disabled={busy}
            />

            <form className="search-form" onSubmit={handleSearchSubmit} noValidate data-reveal>
              <div className="search-tabs" role="tablist" aria-label={isArabic ? "الأدوية" : "Medicines"}>
                {searchMedicines.map((_, index) => (
                  <div className="search-tab" key={`medicine-${index}`}>
                    <button
                      type="button"
                      role="tab"
                      aria-selected={activeSearchMedicine === index}
                      className={activeSearchMedicine === index ? "search-tab__button search-tab__button--active" : "search-tab__button"}
                      onClick={() => setActiveSearchMedicine(index)}
                    >
                      {isArabic ? `دواء ${index + 1}` : `Medicine ${index + 1}`}
                    </button>
                    {searchMedicines.length > 1 && (
                      <button
                        type="button"
                        className="search-tab__remove"
                        onClick={() => {
                          setSearchMedicines((previous) => previous.filter((_, item) => item !== index));
                          setActiveSearchMedicine(0);
                        }}
                        aria-label={isArabic ? "حذف الدواء" : "Remove medicine"}
                      >
                        ×
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type="button"
                  className="search-tabs__add"
                  onClick={() => {
                    setSearchMedicines((previous) => [...previous, ""]);
                    setActiveSearchMedicine(searchMedicines.length);
                  }}
                  disabled={busy || searchMedicines.length >= 4}
                >
                  + {isArabic ? "دواء آخر" : "Add medicine"}
                </button>
              </div>
              <div className="search-form__field">
                <SearchIcon className="search-form__icon" />
                <input
                  type="text"
                  value={currentSearchText}
                  onChange={(event) => {
                    const value = event.target.value;
                    setSearchMedicines((previous) => previous.map((medicine, index) =>
                      index === activeSearchMedicine ? value : medicine
                    ));
                    if (searchError) setSearchError("");
                  }}
                  placeholder="e.g. Panadol Extra"
                  aria-label={t("Medicine name")}
                  aria-invalid={Boolean(searchError)}
                  aria-describedby={searchError ? "search-error" : undefined}
                  disabled={busy}
                />
              </div>
              <button type="submit" className="mg-btn mg-btn--outline" disabled={busy}>
                {submitting === "search" ? (
                  <>
                    <SpinnerIcon size={18} /> Looking that up
                  </>
                ) : (
                  t("Check interactions")
                )}
              </button>
            </form>
            {searchError && (
              <p id="search-error" className="field-error">
                <AlertIcon width={16} height={16} />
                {searchError}
              </p>
            )}
          </div>
        </section>

        {/* ---------- Provenance ---------- */}
        <section className="provenance">
          <div className="shell shell--narrow">
            <div className="provenance__mark" data-reveal>
              <ShieldMark size={40} crossColor="var(--cyan)" />
            </div>
            <blockquote className="provenance__quote" data-reveal>
              {t("The AI only reads the names off your boxes. The verdict itself always comes from a verified medical database — never from the AI's judgement.")}
            </blockquote>
            <span className="provenance__rule" />

            <ul className="sources" data-reveal>
              <li className="source source--navy">
                <h3>DDInter 2.0</h3>
                <p>
                  {t("The interaction database that renders every verdict. Loaded locally, so a venue with no wifi cannot break it.")}
                </p>
              </li>
              <li className="source source--cyan">
                <h3>RxNorm</h3>
                <p>
                  {t("Maps an Egyptian brand name to the generic ingredient the database can actually look up.")}
                </p>
              </li>
              <li className="source source--faint">
                <h3>openFDA</h3>
                <p>
                  {t("The fallback consulted when DDInter has no entry for a pair, before we admit we do not know.")}
                </p>
              </li>
            </ul>
          </div>
        </section>

        {/* ---------- The two real outcomes ---------- */}
        <section className="outcomes">
          <div className="shell">
            <div className="outcomes__grid">
              <article className="outcome outcome--light" data-reveal>
                <PrinterIcon />
                <h3>{t("One page you can print")}</h3>
                <p>
                  {t("The result is a plain-language sheet a caregiver can hand to a doctor or pharmacist — not a screen full of clinical codes.")}
                </p>
              </article>

              <article className="outcome outcome--dark" data-reveal style={{ transitionDelay: "0.12s" }}>
                <InfoIcon />
                <h3>{t("When we cannot confirm, we say so")}</h3>
                <p>
                  {t("An unrecognised box is never dropped or guessed at. It is shown to you as “not enough data to confirm — consult your pharmacist.”")}
                </p>
              </article>
            </div>
          </div>
        </section>
      </main>

      <footer className="site-footer">
        <div className="shell">
          <div className="site-footer__grid">
            <div>
              <div className="site-footer__brand">
                <ShieldMark size={26} crossColor="#071527" />
                <span>MedGuard</span>
              </div>
              <p className="site-footer__blurb">
                {t("MedGuard helps you read and match medicine names. It does not replace your doctor or pharmacist, and it does not decide whether a combination is safe — verified medical data does.")}
              </p>
            </div>

            <div>
              <h4>{t("Product")}</h4>
              <a href="#search">{t("Search by name")}</a>
            </div>

            <div>
              <h4>{t("Data")}</h4>
              <p>DDInter 2.0</p>
              <p>RxNorm</p>
              <p>openFDA</p>
            </div>
          </div>

          <p className="site-footer__legal">
            {t("IMPACT 2026 — Healthcare Track prototype. Not a medical device.")}
          </p>
        </div>
      </footer>
    </div>
  );
}