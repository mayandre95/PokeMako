export const METHOD_FR: Record<string, string> = {
  walk: 'Herbe',
  surf: 'Surf',
  'old-rod': 'Vieille Canne',
  'good-rod': 'Super Canne',
  'super-rod': 'Méga Canne',
  'rock-smash': 'Éclate-Roc',
  headbutt: 'Coup de Boule',
  gift: 'Cadeau',
  'only-one': 'Unique',
  'poke-radar': 'Radar Pokémon',
  'grass-spots': 'Herbe agitée',
  'dark-grass': 'Herbe sombre',
  fishing: 'Pêche',
}

export const CONDITION_FR: Record<string, string> = {
  // Heure
  'time-morning': 'Matin',
  'time-day': 'Jour',
  'time-night': 'Nuit',
  // Météo (Épée/Bouclier, Écarlate/Violet)
  'weather-raining': 'Pluie',
  'weather-thunderstorm': 'Orage',
  'weather-intense-sun': 'Soleil intense',
  'weather-overcast': 'Couvert',
  'weather-sandstorm': 'Tempête de sable',
  'weather-fog': 'Brouillard',
  'weather-snowing': 'Neige',
  // Radar / Essaim / Slot 2
  'radar-on': 'Radar',
  'swarm-yes': 'Essaim',
  'slot2-ruby': 'Ruby en slot 2',
  'slot2-sapphire': 'Saphir en slot 2',
  'slot2-emerald': 'Émeraude en slot 2',
  'slot2-firered': 'Rouge Feu en slot 2',
  'slot2-leafgreen': 'Vert Feuille en slot 2',
  // Progression / événements
  'story-progress-hall-of-fame': 'Après la Ligue',
  'story-progress-before-hall-of-fame': 'Avant la Ligue',
  'save-data-from-lets-go-pikachu': "Données Let's Go Pikachu",
  'save-data-from-lets-go-eevee': "Données Let's Go Évoli",
  'friend-safari-slot-2': 'Safari Ami (slot 2)',
  'backlot-mentioned': 'Backlot en a parlé',
  'coins-620': '620 pièces',
  'coins-2222': '2222 pièces',
  'headbutt-tree-secret': 'Arbre secret',
}

const NEGATIVE_SUFFIXES = ['-no', '-off', '-none', '-not-mentioned', '-normal']
export function isPositiveCondition(c: string): boolean {
  return !NEGATIVE_SUFFIXES.some((s) => c.endsWith(s))
}
