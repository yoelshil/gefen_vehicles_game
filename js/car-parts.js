// car-parts.js - Car Parts mode: learn car parts, quiz, and matching game
// Follows the Brands module pattern with sub-screens

const CarParts = {
  // Learning state
  currentIndex: 0,
  viewedIds: [],
  touchStartX: 0,

  // Quiz state
  quizState: null,
  _transitioning: false,
  _timeouts: [],

  // Matching state
  matchingCards: [],
  matchingFlipped: [],
  matchingPairs: 0,
  matchedPairs: 0,
  matchingMoves: 0,
  matchingTimer: null,
  matchingStartTime: 0,
  isChecking: false,

  _setTimeout(fn, delay) {
    const id = setTimeout(fn, delay);
    this._timeouts.push(id);
    return id;
  },

  cleanup() {
    this._timeouts.forEach(clearTimeout);
    this._timeouts = [];
    this._transitioning = false;
    this.stopMatchingTimer();
    this.isChecking = false;
  },

  init() {
    this.viewedIds = Storage.getCarPartsProgress();
    this.bindEvents();
  },

  bindEvents() {
    // Sub-menu navigation
    document.getElementById('car-parts-learn-btn').addEventListener('click', () => this.showLearning());
    document.getElementById('car-parts-quiz-btn').addEventListener('click', () => this.startQuiz());
    document.getElementById('car-parts-matching-btn').addEventListener('click', () => this.showMatchingDifficulty());

    // Back buttons
    document.getElementById('car-parts-back-to-menu').addEventListener('click', () => this.showPartsMenu());
    document.getElementById('car-parts-quiz-back').addEventListener('click', () => this.showPartsMenu());
    document.getElementById('car-parts-matching-back').addEventListener('click', () => this.showPartsMenu());

    // Learning navigation
    document.getElementById('car-parts-prev').addEventListener('click', () => this.prev());
    document.getElementById('car-parts-next').addEventListener('click', () => this.next());
    document.getElementById('car-parts-speak-btn').addEventListener('click', () => this.speakCurrent());

    // Tap image to hear name
    document.getElementById('car-parts-image').addEventListener('click', () => this.speakCurrent());

    // Tap fun fact to hear it
    document.getElementById('car-parts-fun-fact').addEventListener('click', () => {
      const part = CAR_PARTS_DATA[this.currentIndex];
      if (part) Speech.speak(part.fun_fact);
    });

    // Swipe support in learning mode
    const container = document.getElementById('car-parts-learning');
    container.addEventListener('touchstart', (e) => {
      this.touchStartX = e.touches[0].clientX;
    }, { passive: true });
    container.addEventListener('touchend', (e) => {
      const deltaX = e.changedTouches[0].clientX - this.touchStartX;
      if (Math.abs(deltaX) > 50) {
        if (deltaX < 0) {
          this.next();
        } else {
          this.prev();
        }
      }
    }, { passive: true });

    // Quiz retry
    document.getElementById('car-parts-quiz-retry').addEventListener('click', () => this.startQuiz());

    // Matching difficulty buttons
    document.querySelectorAll('.car-parts-difficulty-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const pairs = parseInt(btn.dataset.pairs);
        this.startMatching(pairs);
      });
    });

    // Matching retry
    document.getElementById('car-parts-matching-retry').addEventListener('click', () => this.showMatchingDifficulty());
  },

  show() {
    this.viewedIds = Storage.getCarPartsProgress();
    this.showPartsMenu();
  },

  // ===== SUB-SCREEN SWITCHING =====
  switchSub(subId) {
    document.querySelectorAll('#screen-car-parts .car-parts-sub').forEach(el =>
      el.classList.remove('active')
    );
    document.getElementById(subId).classList.add('active');
  },

  showPartsMenu() {
    this.switchSub('car-parts-menu');
    const viewed = this.viewedIds.length;
    document.getElementById('car-parts-progress').textContent =
      viewed + '/' + CAR_PARTS_DATA.length + ' חלקים';
  },

  // ===== LEARNING MODE =====
  showLearning() {
    this.currentIndex = 0;
    this.switchSub('car-parts-learning');
    this.buildDots();
    this.renderPart();
  },

  buildDots() {
    const container = document.getElementById('car-parts-dots');
    container.innerHTML = '';
    CAR_PARTS_DATA.forEach((part, i) => {
      const dot = document.createElement('span');
      dot.className = 'progress-dot';
      dot.dataset.index = i;
      container.appendChild(dot);
    });
  },

  renderPart() {
    const part = CAR_PARTS_DATA[this.currentIndex];
    if (!part) return;

    // Image
    const img = document.getElementById('car-parts-image');
    const fallback = document.getElementById('car-parts-fallback');
    img.src = part.image;
    img.alt = part.name_he;
    img.style.display = '';
    fallback.style.display = 'none';
    img.onerror = () => {
      img.style.display = 'none';
      fallback.style.display = 'flex';
      fallback.textContent = part.emoji;
    };

    // Text
    document.getElementById('car-parts-name').textContent = part.name_he;
    document.getElementById('car-parts-fun-fact').textContent = part.fun_fact;

    // Progress
    document.getElementById('car-parts-progress').textContent =
      (this.currentIndex + 1) + '/' + CAR_PARTS_DATA.length;

    // Check first view
    const isFirstView = !this.viewedIds.includes(part.id);

    // Mark as viewed
    if (isFirstView) {
      this.viewedIds.push(part.id);
      Storage.saveCarPartsProgress(this.viewedIds);
      // Auto-read: name, then fun fact
      Speech.speakSequence([part.name_he, part.fun_fact], 1000);
    }

    this.updateDots();
  },

  updateDots() {
    const dots = document.querySelectorAll('#car-parts-dots .progress-dot');
    dots.forEach((dot, i) => {
      dot.classList.remove('viewed', 'current');
      if (i === this.currentIndex) {
        dot.classList.add('current');
      } else if (this.viewedIds.includes(CAR_PARTS_DATA[i].id)) {
        dot.classList.add('viewed');
      }
    });
  },

  next() {
    Speech.stop();
    this.currentIndex = (this.currentIndex + 1) % CAR_PARTS_DATA.length;
    this.renderPart();
  },

  prev() {
    Speech.stop();
    this.currentIndex = (this.currentIndex - 1 + CAR_PARTS_DATA.length) % CAR_PARTS_DATA.length;
    this.renderPart();
  },

  speakCurrent() {
    const part = CAR_PARTS_DATA[this.currentIndex];
    if (part) Speech.speak(part.name_he);
  },

  // ===== QUIZ MODE =====
  startQuiz() {
    this.cleanup();
    this.switchSub('car-parts-quiz-screen');
    document.getElementById('car-parts-quiz-results').style.display = 'none';

    const shuffled = [...CAR_PARTS_DATA].sort(() => Math.random() - 0.5);
    const numQuestions = Math.min(shuffled.length, 10);

    this.quizState = {
      questions: shuffled.slice(0, numQuestions),
      currentQ: 0,
      score: 0,
      wrongAttempts: 0
    };

    this.renderQuizStars();
    this.renderQuizQuestion();
  },

  renderQuizStars() {
    const container = document.getElementById('car-parts-quiz-stars');
    container.innerHTML = '';
    const total = this.quizState.questions.length;
    for (let i = 0; i < total; i++) {
      const star = document.createElement('span');
      star.className = 'star';
      star.textContent = '\u2B50';
      star.dataset.index = i;
      container.appendChild(star);
    }
  },

  renderQuizQuestion() {
    if (this.quizState.currentQ >= this.quizState.questions.length) {
      this.showQuizResults();
      return;
    }

    this._transitioning = false;
    const correctPart = this.quizState.questions[this.quizState.currentQ];
    this.quizState.wrongAttempts = 0;

    // Image
    const img = document.getElementById('car-parts-quiz-image');
    const fallback = document.getElementById('car-parts-quiz-fallback');
    img.src = correctPart.image;
    img.alt = '';
    img.style.display = '';
    fallback.style.display = 'none';
    img.onerror = () => {
      img.style.display = 'none';
      fallback.style.display = 'flex';
      fallback.textContent = correctPart.emoji;
    };

    // Difficulty: Q1-5 = 3 options, Q6+ = 4 options
    const numOptions = this.quizState.currentQ < 5 ? 3 : 4;

    // Generate distractors
    const distractors = this.generateQuizDistractors(correctPart, numOptions - 1);
    const answers = [correctPart, ...distractors].sort(() => Math.random() - 0.5);

    // Render answer buttons
    const container = document.getElementById('car-parts-quiz-answers');
    container.innerHTML = '';
    answers.forEach(part => {
      const btn = document.createElement('button');
      btn.className = 'quiz-answer-btn';
      btn.textContent = part.name_he;
      btn.dataset.partId = part.id;
      btn.addEventListener('click', () => this.handleQuizAnswer(btn, part.id, correctPart));
      container.appendChild(btn);
    });

    // Progress text
    document.getElementById('car-parts-quiz-progress-text').textContent =
      'שאלה ' + (this.quizState.currentQ + 1) + ' מתוך ' + this.quizState.questions.length;
  },

  generateQuizDistractors(correctPart, count) {
    // Pick random other parts as distractors
    return CAR_PARTS_DATA
      .filter(p => p.id !== correctPart.id)
      .sort(() => Math.random() - 0.5)
      .slice(0, count);
  },

  handleQuizAnswer(btn, selectedId, correctPart) {
    if (this._transitioning) return;
    if (btn.classList.contains('disabled') || btn.classList.contains('correct')) return;

    if (selectedId === correctPart.id) {
      // Correct!
      this._transitioning = true;
      btn.classList.add('correct');
      Sounds.correct();

      if (this.quizState.wrongAttempts === 0) {
        this.quizState.score++;
        const star = document.querySelector(`#car-parts-quiz-stars .star[data-index="${this.quizState.currentQ}"]`);
        if (star) star.classList.add('earned');
      }

      Speech.speak('כל הכבוד! ' + correctPart.name_he);

      this._setTimeout(() => {
        this.quizState.currentQ++;
        this._transitioning = false;
        this.renderQuizQuestion();
      }, 1500);
    } else {
      // Wrong
      btn.classList.add('wrong');
      this.quizState.wrongAttempts++;
      Sounds.wrong();

      // Block further clicks immediately if threshold reached
      if (this.quizState.wrongAttempts >= 2) {
        this._transitioning = true;
      }

      Speech.speak('נסה שוב');

      this._setTimeout(() => {
        btn.classList.remove('wrong');
        btn.classList.add('disabled');

        // After 2 wrong: show correct answer
        if (this.quizState.wrongAttempts >= 2) {
          const buttons = document.querySelectorAll('#car-parts-quiz-answers .quiz-answer-btn');
          buttons.forEach(b => {
            if (b.dataset.partId === correctPart.id) {
              b.classList.add('highlight');
            }
          });
          Speech.speak(correctPart.name_he);

          this._setTimeout(() => {
            this.quizState.currentQ++;
            this._transitioning = false;
            this.renderQuizQuestion();
          }, 2000);
        }
      }, 600);
    }
  },

  showQuizResults() {
    const state = this.quizState;
    Storage.saveCarPartsQuizScore(state.score, state.questions.length);

    // Build results
    const resultsStars = document.getElementById('car-parts-quiz-results-stars');
    resultsStars.textContent = '\u2B50'.repeat(state.score) + ' (' + state.score + '/' + state.questions.length + ')';

    const resultsText = document.getElementById('car-parts-quiz-results-text');
    if (state.score === state.questions.length) {
      resultsText.textContent = '!מושלם! זיהית את כל החלקים';
    } else if (state.score >= state.questions.length * 0.7) {
      resultsText.textContent = '!מצוין! הכרת את רוב החלקים';
    } else if (state.score >= state.questions.length * 0.4) {
      resultsText.textContent = '!טוב מאוד! המשך ללמוד ותשתפר';
    } else {
      resultsText.textContent = '!כל הכבוד שניסית! נסה שוב אחרי שתלמד עוד';
    }

    document.getElementById('car-parts-quiz-results').style.display = 'flex';
    Speech.speak('סיימת את חידון החלקים! ' + (state.score === state.questions.length ? 'מושלם!' : 'כל הכבוד!'));

    if (state.score === state.questions.length) {
      App.celebrate();
    }
  },

  // ===== MATCHING MODE =====
  showMatchingDifficulty() {
    this.switchSub('car-parts-matching-screen');
    document.getElementById('car-parts-matching-difficulty').style.display = 'flex';
    document.getElementById('car-parts-matching-grid').style.display = 'none';
    document.getElementById('car-parts-matching-results').style.display = 'none';
    document.querySelector('.car-parts-matching-stats').style.display = 'none';
    this.stopMatchingTimer();
    this.updateMatchingStats(0, 0);
  },

  startMatching(numPairs) {
    this.matchingPairs = numPairs;
    this.matchedPairs = 0;
    this.matchingMoves = 0;
    this.matchingFlipped = [];
    this.isChecking = false;

    // Pick random parts
    const shuffledParts = [...CAR_PARTS_DATA].sort(() => Math.random() - 0.5).slice(0, numPairs);

    // Create card pairs (image + text, classic mode)
    this.matchingCards = [];
    shuffledParts.forEach(part => {
      this.matchingCards.push({ type: 'image', part: part, id: part.id });
      this.matchingCards.push({ type: 'text', part: part, id: part.id });
    });

    // Shuffle cards
    this.matchingCards.sort(() => Math.random() - 0.5);

    // Determine grid layout
    const totalCards = this.matchingCards.length;
    let cols;
    if (totalCards === 8) { cols = 4; }
    else if (totalCards === 12) { cols = 4; }
    else if (totalCards === 16) { cols = 4; }
    else { cols = 4; }

    // Build grid
    const grid = document.getElementById('car-parts-matching-grid');
    grid.innerHTML = '';
    grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;

    this.matchingCards.forEach((card, index) => {
      const cardEl = document.createElement('div');
      cardEl.className = 'match-card';
      cardEl.dataset.index = index;

      const inner = document.createElement('div');
      inner.className = 'match-card-inner';

      // Front (face-down)
      const front = document.createElement('div');
      front.className = 'match-card-front';
      front.textContent = '\u{1F527}';

      // Back (face-up when flipped)
      const back = document.createElement('div');
      if (card.type === 'image') {
        back.className = 'match-card-back card-image';
        const img = document.createElement('img');
        img.src = card.part.image;
        img.alt = '';
        img.loading = 'lazy';
        img.onerror = () => {
          img.style.display = 'none';
          back.textContent = card.part.emoji;
          back.style.fontSize = '2.5rem';
          back.style.display = 'flex';
          back.style.alignItems = 'center';
          back.style.justifyContent = 'center';
        };
        back.appendChild(img);
      } else {
        back.className = 'match-card-back card-text';
        back.textContent = card.part.name_he;
      }

      inner.appendChild(front);
      inner.appendChild(back);
      cardEl.appendChild(inner);

      cardEl.addEventListener('click', () => this.flipMatchingCard(index, cardEl));
      grid.appendChild(cardEl);
    });

    // Show grid
    document.getElementById('car-parts-matching-difficulty').style.display = 'none';
    document.querySelector('.car-parts-matching-stats').style.display = 'flex';
    grid.style.display = 'grid';

    // Start timer
    this.updateMatchingStats(0, 0);
    this.matchingStartTime = Date.now();
    this.startMatchingTimer();
  },

  flipMatchingCard(index, cardEl) {
    if (this.isChecking) return;
    if (cardEl.classList.contains('flipped')) return;
    if (cardEl.classList.contains('matched')) return;
    if (this.matchingFlipped.length >= 2) return;

    cardEl.classList.add('flipped');
    Sounds.flip();

    const card = this.matchingCards[index];
    this.matchingFlipped.push({ index, element: cardEl, card: card });

    if (this.matchingFlipped.length === 2) {
      this.matchingMoves++;
      this.updateMatchingStats(this.matchingMoves, null);
      this.checkMatchingMatch();
    }
  },

  checkMatchingMatch() {
    this.isChecking = true;
    const [first, second] = this.matchingFlipped;

    // Match if same part ID but different card type
    if (first.card.id === second.card.id && first.card.type !== second.card.type) {
      // Match!
      this._setTimeout(() => {
        first.element.classList.add('matched');
        second.element.classList.add('matched');
        this.matchedPairs++;
        Sounds.match();

        Speech.speak(first.card.part.name_he);

        this.matchingFlipped = [];
        this.isChecking = false;

        if (this.matchedPairs === this.matchingPairs) {
          this.matchingComplete();
        }
      }, 300);
    } else {
      // No match
      this._setTimeout(() => {
        first.element.classList.remove('flipped');
        second.element.classList.remove('flipped');
        this.matchingFlipped = [];
        this.isChecking = false;
      }, 1000);
    }
  },

  startMatchingTimer() {
    this.stopMatchingTimer();
    this.matchingTimer = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this.matchingStartTime) / 1000);
      this.updateMatchingStats(null, elapsed);
    }, 1000);
  },

  stopMatchingTimer() {
    if (this.matchingTimer) {
      clearInterval(this.matchingTimer);
      this.matchingTimer = null;
    }
  },

  updateMatchingStats(moves, seconds) {
    if (moves !== null) {
      document.getElementById('car-parts-matching-moves').textContent = 'מהלכים: ' + moves;
    }
    if (seconds !== null) {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      document.getElementById('car-parts-matching-timer').textContent =
        'זמן: ' + mins + ':' + String(secs).padStart(2, '0');
    }
  },

  matchingComplete() {
    this.stopMatchingTimer();
    const elapsed = Math.floor((Date.now() - this.matchingStartTime) / 1000);
    Storage.saveCarPartsMatchingBest(this.matchingPairs, this.matchingMoves, elapsed);

    const mins = Math.floor(elapsed / 60);
    const secs = elapsed % 60;
    const timeStr = mins + ':' + String(secs).padStart(2, '0');

    document.getElementById('car-parts-matching-results-text').textContent =
      'מצאת את כל ' + this.matchingPairs + ' הזוגות!\n' +
      'מהלכים: ' + this.matchingMoves + ' | זמן: ' + timeStr;

    document.getElementById('car-parts-matching-results').style.display = 'flex';
    Speech.speak('כל הכבוד! מצאת את כל הזוגות!');
    App.celebrate();
  }
};
