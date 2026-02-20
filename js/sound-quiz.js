// sound-quiz.js - Sound Quiz mode: hear car name, tap the correct image (no reading!)

const SoundQuiz = {
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
    document.getElementById('sound-quiz-retry').addEventListener('click', () => this.start());
    document.getElementById('sound-quiz-replay').addEventListener('click', () => this.replayName());
  },

  show() {
    this.start();
  },

  start() {
    this.cleanup();
    document.getElementById('sound-quiz-results').style.display = 'none';

    // Shuffle and pick 10 questions
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
    const container = document.getElementById('sound-quiz-stars');
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

    this._transitioning = false;
    const correctCar = this.state.questions[this.state.currentQ];
    this.state.wrongAttempts = 0;

    // Difficulty: Q1-5 = 3 options, Q6+ = 4 options
    const numOptions = this.state.currentQ < 5 ? 3 : 4;

    // Generate distractors
    const distractors = this.generateDistractors(correctCar, numOptions - 1);
    const answers = [correctCar, ...distractors].sort(() => Math.random() - 0.5);

    // Render image answer buttons
    const container = document.getElementById('sound-quiz-answers');
    container.innerHTML = '';

    // Set grid columns based on options count
    container.style.gridTemplateColumns = numOptions <= 3 ? '1fr 1fr 1fr' : '1fr 1fr';

    answers.forEach(car => {
      const btn = document.createElement('button');
      btn.className = 'sound-quiz-answer';
      btn.dataset.carId = car.id;

      const img = document.createElement('img');
      img.src = car.image;
      img.alt = '';
      img.draggable = false;
      img.onerror = () => {
        img.style.display = 'none';
        const emoji = document.createElement('span');
        emoji.className = 'answer-emoji';
        emoji.textContent = car.emoji;
        btn.appendChild(emoji);
      };
      btn.appendChild(img);

      btn.addEventListener('click', () => this.handleAnswer(btn, car.id, correctCar));
      container.appendChild(btn);
    });

    // Progress text
    document.getElementById('sound-quiz-progress-text').textContent =
      'שאלה ' + (this.state.currentQ + 1) + ' מתוך ' + this.state.questions.length;

    // Auto-play the car name after a short delay
    this._setTimeout(() => {
      Speech.speak(correctCar.name_he);
    }, 400);
  },

  generateDistractors(correctCar, count) {
    // Prefer same-category for harder questions
    const sameCategory = CARS_DATA.filter(c =>
      c.id !== correctCar.id && c.category === correctCar.category
    );
    const otherCategory = CARS_DATA.filter(c =>
      c.id !== correctCar.id && c.category !== correctCar.category
    );

    sameCategory.sort(() => Math.random() - 0.5);
    otherCategory.sort(() => Math.random() - 0.5);

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
        const star = document.querySelector(`#sound-quiz-stars .star[data-index="${this.state.currentQ}"]`);
        if (star) star.classList.add('earned');
      }

      Speech.speak('כל הכבוד!');

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

        // After 2 wrong: show correct answer
        if (this.state.wrongAttempts >= 2) {
          const buttons = document.querySelectorAll('#sound-quiz-answers .sound-quiz-answer');
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

  replayName() {
    if (!this.state || this._transitioning) return;
    const car = this.state.questions[this.state.currentQ];
    if (car) {
      Speech.speak(car.name_he);
    }
  },

  showResults() {
    const state = this.state;
    Storage.saveSoundQuizScore(state.score, state.questions.length);

    // Build results
    const resultsStars = document.getElementById('sound-quiz-results-stars');
    resultsStars.textContent = '\u2B50'.repeat(state.score) + ' (' + state.score + '/' + state.questions.length + ')';

    const resultsText = document.getElementById('sound-quiz-results-text');
    if (state.score === state.questions.length) {
      resultsText.textContent = '!מושלם! זיהית את כל הרכבים מהשם';
    } else if (state.score >= state.questions.length * 0.7) {
      resultsText.textContent = '!מצוין! יש לך אוזניים טובות';
    } else if (state.score >= state.questions.length * 0.4) {
      resultsText.textContent = '!טוב מאוד! המשך להתאמן';
    } else {
      resultsText.textContent = '!כל הכבוד שניסית! נסה שוב אחרי שתלמד עוד';
    }

    document.getElementById('sound-quiz-results').style.display = 'flex';
    Speech.speak('סיימת את חידון השמע! ' + (state.score === state.questions.length ? 'מושלם!' : 'כל הכבוד!'));

    if (state.score === state.questions.length) {
      App.celebrate();
    }
  }
};
