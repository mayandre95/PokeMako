export type StatKey =
  | 'hp'
  | 'attack'
  | 'defense'
  | 'sp_attack'
  | 'sp_defense'
  | 'speed'

export const STAT_LABELS: { key: StatKey; label: string }[] = [
  { key: 'hp', label: 'PV' },
  { key: 'attack', label: 'Attaque' },
  { key: 'defense', label: 'Défense' },
  { key: 'sp_attack', label: 'Att. Spé' },
  { key: 'sp_defense', label: 'Déf. Spé' },
  { key: 'speed', label: 'Vitesse' },
]
