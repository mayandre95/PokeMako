export type RoleKey =
  | 'attacker_score'
  | 'tank_role_score'
  | 'support_score'
  | 'sweeper_score'
  | 'versatility_score'

export const ROLE_LABELS: {
  key: RoleKey
  label: string
  tooltip: string
  max: number
  color: string
}[] = [
  {
    key: 'attacker_score',
    label: 'Attaquant',
    tooltip:
      'Capacité à frapper fort grâce à sa meilleure statistique offensive (Attaque ou Attaque Spéciale)',
    max: 350,
    color: '#ef4444',
  },
  {
    key: 'tank_role_score',
    label: 'Tank',
    tooltip:
      'Capacité à encaisser les coups : PV pondérés fortement (protègent contre les deux types de dégâts) + Défense et Défense Spéciale',
    max: 550,
    color: '#22c55e',
  },
  {
    key: 'support_score',
    label: 'Support',
    tooltip:
      'Capacité à survivre et agir tôt pour placer des effets utilitaires, indépendamment de sa force offensive',
    max: 450,
    color: '#8b5cf6',
  },
  {
    key: 'sweeper_score',
    label: 'Sweeper',
    tooltip:
      "Capacité à enchaîner les KO grâce à l'attaque et la vitesse combinées",
    max: 600,
    color: '#f59e0b',
  },
  {
    key: 'versatility_score',
    label: 'Polyvalence',
    tooltip:
      "Équilibre entre les 4 rôles ci-dessus : élevé si le Pokémon est compétent partout, faible s'il excelle dans un seul rôle",
    max: 300,
    color: '#6366f1',
  },
]
