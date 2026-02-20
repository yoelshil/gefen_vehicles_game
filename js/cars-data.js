// cars-data.js - Modular car data for the educational car game
// To add a new car: simply add a new object to the CARS_DATA array

const CARS_DATA = [
  {
    id: "sedan",
    name_he: "מכונית רגילה",
    name_en: "Sedan",
    image: "images/cars/sedan.jpg",
    fun_fact: "מכונית רגילה היא המכונית הכי נפוצה בכביש! יש בה מקום ל-5 אנשים.",
    category: "personal",
    emoji: "\u{1F697}"
  },
  {
    id: "truck",
    name_he: "משאית",
    name_en: "Truck",
    image: "images/cars/truck.jpg",
    fun_fact: "משאיות מובילות מזון, רהיטים וחבילות לכל מקום בארץ!",
    category: "commercial",
    emoji: "\u{1F69A}"
  },
  {
    id: "bus",
    name_he: "אוטובוס",
    name_en: "Bus",
    image: "images/cars/bus.jpg",
    fun_fact: "באוטובוס יכולים לנסוע הרבה אנשים ביחד! עד 50 נוסעים.",
    category: "public",
    emoji: "\u{1F68C}"
  },
  {
    id: "taxi",
    name_he: "מונית",
    name_en: "Taxi",
    image: "images/cars/taxi.jpg",
    fun_fact: "מונית לוקחת אותך לכל מקום שתרצה! בישראל מוניות הן בצבע לבן.",
    category: "public",
    emoji: "\u{1F695}"
  },
  {
    id: "ambulance",
    name_he: "אמבולנס",
    name_en: "Ambulance",
    image: "images/cars/ambulance.jpg",
    fun_fact: "אמבולנס עוזר לאנשים שלא מרגישים טוב ולוקח אותם לבית החולים.",
    category: "emergency",
    emoji: "\u{1F691}"
  },
  {
    id: "firetruck",
    name_he: "כבאית",
    name_en: "Fire Truck",
    image: "images/cars/firetruck.jpg",
    fun_fact: "כבאית אדומה גדולה! הכבאים משתמשים בה כדי לכבות שריפות ולהציל אנשים.",
    category: "emergency",
    emoji: "\u{1F692}"
  },
  {
    id: "police",
    name_he: "ניידת משטרה",
    name_en: "Police Car",
    image: "images/cars/police.jpg",
    fun_fact: "ניידת משטרה שומרת על הסדר. יש לה אורות כחולים ואדומים וסירנה חזקה!",
    category: "emergency",
    emoji: "\u{1F693}"
  },
  {
    id: "tractor",
    name_he: "טרקטור",
    name_en: "Tractor",
    image: "images/cars/tractor.jpg",
    fun_fact: "טרקטור עובד בשדה! הוא חורש את האדמה כדי שנוכל לגדל ירקות ופירות.",
    category: "construction",
    emoji: "\u{1F69C}"
  },
  {
    id: "jeep",
    name_he: "ג'יפ",
    name_en: "Jeep SUV",
    image: "images/cars/jeep.jpg",
    fun_fact: "ג'יפ הוא רכב חזק שיכול לנסוע גם על שטח לא סלול ועל הרים!",
    category: "personal",
    emoji: "\u{1F699}"
  },
  {
    id: "racecar",
    name_he: "מכונית מירוץ",
    name_en: "Race Car",
    image: "images/cars/racecar.jpg",
    fun_fact: "מכונית מירוץ היא הכי מהירה! היא יכולה לנסוע מעל 300 קמ\"ש.",
    category: "personal",
    emoji: "\u{1F3CE}\u{FE0F}"
  },
  {
    id: "offroad",
    name_he: "רכב שטח",
    name_en: "Off-road Vehicle",
    image: "images/cars/offroad.jpg",
    fun_fact: "רכב שטח יכול לנסוע בחול, בבוץ ובסלעים. הוא אוהב הרפתקאות!",
    category: "personal",
    emoji: "\u{1F699}"
  },
  {
    id: "cement-mixer",
    name_he: "מערבל בטון",
    name_en: "Cement Mixer",
    image: "images/cars/cement-mixer.jpg",
    fun_fact: "מערבל הבטון מסובב את התוף כל הזמן כדי שהבטון לא יתקשה!",
    category: "construction",
    emoji: "\u{1F69B}"
  },
  {
    id: "tow-truck",
    name_he: "גרר",
    name_en: "Tow Truck",
    image: "images/cars/tow-truck.jpg",
    fun_fact: "גרר מגיע לעזור כשמכונית מתקלקלת בדרך. הוא גורר אותה למוסך.",
    category: "commercial",
    emoji: "\u{1F69B}"
  },
  {
    id: "electric-car",
    name_he: "רכב חשמלי",
    name_en: "Electric Car",
    image: "images/cars/electric-car.jpg",
    fun_fact: "רכב חשמלי לא צריך דלק! הוא נוסע על חשמל ולא מזהם את האוויר.",
    category: "personal",
    emoji: "\u{26A1}"
  },
  {
    id: "minibus",
    name_he: "מיניבוס",
    name_en: "Minibus",
    image: "images/cars/minibus.jpg",
    fun_fact: "מיניבוס הוא אוטובוס קטן. הוא לוקח ילדים לבית הספר ולטיולים!",
    category: "public",
    emoji: "\u{1F690}"
  },
  {
    id: "motorcycle",
    name_he: "אופנוע",
    name_en: "Motorcycle",
    image: "images/cars/motorcycle.jpg",
    fun_fact: "אופנוע הוא רכב על שני גלגלים. הוא מהיר ויכול לעבור בין מכוניות!",
    category: "personal",
    emoji: "\u{1F3CD}\u{FE0F}"
  },
  {
    id: "garbage-truck",
    name_he: "משאית זבל",
    name_en: "Garbage Truck",
    image: "images/cars/garbage-truck.jpg",
    fun_fact: "משאית זבל אוספת את הזבל מכל הבתים ולוקחת אותו למחזור!",
    category: "commercial",
    emoji: "\u{267B}\u{FE0F}"
  },
  {
    id: "crane",
    name_he: "מנוף",
    name_en: "Crane Truck",
    image: "images/cars/crane.jpg",
    fun_fact: "מנוף יכול להרים דברים כבדים מאוד! הוא עוזר לבנות בניינים גבוהים.",
    category: "construction",
    emoji: "\u{1F3D7}\u{FE0F}"
  },
  {
    id: "bulldozer",
    name_he: "דחפור",
    name_en: "Bulldozer",
    image: "images/cars/bulldozer.jpg",
    fun_fact: "דחפור דוחף אדמה וסלעים! הוא מכין את השטח לפני שבונים.",
    category: "construction",
    emoji: "\u{1F69C}"
  },
  {
    id: "train",
    name_he: "רכבת",
    name_en: "Train",
    image: "images/cars/train.jpg",
    fun_fact: "רכבת נוסעת על מסילה ויכולה לקחת מאות אנשים ממקום למקום!",
    category: "public",
    emoji: "\u{1F686}"
  },
  {
    id: "pickup",
    name_he: "טנדר",
    name_en: "Pickup Truck",
    image: "images/cars/pickup.jpg",
    fun_fact: "לטנדר יש ארגז פתוח מאחור. אפשר לשים בו כל מיני דברים גדולים!",
    category: "personal",
    emoji: "\u{1F6FB}"
  },
  {
    id: "limousine",
    name_he: "לימוזינה",
    name_en: "Limousine",
    image: "images/cars/limousine.jpg",
    fun_fact: "לימוזינה היא מכונית ארוכה וחשובה! נוסעים בה באירועים מיוחדים.",
    category: "personal",
    emoji: "\u{1F698}"
  },
  {
    id: "ice-cream-truck",
    name_he: "משאית גלידה",
    name_en: "Ice Cream Truck",
    image: "images/cars/ice-cream-truck.jpg",
    fun_fact: "משאית גלידה מנגנת מוזיקה שמחה! ילדים רצים אליה לקנות גלידה טעימה.",
    category: "commercial",
    emoji: "\u{1F366}"
  },
  {
    id: "school-bus",
    name_he: "אוטובוס בית ספר",
    name_en: "School Bus",
    image: "images/cars/school-bus.jpg",
    fun_fact: "אוטובוס בית ספר צהוב לוקח ילדים לבית הספר ומחזיר אותם הביתה!",
    category: "public",
    emoji: "\u{1F68B}"
  },
  {
    id: "convertible",
    name_he: "קבריולט",
    name_en: "Convertible",
    image: "images/cars/convertible.jpg",
    fun_fact: "לקבריולט אפשר לפתוח את הגג! אפשר לנסוע ולהרגיש את הרוח.",
    category: "personal",
    emoji: "\u{1F3CE}\u{FE0F}"
  }
];

// Category definitions
const CATEGORIES = {
  personal:     { name_he: "רכב פרטי",      color: "#4A90D9", emoji: "\u{1F697}" },
  commercial:   { name_he: "רכב מסחרי",     color: "#FF9800", emoji: "\u{1F69A}" },
  emergency:    { name_he: "רכב חירום",      color: "#E91E63", emoji: "\u{1F6A8}" },
  construction: { name_he: "רכב בנייה",     color: "#795548", emoji: "\u{1F3D7}\u{FE0F}" },
  public:       { name_he: "תחבורה ציבורית", color: "#4CAF50", emoji: "\u{1F68C}" }
};
