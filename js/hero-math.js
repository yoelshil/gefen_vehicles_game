// hero-math.js - Superhero-themed math game for learning arithmetic
// Modes: Power Counting, Hero Mission (add/subtract), Number Battle (comparison)

const HeroMath = {
  currentMode: null, // 'counting', 'mission', 'battle'
  currentHero: null,
  state: null,
  animationTimeouts: [],
  QUESTIONS_PER_ROUND: 8,

  cleanup() {
    this.animationTimeouts.forEach(t => clearTimeout(t));
    this.animationTimeouts = [];
    Speech.stop();
  },

  init() {
    // Sub-menu mode buttons
    document.getElementById('hero-math-counting-btn').addEventListener('click', () => this.startMode('counting'));
    document.getElementById('hero-math-mission-btn').addEventListener('click', () => this.startMode('mission'));
    document.getElementById('hero-math-battle-btn').addEventListener('click', () => this.startMode('battle'));

    // Back buttons
    document.getElementById('hero-math-game-back').addEventListener('click', () => this.showMenu());
    document.getElementById('hero-math-results-retry').addEventListener('click', () => this.startMode(this.currentMode));
    document.getElementById('hero-math-results-menu').addEventListener('click', () => this.showMenu());
  },

  show() {
    this.showMenu();
  },

  showMenu() {
    this.cleanup();
    document.getElementById('hero-math-menu').style.display = 'flex';
    document.getElementById('hero-math-game').style.display = 'none';
    document.getElementById('hero-math-results').style.display = 'none';
    this._updateMenuStats();
  },

  _updateMenuStats() {
    const state = HeroMathAdaptive.getState();
    const starsEl = document.getElementById('hero-math-total-stars');
    if (starsEl) starsEl.textContent = '⭐ ' + state.totalStars;
    // Update hero collection display
    const collectionEl = document.getElementById('hero-math-collection');
    if (collectionEl) {
      collectionEl.innerHTML = HEROES_DATA.map(h => {
        const unlocked = state.heroesUnlocked.includes(h.id);
        return `<span class="hero-collection-item ${unlocked ? 'unlocked' : 'locked'}"
                  style="${unlocked ? 'background:' + h.color : ''}"
                  title="${h.name_he}">
                  ${unlocked ? this._heroVisual(h, 'collection') : '❓'}
                </span>`;
      }).join('');
    }
  },

  // Returns hero image HTML with emoji fallback
  _heroVisual(hero, size) {
    if (!hero) return '';
    const sizeClass = size || 'medium';
    return `<span class="hero-visual hero-visual-${sizeClass}">
              <img src="${hero.image}" alt="${hero.name_he}" class="hero-img hero-img-${sizeClass}"
                   onerror="this.style.display='none';this.nextElementSibling.style.display='inline'">
              <span class="hero-emoji hero-emoji-${sizeClass}" style="display:none">${hero.emoji}</span>
            </span>`;
  },

  // Pick a random unlocked hero
  _pickHero() {
    const state = HeroMathAdaptive.getState();
    const unlocked = HEROES_DATA.filter(h => state.heroesUnlocked.includes(h.id));
    return unlocked[Math.floor(Math.random() * unlocked.length)];
  },

  startMode(mode) {
    this.cleanup();
    this.currentMode = mode;
    this.currentHero = this._pickHero();
    this.state = {
      questionIndex: 0,
      score: 0,
      questions: [],
      answered: false
    };

    // Generate all questions for this round
    for (let i = 0; i < this.QUESTIONS_PER_ROUND; i++) {
      if (mode === 'counting') {
        this.state.questions.push(HeroMathAdaptive.generateCounting());
      } else if (mode === 'mission') {
        // Mix addition and subtraction based on level
        const subLevel = HeroMathAdaptive.getLevel('subtraction');
        if (subLevel >= 2 && Math.random() < 0.4) {
          this.state.questions.push(HeroMathAdaptive.generateSubtraction());
        } else {
          this.state.questions.push(HeroMathAdaptive.generateAddition());
        }
      } else if (mode === 'battle') {
        this.state.questions.push(HeroMathAdaptive.generateComparison());
      }
    }

    document.getElementById('hero-math-menu').style.display = 'none';
    document.getElementById('hero-math-game').style.display = 'flex';
    document.getElementById('hero-math-results').style.display = 'none';

    // Apply hero theme
    const gameScreen = document.getElementById('hero-math-game');
    gameScreen.style.background = this.currentHero.gradient;

    // Announce hero
    const t = setTimeout(() => {
      Speech.speak(this.currentHero.phrases.intro);
    }, 500);
    this.animationTimeouts.push(t);

    this._showQuestion();
  },

  _showQuestion() {
    const { questionIndex, questions } = this.state;
    if (questionIndex >= questions.length) {
      this._showResults();
      return;
    }

    this.state.answered = false;
    const q = questions[questionIndex];
    const hero = this.currentHero;

    // Update progress
    document.getElementById('hero-math-progress').textContent =
      `${questionIndex + 1}/${questions.length}`;

    // Update power meter
    this._updatePowerMeter();

    // Update hero display
    const heroArea = document.getElementById('hero-math-hero-area');
    heroArea.innerHTML = this._heroVisual(hero, 'large');
    heroArea.className = 'hero-math-hero-area';

    const questionArea = document.getElementById('hero-math-question-area');
    const answersArea = document.getElementById('hero-math-answers');

    if (this.currentMode === 'counting') {
      this._showCountingQuestion(q, questionArea, answersArea);
    } else if (this.currentMode === 'mission') {
      this._showMissionQuestion(q, questionArea, answersArea);
    } else if (this.currentMode === 'battle') {
      this._showBattleQuestion(q, questionArea, answersArea);
    }
  },

  // =================== COUNTING MODE ===================
  _showCountingQuestion(q, questionArea, answersArea) {
    const hero = this.currentHero;
    const count = q.answer;

    // Build items display - animate them in one by one
    let itemsHtml = '<div class="hero-math-items" id="hero-math-items">';
    for (let i = 0; i < count; i++) {
      itemsHtml += `<span class="hero-math-item" style="animation-delay:${i * 0.12}s">${hero.powerEmoji}</span>`;
    }
    itemsHtml += '</div>';

    questionArea.innerHTML = `
      <div class="hero-math-prompt">
        <span class="hero-math-prompt-text">?כמה ${hero.powerName_he} יש</span>
      </div>
      ${itemsHtml}
    `;

    // TTS: announce the question
    const t = setTimeout(() => {
      Speech.speak(`כמה ${hero.powerName_he} יש? ספור אותם`);
    }, 300);
    this.animationTimeouts.push(t);

    // Show answer buttons
    this._showAnswerButtons(q.distractors, q.answer, answersArea, 'counting');
  },

  // =================== MISSION MODE (Add/Subtract) ===================
  _showMissionQuestion(q, questionArea, answersArea) {
    const hero = this.currentHero;
    const isAdd = q.operation === '+';
    const opSymbol = isAdd ? '+' : '−';
    const opWord = isAdd ? 'ועוד' : 'פחות';

    // Visual: show the math problem with hero items
    questionArea.innerHTML = `
      <div class="hero-math-prompt">
        <span class="hero-math-prompt-text">${hero.name_he}</span>
      </div>
      <div class="hero-math-equation">
        <span class="hero-math-num">${q.a}</span>
        <span class="hero-math-op ${isAdd ? 'op-add' : 'op-sub'}">${opSymbol}</span>
        <span class="hero-math-num">${q.b}</span>
        <span class="hero-math-op">=</span>
        <span class="hero-math-num hero-math-mystery">?</span>
      </div>
      <div class="hero-math-equation-items">
        ${this._renderItemGroup(q.a, hero.powerEmoji)}
        <span class="hero-math-op-big ${isAdd ? 'op-add' : 'op-sub'}">${opSymbol}</span>
        ${this._renderItemGroup(q.b, hero.powerEmoji)}
      </div>
    `;

    // TTS
    const numA = HEBREW_NUMBERS[q.a] || q.a;
    const numB = HEBREW_NUMBERS[q.b] || q.b;
    const t = setTimeout(() => {
      Speech.speak(`${numA} ${opWord} ${numB} שווה?`);
    }, 300);
    this.animationTimeouts.push(t);

    this._showAnswerButtons(q.distractors, q.answer, answersArea,
      q.operation === '+' ? 'addition' : 'subtraction');
  },

  _renderItemGroup(count, emoji) {
    // Show actual items up to 15, then just the number
    if (count > 15) {
      return `<span class="hero-math-item-group"><span class="hero-math-big-num">${count}</span><span>${emoji}</span></span>`;
    }
    let html = '<span class="hero-math-item-group">';
    for (let i = 0; i < count; i++) {
      html += `<span class="hero-math-small-item">${emoji}</span>`;
    }
    html += '</span>';
    return html;
  },

  // =================== BATTLE MODE (Comparison) ===================
  _showBattleQuestion(q, questionArea, answersArea) {
    // Pick two random heroes for the battle
    const state = HeroMathAdaptive.getState();
    const unlocked = HEROES_DATA.filter(h => state.heroesUnlocked.includes(h.id));
    const heroA = unlocked[Math.floor(Math.random() * unlocked.length)];
    let heroB = unlocked[Math.floor(Math.random() * unlocked.length)];
    if (unlocked.length > 1) {
      while (heroB.id === heroA.id) {
        heroB = unlocked[Math.floor(Math.random() * unlocked.length)];
      }
    }

    questionArea.innerHTML = `
      <div class="hero-math-prompt">
        <span class="hero-math-prompt-text">?מי חזק יותר</span>
      </div>
      <div class="hero-math-battle">
        <button class="hero-battle-card" data-num="${q.numA}" style="border-color:${heroA.color}">
          ${this._heroVisual(heroA, 'battle')}
          <span class="battle-number" style="color:${heroA.color}">${q.numA}</span>
          <span class="battle-hero-name">${heroA.name_he}</span>
        </button>
        <span class="hero-math-vs">⚡VS⚡</span>
        <button class="hero-battle-card" data-num="${q.numB}" style="border-color:${heroB.color}">
          ${this._heroVisual(heroB, 'battle')}
          <span class="battle-number" style="color:${heroB.color}">${q.numB}</span>
          <span class="battle-hero-name">${heroB.name_he}</span>
        </button>
      </div>
    `;

    // Hide normal answer buttons for battle mode
    answersArea.innerHTML = '';

    // TTS
    const numA = HEBREW_NUMBERS[q.numA] || q.numA;
    const numB = HEBREW_NUMBERS[q.numB] || q.numB;
    const t = setTimeout(() => {
      Speech.speak(`${numA} או ${numB}? מי חזק יותר? מי יש לו יותר?`);
    }, 300);
    this.animationTimeouts.push(t);

    // Add click handlers to battle cards
    const cards = questionArea.querySelectorAll('.hero-battle-card');
    cards.forEach(card => {
      card.addEventListener('click', () => {
        if (this.state.answered) return;
        const num = parseInt(card.dataset.num);
        this._handleBattleAnswer(num, q.answer, cards);
      });
    });
  },

  _handleBattleAnswer(chosen, correct, cards) {
    this.state.answered = true;
    const skill = 'comparison';

    cards.forEach(card => {
      const num = parseInt(card.dataset.num);
      if (num === correct) {
        card.classList.add('battle-winner');
      } else {
        card.classList.add('battle-loser');
      }
    });

    if (chosen === correct) {
      this.state.score++;
      const result = HeroMathAdaptive.recordCorrect(skill);
      Sounds.powerUp();
      this._speakPraise(result === 'level_up');

      // Speak the number
      const t1 = setTimeout(() => {
        const numHe = HEBREW_NUMBERS[correct] || correct;
        Speech.speak(`${numHe} יותר גדול!`);
      }, 1200);
      this.animationTimeouts.push(t1);
    } else {
      HeroMathAdaptive.recordWrong(skill);
      Sounds.wrong();
      this._speakEncourage();

      const t1 = setTimeout(() => {
        const numHe = HEBREW_NUMBERS[correct] || correct;
        Speech.speak(`${numHe} יותר גדול`);
      }, 1200);
      this.animationTimeouts.push(t1);
    }

    this._updatePowerMeter();
    const t = setTimeout(() => this._nextQuestion(), 2500);
    this.animationTimeouts.push(t);
  },

  // =================== ANSWER BUTTONS (for counting & mission) ===================
  _showAnswerButtons(options, answer, container, skill) {
    container.innerHTML = options.map(num => `
      <button class="hero-math-answer-btn" data-num="${num}">
        ${num}
      </button>
    `).join('');

    container.querySelectorAll('.hero-math-answer-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        if (this.state.answered) return;
        const chosen = parseInt(btn.dataset.num);
        this._handleAnswer(chosen, answer, container, skill);
      });
    });
  },

  _handleAnswer(chosen, correct, container, skill) {
    this.state.answered = true;
    const buttons = container.querySelectorAll('.hero-math-answer-btn');

    buttons.forEach(btn => {
      const num = parseInt(btn.dataset.num);
      btn.classList.add('disabled');
      if (num === correct) {
        btn.classList.add('correct');
      } else if (num === chosen && num !== correct) {
        btn.classList.add('wrong');
      }
    });

    const heroArea = document.getElementById('hero-math-hero-area');

    if (chosen === correct) {
      this.state.score++;
      const result = HeroMathAdaptive.recordCorrect(skill);
      Sounds.powerUp();
      heroArea.classList.add('hero-celebrate');
      this._speakPraise(result === 'level_up');

      // Speak the correct number
      const t1 = setTimeout(() => {
        const numHe = HEBREW_NUMBERS[correct] || correct;
        Speech.speak(`${numHe}!`);
      }, 1000);
      this.animationTimeouts.push(t1);
    } else {
      HeroMathAdaptive.recordWrong(skill);
      Sounds.wrong();
      heroArea.classList.add('hero-sad');
      this._speakEncourage();

      // Show and speak correct answer
      const t1 = setTimeout(() => {
        const numHe = HEBREW_NUMBERS[correct] || correct;
        Speech.speak(`התשובה היא ${numHe}`);
      }, 1200);
      this.animationTimeouts.push(t1);
    }

    this._updatePowerMeter();
    const t = setTimeout(() => this._nextQuestion(), 2800);
    this.animationTimeouts.push(t);
  },

  _nextQuestion() {
    this.state.questionIndex++;
    // Regenerate upcoming questions with updated difficulty
    const remaining = this.QUESTIONS_PER_ROUND - this.state.questionIndex;
    for (let i = 0; i < remaining; i++) {
      const idx = this.state.questionIndex + i;
      if (this.currentMode === 'counting') {
        this.state.questions[idx] = HeroMathAdaptive.generateCounting();
      } else if (this.currentMode === 'mission') {
        const subLevel = HeroMathAdaptive.getLevel('subtraction');
        if (subLevel >= 2 && Math.random() < 0.4) {
          this.state.questions[idx] = HeroMathAdaptive.generateSubtraction();
        } else {
          this.state.questions[idx] = HeroMathAdaptive.generateAddition();
        }
      } else if (this.currentMode === 'battle') {
        this.state.questions[idx] = HeroMathAdaptive.generateComparison();
      }
    }
    this._showQuestion();
  },

  // =================== POWER METER ===================
  _updatePowerMeter() {
    const meter = document.getElementById('hero-math-power-meter');
    if (!meter) return;
    const hero = this.currentHero;
    const { score } = this.state;
    let html = '';
    for (let i = 0; i < this.QUESTIONS_PER_ROUND; i++) {
      const filled = i < score;
      html += `<span class="power-orb ${filled ? 'filled' : ''}"
                style="${filled ? 'background:' + hero.color + ';border-color:' + hero.color : ''}">
                ${filled ? hero.powerEmoji : '○'}
              </span>`;
    }
    meter.innerHTML = html;
  },

  // =================== RESULTS ===================
  _showResults() {
    this.cleanup();
    const { score, questions } = this.state;
    const total = questions.length;
    const hero = this.currentHero;

    // Add stars
    HeroMathAdaptive.addStars(score);

    // Maybe unlock a new hero
    const newHeroId = HeroMathAdaptive.unlockNextHero();
    const newHero = newHeroId ? HEROES_DATA.find(h => h.id === newHeroId) : null;

    document.getElementById('hero-math-game').style.display = 'none';
    const results = document.getElementById('hero-math-results');
    results.style.display = 'flex';

    // Build results content
    const percentage = Math.round((score / total) * 100);
    let title, emoji;
    if (percentage >= 90) { title = '!גיבור על אמיתי'; emoji = '🏆'; }
    else if (percentage >= 70) { title = '!כל הכבוד'; emoji = '🌟'; }
    else if (percentage >= 50) { title = '!יפה מאוד'; emoji = '👏'; }
    else { title = '!ניסיון טוב'; emoji = '💪'; }

    let starsHtml = '';
    for (let i = 0; i < total; i++) {
      starsHtml += `<span class="star ${i < score ? 'earned' : ''}">⭐</span>`;
    }

    let newHeroHtml = '';
    if (newHero) {
      newHeroHtml = `
        <div class="hero-math-unlock">
          <div class="hero-unlock-title">!גיבור חדש נפתח</div>
          ${this._heroVisual(newHero, 'large')}
          <div class="hero-unlock-name">${newHero.name_he}</div>
        </div>
      `;
    }

    document.getElementById('hero-math-results-content').innerHTML = `
      <div class="hero-math-results-hero">
        ${this._heroVisual(hero, 'large')}
      </div>
      <h2 class="results-title">${emoji} ${title}</h2>
      <div class="hero-math-results-stars">${starsHtml}</div>
      <p class="results-text">${score} מתוך ${total}</p>
      ${newHeroHtml}
    `;

    // Celebration effects
    if (percentage >= 70) {
      Sounds.celebration();
      App.celebrate();
    } else {
      Sounds.correct();
    }

    // TTS results
    const t = setTimeout(() => {
      if (newHero) {
        Speech.speakSequence([title.replace('!', ''), `גיבור חדש נפתח! ${newHero.name_he}`], 1000);
      } else {
        Speech.speak(title.replace('!', ''));
      }
    }, 500);
    this.animationTimeouts.push(t);
  },

  // =================== SPEECH HELPERS ===================
  _speakPraise(isLevelUp) {
    const hero = this.currentHero;
    if (isLevelUp) {
      const phrase = HERO_LEVEL_UP[Math.floor(Math.random() * HERO_LEVEL_UP.length)];
      const t = setTimeout(() => Speech.speak(phrase.replace('!', '')), 300);
      this.animationTimeouts.push(t);
    } else {
      // Mix hero-specific and general praise
      const pool = [...hero.phrases.correct, ...HERO_PRAISE];
      const phrase = pool[Math.floor(Math.random() * pool.length)];
      const t = setTimeout(() => Speech.speak(phrase.replace('!', '')), 300);
      this.animationTimeouts.push(t);
    }
  },

  _speakEncourage() {
    const hero = this.currentHero;
    const pool = [...hero.phrases.wrong, ...HERO_ENCOURAGE];
    const phrase = pool[Math.floor(Math.random() * pool.length)];
    const t = setTimeout(() => Speech.speak(phrase.replace('!', '')), 300);
    this.animationTimeouts.push(t);
  }
};
