const translations = {
  en: {
    welcome: "Welcome, Trainer",
    subtitle: "Manage your clients and plans from one place",
    "nav-home": "Home",
    "nav-clients": "Clients",
    "nav-plans": "Plans",
    "nav-progress": "Progress",
    "nav-settings": "Settings",
    "quick-actions": "Quick Actions",
    "add-client": "➕ Add New Client",
    "create-plan": "📄 Create New Plan",
    "view-progress": "📊 View Progress Logs",
    "recent-activity": "Recent Activity",
    "no-activity": "No recent updates yet.",
    "clients-header": "Clients",
    "clients-subtext": "View and manage your current clients",
    "settings-header": "Settings",
    "settings-subtext": "Update your personal information",
    "label-name": "Name",
    "label-email": "Email",
    "label-password": "Password",
    "save-button": "Save Changes",
    "add-client-header": "Add New Client",
    "add-client-subtext": "Enter client details below",
    "label-age": "Age",
    "label-weight": "Weight (kg)",
    "label-goal": "Fitness Goal",
    "submit-button": "Add Client",
    "fullName": "Client's Full Name",
    "age": "25",
    "weight": "e.g. 85",
    "plans-title": "Plans",
    "plans-description": "Manage, create and assign workout or meal plans",
    "existing-plans": "Existing Plans",
    "create-new-plan": "Create New Plan",
    "add-plan": "➕ New Plan (Coming Soon)",
    "plan-muscle": "Muscle Gain",
    "plan-fatloss": "Fat Loss",
    "plan-meal": "Meal Plan",
    "label-membership": "Membership Active",
    "label-start-date": "Start Date",
    "label-end-date": "End Date",
    "label-notes": "Notes",
    "option-fat_loss": "Fat Loss",
    "option-muscle_gain": "Muscle Gain",
    "option-maintenance": "Maintenance",
    "create-plan-header": "Create New Plan",
    "back-button": "Back",
    "delete-button": "Delete",
    "edit-button": "Edit",
    "confirmation-message": "Are you sure?",
    "yes": "Yes",
    "no": "No",
    "error-invalid-email": "Invalid email format",
    "error-invalid-age": "Please enter a valid age",
    "error-invalid-weight": "Please enter a valid weight"
  },
  ar: {
    welcome: "مرحباً، مدرب",
    subtitle: "قم بإدارة عملائك وخططهم من مكان واحد",
    "nav-home": "الرئيسية",
    "nav-clients": "العملاء",
    "nav-plans": "الخطط",
    "nav-progress": "التقدم",
    "nav-settings": "الإعدادات",
    "quick-actions": "إجراءات سريعة",
    "add-client": "➕ إضافة عميل جديد",
    "create-plan": "📄 إنشاء خطة جديدة",
    "view-progress": "📊 عرض سجلات التقدم",
    "recent-activity": "النشاطات الأخيرة",
    "no-activity": "لا توجد تحديثات حتى الآن.",
    "clients-header": "العملاء",
    "clients-subtext": "عرض وإدارة عملائك الحاليين",
    "settings-header": "الإعدادات",
    "settings-subtext": "تحديث معلوماتك الشخصية",
    "label-name": "الاسم",
    "label-email": "البريد الإلكتروني",
    "label-password": "كلمة المرور",
    "save-button": "حفظ التغييرات",
    "add-client-header": "إضافة عميل جديد",
    "add-client-subtext": "أدخل بيانات العميل أدناه",
    "label-age": "العمر",
    "label-weight": "الوزن (كجم)",
    "label-goal": "الهدف من اللياقة",
    "submit-button": "إضافة العميل",
    "fullName": "الاسم الكامل للعميل",
    "age": "٢٥",
    "weight": "مثلاً ٨٥",
    "plans-title": "الخطط",
    "plans-description": "إدارة وإنشاء وتعيين خطط التمارين أو التغذية",
    "existing-plans": "الخطط الحالية",
    "create-new-plan": "إنشاء خطة جديدة",
    "add-plan": "➕ خطة جديدة (قريباً)",
    "plan-muscle": "زيادة الكتلة العضلية",
    "plan-fatloss": "خسارة الدهون",
    "plan-meal": "خطة وجبات - عالية البروتين",
    "label-membership": "العضوية نشطة",
    "label-start-date": "تاريخ البدء",
    "label-end-date": "تاريخ الانتهاء",
    "label-notes": "ملاحظات",
    "option-fat_loss": "خسارة الدهون",
    "option-muscle_gain": "زيادة الكتلة العضلية",
    "option-maintenance": "الحفاظ على الوزن",
    "create-plan-header": "إنشاء خطة",
    "back-button": "رجوع",
    "delete-button": "حذف",
    "edit-button": "تعديل",
    "confirmation-message": "هل أنت متأكد؟",
    "yes": "نعم",
    "no": "لا",
    "error-invalid-email": "تنسيق البريد الإلكتروني غير صالح",
    "error-invalid-age": "يرجى إدخال عمر صالح",
    "error-invalid-weight": "يرجى إدخال وزن صالح"
  }
};

function setLanguage(lang) {
  try {
    localStorage.setItem("lang", lang);
    applyLanguage(lang);
  } catch (err) {
    console.error("Error setting language:", err);
  }
}

function applyLanguage(lang) {
  try {
    const dict = translations[lang] || translations["en"];
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";

    for (const key in dict) {
      const el = document.getElementById(key);
      if (!el) continue;
        if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
        el.placeholder = dict[key];
        } else if (el.tagName === "OPTION") {
        el.textContent = dict[key];
        } else {
        el.textContent = dict[key];
        }
    }
  } catch (err) {
    console.error("Error applying language:", err);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  try {
    const savedLang = localStorage.getItem("lang") || "en";
    applyLanguage(savedLang);
  } catch (err) {
    console.error("Error during DOMContentLoaded language setup:", err);
  }
});
