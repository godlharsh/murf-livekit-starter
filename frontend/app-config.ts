export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;

  accent?: string;
  logoDark?: string;
  accentDark?: string;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorDark?: `#${string}`;
  audioVisualizerColorShift?: number;

  audioVisualizerBarCount?: number;

  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;

  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;

  audioVisualizerWaveLineWidth?: number;

  // Agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  // ==========================================================
  // BHARAT BUDDY BRANDING
  // ==========================================================

  companyName: 'Bharat Buddy',

  pageTitle: 'Your AI Voice Tutor',

  pageDescription:
    'Learn, practice, and improve with your friendly AI voice tutor.',

  // ==========================================================
  // FEATURES
  // ==========================================================

  supportsChatInput: true,

  supportsVideoInput: true,

  supportsScreenShare: true,

  isPreConnectBufferEnabled: true,

  // ==========================================================
  // BRANDING
  // ==========================================================

  logo: '/murf-logo.svg',

  logoDark: '/murf-logo-dark.svg',

  // ==========================================================
  // COLORS
  // ==========================================================

  accent: '#6366F1',

  accentDark: '#818CF8',

  // ==========================================================
  // START BUTTON
  // ==========================================================

  startButtonText: 'Start Learning',

  // ==========================================================
  // AUDIO VISUALIZER
  // ==========================================================

  audioVisualizerType: 'aura',

  audioVisualizerColor: '#6366F1',

  audioVisualizerColorDark: '#818CF8',

  audioVisualizerColorShift: 0.3,

  // ==========================================================
  // AGENT DISPATCH
  // ==========================================================

  agentName: process.env.AGENT_NAME ?? 'my-agent',

  // ==========================================================
  // LIVEKIT CLOUD SANDBOX
  // ==========================================================

  sandboxId: undefined,
};