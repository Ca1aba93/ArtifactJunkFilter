import itertools

from src.basic_data import main_weights, all_substats, sub_weights, get_allowed_main_stats


# 根据给定的主、副词条范围，生成所有符合要求的主副属性组合（初始3、4词条，不计顺序）
def get_all_comb(main_range: set, sub_range: set):
    distribution_4stats = []
    distribution_3stats = []
    all_sub = all_substats.copy()
    sub_complement = all_sub - sub_range

    for main_stat in main_range:
        temp_sub_range = sub_range - {main_stat}
        temp_complement = sub_complement - {main_stat}

        if len(temp_sub_range) >= 3:
            selected_num = 3
            complement_num = 0
        else:
            selected_num = len(temp_sub_range)
            complement_num = 3 - len(temp_sub_range)

        for selected_sub in itertools.combinations(temp_sub_range, selected_num):
            for complement_sub in itertools.combinations(temp_complement, complement_num):
                distribution_3stats.append((main_stat, *selected_sub, *complement_sub))

        if len(temp_sub_range) >= 4:
            selected_num = 4
            complement_num = 0
        else:
            selected_num = len(temp_sub_range)
            complement_num = 4 - len(temp_sub_range)

        for selected_sub in itertools.combinations(temp_sub_range, selected_num):
            for complement_sub in itertools.combinations(temp_complement, complement_num):
                distribution_4stats.append((main_stat, *selected_sub, *complement_sub))

    all_distribution = distribution_3stats + distribution_4stats
    return all_distribution


def get_probability_for_combination(combination: tuple, equip_type: str) -> float:
    # 计算主属性生成概率
    main_stat = combination[0]
    main_weight = main_weights[equip_type].copy()
    main_prob = main_weight[main_stat] / sum(main_weight.values())

    # 计算副属性生成概率
    sub_stats = combination[1:]
    sub_weight = sub_weights.copy()
    sub_weight.pop(main_stat, None)

    sub_prob = 0.0
    for sub_perm in itertools.permutations(sub_stats):
        perm_weight = sub_weight.copy()
        if len(sub_perm) == 3:
            pp = 0.8  # permutation_probability
        else:
            pp = 0.2
        for sub_stat in sub_perm:
            pp *= perm_weight[sub_stat] / sum(perm_weight.values())
            perm_weight.pop(sub_stat)
        sub_prob += pp

    comb_probability = main_prob * sub_prob
    return comb_probability


def calculate_prob_for_stats_all_comb(target_main_stats: set, target_sub_stats: set, equip_type: str) -> float:
    """
    生成所有可能的组合:
    规则1：如果输入空集，则按最大允许范围计算
    规则2：如果输入范围超过允许范围，则取交集进行计算
    规则3：要求的副词条若是大于等于4（3）条，则输出从中取4（3）个的所有组合
    规则4：要求的副词条若是小于等于3条，则会从补集中任意选取词条，补足4（3）条
    规则5：会按以上条件生成初始3、4词条的所有组合可能
    计算满足一定要求的属性组合的概率
    """
    # 获取属性允许范围
    allowed_main = get_allowed_main_stats(equip_type)
    allowed_sub = all_substats.copy()

    # 如果输入集合为空，则使用最大允许范围
    main_range = target_main_stats & allowed_main or allowed_main
    sub_range = target_sub_stats & allowed_sub or allowed_sub

    # 计算所有组合的概率相加的结果
    total_prob = 0.0
    for comb in get_all_comb(main_range, sub_range):
        prob = get_probability_for_combination(comb, equip_type)
        total_prob += prob

    return total_prob


def calculate_prob_for_specified_stats(target_main_stat: str, target_sub_stats: set, equip_type: str) -> float:
    # 计算给定词条的圣遗物生成概率

    main_weight = main_weights[equip_type].copy()
    main_prob = main_weight[target_main_stat] / sum(main_weight.values())

    sub_weight = sub_weights.copy()
    sub_weight.pop(target_main_stat, None)
    sub_prob = 0.0
    for sub_perm in itertools.permutations(target_sub_stats):
        perm_weight = sub_weight.copy()
        if len(sub_perm) == 3:
            pp = 0.8  # permutation_probability
        else:
            pp = 0.2
        for sub_stat in sub_perm:
            pp *= perm_weight[sub_stat] / sum(perm_weight.values())
            perm_weight.pop(sub_stat)
        sub_prob += pp

    final_prob = main_prob * sub_prob
    return final_prob


if __name__ == "__main__":
    pass
