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
  },
  {
    id: 'venom',
    name_he: 'ונום',
    emoji: '👅',
    color: '#212121',
    colorLight: '#E0E0E0',
    gradient: 'linear-gradient(135deg, #424242, #000000)',
    powerEmoji: '🖤',
    powerName_he: 'סימביוטים',
    image: 'images/heroes/venom.png',
    phrases: {
      correct: ['!ונום אוהב את זה', '!כוח חושך', '!מפחיד וחכם'],
      wrong: ['!ונום אומר נסה שוב', '!עוד פעם'],
      intro: 'ונום צריך את עזרתך'
    }
  },
  {
    id: 'vision',
    name_he: 'ויז\'ן',
    emoji: '🔮',
    color: '#880E4F',
    colorLight: '#F8BBD0',
    gradient: 'linear-gradient(135deg, #AD1457, #880E4F)',
    powerEmoji: '💎',
    powerName_he: 'קרניים',
    image: 'images/heroes/vision.png',
    phrases: {
      correct: ['!ויז\'ן מחשב נכון', '!חישוב מושלם', '!מוח על'],
      wrong: ['!ויז\'ן אומר נסה שוב', '!קרוב'],
      intro: 'ויז\'ן צריך את עזרתך'
    }
  },
  {
    id: 'wolverine',
    name_he: 'וולברין',
    emoji: '🐺',
    color: '#F9A825',
    colorLight: '#FFF9C4',
    gradient: 'linear-gradient(135deg, #F9A825, #F57F17)',
    powerEmoji: '🔪',
    powerName_he: 'טפרים',
    image: 'images/heroes/wolverine.png',
    phrases: {
      correct: ['!וולברין מרוצה', '!טפרים חדות', '!חזק'],
      wrong: ['!וולברין אומר נסה שוב', '!עוד פעם'],
      intro: 'וולברין צריך את עזרתך'
    }
  },
  {
    id: 'strange',
    name_he: 'דוקטור סטריינג\'',
    emoji: '🪄',
    color: '#C62828',
    colorLight: '#FFCDD2',
    gradient: 'linear-gradient(135deg, #D32F2F, #4A148C)',
    powerEmoji: '🌀',
    powerName_he: 'כישופים',
    image: 'images/heroes/strange.png',
    phrases: {
      correct: ['!קסם מושלם', '!דוקטור סטריינג\' מתרשם', '!כוח קסום'],
      wrong: ['!דוקטור סטריינג\' אומר נסה שוב', '!כמעט'],
      intro: 'דוקטור סטריינג\' צריך את עזרתך'
    }
  },
  {
    id: 'thing',
    name_he: 'הדבר',
    emoji: '🪨',
    color: '#E65100',
    colorLight: '#FFE0B2',
    gradient: 'linear-gradient(135deg, #E65100, #BF360C)',
    powerEmoji: '🧱',
    powerName_he: 'סלעים',
    image: 'images/heroes/thing.png',
    phrases: {
      correct: ['!הגיע הזמן לריסוק', '!הדבר מרוצה', '!חזק כמו סלע'],
      wrong: ['!הדבר אומר נסה שוב', '!עוד פעם'],
      intro: 'הדבר צריך את עזרתך'
    }
  },
  {
    id: 'colossus',
    name_he: 'קולוסוס',
    emoji: '🦾',
    color: '#B71C1C',
    colorLight: '#FFCDD2',
    gradient: 'linear-gradient(135deg, #C62828, #880E4F)',
    powerEmoji: '🛡️',
    powerName_he: 'מגנים',
    image: 'images/heroes/colossus.png',
    phrases: {
      correct: ['!קולוסוס מתרשם', '!כוח פלדה', '!חזק'],
      wrong: ['!קולוסוס אומר נסה שוב', '!עוד פעם'],
      intro: 'קולוסוס צריך את עזרתך'
    }
  },
  {
    id: 'antman',
    name_he: 'אנט-מן',
    emoji: '🐜',
    color: '#D32F2F',
    colorLight: '#FFCDD2',
    gradient: 'linear-gradient(135deg, #D32F2F, #616161)',
    powerEmoji: '🐜',
    powerName_he: 'נמלים',
    image: 'images/heroes/antman.png',
    phrases: {
      correct: ['!אנט-מן מתרשם', '!קטן אבל חזק', '!גודל לא משנה'],
      wrong: ['!אנט-מן אומר נסה שוב', '!קרוב'],
      intro: 'אנט-מן צריך את עזרתך'
    }
  },
  {
    id: 'blackwidow',
    name_he: 'האלמנה השחורה',
    emoji: '🕷️',
    color: '#263238',
    colorLight: '#CFD8DC',
    gradient: 'linear-gradient(135deg, #37474F, #263238)',
    powerEmoji: '🎯',
    powerName_he: 'מטרות',
    image: 'images/heroes/blackwidow.png',
    phrases: {
      correct: ['!האלמנה השחורה גאה', '!דיוק מושלם', '!מעולה'],
      wrong: ['!האלמנה אומרת נסי שוב', '!קרוב'],
      intro: 'האלמנה השחורה צריכה את עזרתך'
    }
  },
  {
    id: 'marvel',
    name_he: 'קפטן מארוול',
    emoji: '🌟',
    color: '#E65100',
    colorLight: '#FFE0B2',
    gradient: 'linear-gradient(135deg, #FF6F00, #E65100)',
    powerEmoji: '☄️',
    powerName_he: 'כדורי אש',
    image: 'images/heroes/marvel.png',
    phrases: {
      correct: ['!קפטן מארוול מתרשמת', '!כוח קוסמי', '!מדהים'],
      wrong: ['!קפטן מארוול אומרת נסי שוב', '!כמעט'],
      intro: 'קפטן מארוול צריכה את עזרתך'
    }
  },
  {
    id: 'deadpool',
    name_he: 'דדפול',
    emoji: '😜',
    color: '#C62828',
    colorLight: '#FFCDD2',
    gradient: 'linear-gradient(135deg, #C62828, #B71C1C)',
    powerEmoji: '⚔️',
    powerName_he: 'חרבות',
    image: 'images/heroes/deadpool.png',
    phrases: {
      correct: ['!דדפול אוהב את זה', '!מגניב', '!וואו באמת'],
      wrong: ['!דדפול אומר נסה שוב', '!אופס'],
      intro: 'דדפול צריך את עזרתך'
    }
  },
  {
    id: 'drax',
    name_he: 'דראקס',
    emoji: '🗡️',
    color: '#607D8B',
    colorLight: '#CFD8DC',
    gradient: 'linear-gradient(135deg, #78909C, #455A64)',
    powerEmoji: '🗡️',
    powerName_he: 'סכינים',
    image: 'images/heroes/drax.png',
    phrases: {
      correct: ['!דראקס ההורס מרוצה', '!כוח ענק', '!חזק'],
      wrong: ['!דראקס אומר נסה שוב', '!עוד פעם'],
      intro: 'דראקס צריך את עזרתך'
    }
  },
  {
    id: 'doom',
    name_he: 'דוקטור דום',
    emoji: '👑',
    color: '#2E7D32',
    colorLight: '#C8E6C9',
    gradient: 'linear-gradient(135deg, #2E7D32, #1B5E20)',
    powerEmoji: '⚡',
    powerName_he: 'קסמים',
    image: 'images/heroes/doom.png',
    phrases: {
      correct: ['!דוקטור דום מרוצה', '!כוח מוחלט', '!מושלם'],
      wrong: ['!דוקטור דום אומר נסה שוב', '!עוד פעם'],
      intro: 'דוקטור דום צריך את עזרתך'
    }
  },
  {
    id: 'juggernaut',
    name_he: 'ג\'אגרנאוט',
    emoji: '🔴',
    color: '#B71C1C',
    colorLight: '#FFCDD2',
    gradient: 'linear-gradient(135deg, #C62828, #7F0000)',
    powerEmoji: '💥',
    powerName_he: 'מהלומות',
    image: 'images/heroes/juggernaut.png',
    phrases: {
      correct: ['!ג\'אגרנאוט מרוצה', '!כוח בלתי ניתן לעצירה', '!חזק'],
      wrong: ['!ג\'אגרנאוט אומר נסה שוב', '!עוד פעם'],
      intro: 'ג\'אגרנאוט צריך את עזרתך'
    }
  },
  {
    id: 'thanos',
    name_he: 'תאנוס',
    emoji: '🟣',
    color: '#4A148C',
    colorLight: '#E1BEE7',
    gradient: 'linear-gradient(135deg, #6A1B9A, #4A148C)',
    powerEmoji: '💎',
    powerName_he: 'אבני אינסוף',
    image: 'images/heroes/thanos.png',
    phrases: {
      correct: ['!תאנוס מרוצה', '!כוח בלתי נתפס', '!בלתי ניתן לעצירה'],
      wrong: ['!תאנוס אומר נסה שוב', '!עוד פעם'],
      intro: 'תאנוס צריך את עזרתך'
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
