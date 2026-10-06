import type { ProjectManifest } from './types.js';

export const veilManifest: ProjectManifest = {
  id: 'the-veil',
  displayName: 'The Veil',
  repo: 'kas1987/The-Veil',
  defaultRouter: 'veil-router',
  defaultDispatcher: 'veil-dispatcher',
  agents: ['Lorekeeper', 'Architect', 'VoiceSteward'],
  safeIntents: ['chat', 'agent_handoff', 'voice_pipeline'],
  writeIntents: ['docs_update', 'code_patch'],
};
