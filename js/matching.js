// matching.js - Matching/memory card game: match car images to their names

const Matching = {
  pairs: 0,
  cards: [],
  flippedCards: [],
  matchedPairs: 0,
  moves: 0,
  timerInterval: null,
  startTime: 0,
  isChecking: false,
  mode: 'classic', // 'classic' (image+text), 'images' (image+emoji), 'audio' (image+sound)

  cleanup() {
    this.stopTimer();
    this.isChecking = false;
  },

  init() {
    document.querySelectorAll('.difficulty-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const pairs = parseInt(btn.dataset.pairs);
        this.startGame(pairs);
      });
    });

    document.getElementById('matching-retry').addEventListener('click', () => {
      document.getElementById('matching-results').style.display = 'none';
      this.showDifficulty();
    });

    // Mode toggle buttons
    document.getElementById('matching-mode-classic').addEventListener('click', () => this.setMode('classic'));
    document.getElementById('matching-mode-images').addEventListener('click', () => this.setMode('images'));
    document.getElementById('matching-mode-audio').addEventListener('click', () => this.setMode('audio'));
  },

  setMode(mode) {
    this.mode = mode;
    document.getElementById('matching-mode-classic').classList.toggle('active', mode === 'classic');
    document.getElementById('matching-mode-images').classList.toggle('active', mode === 'images');
    document.getElementById('matching-mode-audio').classList.toggle('active', mode === 'audio');
  },

  show() {
    this.showDifficulty();
  },

  showDifficulty() {
    document.getElementById('matching-difficulty').style.display = 'flex';
    document.getElementById('matching-grid').style.display = 'none';
    document.getElementById('matching-results').style.display = 'none';
    this.stopTimer();
    this.updateStats(0, 0);
    // Update mode toggle visuals
    document.getElementById('matching-mode-classic').classList.toggle('active', this.mode === 'classic');
    document.getElementById('matching-mode-images').classList.toggle('active', this.mode === 'images');
    document.getElementById('matching-mode-audio').classList.toggle('active', this.mode === 'audio');
  },

  startGame(numPairs) {
    this.pairs = numPairs;
    this.matchedPairs = 0;
    this.moves = 0;
    this.flippedCards = [];
    this.isChecking = false;

    // Pick random cars
    const shuffledCars = [...CARS_DATA].sort(() => Math.random() - 0.5).slice(0, numPairs);

    // Create card pairs
    this.cards = [];
    shuffledCars.forEach(car => {
      this.cards.push({ type: 'image', car: car, id: car.id });
      if (this.mode === 'images') {
        // Image-only mode: match full photo to mini thumbnail (no reading required)
        this.cards.push({ type: 'thumbnail', car: car, id: car.id });
      } else if (this.mode === 'audio') {
        // Audio mode: match photo to sound (no reading required)
        this.cards.push({ type: 'audio', car: car, id: car.id });
      } else {
        // Classic mode: match photo to Hebrew text
        this.cards.push({ type: 'text', car: car, id: car.id });
      }
    });

    // Shuffle cards
    this.cards.sort(() => Math.random() - 0.5);

    // Determine grid layout
    const totalCards = this.cards.length;
    let cols, rows;
    if (totalCards === 8) { cols = 4; rows = 2; }
    else if (totalCards === 12) { cols = 4; rows = 3; }
    else if (totalCards === 16) { cols = 4; rows = 4; }
    else { cols = 4; rows = Math.ceil(totalCards / 4); }

    // Build grid
    const grid = document.getElementById('matching-grid');
    grid.innerHTML = '';
    grid.dataset.cols = cols;
    grid.dataset.rows = rows;
    grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;

    this.cards.forEach((card, index) => {
      const cardEl = document.createElement('div');
      cardEl.className = 'match-card';
      cardEl.dataset.index = index;

      const inner = document.createElement('div');
      inner.className = 'match-card-inner';

      // Front (face-down)
      const front = document.createElement('div');
      front.className = 'match-card-front';
      front.textContent = '\u{1F697}';

      // Back (face-up when flipped)
      const back = document.createElement('div');
      if (card.type === 'image') {
        back.className = 'match-card-back card-image';
        const img = document.createElement('img');
        img.src = card.car.image;
        img.alt = '';
        img.loading = 'lazy';
        img.onerror = () => {
          img.style.display = 'none';
          back.textContent = card.car.emoji;
          back.style.fontSize = '2.5rem';
          back.style.display = 'flex';
          back.style.alignItems = 'center';
          back.style.justifyContent = 'center';
        };
        back.appendChild(img);
      } else if (card.type === 'thumbnail') {
        back.className = 'match-card-back card-thumbnail';
        const cat = CATEGORIES[card.car.category];
        if (cat) {
          back.style.backgroundColor = cat.color;
        }
        const thumbImg = document.createElement('img');
        thumbImg.src = card.car.image;
        thumbImg.alt = '';
        thumbImg.loading = 'lazy';
        thumbImg.onerror = () => {
          thumbImg.style.display = 'none';
          back.textContent = card.car.emoji;
          back.style.fontSize = '2.5rem';
        };
        back.appendChild(thumbImg);
      } else if (card.type === 'audio') {
        back.className = 'match-card-back card-audio';
        // The ::after CSS pseudo-element shows the 🔊 icon
      } else {
        back.className = 'match-card-back card-text';
        back.textContent = card.car.name_he;
      }

      inner.appendChild(front);
      inner.appendChild(back);
      cardEl.appendChild(inner);

      cardEl.addEventListener('click', () => this.flipCard(index, cardEl));
      grid.appendChild(cardEl);
    });

    // Show grid
    document.getElementById('matching-difficulty').style.display = 'none';
    grid.style.display = 'grid';

    // Start timer
    this.updateStats(0, 0);
    this.startTime = Date.now();
    this.startTimer();
  },

  flipCard(index, cardEl) {
    if (this.isChecking) return;
    if (cardEl.classList.contains('flipped')) return;
    if (cardEl.classList.contains('matched')) return;
    if (this.flippedCards.length >= 2) return;

    cardEl.classList.add('flipped');
    Sounds.flip();

    const card = this.cards[index];
    // In audio mode, auto-play the car name when flipping an audio card
    if (card.type === 'audio') {
      setTimeout(() => Speech.speak(card.car.name_he), 300);
    }

    this.flippedCards.push({ index, element: cardEl, card: card });

    if (this.flippedCards.length === 2) {
      this.moves++;
      this.updateStats(this.moves, null);
      this.checkMatch();
    }
  },

  checkMatch() {
    this.isChecking = true;
    const [first, second] = this.flippedCards;

    // Match if same car ID but different card type (image+text, image+emoji, or image+audio)
    if (first.card.id === second.card.id && first.card.type !== second.card.type) {
      // Match!
      setTimeout(() => {
        first.element.classList.add('matched');
        second.element.classList.add('matched');
        this.matchedPairs++;
        Sounds.match();

        Speech.speak(first.card.car.name_he);

        this.flippedCards = [];
        this.isChecking = false;

        if (this.matchedPairs === this.pairs) {
          this.gameComplete();
        }
      }, 300);
    } else {
      // No match
      setTimeout(() => {
        first.element.classList.remove('flipped');
        second.element.classList.remove('flipped');
        this.flippedCards = [];
        this.isChecking = false;
      }, 1000);
    }
  },

  startTimer() {
    this.stopTimer();
    this.timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
      this.updateStats(null, elapsed);
    }, 1000);
  },

  stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  },

  updateStats(moves, seconds) {
    if (moves !== null) {
      document.getElementById('matching-moves').textContent = 'מהלכים: ' + moves;
    }
    if (seconds !== null) {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      document.getElementById('matching-timer').textContent =
        'זמן: ' + mins + ':' + String(secs).padStart(2, '0');
    }
  },

  gameComplete() {
    this.stopTimer();
    const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
    Storage.saveMatchingBest(this.pairs, this.moves, elapsed);

    const mins = Math.floor(elapsed / 60);
    const secs = elapsed % 60;
    const timeStr = mins + ':' + String(secs).padStart(2, '0');

    document.getElementById('matching-results-text').textContent =
      'מצאת את כל ' + this.pairs + ' הזוגות!\n' +
      'מהלכים: ' + this.moves + ' | זמן: ' + timeStr;

    document.getElementById('matching-results').style.display = 'flex';
    Speech.speak('כל הכבוד! מצאת את כל הזוגות!');
    App.celebrate();
  }
};
