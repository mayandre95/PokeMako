export type ScoreKey =
  | 'power_score'
  | 'offensive_score'
  | 'tank_score'
  | 'meta_score'

export const SCORE_LABELS: {
  key: ScoreKey
  label: string // label long — fiche Pokémon (ScoreBar)
  labelShort: string // label court — tableau comparateur
  tooltip: string
  max: number
  color: string
}[] = [
  {
    key: 'power_score',
    label: 'Score total (BST)',
    labelShort: 'Power (BST)',
    tooltip:
      'Somme des 6 statistiques de base : PV + Attaque + Défense + Att. Spé + Déf. Spé + Vitesse',
    max: 800,
    color: '#6366f1',
  },
  {
    key: 'offensive_score',
    label: 'Score offensif',
    labelShort: 'Offensif',
    tooltip: 'Capacité à attaquer vite et fort : Attaque + Att. Spé + Vitesse',
    max: 450,
    color: '#ef4444',
  },
  {
    key: 'tank_score',
    label: 'Score défensif',
    labelShort: 'Défensif',
    tooltip: 'Résistance aux dégâts : PV + Défense + Déf. Spé',
    max: 450,
    color: '#22c55e',
  },
  {
    key: 'meta_score',
    label: 'Score méta',
    labelShort: 'Méta',
    tooltip:
      'Score total ajusté selon les résistances et faiblesses de type : +10 par immunité, +5 par résistance, −10 par faiblesse',
    max: 900,
    color: '#f59e0b',
  },
]
