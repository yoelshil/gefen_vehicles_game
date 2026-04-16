// app.js - Main application controller: screen routing, initialization

const App = {
  speechInitialized: false,
  deferredInstallPrompt: null,

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

    // Register service worker
    this.registerServiceWorker();

    // Setup PWA install prompt
    this.setupInstallPrompt();

    // Setup WhatsApp share
    this.setupShare();

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

  registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('./service-worker.js').catch(() => {});
    }
  },

  setupInstallPrompt() {
    const installBtn = document.getElementById('install-btn');

    // Catch the beforeinstallprompt event (Chrome/Android)
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredInstallPrompt = e;
      installBtn.style.display = 'flex';
    });

    installBtn.addEventListener('click', () => {
      if (this.deferredInstallPrompt) {
        // Android / Chrome: use native prompt
        this.deferredInstallPrompt.prompt();
        this.deferredInstallPrompt.userChoice.then(() => {
          this.deferredInstallPrompt = null;
          installBtn.style.display = 'none';
        });
      } else if (this.isIOS()) {
        // iOS: show manual instructions
        this.showIOSInstallBanner();
      }
    });

    // On iOS show the install button with manual instructions
    if (this.isIOS() && !this.isStandalone()) {
      installBtn.style.display = 'flex';
    }

    // Hide install button if already installed
    window.addEventListener('appinstalled', () => {
      installBtn.style.display = 'none';
      this.deferredInstallPrompt = null;
    });
  },

  isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) ||
      (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  },

  isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches ||
      navigator.standalone === true;
  },

  showIOSInstallBanner() {
    // Remove existing banner if any
    const existing = document.querySelector('.ios-install-banner');
    if (existing) existing.remove();

    const banner = document.createElement('div');
    banner.className = 'ios-install-banner';
    banner.innerHTML = `
      <button class="close-banner" aria-label="סגור">&times;</button>
      <p>להתקנה על המכשיר:</p>
      <p>לחץ על <strong style="font-size:1.3em">⎙</strong> (שיתוף) בתחתית הדפדפן</p>
      <p>ואז בחר <strong>"הוסף למסך הבית"</strong></p>
    `;
    document.body.appendChild(banner);
    banner.querySelector('.close-banner').addEventListener('click', () => banner.remove());
  },

  setupShare() {
    document.getElementById('share-whatsapp-btn').addEventListener('click', () => {
      const gameUrl = window.location.href;
      const text = encodeURIComponent('בואו לשחק במשחק המכוניות של גפן! 🚗🎮\n' + gameUrl);
      window.open('https://wa.me/?text=' + text, '_blank');
    });
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
