// hero-math-adaptive.js - Adaptive difficulty engine for hero math game
// Tracks performance per skill and adjusts difficulty automatically

const HeroMathAdaptive = {
  // Default state per skill
  _defaultSkill() {
    return { level: 1, streak: 0, wrongStreak: 0, totalCorrect: 0, totalWrong: 0 };
  },

  // Load or initialize adaptive state
  _state: null,

  getState() {
    if (!this._state) {
      this._state = Storage.getHeroMathAdaptive() || {
        counting: this._defaultSkill(),
        addition: this._defaultSkill(),
        subtraction: this._defaultSkill(),
        comparison: this._defaultSkill(),
        heroesUnlocked: ['spiderman'], // Start with Spider-Man
        totalStars: 0,
        roundsCompleted: 0
      };
    }
    return this._state;
  },

  save() {
    Storage.saveHeroMathAdaptive(this._state);
  },

  // Record a correct answer for a skill
  recordCorrect(skill) {
    const s = this.getState()[skill];
    if (!s) return;
    s.streak++;
    s.wrongStreak = 0;
    s.totalCorrect++;

    // Level up after 3 correct in a row
    if (s.streak >= 3 && s.level < 5) {
      s.level++;
      s.streak = 0;
      this.save();
      return 'level_up';
    }
    this.save();
    return 'correct';
  },

  // Record a wrong answer for a skill
  recordWrong(skill) {
    const s = this.getState()[skill];
    if (!s) return;
    s.streak = 0;
    s.wrongStreak++;
    s.totalWrong++;

    // Level down after 2 wrong in a row
    if (s.wrongStreak >= 2 && s.level > 1) {
      s.level--;
      s.wrongStreak = 0;
      this.save();
      return 'level_down';
    }
    this.save();
    return 'wrong';
  },

  getLevel(skill) {
    return this.getState()[skill]?.level || 1;
  },

  // Unlock a new hero (called after completing a round)
  unlockNextHero() {
    const state = this.getState();
    state.roundsCompleted++;
    // Unlock a new hero every 2 rounds
    if (state.roundsCompleted % 2 === 0) {
      const allIds = HEROES_DATA.map(h => h.id);
      const locked = allIds.filter(id => !state.heroesUnlocked.includes(id));
      if (locked.length > 0) {
        state.heroesUnlocked.push(locked[0]);
        this.save();
        return locked[0]; // Return newly unlocked hero ID
      }
    }
    this.save();
    return null;
  },

  addStars(count) {
    this.getState().totalStars += count;
    this.save();
  },

  // Generate a counting problem based on current level
  generateCounting() {
    const level = this.getLevel('counting');
    let min, max;
    switch (level) {
      case 1: min = 11; max = 15; break;
      case 2: min = 11; max = 20; break;
      case 3: min = 15; max = 30; break;
      case 4: min = 20; max = 40; break;
      case 5: min = 30; max = 50; break;
      default: min = 11; max = 15;
    }
    const answer = min + Math.floor(Math.random() * (max - min + 1));
    const distractors = this._generateDistractors(answer, min, max);
    return { answer, distractors, level };
  },

  // Generate an addition problem based on current level
  generateAddition() {
    const level = this.getLevel('addition');
    let a, b;
    switch (level) {
      case 1: // a + 1 or a + 2, sum <= 15
        b = Math.random() < 0.5 ? 1 : 2;
        a = 5 + Math.floor(Math.random() * (15 - b - 5 + 1));
        break;
      case 2: // sum <= 20
        b = 1 + Math.floor(Math.random() * 5);
        a = 5 + Math.floor(Math.random() * (20 - b - 5 + 1));
        break;
      case 3: // +3 to +5, sum <= 25
        b = 3 + Math.floor(Math.random() * 3);
        a = 5 + Math.floor(Math.random() * (25 - b - 5 + 1));
        break;
      case 4: // larger numbers, sum <= 35
        b = 2 + Math.floor(Math.random() * 8);
        a = 8 + Math.floor(Math.random() * (35 - b - 8 + 1));
        break;
      case 5: // sum <= 50
        b = 3 + Math.floor(Math.random() * 10);
        a = 10 + Math.floor(Math.random() * (50 - b - 10 + 1));
        break;
      default:
        a = 7; b = 2;
    }
    const answer = a + b;
    const distractors = this._generateDistractors(answer, Math.max(answer - 5, 2), answer + 5);
    return { a, b, answer, distractors, operation: '+', level };
  },

  // Generate a subtraction problem based on current level
  generateSubtraction() {
    const level = this.getLevel('subtraction');
    let a, b;
    switch (level) {
      case 1: // -1 or -2, minuend <= 15
        b = Math.random() < 0.5 ? 1 : 2;
        a = 11 + Math.floor(Math.random() * (15 - 11 + 1));
        break;
      case 2: // minuend <= 20
        b = 1 + Math.floor(Math.random() * 3);
        a = 11 + Math.floor(Math.random() * (20 - 11 + 1));
        break;
      case 3: // -3 to -5
        b = 3 + Math.floor(Math.random() * 3);
        a = 13 + Math.floor(Math.random() * (25 - 13 + 1));
        break;
      case 4: // larger
        b = 2 + Math.floor(Math.random() * 8);
        a = 15 + Math.floor(Math.random() * (35 - 15 + 1));
        break;
      case 5: // big numbers
        b = 3 + Math.floor(Math.random() * 12);
        a = 20 + Math.floor(Math.random() * (50 - 20 + 1));
        break;
      default:
        a = 13; b = 2;
    }
    // Ensure result >= 1
    if (a - b < 1) a = b + 1 + Math.floor(Math.random() * 5);
    const answer = a - b;
    const distractors = this._generateDistractors(answer, Math.max(answer - 5, 0), answer + 5);
    return { a, b, answer, distractors, operation: '-', level };
  },

  // Generate a comparison problem based on current level
  generateComparison() {
    const level = this.getLevel('comparison');
    let numA, numB, minGap;
    switch (level) {
      case 1: minGap = 7; break;
      case 2: minGap = 5; break;
      case 3: minGap = 3; break;
      case 4: minGap = 1; break;
      case 5: minGap = 1; break;
      default: minGap = 7;
    }
    const maxNum = level <= 2 ? 20 : level <= 4 ? 35 : 50;
    const gap = minGap + Math.floor(Math.random() * 4);
    numA = 5 + Math.floor(Math.random() * (maxNum - gap - 5 + 1));
    numB = numA + gap;
    // Randomly swap so the bigger isn't always on the right
    if (Math.random() < 0.5) {
      [numA, numB] = [numB, numA];
    }
    const bigger = Math.max(numA, numB);
    return { numA, numB, answer: bigger, level };
  },

  // Generate 3 answer options including the correct answer
  _generateDistractors(answer, min, max) {
    const options = new Set([answer]);
    let attempts = 0;
    while (options.size < 3 && attempts < 50) {
      attempts++;
      // Generate distractor close to answer but not equal
      let d;
      if (Math.random() < 0.5) {
        d = answer + (1 + Math.floor(Math.random() * 3)) * (Math.random() < 0.5 ? 1 : -1);
      } else {
        d = min + Math.floor(Math.random() * (max - min + 1));
      }
      if (d >= 1 && d !== answer) {
        options.add(d);
      }
    }
    // Ensure we have exactly 3
    while (options.size < 3) {
      options.add(answer + options.size);
    }
    return Array.from(options).sort(() => Math.random() - 0.5);
  },

  reset() {
    this._state = null;
  }
};
