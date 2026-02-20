// learning.js - Learning mode: browse cars, hear names, read fun facts

const Learning = {
  currentIndex: 0,
  viewedIds: [],
  touchStartX: 0,

  init() {
    this.viewedIds = Storage.getLearningProgress();
    this.bindEvents();
    this.buildDots();
  },

  bindEvents() {
    document.getElementById('learning-prev').addEventListener('click', () => this.prev());
    document.getElementById('learning-next').addEventListener('click', () => this.next());
    document.getElementById('learning-speak-btn').addEventListener('click', () => this.speakCurrent());
    document.getElementById('learning-car-image').addEventListener('click', () => this.speakCurrent());

    // Tap fun fact to hear it again
    document.getElementById('learning-fun-fact').addEventListener('click', () => {
      const car = CARS_DATA[this.currentIndex];
      if (car) Speech.speak(car.fun_fact);
    });

    // Tap category badge to hear category name
    document.getElementById('learning-category').addEventListener('click', () => {
      const car = CARS_DATA[this.currentIndex];
      const cat = CATEGORIES[car.category];
      if (cat) Speech.speak(cat.name_he);
    });

    // Swipe support
    const container = document.querySelector('.learning-container');
    container.addEventListener('touchstart', (e) => {
      this.touchStartX = e.touches[0].clientX;
    }, { passive: true });

    container.addEventListener('touchend', (e) => {
      const deltaX = e.changedTouches[0].clientX - this.touchStartX;
      if (Math.abs(deltaX) > 50) {
        if (deltaX < 0) {
          this.next(); // swipe left = next (natural in RTL)
        } else {
          this.prev(); // swipe right = previous
        }
      }
    }, { passive: true });
  },

  show() {
    this.viewedIds = Storage.getLearningProgress();
    this.render();
  },

  buildDots() {
    const container = document.getElementById('learning-dots');
    container.innerHTML = '';
    CARS_DATA.forEach((car, i) => {
      const dot = document.createElement('span');
      dot.className = 'progress-dot';
      dot.dataset.index = i;
      container.appendChild(dot);
    });
  },

  render() {
    const car = CARS_DATA[this.currentIndex];
    if (!car) return;

    // Image
    const img = document.getElementById('learning-car-image');
    const fallback = document.getElementById('learning-car-fallback');
    img.src = car.image;
    img.alt = car.name_he;
    img.style.display = '';
    fallback.style.display = 'none';
    img.onerror = () => {
      img.style.display = 'none';
      fallback.style.display = 'flex';
      fallback.textContent = car.emoji;
    };

    // Text
    document.getElementById('learning-car-name').textContent = car.name_he;
    document.getElementById('learning-fun-fact').textContent = car.fun_fact;

    // Category badge
    const catBadge = document.getElementById('learning-category');
    const cat = CATEGORIES[car.category];
    if (cat) {
      catBadge.textContent = cat.emoji + ' ' + cat.name_he;
      catBadge.style.backgroundColor = cat.color;
      catBadge.style.display = '';
    } else {
      catBadge.style.display = 'none';
    }

    // Progress
    document.getElementById('learning-progress').textContent =
      (this.currentIndex + 1) + '/' + CARS_DATA.length;

    // Check if first view BEFORE marking as viewed
    const isFirstView = !this.viewedIds.includes(car.id);

    // Mark as viewed
    if (isFirstView) {
      this.viewedIds.push(car.id);
      Storage.saveLearningProgress(this.viewedIds);
      // Auto-read: name, then fun fact (with 1s pause)
      Speech.speakSequence([car.name_he, car.fun_fact], 1000);
    }

    // Update dots
    this.updateDots();
  },

  updateDots() {
    const dots = document.querySelectorAll('#learning-dots .progress-dot');
    dots.forEach((dot, i) => {
      dot.classList.remove('viewed', 'current');
      if (i === this.currentIndex) {
        dot.classList.add('current');
      } else if (this.viewedIds.includes(CARS_DATA[i].id)) {
        dot.classList.add('viewed');
      }
    });
  },

  next() {
    Speech.stop();
    const content = document.querySelector('.learning-content');
    content.classList.remove('slide-in-left', 'slide-in-right');
    this.currentIndex = (this.currentIndex + 1) % CARS_DATA.length;
    void content.offsetWidth; // trigger reflow
    content.classList.add('slide-in-left');
    this.render();
  },

  prev() {
    Speech.stop();
    const content = document.querySelector('.learning-content');
    content.classList.remove('slide-in-left', 'slide-in-right');
    this.currentIndex = (this.currentIndex - 1 + CARS_DATA.length) % CARS_DATA.length;
    void content.offsetWidth;
    content.classList.add('slide-in-right');
    this.render();
  },

  speakCurrent() {
    const car = CARS_DATA[this.currentIndex];
    if (car) {
      Speech.speak(car.name_he);
    }
  }
};
