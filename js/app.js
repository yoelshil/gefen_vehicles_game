// app.js - Main application controller: screen routing, initialization

const App = {
  speechInitialized: false,

  init() {
    // Initialize modules
    Learning.init();
    Brands.init();
    Quiz.init();
    Matching.init();
    SoundQuiz.init();
    OddOneOut.init();
    CarParts.init();
    Puzzle.init();

    // Bind menu buttons
    document.querySelectorAll('[data-screen]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const screenId = btn.dataset.screen;
        this.showScreen(screenId);
      });
    });

    // Settings (parental gate: long-press 2 seconds)
    let settingsTimer = null;
    const settingsBtn = document.getElementById('settings-btn');
    settingsBtn.addEventListener('touchstart', (e) => {
      e.preventDefault();
      settingsTimer = setTimeout(() => {
        document.getElementById('settings-modal').style.display = 'flex';
      }, 2000);
    });
    settingsBtn.addEventListener('touchend', () => clearTimeout(settingsTimer));
    settingsBtn.addEventListener('touchmove', () => clearTimeout(settingsTimer));
    // Mouse fallback for desktop testing
    settingsBtn.addEventListener('mousedown', () => {
      settingsTimer = setTimeout(() => {
        document.getElementById('settings-modal').style.display = 'flex';
      }, 2000);
    });
    settingsBtn.addEventListener('mouseup', () => clearTimeout(settingsTimer));
    settingsBtn.addEventListener('mouseleave', () => clearTimeout(settingsTimer));

    // Settings modal
    document.getElementById('settings-close').addEventListener('click', () => {
      document.getElementById('settings-modal').style.display = 'none';
    });
    document.getElementById('reset-progress').addEventListener('click', () => {
      Storage.resetAll();
      document.getElementById('settings-modal').style.display = 'none';
      Speech.speak('כל ההתקדמות אופסה');
    });

    // Fullscreen button
    document.getElementById('fullscreen-btn').addEventListener('click', () => this.toggleFullscreen());

    // Initialize speech and sounds on first interaction
    const initAll = () => {
      this.initSpeech();
      try { Sounds.init(); } catch (e) { /* Audio API not supported */ }
    };
    document.addEventListener('click', initAll, { once: true });
    document.addEventListener('touchend', initAll, { once: true });
  },

  toggleFullscreen() {
    const elem = document.documentElement;
    if (!document.fullscreenElement && !document.webkitFullscreenElement) {
      // Enter fullscreen
      if (elem.requestFullscreen) {
        elem.requestFullscreen();
      } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen(); // Safari / older Android
      }
    } else {
      // Exit fullscreen
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      }
    }
  },

  async initSpeech() {
    if (this.speechInitialized) return;
    this.speechInitialized = true;

    await Speech.init();
    if (Speech.isFallback()) {
      // Show info that using fallback (needs internet)
      const warning = document.getElementById('tts-warning');
      warning.textContent = '🔊 הקראה בעברית פועלת דרך האינטרנט (לא נמצא קול עברי מקומי)';
      warning.style.display = 'block';
      setTimeout(() => { warning.style.display = 'none'; }, 4000);
    } else if (!Speech.isAvailable()) {
      document.getElementById('tts-warning').style.display = 'block';
      setTimeout(() => {
        document.getElementById('tts-warning').style.display = 'none';
      }, 5000);
    }
  },

  showScreen(screenId) {
    // Stop any ongoing speech
    Speech.stop();

    // Cleanup all game modules (clear pending timeouts, reset transitioning)
    Quiz.cleanup();
    Brands.cleanup();
    SoundQuiz.cleanup();
    OddOneOut.cleanup();
    Matching.cleanup();
    CarParts.cleanup();
    Puzzle.cleanup();

    // Hide all screens
    document.querySelectorAll('.screen').forEach(screen => {
      screen.classList.remove('active');
    });

    // Show target screen
    const target = document.getElementById(screenId);
    if (target) {
      target.classList.add('active');

      // Call show() for each mode to initialize its state
      switch (screenId) {
        case 'screen-learning':
          Learning.show();
          break;
        case 'screen-brands':
          Brands.show();
          break;
        case 'screen-quiz':
          Quiz.show();
          break;
        case 'screen-matching':
          Matching.show();
          break;
        case 'screen-sound-quiz':
          SoundQuiz.show();
          break;
        case 'screen-odd-one-out':
          OddOneOut.show();
          break;
        case 'screen-car-parts':
          CarParts.show();
          break;
        case 'screen-puzzle':
          Puzzle.show();
          break;
      }
    }
  },

  celebrate() {
    Sounds.celebration();
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FED766', '#2AB7CA', '#F0B67F', '#FE5F55', '#7BC950'];
    for (let i = 0; i < 40; i++) {
      const confetti = document.createElement('div');
      confetti.className = 'confetti';
      confetti.style.left = Math.random() * 100 + 'vw';
      confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
      confetti.style.animationDuration = (2 + Math.random() * 2) + 's';
      confetti.style.animationDelay = Math.random() * 0.5 + 's';
      confetti.style.width = (6 + Math.random() * 8) + 'px';
      confetti.style.height = (6 + Math.random() * 8) + 'px';
      confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
      document.body.appendChild(confetti);

      // Clean up
      setTimeout(() => confetti.remove(), 4000);
    }
  }
};

// Start the app
document.addEventListener('DOMContentLoaded', () => App.init());
