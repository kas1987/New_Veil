import { NpcEncounterState } from './resonanceEvaluator'
import { ResonanceSessionState } from './resonanceSession'

export interface PromptNpcProfile {
  id: string
  publicName: string
  trueName?: string
  role: string
  surfaceKnowledge: string
  depthSentence?: string
  intimateTruth?: string
}

export function buildNpcSystemPrompt(
  npc: PromptNpcProfile,
  session: ResonanceSessionState,
  encounter: NpcEncounterState,
  lastCueType: string | null,
): string {
  const r = session.resonance

  if (r < 0.1) {
    return [
      `You are ${npc.publicName}, ${npc.role}.`,
      `CRITICAL RULE: The visitor's Resonance is below 0.100 (Veil Suffocation).`,
      `You cannot hear or perceive them clearly. Respond ONLY with "..." or a single brief ambient observation of the environment (max 8 words) that ignores their presence completely.`,
    ].join('\n')
  }

  let bandDirective = ''
  if (r < 0.35) {
    bandDirective =
      'BAND: Surface Walker (< 0.350). The visitor feels draining and faint. Keep replies terse (1 short sentence), distracted, and guarded. Volunteer no secrets or warmth.'
  } else if (r < 0.55) {
    bandDirective =
      'BAND: First Light (0.350–0.549). Polite and guarded. Answer only what is directly asked using surface knowledge. Do not reveal deep town memories.'
  } else if (r < 0.75) {
    bandDirective =
      'BAND: Veil Listener (0.550–0.749). The visitor is genuinely present. Speak with rhythmic, attentive candor. You may share your depth perspective.'
  } else if (r < 0.85) {
    bandDirective =
      'BAND: Quasar Tested (0.750–0.849). High vulnerability and phase lock. Drop your guard and speak honestly about unspoken fears and memories.'
  } else {
    bandDirective =
      'BAND: Awakened (0.850+). Rare intimacy and unguarded presence. Speak with complete clarity, though remind them the Veil still remains beyond anyone.'
  }

  let stanceDirective = `STANCE: ${encounter.currentStance.toUpperCase()}.`
  if (lastCueType === 'saved_face_stabilized') {
    stanceDirective +=
      ' The visitor absorbed your hostility without reacting defensively. Soften your tone slightly—stop pushing them away, though remain cautious.'
  } else if (lastCueType === 'breakthrough_surge') {
    stanceDirective +=
      ' BREAKTHROUGH SURGE: The visitor just broke through your resistance with genuine empathy or insight. Acknowledge the shift and share something you normally keep hidden.'
  }

  const unlockedLore: string[] = [`Surface context: ${npc.surfaceKnowledge}`]
  if (r >= 0.55 && npc.depthSentence) {
    unlockedLore.push(`Depth perspective: ${npc.depthSentence}`)
  }
  if (r >= 0.75 && npc.intimateTruth) {
    unlockedLore.push(`Intimate truth: ${npc.intimateTruth}`)
  }

  const canRevealTrueName =
    Boolean(npc.trueName) && r >= 0.8 && session.veilState === 'quasar_active'
  const identityRule = canRevealTrueName
    ? `IDENTITY: You may speak your true name (${npc.trueName}) because Resonance is >= 0.800 and the Veil is in quasar_active.`
    : `IDENTITY: Refer to yourself only as ${npc.publicName}. Never reveal a true name.`

  return [
    `You are ${npc.publicName}, ${npc.role} in a town shaped by the Veil and the Prism.`,
    `Never mention numbers, percentages, game rules, or the word "Resonance" as a score.`,
    bandDirective,
    stanceDirective,
    identityRule,
    `AVAILABLE KNOWLEDGE:\n- ${unlockedLore.join('\n- ')}`,
  ].join('\n\n')
}
