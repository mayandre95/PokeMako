MAX_TEAM_SIZE = 6

# Une faiblesse partagée pèse dans le score de suggestion proportionnellement à
# son weak_count (1 à 6) ; combler une lacune de couverture offensive vaut un
# bonus fixe — le défensif domine par construction (le ticket demande de
# combler les faiblesses en priorité), l'offensif départage en complément.
OFFENSIVE_GAP_BONUS = 3


def _multiplier(
    chart: dict, attacker_type_id: int, defender_type_ids: list[int]
) -> float:
    mult = 1.0
    for defender_id in defender_type_ids:
        mult *= chart.get((attacker_type_id, defender_id), 1.0)
    return mult


def analyze_weaknesses(
    team: list[dict], chart: dict, all_type_ids: list[int]
) -> list[dict]:
    """Pour chaque type attaquant, combien de membres de l'équipe y sont
    vulnérables (multiplicateur > 1) — triées par weak_count décroissant."""
    weaknesses = []
    for attacker_id in all_type_ids:
        weak_members = [
            m["id"]
            for m in team
            if _multiplier(chart, attacker_id, m["type_ids"]) > 1.0
        ]
        if weak_members:
            weaknesses.append(
                {
                    "type_id": attacker_id,
                    "weak_count": len(weak_members),
                    "members": weak_members,
                }
            )
    weaknesses.sort(key=lambda w: w["weak_count"], reverse=True)
    return weaknesses


def analyze_offensive_coverage(
    team: list[dict], chart: dict, all_type_ids: list[int]
) -> dict:
    """Pour chaque type défenseur, l'équipe a-t-elle au moins un type propre
    (logique STAB) qui y serait super efficace ?"""
    covered, gaps = [], []
    for defender_id in all_type_ids:
        is_covered = any(
            chart.get((t, defender_id), 1.0) > 1.0
            for member in team
            for t in member["type_ids"]
        )
        (covered if is_covered else gaps).append(defender_id)
    return {"covered": covered, "gaps": gaps}


def analyze_member_matchups(
    team: list[dict], chart: dict, all_type_ids: list[int]
) -> dict[int, dict]:
    """Vue par membre (complémentaire de analyze_weaknesses, qui raisonne à
    l'échelle de l'équipe) : pour chaque Pokémon, les types face auxquels il
    est faible et ceux qu'il résiste ou dont il est immunisé."""
    matchups = {}
    for member in team:
        weak, strong = [], []
        for type_id in all_type_ids:
            mult = _multiplier(chart, type_id, member["type_ids"])
            if mult > 1.0:
                weak.append(type_id)
            elif mult < 1.0:
                strong.append(type_id)
        matchups[member["id"]] = {"weaknesses": weak, "resistances": strong}
    return matchups


def analyze_remaining_weaknesses(
    team: list[dict], weaknesses: list[dict], chart: dict
) -> list[dict]:
    """Sous-ensemble des faiblesses cumulées pour lesquelles AUCUN membre ne
    résiste ni n'est immunisé — celles où l'équipe n'a littéralement aucune
    réponse disponible, contrairement aux faiblesses cumulées qui comptent
    aussi celles où un membre peut simplement switcher dessus sans risque."""
    return [
        w
        for w in weaknesses
        if not any(_multiplier(chart, w["type_id"], m["type_ids"]) < 1.0 for m in team)
    ]


def suggest_recruits(
    weaknesses: list[dict],
    offensive_gaps: list[int],
    candidates: list[dict],
    chart: dict,
    limit: int = 5,
) -> list[dict]:
    """Score chaque candidat : faiblesses communes résistées (pondérées par
    weak_count) + bonus fixe par lacune offensive couverte par un de ses
    propres types. Égalité départagée par power_score."""
    scored = []
    for candidate in candidates:
        covers = [
            w["type_id"]
            for w in weaknesses
            if _multiplier(chart, w["type_id"], candidate["type_ids"]) < 1.0
        ]
        defensive_score = sum(
            w["weak_count"] for w in weaknesses if w["type_id"] in covers
        )
        offensive_score = sum(
            OFFENSIVE_GAP_BONUS
            for gap_id in offensive_gaps
            if any(chart.get((t, gap_id), 1.0) > 1.0 for t in candidate["type_ids"])
        )
        score = defensive_score + offensive_score
        if score > 0:
            scored.append({**candidate, "score": score, "covers": covers})

    scored.sort(key=lambda c: (c["score"], c["power_score"] or 0), reverse=True)
    return scored[:limit]
