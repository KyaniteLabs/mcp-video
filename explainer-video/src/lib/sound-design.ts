// Procedural sound design using Web Audio API
// No external audio files - everything generated in-browser

export interface SoundDesignConfig {
  masterVolume?: number;
  enableDrone?: boolean;
  enableUI?: boolean;
  enableTransitions?: boolean;
}

class SoundDesignEngine {
  private ctx: AudioContext | null = null;
  private masterGain: GainNode | null = null;
  private droneOsc: OscillatorNode | null = null;
  private droneGain: GainNode | null = null;
  private active = false;

  init() {
    if (typeof window === 'undefined') return;
    this.ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    this.masterGain = this.ctx.createGain();
    this.masterGain.gain.value = 0.3;
    this.masterGain.connect(this.ctx.destination);
    this.active = true;
  }

  // Continuous ambient drone that shifts with scene colors
  startDrone(baseFreq: number = 80, harmonic: number = 0.5) {
    if (!this.ctx || !this.masterGain) return;
    
    // Main drone oscillator
    this.droneOsc = this.ctx.createOscillator();
    this.droneGain = this.ctx.createGain();
    
    this.droneOsc.type = 'sine';
    this.droneOsc.frequency.value = baseFreq;
    
    // Subtle harmonic overtone
    const harmonicOsc = this.ctx.createOscillator();
    const harmonicGain = this.ctx.createGain();
    harmonicOsc.type = 'triangle';
    harmonicOsc.frequency.value = baseFreq * 1.5;
    harmonicGain.gain.value = harmonic * 0.1;
    
    this.droneGain.gain.value = 0.05; // Very subtle
    
    this.droneOsc.connect(this.droneGain);
    harmonicOsc.connect(harmonicGain);
    this.droneGain.connect(this.masterGain);
    harmonicGain.connect(this.masterGain);
    
    this.droneOsc.start();
    harmonicOsc.start();
    
    // Slowly modulate frequency for "living" feel
    const lfo = this.ctx.createOscillator();
    lfo.frequency.value = 0.1; // 0.1Hz = 10 second cycle
    const lfoGain = this.ctx.createGain();
    lfoGain.gain.value = 2; // +/- 2Hz variation
    lfo.connect(lfoGain);
    lfoGain.connect(this.droneOsc.frequency);
    lfo.start();
  }

  // Shift drone frequency (for scene transitions)
  shiftDrone(targetFreq: number, duration: number = 2) {
    if (!this.droneOsc || !this.ctx) return;
    const now = this.ctx.currentTime;
    this.droneOsc.frequency.exponentialRampToValueAtTime(targetFreq, now + duration);
  }

  // UI "blip" sound - short sine burst
  playBlip(frequency: number = 800, duration: number = 0.05) {
    if (!this.ctx || !this.masterGain) return;
    
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    
    osc.type = 'sine';
    osc.frequency.value = frequency;
    
    gain.gain.setValueAtTime(0.1, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
    
    osc.connect(gain);
    gain.connect(this.masterGain);
    
    osc.start();
    osc.stop(this.ctx.currentTime + duration);
  }

  // UI "click" - shorter, sharper
  playClick(pitch: 'low' | 'mid' | 'high' = 'mid') {
    const freqs = { low: 400, mid: 800, high: 1200 };
    this.playBlip(freqs[pitch], 0.03);
  }

  // Data "whoosh" for transitions
  playWhoosh(duration: number = 0.3, direction: 'up' | 'down' = 'up') {
    if (!this.ctx || !this.masterGain) return;
    
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    const filter = this.ctx.createBiquadFilter();
    
    osc.type = 'sawtooth';
    filter.type = 'lowpass';
    
    const now = this.ctx.currentTime;
    
    if (direction === 'up') {
      osc.frequency.setValueAtTime(100, now);
      osc.frequency.exponentialRampToValueAtTime(2000, now + duration);
      filter.frequency.setValueAtTime(200, now);
      filter.frequency.exponentialRampToValueAtTime(3000, now + duration);
    } else {
      osc.frequency.setValueAtTime(2000, now);
      osc.frequency.exponentialRampToValueAtTime(100, now + duration);
      filter.frequency.setValueAtTime(3000, now);
      filter.frequency.exponentialRampToValueAtTime(200, now + duration);
    }
    
    gain.gain.setValueAtTime(0.05, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + duration);
    
    osc.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);
    
    osc.start();
    osc.stop(now + duration);
  }

  // Success/POSITIVE chime
  playChime() {
    if (!this.ctx || !this.masterGain) return;
    
    const now = this.ctx.currentTime;
    const notes = [523.25, 659.25, 783.99]; // C major chord
    
    notes.forEach((freq, i) => {
      const osc = this.ctx!.createOscillator();
      const gain = this.ctx!.createGain();
      
      osc.type = 'sine';
      osc.frequency.value = freq;
      
      gain.gain.setValueAtTime(0, now + i * 0.05);
      gain.gain.linearRampToValueAtTime(0.1, now + i * 0.05 + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.05 + 0.5);
      
      osc.connect(gain);
      gain.connect(this.masterGain!);
      
      osc.start(now + i * 0.05);
      osc.stop(now + i * 0.05 + 0.5);
    });
  }

  // Scanning/processing sound (for color analysis scene)
  playScan(duration: number = 1) {
    if (!this.ctx || !this.masterGain) return;
    
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    
    osc.type = 'square';
    osc.frequency.value = 200;
    
    // Rapid frequency modulation
    const lfo = this.ctx.createOscillator();
    lfo.frequency.value = 20;
    const lfoGain = this.ctx.createGain();
    lfoGain.gain.value = 100;
    lfo.connect(lfoGain);
    lfoGain.connect(osc.frequency);
    lfo.start();
    
    gain.gain.setValueAtTime(0.03, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
    
    osc.connect(gain);
    gain.connect(this.masterGain);
    
    osc.start();
    osc.stop(this.ctx.currentTime + duration);
  }

  // Typing texture (white noise burst)
  playTyping(intensity: number = 1) {
    if (!this.ctx || !this.masterGain) return;
    
    const bufferSize = this.ctx.sampleRate * 0.05;
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * intensity;
    }
    
    const noise = this.ctx.createBufferSource();
    noise.buffer = buffer;
    
    const filter = this.ctx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.value = 2000;
    
    const gain = this.ctx.createGain();
    gain.gain.value = 0.02;
    
    noise.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);
    
    noise.start();
  }

  stop() {
    if (this.droneOsc) {
      this.droneOsc.stop();
      this.droneOsc = null;
    }
    if (this.ctx) {
      this.ctx.close();
      this.ctx = null;
    }
    this.active = false;
  }
}

export const soundDesign = new SoundDesignEngine();

// React hook for frame-based sound triggers
export const useSoundDesign = () => {
  return soundDesign;
};
