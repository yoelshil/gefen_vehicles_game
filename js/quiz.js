// quiz.js - Quiz mode: identify cars by their images

const Quiz = {
  state: null,
  _transitioning: false,
  _timeouts: [],

  _setTimeout(fn, delay) {
    const id = setTimeout(fn, delay);
    this._timeouts.push(id);
    return id;
  },

  cleanup() {
    this._timeouts.forEach(clearTimeout);
    this._timeouts = [];
    this._transitioning = false;
  },

  init() {
    document.getElementById('quiz-retry').addEventListener('click', () => this.start());
  },

  show() {
    this.start();
  },

  start() {
    this.cleanup();
    document.getElementById('quiz-results').style.display = 'none';

    // Shuffle and pick 10 questions (or all if fewer than 10)
    const shuffled = [...CARS_DATA].sort(() => Math.random() - 0.5);
    const numQuestions = Math.min(shuffled.length, 10);

    this.state = {
      questions: shuffled.slice(0, numQuestions),
      currentQ: 0,
      score: 0,
      wrongAttempts: 0
    };

    this.renderStars();
    this.renderQuestion();
  },

  renderStars() {
    const container = document.getElementById('quiz-stars');
    container.innerHTML = '';
    const total = this.state.questions.length;
    for (let i = 0; i < total; i++) {
      const star = document.createElement('span');
      star.className = 'star';
      star.textContent = '\u2B50';
      star.dataset.index = i;
      container.appendChild(star);
    }
  },

  renderQuestion() {
    if (this.state.currentQ >= this.state.questions.length) {
      this.showResults();
      return;
    }

    const correctCar = this.state.questions[this.state.currentQ];
    this.state.wrongAttempts = 0;

    // Image
    const img = document.getElementById('quiz-car-image');
    const fallback = document.getElementById('quiz-car-fallback');
    img.src = correctCar.image;
    img.alt = '';
    img.style.display = '';
    fallback.style.display = 'none';
    img.onerror = () => {
      img.style.display = 'none';
      fallback.style.display = 'flex';
      fallback.textContent = correctCar.emoji;
    };

    // Difficulty: Q1-5 = 3 options, Q6+ = 4 options
    const numOptions = this.state.currentQ < 5 ? 3 : 4;

    // Generate distractors
    const distractors = this.generateDistractors(correctCar, numOptions - 1);
    const answers = [correctCar, ...distractors].sort(() => Math.random() - 0.5);

    // Render answer buttons
    const container = document.getElementById('quiz-answers');
    container.innerHTML = '';
    answers.forEach(car => {
      const btn = document.createElement('button');
      btn.className = 'quiz-answer-btn';
      btn.textContent = car.name_he;
      btn.dataset.carId = car.id;
      btn.addEventListener('click', () => this.handleAnswer(btn, car.id, correctCar));
      container.appendChild(btn);
    });

    // Progress text
    document.getElementById('quiz-progress-text').textContent =
      'שאלה ' + (this.state.currentQ + 1) + ' מתוך ' + this.state.questions.length;
  },

  generateDistractors(correctCar, count) {
    // Prefer same-category distractors for harder questions
    const sameCategory = CARS_DATA.filter(c =>
      c.id !== correctCar.id && c.category === correctCar.category
    );
    const otherCategory = CARS_DATA.filter(c =>
      c.id !== correctCar.id && c.category !== correctCar.category
    );

    // Shuffle both pools
    sameCategory.sort(() => Math.random() - 0.5);
    otherCategory.sort(() => Math.random() - 0.5);

    // For later questions, prefer same-category
    let pool;
    if (this.state.currentQ >= 7) {
      pool = [...sameCategory, ...otherCategory];
    } else {
      pool = [...otherCategory, ...sameCategory];
    }

    return pool.slice(0, count);
  },

  handleAnswer(btn, selectedId, correctCar) {
    if (this._transitioning) return;
    if (btn.classList.contains('disabled') || btn.classList.contains('correct')) return;

    if (selectedId === correctCar.id) {
      // Correct!
      this._transitioning = true;
      btn.classList.add('correct');
      Sounds.correct();

      if (this.state.wrongAttempts === 0) {
        this.state.score++;
        const star = document.querySelector(`#quiz-stars .star[data-index="${this.state.currentQ}"]`);
        if (star) star.classList.add('earned');
      }

      Speech.speak('כל הכבוד! ' + correctCar.name_he);

      this._setTimeout(() => {
        this.state.currentQ++;
        this._transitioning = false;
        this.renderQuestion();
      }, 1500);
    } else {
      // Wrong
      btn.classList.add('wrong');
      this.state.wrongAttempts++;
      Sounds.wrong();

      // Block further clicks immediately if threshold reached
      if (this.state.wrongAttempts >= 2) {
        this._transitioning = true;
      }

      Speech.speak('נסה שוב');

      this._setTimeout(() => {
        btn.classList.remove('wrong');
        btn.classList.add('disabled');

        // After 2 wrong attempts, show correct answer
        if (this.state.wrongAttempts >= 2) {
          const buttons = document.querySelectorAll('#quiz-answers .quiz-answer-btn');
          buttons.forEach(b => {
            if (b.dataset.carId === correctCar.id) {
              b.classList.add('highlight');
            }
          });
          Speech.speak(correctCar.name_he);

          this._setTimeout(() => {
            this.state.currentQ++;
            this._transitioning = false;
            this.renderQuestion();
          }, 2000);
        }
      }, 600);
    }
  },

  showResults() {
    const state = this.state;
    Storage.saveQuizScore(state.score, state.questions.length);

    // Build results
    const resultsStars = document.getElementById('results-stars');
    resultsStars.textContent = '\u2B50'.repeat(state.score) + ' (' + state.score + '/' + state.questions.length + ')';

    const resultsText = document.getElementById('results-text');
    if (state.score === state.questions.length) {
      resultsText.textContent = '!מושלם! ענית נכון על כל השאלות';
    } else if (state.score >= state.questions.length * 0.7) {
      resultsText.textContent = '!מצוין! הכרת את רוב הרכבים';
    } else if (state.score >= state.questions.length * 0.4) {
      resultsText.textContent = '!טוב מאוד! המשך ללמוד ותשתפר';
    } else {
      resultsText.textContent = '!כל הכבוד שניסית! נסה שוב אחרי שתלמד עוד';
    }

    document.getElementById('quiz-results').style.display = 'flex';
    Speech.speak('סיימת את החידון! ' + (state.score === state.questions.length ? 'מושלם!' : 'כל הכבוד!'));

    if (state.score === state.questions.length) {
      App.celebrate();
    }
  }
};
