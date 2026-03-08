// heroes-data.js - Marvel superhero data for the math game

const HEROES_DATA = [
  {
    id: 'spiderman',
    name_he: 'ספיידרמן',
    emoji: '🕷️',
    color: '#E23636',
    colorLight: '#FFCDD2',
    gradient: 'linear-gradient(135deg, #E23636, #C62828)',
    powerEmoji: '🕸️',
    powerName_he: 'רשתות',
    image: 'images/heroes/spiderman.png',
    phrases: {
      correct: ['!ספיידרמן גאה בך', '!כוח עכביש', '!רשת מושלמת'],
      wrong: ['!ספיידרמן אומר נסה שוב', '!עוד ניסיון'],
      intro: 'ספיידרמן צריך את עזרתך'
    }
  },
  {
    id: 'ironman',
    name_he: 'איירון מן',
    emoji: '🤖',
    color: '#B71C1C',
    colorLight: '#FFCCBC',
    gradient: 'linear-gradient(135deg, #FF6F00, #B71C1C)',
    powerEmoji: '💥',
    powerName_he: 'פיצוצים',
    image: 'images/heroes/ironman.png',
    phrases: {
      correct: ['!איירון מן מתרשם', '!טכנולוגיה מעולה', '!כוח מוחות'],
      wrong: ['!איירון מן אומר נסה שוב', '!קרוב'],
      intro: 'איירון מן צריך את עזרתך'
    }
  },
  {
    id: 'hulk',
    name_he: 'האלק',
    emoji: '👊',
    color: '#2E7D32',
    colorLight: '#C8E6C9',
    gradient: 'linear-gradient(135deg, #4CAF50, #1B5E20)',
    powerEmoji: '💪',
    powerName_he: 'מכות',
    image: 'images/heroes/hulk.png',
    phrases: {
      correct: ['!האלק חזק', '!כוח ענק', '!האלק מרוצה'],
      wrong: ['!האלק אומר נסה שוב', '!עוד פעם'],
      intro: 'האלק צריך את עזרתך'
    }
  },
  {
    id: 'captain',
    name_he: 'קפטן אמריקה',
    emoji: '🛡️',
    color: '#1565C0',
    colorLight: '#BBDEFB',
    gradient: 'linear-gradient(135deg, #1976D2, #0D47A1)',
    powerEmoji: '⭐',
    powerName_he: 'כוכבים',
    image: 'images/heroes/captain.png',
    phrases: {
      correct: ['!קפטן אמריקה גאה', '!מגן מושלם', '!גיבור אמיתי'],
      wrong: ['!הקפטן אומר נסה שוב', '!אל תוותר'],
      intro: 'קפטן אמריקה צריך את עזרתך'
    }
  },
  {
    id: 'thor',
    name_he: 'ת\'ור',
    emoji: '⚡',
    color: '#7B1FA2',
    colorLight: '#E1BEE7',
    gradient: 'linear-gradient(135deg, #9C27B0, #4A148C)',
    powerEmoji: '🔨',
    powerName_he: 'ברקים',
    image: 'images/heroes/thor.png',
    phrases: {
      correct: ['!כוח הרעם', '!ת\'ור מתרשם', '!ברק מעולה'],
      wrong: ['!ת\'ור אומר נסה שוב', '!עוד פעם'],
      intro: 'ת\'ור צריך את עזרתך'
    }
  },
  {
    id: 'panther',
    name_he: 'הפנתר השחור',
    emoji: '🐾',
    color: '#37474F',
    colorLight: '#CFD8DC',
    gradient: 'linear-gradient(135deg, #546E7A, #263238)',
    powerEmoji: '✨',
    powerName_he: 'ניצוצות',
    image: 'images/heroes/panther.png',
    phrases: {
      correct: ['!ווקנדה לנצח', '!כוח הפנתר', '!מדהים'],
      wrong: ['!הפנתר אומר נסה שוב', '!קרוב מאוד'],
      intro: 'הפנתר השחור צריך את עזרתך'
    }
  }
];

// Hebrew number names for TTS
const HEBREW_NUMBERS = {
  0: 'אפס', 1: 'אחת', 2: 'שתיים', 3: 'שלוש', 4: 'ארבע', 5: 'חמש',
  6: 'שש', 7: 'שבע', 8: 'שמונה', 9: 'תשע', 10: 'עשר',
  11: 'אחת עשרה', 12: 'שתים עשרה', 13: 'שלוש עשרה', 14: 'ארבע עשרה',
  15: 'חמש עשרה', 16: 'שש עשרה', 17: 'שבע עשרה', 18: 'שמונה עשרה',
  19: 'תשע עשרה', 20: 'עשרים',
  21: 'עשרים ואחת', 22: 'עשרים ושתיים', 23: 'עשרים ושלוש', 24: 'עשרים וארבע',
  25: 'עשרים וחמש', 26: 'עשרים ושש', 27: 'עשרים ושבע', 28: 'עשרים ושמונה',
  29: 'עשרים ותשע', 30: 'שלושים',
  31: 'שלושים ואחת', 32: 'שלושים ושתיים', 33: 'שלושים ושלוש', 34: 'שלושים וארבע',
  35: 'שלושים וחמש', 36: 'שלושים ושש', 37: 'שלושים ושבע', 38: 'שלושים ושמונה',
  39: 'שלושים ותשע', 40: 'ארבעים',
  41: 'ארבעים ואחת', 42: 'ארבעים ושתיים', 43: 'ארבעים ושלוש', 44: 'ארבעים וארבע',
  45: 'ארבעים וחמש', 46: 'ארבעים ושש', 47: 'ארבעים ושבע', 48: 'ארבעים ושמונה',
  49: 'ארבעים ותשע', 50: 'חמישים'
};

// General encouragement phrases
const HERO_PRAISE = [
  '!כל הכבוד', '!מעולה', '!מדהים', '!וואו', '!גיבור על אמיתי',
  '!נכון מאוד', '!יופי', '!בול', '!מושלם'
];

const HERO_ENCOURAGE = [
  '!נסה שוב', '!כמעט', '!קרוב', '!אפשר לנסות שוב', '!בוא ננסה שוב'
];

const HERO_LEVEL_UP = [
  '!עלית שלב', '!אתה מתקדם', '!הולך ונהיה גיבור על'
];
