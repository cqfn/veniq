from typing import List, Tuple

from veniq.baselines.semi.grouping_size import is_similar_size
from veniq.baselines.semi.overlap import is_overlap


def _temp_hasMoreBenefitThan(oport_1: Tuple[int],
                             oport_2: Tuple[int]) -> bool:
    """
    Temporary method implementing fitness function for
    ranking hypotheses.
    To be substituted with metric implemented in veniq.baselines.semi.fitness_func
    Returns True if oport_1 has more benefit than oport_2
    """
    return True


def _temp_fitness_f(oport: Tuple[int]) -> float:
    """
    Actually, this function also needs to have access to the whole
    method body. We will fix it in the next PR.
    """
    return 1.0


def in_same_group(oport_1: Tuple[int], oport_2: Tuple[int],
                  max_size_difference: float = 0.2,
                  min_overlap: float = 0.1) -> bool:
    """
    Checks if two oportunuties should be grouped, 
    by checking overlap and size difference.
    """
    return is_similar_size(oport_1, oport_2,
                           max_size_difference=max_size_difference) and \
           is_overlap(oport_1, oport_2, min_overlap=min_overlap)


def group_and_rank_in_groups(oportunities: List[Tuple[int]],
                             **kwargs) -> List[Tuple[int]]:
    """
        Implements Fig.7 in the paper. Groups oportunities
        and selects primary per group. Returns the set
        of primary oportunities
    """
    alternatives = set()

    for i, oport_1 in enumerate(oportunities):
        if i in alternatives:
            continue

        for j in range(i+1, len(oportunities)):
            oport_2 = oportunities[j]
            if oport_2 in alternatives:
                continue

            if in_same_group(oport_1, oport_2, **kwargs):
                if _temp_hasMoreBenefitThan(oport_1, oport_2):
                    alternatives.add(j)
                else:
                    alternatives.add(i)

    primary_oport_indices = set(range(len(oportunities))) - alternatives
    return [oportunities[i] for i in primary_oport_indices]


def output_best_oportunities(oportunities: List[Tuple[int]],
                             top_k: int = 5,
                             **kwargs) -> List[Tuple[int]]:
    """
    Runs grouping and ranking to produce the set of 'primanry oportunities'.
    Given the final list, outputs top-k according to the fitness functon.
    """
    primary_oportunities = group_and_rank_in_groups(oportunities, **kwargs)
    primary_oportunities_eval = {o: _temp_fitness_f(o) for o in
                                 primary_oportunities}
    sorted_oport = sorted(primary_oportunities_eval.items(),
                          key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_oport[:top_k]]
