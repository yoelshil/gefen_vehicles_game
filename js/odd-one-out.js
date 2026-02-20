// odd-one-out.js - "Who Doesn't Belong?" mode: find the car from a different category (no reading!)

const OddOneOut = {
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
    document.getElementById('odd-retry').addEventListener('click', () => this.start());
  },

  show() {
    this.start();
  },

  start() {
    this.cleanup();
    document.getElementById('odd-results').style.display = 'none';
    document.getElementById('odd-hint').innerHTML = '';

    const rounds = this._generateRounds(8);

    this.state = {
      rounds: rounds,
      currentR: 0,
      score: 0,
      wrongAttempts: 0
    };

    this.renderStars();
    this.renderRound();
  },

  _generateRounds(count) {
    const categories = Object.keys(CATEGORIES);
    const rounds = [];
    const usedCombos = new Set();

    // Build a pool of possible rounds
    for (let ci = 0; ci < categories.length; ci++) {
      const mainCat = categories[ci];
      const sameCars = CARS_DATA.filter(c => c.category === mainCat);
      if (sameCars.length < 3) continue;

      for (let oi = 0; oi < categories.length; oi++) {
        if (oi === ci) continue;
        const oddCat = categories[oi];
        const oddCars = CARS_DATA.filter(c => c.category === oddCat);
        if (oddCars.length < 1) continue;

        rounds.push({
          mainCategory: mainCat,
          oddCategory: oddCat,
          sameCars: sameCars,
          oddCars: oddCars
        });
      }
    }

    // Shuffle and pick unique rounds
    const shuffled = rounds.sort(() => Math.random() - 0.5).slice(0, count * 2);
    const picked = [];

    for (const round of shuffled) {
      if (picked.length >= count) break;

      // Randomly pick 3 same-category cars and 1 odd car
      const samePick = [...round.sameCars].sort(() => Math.random() - 0.5).slice(0, 3);
      const oddPick = [...round.oddCars].sort(() => Math.random() - 0.5)[0];

      // Check uniqueness by car combination
      const key = samePick.map(c => c.id).sort().join(',') + '|' + oddPick.id;
      if (usedCombos.has(key)) continue;
      usedCombos.add(key);

      picked.push({
        mainCategory: round.mainCategory,
        oddCategory: round.oddCategory,
        sameCars: samePick,
        oddCar: oddPick
      });
    }

    return picked;
  },

  renderStars() {
    const container = document.getElementById('odd-stars');
    container.innerHTML = '';
    const total = this.state.rounds.length;
    for (let i = 0; i < total; i++) {
      const star = document.createElement('span');
      star.className = 'star';
      star.textContent = '\u2B50';
      star.dataset.index = i;
      container.appendChild(star);
    }
  },

  renderRound() {
    if (this.state.currentR >= this.state.rounds.length) {
      this.showResults();
      return;
    }

    this._transitioning = false;
    const round = this.state.rounds[this.state.currentR];
    this.state.wrongAttempts = 0;

    // Clear hint
    document.getElementById('odd-hint').innerHTML = '';

    // Mix all 4 cars and shuffle
    const allCars = [...round.sameCars, round.oddCar].sort(() => Math.random() - 0.5);

    // Render 2x2 grid of images
    const grid = document.getElementById('odd-grid');
    grid.innerHTML = '';

    allCars.forEach(car => {
      const card = document.createElement('button');
      card.className = 'odd-card';
      card.dataset.carId = car.id;
      card.dataset.isOdd = car.id === round.oddCar.id ? 'true' : 'false';

      const img = document.createElement('img');
      img.src = car.image;
      img.alt = '';
      img.draggable = false;
      img.onerror = () => {
        img.style.display = 'none';
        const emoji = document.createElement('span');
        emoji.className = 'answer-emoji';
        emoji.textContent = car.emoji;
        card.appendChild(emoji);
      };
      card.appendChild(img);

      card.addEventListener('click', () => this.handleAnswer(card, car, round));
      grid.appendChild(card);
    });

    // Progress
    document.getElementById('odd-progress-text').textContent =
      'שלב ' + (this.state.currentR + 1) + ' מתוך ' + this.state.rounds.length;

    // Announce the question via TTS
    this._setTimeout(() => {
      Speech.speak('מי לא שייך?');
    }, 300);
  },

  handleAnswer(card, selectedCar, round) {
    if (this._transitioning) return;
    if (card.classList.contains('disabled')) return;

    if (selectedCar.id === round.oddCar.id) {
      // Correct! Found the odd one out
      this._transitioning = true;
      card.classList.add('correct-odd');
      Sounds.correct();

      if (this.state.wrongAttempts === 0) {
        this.state.score++;
        const star = document.querySelector(`#odd-stars .star[data-index="${this.state.currentR}"]`);
        if (star) star.classList.add('earned');
      }

      // Show category info with emojis
      const mainCat = CATEGORIES[round.mainCategory];
      const oddCat = CATEGORIES[round.oddCategory];
      const sameNames = round.sameCars.map(c => c.name_he).join(', ');
      document.getElementById('odd-hint').innerHTML =
        '<strong>' + oddCat.emoji + ' ' + round.oddCar.name_he + '</strong> הוא ' + oddCat.name_he +
        '<br>' + mainCat.emoji + ' ' + sameNames + ' הם ' + mainCat.name_he;

      // Announce full explanation with car names
      Speech.speakSequence([
        'כל הכבוד!',
        round.oddCar.name_he + ' לא שייך כי הוא ' + oddCat.name_he,
        sameNames + ' הם ' + mainCat.name_he
      ], 700);

      this._setTimeout(() => {
        this.state.currentR++;
        this._transitioning = false;
        this.renderRound();
      }, 4500);
    } else {
      // Wrong - not the odd one
      card.classList.add('wrong-pick');
      this.state.wrongAttempts++;
      Sounds.wrong();

      // Block further clicks immediately if threshold reached
      if (this.state.wrongAttempts >= 3) {
        this._transitioning = true;
      }

      Speech.speak('נסה שוב');

      this._setTimeout(() => {
        card.classList.remove('wrong-pick');
        card.classList.add('disabled');

        // After 2 wrong: show hint with category emojis
        if (this.state.wrongAttempts >= 2) {
          const mainCat = CATEGORIES[round.mainCategory];
          const oddCat = CATEGORIES[round.oddCategory];
          // Show hint: "3 of them are [category emoji]"
          document.getElementById('odd-hint').innerHTML =
            'רמז: שלושה מהם ' + mainCat.emoji + ' ' + mainCat.name_he;

          // After one more wrong (3 total), reveal the answer
          if (this.state.wrongAttempts >= 3) {
            // Highlight the odd one
            const cards = document.querySelectorAll('#odd-grid .odd-card');
            cards.forEach(c => {
              if (c.dataset.isOdd === 'true') {
                c.classList.add('correct-odd');
              }
            });

            const sameNames = round.sameCars.map(c => c.name_he).join(', ');
            document.getElementById('odd-hint').innerHTML =
              '<strong>' + oddCat.emoji + ' ' + round.oddCar.name_he + '</strong> הוא ' + oddCat.name_he +
              '<br>' + mainCat.emoji + ' ' + sameNames + ' הם ' + mainCat.name_he;

            Speech.speakSequence([
              round.oddCar.name_he + ' לא שייך כי הוא ' + oddCat.name_he,
              sameNames + ' הם ' + mainCat.name_he
            ], 700);

            this._setTimeout(() => {
              this.state.currentR++;
              this._transitioning = false;
              this.renderRound();
            }, 4000);
          }
        }
      }, 600);
    }
  },

  showResults() {
    const state = this.state;
    Storage.saveOddOneOutScore(state.score, state.rounds.length);

    const resultsStars = document.getElementById('odd-results-stars');
    resultsStars.textContent = '\u2B50'.repeat(state.score) + ' (' + state.score + '/' + state.rounds.length + ')';

    const resultsText = document.getElementById('odd-results-text');
    if (state.score === state.rounds.length) {
      resultsText.textContent = '!מושלם! מצאת את כל השונים';
    } else if (state.score >= state.rounds.length * 0.7) {
      resultsText.textContent = '!מצוין! יש לך עיניים חדות';
    } else if (state.score >= state.rounds.length * 0.4) {
      resultsText.textContent = '!טוב מאוד! המשך להתאמן';
    } else {
      resultsText.textContent = '!כל הכבוד שניסית! נסה שוב';
    }

    document.getElementById('odd-results').style.display = 'flex';
    Speech.speak('סיימת! ' + (state.score === state.rounds.length ? 'מושלם!' : 'כל הכבוד!'));

    if (state.score === state.rounds.length) {
      App.celebrate();
    }
  }
};
