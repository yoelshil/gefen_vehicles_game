// puzzle.js - Puzzle mode: assemble car images from pieces (tap-to-select, tap-to-place)

const Puzzle = {
  currentCar: null,
  cols: 0,
  rows: 0,
  totalPieces: 0,
  placedPieces: 0,
  moves: 0,
  selectedPiece: null,
  timerInterval: null,
  startTime: 0,
  _useFallback: false,
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
    this.stopTimer();
    this.selectedPiece = null;
  },

  init() {
    // Difficulty buttons
    document.querySelectorAll('.puzzle-difficulty-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const cols = parseInt(btn.dataset.cols);
        const rows = parseInt(btn.dataset.rows);
        this.startGame(cols, rows);
      });
    });

    // Retry button
    document.getElementById('puzzle-retry').addEventListener('click', () => {
      document.getElementById('puzzle-results').style.display = 'none';
      this.showDifficulty();
    });
  },

  show() {
    this.showDifficulty();
  },

  showDifficulty() {
    this.cleanup();
    document.getElementById('puzzle-difficulty').style.display = 'flex';
    document.getElementById('puzzle-game-area').style.display = 'none';
    document.getElementById('puzzle-results').style.display = 'none';
    this.updateStats(0, 0);
  },

  startGame(cols, rows) {
    this.cleanup();
    this.cols = cols;
    this.rows = rows;
    this.totalPieces = cols * rows;
    this.placedPieces = 0;
    this.moves = 0;
    this.selectedPiece = null;
    this._useFallback = false;

    // Pick random car
    this.currentCar = CARS_DATA[Math.floor(Math.random() * CARS_DATA.length)];

    // Show game area immediately
    document.getElementById('puzzle-difficulty').style.display = 'none';
    document.getElementById('puzzle-game-area').style.display = 'flex';
    document.getElementById('puzzle-car-label').textContent = '🧩 ' + this.currentCar.name_he;

    // Preload image, then build board
    const testImg = new Image();
    testImg.onload = () => {
      this._useFallback = false;
      this.buildBoard();
    };
    testImg.onerror = () => {
      this._useFallback = true;
      this.buildBoard();
    };
    testImg.src = this.currentCar.image;

    // Start timer
    this.updateStats(0, 0);
    this.startTime = Date.now();
    this.startTimer();
  },

  buildBoard() {
    const car = this.currentCar;
    const { cols, rows } = this;
    const grid = document.getElementById('puzzle-grid');
    const tray = document.getElementById('puzzle-tray');

    grid.innerHTML = '';
    tray.innerHTML = '';

    // Set grid layout
    grid.style.gridTemplateColumns = 'repeat(' + cols + ', 1fr)';
    grid.style.gridTemplateRows = 'repeat(' + rows + ', 1fr)';

    // Set tray data attribute for CSS sizing
    tray.dataset.pieces = this.totalPieces;

    // Create grid cells and pieces
    const pieces = [];

    for (var r = 0; r < rows; r++) {
      for (var c = 0; c < cols; c++) {
        // === Grid cell (target) ===
        var cell = document.createElement('div');
        cell.className = 'puzzle-cell';
        cell.dataset.row = r;
        cell.dataset.col = c;

        if (!this._useFallback) {
          // Add very faint hint showing where this piece goes
          var hint = document.createElement('div');
          hint.className = 'puzzle-cell-hint';
          hint.style.backgroundImage = 'url(' + car.image + ')';
          hint.style.backgroundSize = (cols * 100) + '% ' + (rows * 100) + '%';
          hint.style.backgroundPosition = this._bgPos(c, cols) + ' ' + this._bgPos(r, rows);
          cell.appendChild(hint);
        }

        // Use closure to capture cell reference
        (function(cellRef, self) {
          cellRef.addEventListener('click', function() { self.placePiece(cellRef); });
        })(cell, this);

        grid.appendChild(cell);

        // === Piece (for tray) ===
        var piece = document.createElement('div');
        piece.className = 'puzzle-piece';
        piece.dataset.row = r;
        piece.dataset.col = c;

        if (!this._useFallback) {
          piece.style.backgroundImage = 'url(' + car.image + ')';
          piece.style.backgroundSize = (cols * 100) + '% ' + (rows * 100) + '%';
          piece.style.backgroundPosition = this._bgPos(c, cols) + ' ' + this._bgPos(r, rows);
        } else {
          // Fallback: emoji with number
          piece.style.display = 'flex';
          piece.style.alignItems = 'center';
          piece.style.justifyContent = 'center';
          piece.style.fontSize = '2rem';
          piece.style.background = 'linear-gradient(135deg, #e3f2fd, #bbdefb)';
          piece.style.position = 'relative';
          piece.textContent = car.emoji;
          var num = document.createElement('span');
          num.className = 'puzzle-piece-number';
          num.textContent = (r * cols + c + 1);
          piece.appendChild(num);
        }

        // Use closure to capture piece reference
        (function(pieceRef, self) {
          pieceRef.addEventListener('click', function() { self.selectPiece(pieceRef); });
        })(piece, this);

        pieces.push(piece);
      }
    }

    // Shuffle pieces (Fisher-Yates)
    for (var i = pieces.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var temp = pieces[i];
      pieces[i] = pieces[j];
      pieces[j] = temp;
    }

    // Add shuffled pieces to tray
    for (var p = 0; p < pieces.length; p++) {
      tray.appendChild(pieces[p]);
    }

    // Announce
    this._setTimeout(function() {
      Speech.speak('הרכב את הפאזל של ' + car.name_he);
    }, 300);
  },

  // Calculate background-position percentage
  _bgPos: function(index, total) {
    if (total <= 1) return '0%';
    return ((index / (total - 1)) * 100) + '%';
  },

  selectPiece: function(pieceEl) {
    if (this._transitioning) return;
    if (pieceEl.classList.contains('puzzle-piece-placed')) return;

    // Deselect current
    if (this.selectedPiece) {
      this.selectedPiece.classList.remove('puzzle-piece-selected');
    }

    // Toggle: if same piece, just deselect
    if (this.selectedPiece === pieceEl) {
      this.selectedPiece = null;
      return;
    }

    // Select new piece
    pieceEl.classList.add('puzzle-piece-selected');
    this.selectedPiece = pieceEl;
    Sounds.flip();
  },

  placePiece: function(cellEl) {
    if (!this.selectedPiece) return;
    if (this._transitioning) return;
    if (cellEl.classList.contains('puzzle-cell-filled')) return;

    this.moves++;
    this.updateStats(this.moves, null);

    var pieceRow = this.selectedPiece.dataset.row;
    var pieceCol = this.selectedPiece.dataset.col;
    var cellRow = cellEl.dataset.row;
    var cellCol = cellEl.dataset.col;

    if (pieceRow === cellRow && pieceCol === cellCol) {
      this.handleCorrect(this.selectedPiece, cellEl);
    } else {
      this.handleWrong(this.selectedPiece);
    }
  },

  handleCorrect: function(pieceEl, cellEl) {
    this._transitioning = true;

    // Transfer the visual from piece to cell
    if (!this._useFallback) {
      cellEl.style.backgroundImage = pieceEl.style.backgroundImage;
      cellEl.style.backgroundSize = pieceEl.style.backgroundSize;
      cellEl.style.backgroundPosition = pieceEl.style.backgroundPosition;
    } else {
      cellEl.style.display = 'flex';
      cellEl.style.alignItems = 'center';
      cellEl.style.justifyContent = 'center';
      cellEl.style.fontSize = '2rem';
      cellEl.style.background = pieceEl.style.background;
      // Copy text content (emoji) but not the number
      var emojiText = this.currentCar.emoji;
      cellEl.textContent = emojiText;
    }

    cellEl.classList.add('puzzle-cell-filled');

    // Remove hint if present
    var hint = cellEl.querySelector('.puzzle-cell-hint');
    if (hint) hint.remove();

    // Remove piece from tray
    pieceEl.classList.remove('puzzle-piece-selected');
    pieceEl.classList.add('puzzle-piece-placed');
    this.selectedPiece = null;

    this.placedPieces++;
    Sounds.correct();

    // Announce progress at milestones
    var pct = this.placedPieces / this.totalPieces;
    if (pct === 0.25 || pct === 0.5 || pct === 0.75) {
      Speech.speak(this.placedPieces + ' מתוך ' + this.totalPieces);
    }

    var self = this;
    this._setTimeout(function() {
      self._transitioning = false;

      if (self.placedPieces === self.totalPieces) {
        self.gameComplete();
      }
    }, 400);
  },

  handleWrong: function(pieceEl) {
    Sounds.wrong();
    pieceEl.classList.add('puzzle-piece-wrong');
    pieceEl.classList.remove('puzzle-piece-selected');
    this.selectedPiece = null;

    var self = this;
    this._setTimeout(function() {
      pieceEl.classList.remove('puzzle-piece-wrong');
    }, 500);
  },

  startTimer: function() {
    this.stopTimer();
    var self = this;
    this.timerInterval = setInterval(function() {
      var elapsed = Math.floor((Date.now() - self.startTime) / 1000);
      self.updateStats(null, elapsed);
    }, 1000);
  },

  stopTimer: function() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  },

  updateStats: function(moves, seconds) {
    if (moves !== null) {
      document.getElementById('puzzle-moves').textContent = 'מהלכים: ' + moves;
    }
    if (seconds !== null) {
      var mins = Math.floor(seconds / 60);
      var secs = seconds % 60;
      document.getElementById('puzzle-timer').textContent =
        'זמן: ' + mins + ':' + String(secs).padStart(2, '0');
    }
  },

  gameComplete: function() {
    this.stopTimer();
    var elapsed = Math.floor((Date.now() - this.startTime) / 1000);
    Storage.savePuzzleBest(this.totalPieces, this.moves, elapsed);

    var mins = Math.floor(elapsed / 60);
    var secs = elapsed % 60;
    var timeStr = mins + ':' + String(secs).padStart(2, '0');

    // Build results content
    var resultsCarDiv = document.getElementById('puzzle-results-car');
    resultsCarDiv.innerHTML = '';

    if (!this._useFallback) {
      var img = document.createElement('img');
      img.src = this.currentCar.image;
      img.alt = this.currentCar.name_he;
      img.onerror = function() {
        img.style.display = 'none';
      };
      resultsCarDiv.appendChild(img);
    }

    var nameEl = document.createElement('div');
    nameEl.className = 'puzzle-results-car-name';
    nameEl.textContent = this.currentCar.name_he;
    resultsCarDiv.appendChild(nameEl);

    document.getElementById('puzzle-results-text').textContent =
      'הרכבת פאזל של ' + this.totalPieces + ' חלקים!' +
      '\nמהלכים: ' + this.moves + ' | זמן: ' + timeStr;

    // Show results after a brief moment to see the completed puzzle
    var self = this;
    this._setTimeout(function() {
      document.getElementById('puzzle-results').style.display = 'flex';
    }, 1500);

    // TTS
    Speech.speakSequence([
      'כל הכבוד! הרכבת את הפאזל!',
      this.currentCar.name_he,
      this.currentCar.fun_fact
    ], 800);

    App.celebrate();
  }
};
