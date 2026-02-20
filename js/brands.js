// brands.js - Brands mode: learn car companies, logos, and take a brand quiz

const Brands = {
  currentIndex: 0,
  viewedIds: [],
  quizState: null,
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
    this.viewedIds = Storage.getBrandsProgress();
    this.bindEvents();
  },

  bindEvents() {
    document.getElementById('brands-learn-btn').addEventListener('click', () => this.showLearning());
    document.getElementById('brands-quiz-btn').addEventListener('click', () => this.startQuiz());
    document.getElementById('brands-back-to-menu').addEventListener('click', () => this.showBrandsMenu());
    document.getElementById('brands-quiz-back').addEventListener('click', () => this.showBrandsMenu());

    document.getElementById('brands-prev').addEventListener('click', () => this.prev());
    document.getElementById('brands-next').addEventListener('click', () => this.next());
    document.getElementById('brands-speak-btn').addEventListener('click', () => this.speakCurrent());

    // Tap fun fact to hear it again
    document.getElementById('brands-fun-fact').addEventListener('click', () => {
      const brands = this.getUnlockedBrands();
      const brand = brands[this.currentIndex];
      if (brand) Speech.speak(brand.fun_fact);
    });
  },

  show() {
    this.viewedIds = Storage.getBrandsProgress();
    this.showBrandsMenu();
  },

  getUnlockedBrands() {
    const count = Storage.getUnlockedBrandsCount();
    return BRANDS_DATA.slice(0, count);
  },

  showBrandsMenu() {
    this.switchSub('brands-menu');
    const unlocked = this.getUnlockedBrands().length;
    document.getElementById('brands-progress').textContent = unlocked + '/' + BRANDS_DATA.length + ' חברות';
  },

  switchSub(subId) {
    document.querySelectorAll('.brands-sub').forEach(el => el.classList.remove('active'));
    document.getElementById(subId).classList.add('active');
  },

  // ===== LEARNING =====
  showLearning() {
    this.currentIndex = 0;
    this.switchSub('brands-learning');
    this.buildBrandDots();
    this.renderBrand();
  },

  buildBrandDots() {
    const container = document.getElementById('brands-dots');
    container.innerHTML = '';
    const brands = this.getUnlockedBrands();
    brands.forEach((brand, i) => {
      const dot = document.createElement('span');
      dot.className = 'progress-dot';
      dot.dataset.index = i;
      container.appendChild(dot);
    });
  },

  renderBrand() {
    const brands = this.getUnlockedBrands();
    const brand = brands[this.currentIndex];
    if (!brand) return;

    // Logo
    const logo = document.getElementById('brands-logo');
    const logoFallback = document.getElementById('brands-logo-fallback');
    logo.src = brand.logo;
    logo.alt = brand.name_he;
    logo.style.display = '';
    logoFallback.style.display = 'none';
    logo.onerror = () => {
      logo.style.display = 'none';
      logoFallback.style.display = 'flex';
      logoFallback.textContent = brand.name_en.charAt(0);
      logoFallback.style.background = `linear-gradient(135deg, ${brand.logo_colors[0]}40, ${brand.logo_colors[1]})`;
    };

    // Name and flag
    document.getElementById('brands-flag').textContent = brand.country_flag;
    document.getElementById('brands-name-text').textContent = brand.name_he;
    document.getElementById('brands-country').textContent = 'מדינה: ' + brand.country;
    document.getElementById('brands-fun-fact').textContent = brand.fun_fact;

    // Example car
    const exImg = document.getElementById('brands-example-car');
    const exFallback = document.getElementById('brands-example-fallback');
    exImg.src = brand.example_car;
    exImg.alt = brand.name_he;
    exImg.style.display = '';
    exFallback.style.display = 'none';
    exImg.onerror = () => {
      exImg.style.display = 'none';
      exFallback.style.display = 'flex';
    };

    // Progress
    document.getElementById('brands-progress').textContent =
      (this.currentIndex + 1) + '/' + brands.length;

    // Check first view BEFORE marking as viewed
    const isFirstView = !this.viewedIds.includes(brand.id);

    // Mark viewed
    if (isFirstView) {
      this.viewedIds.push(brand.id);
      Storage.saveBrandsProgress(this.viewedIds);
      // Auto-read: name, country, then fun fact
      Speech.speakSequence([brand.name_he, 'מ' + brand.country, brand.fun_fact], 1000);
    }

    this.updateBrandDots(brands);
  },

  updateBrandDots(brands) {
    const dots = document.querySelectorAll('#brands-dots .progress-dot');
    dots.forEach((dot, i) => {
      dot.classList.remove('viewed', 'current');
      if (i === this.currentIndex) {
        dot.classList.add('current');
      } else if (brands[i] && this.viewedIds.includes(brands[i].id)) {
        dot.classList.add('viewed');
      }
    });
  },

  next() {
    Speech.stop();
    const brands = this.getUnlockedBrands();
    this.currentIndex = (this.currentIndex + 1) % brands.length;
    this.renderBrand();
  },

  prev() {
    Speech.stop();
    const brands = this.getUnlockedBrands();
    this.currentIndex = (this.currentIndex - 1 + brands.length) % brands.length;
    this.renderBrand();
  },

  speakCurrent() {
    const brands = this.getUnlockedBrands();
    const brand = brands[this.currentIndex];
    if (brand) {
      Speech.speak(brand.name_he);
    }
  },

  // ===== QUIZ =====
  startQuiz() {
    this.cleanup();
    const brands = this.getUnlockedBrands();
    if (brands.length < 3) {
      Speech.speak('צריך ללמוד עוד חברות קודם');
      return;
    }

    this.switchSub('brands-quiz-screen');

    // Restore elements that may have been hidden by results screen
    const q = document.querySelector('#brands-quiz-screen .quiz-question');
    const img = document.querySelector('#brands-quiz-screen .quiz-image-wrapper');
    const prog = document.getElementById('brands-quiz-progress-text');
    if (q) q.style.display = '';
    if (img) img.style.display = '';
    if (prog) prog.style.display = '';

    const shuffled = [...brands].sort(() => Math.random() - 0.5);
    const numQuestions = Math.min(shuffled.length, 8);

    this.quizState = {
      questions: shuffled.slice(0, numQuestions),
      currentQ: 0,
      score: 0,
      wrongAttempts: 0,
      allBrands: brands
    };

    this.renderQuizStars();
    this.renderBrandQuestion();
  },

  renderQuizStars() {
    const container = document.getElementById('brands-quiz-stars');
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

  renderBrandQuestion() {
    const state = this.quizState;
    if (state.currentQ >= state.questions.length) {
      this.showBrandQuizResults();
      return;
    }

    const correctBrand = state.questions[state.currentQ];
    state.wrongAttempts = 0;

    // Show logo
    const logo = document.getElementById('brands-quiz-logo');
    const fallback = document.getElementById('brands-quiz-logo-fallback');
    logo.src = correctBrand.logo;
    logo.alt = '';
    logo.style.display = '';
    fallback.style.display = 'none';
    logo.onerror = () => {
      logo.style.display = 'none';
      fallback.style.display = 'flex';
      fallback.textContent = correctBrand.name_en.charAt(0);
    };

    // Generate answers
    const numOptions = state.currentQ < 3 ? 3 : 4;
    const distractors = state.allBrands
      .filter(b => b.id !== correctBrand.id)
      .sort(() => Math.random() - 0.5)
      .slice(0, numOptions - 1);

    const answers = [correctBrand, ...distractors].sort(() => Math.random() - 0.5);

    // Render answers
    const container = document.getElementById('brands-quiz-answers');
    container.innerHTML = '';
    answers.forEach(brand => {
      const btn = document.createElement('button');
      btn.className = 'quiz-answer-btn';
      btn.textContent = brand.name_he;
      btn.dataset.brandId = brand.id;
      btn.addEventListener('click', () => this.handleBrandAnswer(btn, brand.id, correctBrand));
      container.appendChild(btn);
    });

    // Progress
    document.getElementById('brands-quiz-progress-text').textContent =
      'שאלה ' + (state.currentQ + 1) + ' מתוך ' + state.questions.length;
  },

  handleBrandAnswer(btn, selectedId, correctBrand) {
    if (this._transitioning) return;
    if (btn.classList.contains('disabled') || btn.classList.contains('correct')) return;

    if (selectedId === correctBrand.id) {
      this._transitioning = true;
      btn.classList.add('correct');
      Sounds.correct();
      if (this.quizState.wrongAttempts === 0) {
        this.quizState.score++;
        const star = document.querySelector(`#brands-quiz-stars .star[data-index="${this.quizState.currentQ}"]`);
        if (star) star.classList.add('earned');
      }
      Speech.speak('כל הכבוד! ' + correctBrand.name_he);
      this._setTimeout(() => {
        this.quizState.currentQ++;
        this._transitioning = false;
        this.renderBrandQuestion();
      }, 1500);
    } else {
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
        if (this.quizState.wrongAttempts >= 2) {
          const buttons = document.querySelectorAll('#brands-quiz-answers .quiz-answer-btn');
          buttons.forEach(b => {
            if (b.dataset.brandId === correctBrand.id) {
              b.classList.add('highlight');
            }
          });
          Speech.speak(correctBrand.name_he);
          this._setTimeout(() => {
            this.quizState.currentQ++;
            this._transitioning = false;
            this.renderBrandQuestion();
          }, 2000);
        }
      }, 600);
    }
  },

  showBrandQuizResults() {
    const state = this.quizState;
    Storage.saveBrandsQuizScore(state.score, state.questions.length);

    const answersDiv = document.getElementById('brands-quiz-answers');
    answersDiv.innerHTML = `
      <div class="results-content" style="grid-column: 1/-1;">
        <h2 class="results-title">!סיימת את חידון החברות</h2>
        <div class="results-stars">${'\u2B50'.repeat(state.score)} (${state.score}/${state.questions.length})</div>
        <p class="results-text">${state.score === state.questions.length ? '!מושלם! הכרת את כל החברות' : '!כל הכבוד, המשך ללמוד'}</p>
        <div class="results-buttons">
          <button class="menu-btn results-btn" onclick="Brands.startQuiz()">🔄 שחק שוב</button>
          <button class="menu-btn results-btn" onclick="Brands.showBrandsMenu()">🏠 חזרה</button>
        </div>
      </div>
    `;
    document.querySelector('#brands-quiz-screen .quiz-question').style.display = 'none';
    document.querySelector('#brands-quiz-screen .quiz-image-wrapper').style.display = 'none';
    document.getElementById('brands-quiz-progress-text').style.display = 'none';

    if (state.score === state.questions.length) {
      App.celebrate();
    }
  }
};
