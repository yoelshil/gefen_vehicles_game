// storage.js - localStorage persistence wrapper

const Storage = {
  _prefix: 'gefen_game_',

  _get(key) {
    try {
      const val = localStorage.getItem(this._prefix + key);
      return val ? JSON.parse(val) : null;
    } catch (e) {
      return null;
    }
  },

  _set(key, value) {
    try {
      localStorage.setItem(this._prefix + key, JSON.stringify(value));
    } catch (e) {
      // localStorage full or unavailable (private browsing)
    }
  },

  // Learning mode
  saveLearningProgress(viewedIds) {
    this._set('learning_viewed', viewedIds);
  },

  getLearningProgress() {
    return this._get('learning_viewed') || [];
  },

  // Brands mode
  saveBrandsProgress(viewedIds) {
    this._set('brands_viewed', viewedIds);
  },

  getBrandsProgress() {
    return this._get('brands_viewed') || [];
  },

  getUnlockedBrandsCount() {
    const viewed = this.getBrandsProgress();
    // Always unlock 2 more than viewed, capped at total brands
    // This ensures viewing all unlocked brands always unlocks more
    const base = INITIAL_UNLOCKED_BRANDS;
    if (viewed.length < base) return base;
    return Math.min(BRANDS_DATA.length, viewed.length + 2);
  },

  // Quiz mode
  saveQuizScore(score, total) {
    const best = this.getQuizHighScore();
    if (score > best.score) {
      this._set('quiz_best', { score, total });
    }
    // Track total stars
    const totalStars = (this._get('quiz_total_stars') || 0) + score;
    this._set('quiz_total_stars', totalStars);
  },

  getQuizHighScore() {
    return this._get('quiz_best') || { score: 0, total: 0 };
  },

  getQuizTotalStars() {
    return this._get('quiz_total_stars') || 0;
  },

  // Brands quiz
  saveBrandsQuizScore(score, total) {
    const best = this.getBrandsQuizHighScore();
    if (score > best.score) {
      this._set('brands_quiz_best', { score, total });
    }
  },

  getBrandsQuizHighScore() {
    return this._get('brands_quiz_best') || { score: 0, total: 0 };
  },

  // Matching mode
  saveMatchingBest(pairs, moves, time) {
    const key = 'matching_best_' + pairs;
    const best = this.getMatchingBest(pairs);
    if (!best || moves < best.moves) {
      this._set(key, { moves, time });
    }
  },

  getMatchingBest(pairs) {
    return this._get('matching_best_' + pairs);
  },

  // Sound Quiz
  saveSoundQuizScore(score, total) {
    const best = this.getSoundQuizHighScore();
    if (score > best.score) {
      this._set('sound_quiz_best', { score, total });
    }
  },

  getSoundQuizHighScore() {
    return this._get('sound_quiz_best') || { score: 0, total: 0 };
  },

  // Odd One Out
  saveOddOneOutScore(score, total) {
    const best = this.getOddOneOutHighScore();
    if (score > best.score) {
      this._set('odd_best', { score, total });
    }
  },

  getOddOneOutHighScore() {
    return this._get('odd_best') || { score: 0, total: 0 };
  },

  // Car Parts - Learning progress
  saveCarPartsProgress(viewedIds) {
    this._set('car_parts_viewed', viewedIds);
  },

  getCarPartsProgress() {
    return this._get('car_parts_viewed') || [];
  },

  // Car Parts - Quiz
  saveCarPartsQuizScore(score, total) {
    const best = this.getCarPartsQuizHighScore();
    if (score > best.score) {
      this._set('car_parts_quiz_best', { score, total });
    }
  },

  getCarPartsQuizHighScore() {
    return this._get('car_parts_quiz_best') || { score: 0, total: 0 };
  },

  // Car Parts - Matching
  saveCarPartsMatchingBest(pairs, moves, time) {
    const key = 'car_parts_matching_best_' + pairs;
    const best = this.getCarPartsMatchingBest(pairs);
    if (!best || moves < best.moves) {
      this._set(key, { moves, time });
    }
  },

  getCarPartsMatchingBest(pairs) {
    return this._get('car_parts_matching_best_' + pairs);
  },

  // Puzzle mode
  savePuzzleBest(pieces, moves, time) {
    const key = 'puzzle_best_' + pieces;
    const best = this.getPuzzleBest(pieces);
    if (!best || moves < best.moves) {
      this._set(key, { moves, time });
    }
  },

  getPuzzleBest(pieces) {
    return this._get('puzzle_best_' + pieces);
  },

  // Reset all
  resetAll() {
    const keys = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(this._prefix)) {
        keys.push(key);
      }
    }
    keys.forEach(key => {
      try { localStorage.removeItem(key); } catch (e) {}
    });
  }
};
