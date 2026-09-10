import { useLanguage } from "../state/LanguageContext.jsx";
import "./ConditionSelector.css";

const CONDITIONS = [
  { key: "pregnancy", icon: "♧", english: "Pregnancy", arabic: "الحمل" },
  { key: "high_blood_pressure", icon: "⌁", english: "High blood pressure", arabic: "ارتفاع ضغط الدم" },
  { key: "diabetes", icon: "◉", english: "Diabetes", arabic: "السكري" },
  { key: "lactation", icon: "◌", english: "Breastfeeding", arabic: "الرضاعة الطبيعية" },
  { key: "heart", icon: "♡", english: "Heart disease", arabic: "أمراض القلب" },
];

export default function ConditionSelector({ selectedConditions, onChange, disabled = false }) {
  const { isArabic } = useLanguage();

  function toggle(condition) {
    if (selectedConditions.includes(condition)) {
      onChange(selectedConditions.filter((item) => item !== condition));
    } else {
      onChange([...selectedConditions, condition]);
    }
  }

  return (
    <section className="condition-selector" aria-labelledby="condition-selector-title">
      <div className="condition-selector__intro">
        <div>
          <p className="condition-selector__eyebrow">{isArabic ? "ملف المريض" : "Patient profile"}</p>
          <h3 id="condition-selector-title" className="condition-selector__title">
            {isArabic ? "هل تنطبق أي من هذه الحالات؟" : "Do any of these conditions apply?"}
          </h3>
          <p className="condition-selector__hint">
            {isArabic
              ? "سنستخدمها لإظهار تحذيرات إضافية مرتبطة بالدواء."
              : "We will use these to show additional medicine warnings."}
          </p>
        </div>
        <span className="condition-selector__optional">
          {isArabic ? "اختياري" : "Optional"}
        </span>
      </div>

      <div className="condition-selector__grid">
        {CONDITIONS.map((condition) => {
          const selected = selectedConditions.includes(condition.key);
          return (
            <button
              key={condition.key}
              type="button"
              className={`condition-chip${selected ? " condition-chip--selected" : ""}`}
              onClick={() => toggle(condition.key)}
              aria-pressed={selected}
              disabled={disabled}
            >
              <span className="condition-chip__icon" aria-hidden="true">{condition.icon}</span>
              <span>{isArabic ? condition.arabic : condition.english}</span>
              <span className="condition-chip__check" aria-hidden="true">{selected ? "✓" : ""}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
