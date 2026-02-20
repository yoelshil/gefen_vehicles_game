// brands-data.js - Car brands data for the educational car game
// To add a new brand: simply add a new object to the BRANDS_DATA array

const BRANDS_DATA = [
  {
    id: "toyota",
    name_he: "טויוטה",
    name_en: "Toyota",
    logo: "images/brands/toyota-logo.png",
    example_car: "images/brands/toyota-car.jpg",
    fun_fact: "טויוטה היא החברה שמוכרת הכי הרבה מכוניות בעולם! היא מגיעה מיפן.",
    country: "יפן",
    country_flag: "\u{1F1EF}\u{1F1F5}",
    logo_colors: ["#EB0A1E", "#FFFFFF"]
  },
  {
    id: "mercedes",
    name_he: "מרצדס-בנץ",
    name_en: "Mercedes-Benz",
    logo: "images/brands/mercedes-logo.png",
    example_car: "images/brands/mercedes-car.jpg",
    fun_fact: "למרצדס יש כוכב עם שלוש קצוות בלוגו. היא מכונית יוקרה מגרמניה!",
    country: "גרמניה",
    country_flag: "\u{1F1E9}\u{1F1EA}",
    logo_colors: ["#333333", "#C0C0C0"]
  },
  {
    id: "bmw",
    name_he: "ב.מ.וו",
    name_en: "BMW",
    logo: "images/brands/bmw-logo.png",
    example_car: "images/brands/bmw-car.jpg",
    fun_fact: "ב.מ.וו מגרמניה! הלוגו שלה נראה כמו מדחף של מטוס בצבעי כחול ולבן.",
    country: "גרמניה",
    country_flag: "\u{1F1E9}\u{1F1EA}",
    logo_colors: ["#0066B1", "#FFFFFF"]
  },
  {
    id: "hyundai",
    name_he: "יונדאי",
    name_en: "Hyundai",
    logo: "images/brands/hyundai-logo.png",
    example_car: "images/brands/hyundai-car.jpg",
    fun_fact: "יונדאי מגיעה מקוריאה הדרומית. השם שלה אומר 'מודרני' בקוריאנית!",
    country: "קוריאה הדרומית",
    country_flag: "\u{1F1F0}\u{1F1F7}",
    logo_colors: ["#002C5F", "#FFFFFF"]
  },
  {
    id: "mazda",
    name_he: "מאזדה",
    name_en: "Mazda",
    logo: "images/brands/mazda-logo.png",
    example_car: "images/brands/mazda-car.jpg",
    fun_fact: "מאזדה מיפן עושה מכוניות שכיף לנהוג בהן! הלוגו שלה נראה כמו כנפיים.",
    country: "יפן",
    country_flag: "\u{1F1EF}\u{1F1F5}",
    logo_colors: ["#910000", "#FFFFFF"]
  },
  {
    id: "kia",
    name_he: "קיה",
    name_en: "Kia",
    logo: "images/brands/kia-logo.png",
    example_car: "images/brands/kia-car.jpg",
    fun_fact: "קיה גם מקוריאה הדרומית! היא עושה מכוניות בעיצוב מיוחד ובצבעים יפים.",
    country: "קוריאה הדרומית",
    country_flag: "\u{1F1F0}\u{1F1F7}",
    logo_colors: ["#05141F", "#FFFFFF"]
  },
  {
    id: "tesla",
    name_he: "טסלה",
    name_en: "Tesla",
    logo: "images/brands/tesla-logo.png",
    example_car: "images/brands/tesla-car.jpg",
    fun_fact: "כל המכוניות של טסלה חשמליות! הן לא צריכות דלק בכלל, רק חשמל.",
    country: "ארצות הברית",
    country_flag: "\u{1F1FA}\u{1F1F8}",
    logo_colors: ["#CC0000", "#FFFFFF"]
  },
  {
    id: "volkswagen",
    name_he: "פולקסווגן",
    name_en: "Volkswagen",
    logo: "images/brands/volkswagen-logo.png",
    example_car: "images/brands/volkswagen-car.jpg",
    fun_fact: "פולקסווגן זה אומר 'מכונית העם' בגרמנית! הלוגו שלה הוא האותיות V ו-W.",
    country: "גרמניה",
    country_flag: "\u{1F1E9}\u{1F1EA}",
    logo_colors: ["#001E50", "#FFFFFF"]
  },
  {
    id: "suzuki",
    name_he: "סוזוקי",
    name_en: "Suzuki",
    logo: "images/brands/suzuki-logo.png",
    example_car: "images/brands/suzuki-car.jpg",
    fun_fact: "סוזוקי מיפן עושה מכוניות קטנות וחסכוניות. הלוגו שלה נראה כמו האות S!",
    country: "יפן",
    country_flag: "\u{1F1EF}\u{1F1F5}",
    logo_colors: ["#E30613", "#FFFFFF"]
  },
  {
    id: "mitsubishi",
    name_he: "מיצובישי",
    name_en: "Mitsubishi",
    logo: "images/brands/mitsubishi-logo.png",
    example_car: "images/brands/mitsubishi-car.jpg",
    fun_fact: "הלוגו של מיצובישי הוא שלושה יהלומים אדומים! השם אומר 'שלושה יהלומים' ביפנית.",
    country: "יפן",
    country_flag: "\u{1F1EF}\u{1F1F5}",
    logo_colors: ["#ED0000", "#FFFFFF"]
  }
];

// Initial unlock: first 5 brands are available, rest unlock as child progresses
const INITIAL_UNLOCKED_BRANDS = 5;
