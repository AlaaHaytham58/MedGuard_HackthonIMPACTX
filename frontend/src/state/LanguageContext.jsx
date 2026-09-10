import { createContext, useContext, useEffect, useMemo, useState } from "react";

const LanguageContext = createContext(null);

const translations = {
  "Check": "تحقق",
  "Results": "النتائج",
  "Search by medicine name": "البحث باسم الدواء",
  "Built for Egyptian medicine boxes": "مصمم لعبوات الأدوية المصرية",
  "Know if your medicines are safe together": "اعرف ما إذا كانت أدويتك آمنة معًا",
  "Photograph the boxes you have at home. MedGuard reads the active ingredient off each one and checks the combination against a verified medical database.": "صوّر العبوات الموجودة لديك. يقرأ ميدغارد المادة الفعالة من كل عبوة ويفحص الجمع بينها باستخدام قاعدة بيانات طبية موثوقة.",
  "No account. No cost. Works with brand names.": "لا حاجة لحساب. مجانًا. يعمل بأسماء العلامات التجارية.",
  "You photograph the boxes": "صوّر العبوات",
  "Egyptian brand names are fine — Brufen, Concor, Marevan. You never need to know the generic name.": "أسماء العلامات التجارية المصرية مناسبة مثل بروفين وكونكور وماريفان. لا تحتاج إلى معرفة الاسم العلمي.",
  "AI reads the ingredient": "يقرأ الذكاء الاصطناعي المادة الفعالة",
  "Vision pulls the brand name off the packaging and maps it to its active ingredient. That is all the AI does.": "يستخرج النظام اسم العلامة من العبوة ويربطه بمادتها الفعالة. هذه هي مهمة الذكاء الاصطناعي فقط.",
  "A database gives the verdict": "قاعدة البيانات تحدد النتيجة",
  "DDInter 2.0 decides whether the combination is dangerous. Never the AI — that boundary is the whole point.": "تحدد قاعدة DDInter 2.0 مدى خطورة الجمع بين الأدوية، وليس الذكاء الاصطناعي.",
  "Start your check": "ابدأ الفحص",
  "Drag your medicine photos here": "اسحب صور أدويتك إلى هنا",
  "Ready to check": "جاهزة للفحص",
  "Choose photos": "اختر الصور",
  "Add another photo": "أضف صورة أخرى",
  "Search by name": "البحث بالاسم",
  "Pick the boxes you have": "اختر العبوات التي لديك",
  "What we are actually checking": "ما الذي نفحصه فعليًا",
  "Or type the name instead": "أو اكتب الاسم بدلًا من ذلك",
  "Recognise your medicine by its packaging, not by a generic name you were never told. Tap a box to add it to the check.": "تعرّف على دوائك من عبوته، وليس من اسم علمي لم يخبرك به أحد. اضغط على العبوة لإضافتها إلى الفحص.",
  "Your box not here?": "عبوتك غير موجودة؟",
  "Photograph it instead": "صوّرها بدلًا من ذلك",
  "that is what MedGuard is built for.": "هذا هو ما صُمم ميدغارد من أجله.",
  "Nothing picked yet — tap a box above and we will show you the active ingredients we would look up.": "لم تختر شيئًا بعد. اضغط على عبوة أعلاه وسنعرض لك المواد الفعالة التي سنبحث عنها.",
  "Add one more box — a combination needs at least two medicines.": "أضف عبوة أخرى. يحتاج الجمع إلى دواءين على الأقل.",
  "Check my medicines": "افحص أدويتي",
  "Pick at least two boxes to check a combination.": "اختر عبوتين على الأقل لفحص الجمع بينهما.",
  "The verdict comes from the DDInter catalogue, not the AI.": "النتيجة من كتالوج DDInter، وليست من الذكاء الاصطناعي.",
  "The AI only reads the names off your boxes. The verdict itself always comes from a verified medical database — never from the AI's judgement.": "يقرأ الذكاء الاصطناعي أسماء الأدوية من عبواتك فقط. أما النتيجة فتأتي دائمًا من قاعدة بيانات طبية موثوقة، وليس من حكم الذكاء الاصطناعي.",
  "The interaction database that renders every verdict. Loaded locally, so a venue with no wifi cannot break it.": "قاعدة بيانات التداخلات التي تحدد كل نتيجة. محملة محليًا، لذلك لا يؤثر انقطاع الإنترنت عليها.",
  "Maps an Egyptian brand name to the generic ingredient the database can actually look up.": "تربط اسم العلامة التجارية المصرية بالمادة الفعالة التي تستطيع قاعدة البيانات البحث عنها.",
  "The fallback consulted when DDInter has no entry for a pair, before we admit we do not know.": "المرجع البديل عند عدم وجود سجل للزوج في DDInter، قبل أن نقر بعدم المعرفة.",
  "One page you can print": "صفحة واحدة يمكنك طباعتها",
  "The result is a plain-language sheet a caregiver can hand to a doctor or pharmacist — not a screen full of clinical codes.": "النتيجة ورقة بلغة واضحة يمكن لمقدم الرعاية تقديمها للطبيب أو الصيدلي، وليست شاشة مليئة بالرموز الطبية.",
  "When we cannot confirm, we say so": "عندما لا نستطيع التأكد، نخبرك بذلك",
  "An unrecognised box is never dropped or guessed at. It is shown to you as “not enough data to confirm — consult your pharmacist.”": "لا يتم تجاهل العبوة غير المعروفة أو التخمين بشأنها. نوضح لك أنه لا توجد بيانات كافية للتأكد، ويجب استشارة الصيدلي.",
  "Product": "المنتج",
  "Data": "البيانات",
  "MedGuard helps you read and match medicine names. It does not replace your doctor or pharmacist, and it does not decide whether a combination is safe — verified medical data does.": "يساعدك ميدغارد على قراءة أسماء الأدوية ومطابقتها. لا يحل محل طبيبك أو صيدليك، ولا يقرر ما إذا كان الجمع بين الأدوية آمنًا، فالبيانات الطبية الموثوقة هي التي تفعل ذلك.",
  "IMPACT 2026 — Healthcare Track prototype. Not a medical device.": "IMPACT 2026 — نموذج أولي لمسار الرعاية الصحية. ليس جهازًا طبيًا.",
  "Medicine name": "اسم الدواء",
  "Check interactions": "افحص التداخلات",
  "What the database found": "ما وجدته قاعدة البيانات",
  "Print this page": "اطبع هذه الصفحة",
  "Check other medicines": "افحص أدوية أخرى",
  "No check to show yet": "لا يوجد فحص لعرضه بعد",
  "Start a check": "ابدأ فحصًا",
  "Same ingredient, different boxes": "المادة الفعالة نفسها، عبوات مختلفة",
  "Pairs with no record": "أزواج بلا سجل",
  "We could not identify these": "تعذر التعرف على هذه الأدوية",
  "Same ingredient, other brands": "المادة الفعالة نفسها، علامات تجارية أخرى",
  "Nothing to report": "لا توجد نتائج للإبلاغ عنها",
  "Earlier checks this session": "الفحوصات السابقة في هذه الجلسة",
  "What to do:": "ما يجب فعله:",
  "Demo data — your photos were not read": "بيانات تجريبية — لم تتم قراءة صورك",
  "The server is running with": "الخادم يعمل باستخدام",
  "so the medicines below are a fixed sample, not what is on your boxes. Turn mock extraction off to check real photos.": "لذلك فإن الأدوية أدناه عينة ثابتة وليست الأدوية الموجودة على عبواتك. أوقف الاستخراج التجريبي لفحص الصور الحقيقية.",
  "Checked": "تم الفحص",
  "Just now": "الآن",
  "These medicines should not be taken together": "لا ينبغي تناول هذه الأدوية معًا",
  "Take care with this combination": "توخَّ الحذر عند الجمع بين هذه الأدوية",
  "No interaction found on record": "لا يوجد تداخل مسجل",
  "Not enough data to confirm": "لا توجد بيانات كافية للتأكد",
  "A verified medical database flagged a serious problem with this combination. Speak to a pharmacist or doctor before taking these together.": "أشارت قاعدة بيانات طبية موثوقة إلى مشكلة خطيرة في هذا الجمع. تحدث إلى الصيدلي أو الطبيب قبل تناول هذه الأدوية معًا.",
  "A verified medical database has a record for this combination. It is not necessarily dangerous, but it is worth asking your pharmacist about.": "لدى قاعدة بيانات طبية موثوقة سجل لهذا الجمع. قد لا يكون خطيرًا بالضرورة، لكن من الأفضل سؤال الصيدلي عنه.",
  "The database holds no interaction record for these medicines. That is not the same as confirming they are safe together — ask your pharmacist if you are unsure.": "لا تحتوي قاعدة البيانات على سجل تداخل لهذه الأدوية. هذا لا يعني أنها آمنة معًا، لذا اسأل الصيدلي إذا لم تكن متأكدًا.",
  "We could not confirm this combination against the medical database. Ask your pharmacist before taking these together.": "تعذر التأكد من هذا الجمع باستخدام قاعدة البيانات الطبية. اسأل الصيدلي قبل تناول هذه الأدوية معًا.",
  "Severity not rated": "لم يتم تصنيف الخطورة",
  "Major severity": "خطورة كبيرة",
  "Moderate severity": "خطورة متوسطة",
  "Minor severity": "خطورة بسيطة",
  "Same ingredient, different boxes": "المادة الفعالة نفسها، عبوات مختلفة",
  " appears in ": " موجودة في ",
  " of your boxes": " من عبواتك",
  "These were not checked at all. Show them to your pharmacist rather than assuming they are fine.": "لم يتم فحص هذه الأدوية على الإطلاق. اعرضها على الصيدلي بدلًا من افتراض أنها آمنة.",
  "If a pharmacy does not stock your brand, these Egyptian products contain the same active ingredient. Confirm any swap with the pharmacist.": "إذا لم يتوفر دواؤك في الصيدلية، تحتوي هذه المنتجات المصرية على المادة الفعالة نفسها. تأكد من أي بديل مع الصيدلي.",
  "Instead of": "بدلًا من",
  "No pairs could be compared. Ask your pharmacist before combining these.": "تعذر مقارنة أي أزواج. اسأل الصيدلي قبل الجمع بين هذه الأدوية.",
  "The photos had": "احتوت الصور على",
  "A clearer shot may pick up more of the label.": "قد تُظهر صورة أوضح مزيدًا من تفاصيل الملصق.",
  "The AI only read the names off your boxes. Every verdict above came from the DDInter catalogue. MedGuard does not replace your doctor or pharmacist.": "قرأ الذكاء الاصطناعي أسماء الأدوية من عبواتك فقط. جاءت كل النتائج أعلاه من كتالوج DDInter. لا يحل ميدغارد محل طبيبك أو صيدليك.",
  "Concomitant use of apixaban with other agents that alter hemostasis such as aspirin, nonsteroidal anti-inflammatory drugs (NSAIDs), platelet aggregation inhibitors, other anticoagulants, thrombolytic agents, or drugs that cause thrombocytopenia may increase the risk of bleeding. In patients receiving neuraxial anesthesia or spinal puncture, the risk of developing an epidural or spinal hematoma during apixaban therapy may also be increased by the concomitant use of other drugs that affect coagulation. The development of epidural and spinal hematoma can lead to long-term neurological injury or permanent paralysis.": "قد يؤدي الاستخدام المتزامن لأبيكسابان مع أدوية أخرى تؤثر في تخثر الدم، مثل الأسبرين ومضادات الالتهاب غير الستيرويدية ومثبطات تجمع الصفائح ومضادات التخثر الأخرى والأدوية الحالّة للجلطات أو الأدوية التي تسبب نقص الصفائح، إلى زيادة خطر النزيف. وقد يزداد لدى المرضى الذين يتلقون تخديرًا حول النخاع أو يخضعون لبزل العمود الفقري خطر حدوث ورم دموي فوق الجافية أو في العمود الفقري أثناء العلاج بأبيكسابان عند استخدام أدوية أخرى تؤثر في التخثر. وقد يؤدي ذلك إلى إصابة عصبية طويلة الأمد أو شلل دائم.",
  "Caution is recommended if apixaban must be used with other agents that alter hemostasis. Patients should be monitored for increased anticoagulant effects and bleeding complications. In patients undergoing neuraxial intervention, coadministration of these agents should be approached with caution and only after thorough assessment of risks and benefits. Besides bleeding complications, patients should also be monitored frequently for signs and symptoms of neurologic impairment such as midline back pain, sensory and motor deficits (numbness or weakness in lower limbs), and bowel or bladder dysfunction.": "يوصى بالحذر إذا كان لا بد من استخدام أبيكسابان مع أدوية أخرى تؤثر في تخثر الدم. يجب مراقبة المرضى لاحتمال زيادة تأثير مضادات التخثر وحدوث مضاعفات النزيف. وعند إجراء تدخل حول النخاع، يجب استخدام هذه الأدوية معًا بحذر وبعد تقييم شامل للمخاطر والفوائد. إضافة إلى مضاعفات النزيف، يجب مراقبة علامات وأعراض الاضطراب العصبي مثل ألم منتصف الظهر واضطراب الإحساس والحركة، ومشكلات الأمعاء أو المثانة.",
};

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => localStorage.getItem("medguard-language") || "en");

  useEffect(() => {
    localStorage.setItem("medguard-language", language);
    document.documentElement.lang = language;
    document.documentElement.dir = language === "ar" ? "rtl" : "ltr";
  }, [language]);

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      isArabic: language === "ar",
      t: (text) => (language === "ar" ? translations[text] || text : text),
    }),
    [language]
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be used inside LanguageProvider");
  return context;
}
