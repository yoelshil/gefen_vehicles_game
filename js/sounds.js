// sounds.js - Sound effects using Web Audio API (no files needed)

const Sounds = {
  _ctx: null,

  init() {
    try {
      if (!this._ctx) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) this._ctx = new AudioCtx();
      }
      if (this._ctx && this._ctx.state === 'suspended') {
        this._ctx.resume();
      }
    } catch (e) {
      this._ctx = null;
    }
  },

  _ensureContext() {
    if (!this._ctx) this.init();
    return this._ctx;
  },

  // Correct answer - happy ascending double chime
  correct() {
    const ctx = this._ensureContext();
    if (!ctx) return;
    const now = ctx.currentTime;

    // First note - bright
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.frequency.value = 880;
    osc1.type = 'sine';
    gain1.gain.setValueAtTime(0.3, now);
    gain1.gain.exponentialRampToValueAtTime(0.01, now + 0.25);
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    osc1.start(now);
    osc1.stop(now + 0.25);

    // Second note - higher, happy
    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.frequency.value = 1320;
    osc2.type = 'sine';
    gain2.gain.setValueAtTime(0.25, now + 0.15);
    gain2.gain.exponentialRampToValueAtTime(0.01, now + 0.5);
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    osc2.start(now + 0.15);
    osc2.stop(now + 0.5);
  },

  // Wrong answer - gentle soft low tone
  wrong() {
    const ctx = this._ensureContext();
    if (!ctx) return;
    const now = ctx.currentTime;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.frequency.setValueAtTime(330, now);
    osc.frequency.exponentialRampToValueAtTime(220, now + 0.3);
    osc.type = 'sine';
    gain.gain.setValueAtTime(0.18, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.3);
  },

  // Card flip - quick rising swoosh
  flip() {
    const ctx = this._ensureContext();
    if (!ctx) return;
    const now = ctx.currentTime;

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.frequency.setValueAtTime(300, now);
    osc.frequency.exponentialRampToValueAtTime(800, now + 0.15);
    osc.type = 'triangle';
    gain.gain.setValueAtTime(0.12, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.15);
  },

  // Match found - bright sparkle ding
  match() {
    const ctx = this._ensureContext();
    if (!ctx) return;
    const now = ctx.currentTime;

    const frequencies = [1047, 1319, 1568]; // C6, E6, G6 - major chord
    frequencies.forEach((freq, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.frequency.value = freq;
      osc.type = 'sine';
      const start = now + i * 0.08;
      gain.gain.setValueAtTime(0.2, start);
      gain.gain.exponentialRampToValueAtTime(0.01, start + 0.4);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(start);
      osc.stop(start + 0.4);
    });
  },

  // Celebration - joyful ascending fanfare
  celebration() {
    const ctx = this._ensureContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    const masterGain = ctx.createGain();
    masterGain.gain.value = 0.25;
    masterGain.connect(ctx.destination);

    // C major ascending fanfare: C5, E5, G5, C6, E6 (hold)
    const notes = [
      { freq: 523, start: 0, dur: 0.2 },
      { freq: 659, start: 0.2, dur: 0.2 },
      { freq: 784, start: 0.4, dur: 0.2 },
      { freq: 1047, start: 0.65, dur: 0.35 },
      { freq: 1319, start: 1.05, dur: 0.5 },
      { freq: 1568, start: 1.1, dur: 0.5 }
    ];

    notes.forEach(note => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.frequency.value = note.freq;
      osc.type = 'sine';
      const t = now + note.start;
      gain.gain.setValueAtTime(0.3, t);
      gain.gain.exponentialRampToValueAtTime(0.01, t + note.dur);
      osc.connect(gain);
      gain.connect(masterGain);
      osc.start(t);
      osc.stop(t + note.dur);
    });
  }
};
