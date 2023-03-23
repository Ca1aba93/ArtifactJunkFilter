import itertools
import json
import multiprocessing as mp
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from src.artifact_generation_probability import get_probability_for_combination
from src.basic_data import xzs_configs, sub_stats_for_all, main_weights, get_criteria, half_up, artifact_types
from src.expansion_xzs_config import XZSConfig

mpl.use("TkAgg")
lock = mp.Lock()

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)


# 通过圣遗物的装备类型获得该部位的主词条范围
def get_allowed_main_stats(artifact_type: str) -> set:
    properties = main_weights.get(artifact_type, {})
    return set(properties.keys())


# 获得只包含1、2、3、4个目标副词条的组合
def get_combinations_with_target_substats(target_stats: set, artifact_type: str):
    # 获取属性允许范围
    allowed_main = get_allowed_main_stats(artifact_type)
    main_range = target_stats & allowed_main or allowed_main  # 花或羽
    all_sub = sub_stats_for_all.copy()
    sub_range = target_stats & all_sub  # 副词条允许范围只能为交集
    sub_complement = all_sub - sub_range  # 补充副词条只能从补集中获取

    # 结果储存
    result = []

    # 副词条有3、4两档，要计算目标副词条有且仅有1、2、3、4条，首先要保证目标副词条长度，以及补集词条长度
    # 允许的副词条一共有10个，首先要从中排除掉可能的主词条，再减去目标词条集（最多有五个，未来可能扩展），所以要预留足够的判断条件
    # 目标词条集以及补集的长度肯定大于等于2，其他情况要用条件判断
    for main_stat in main_range:
        temp_sub_range = sub_range - {main_stat}
        temp_complement = sub_complement - {main_stat}

        for selected_sub in itertools.combinations(temp_sub_range, 1):
            for complement_sub in itertools.combinations(temp_complement, 2):
                result.append((main_stat, *selected_sub, *complement_sub))

        if len(temp_complement) >= 3:
            for selected_sub in itertools.combinations(temp_sub_range, 1):
                for complement_sub in itertools.combinations(temp_complement, 3):
                    result.append((main_stat, *selected_sub, *complement_sub))

        for selected_sub in itertools.combinations(temp_sub_range, 2):
            for complement_sub in itertools.combinations(temp_complement, 1):
                result.append((main_stat, *selected_sub, *complement_sub))

        for selected_sub in itertools.combinations(temp_sub_range, 2):
            for complement_sub in itertools.combinations(temp_complement, 2):
                result.append((main_stat, *selected_sub, *complement_sub))

        if len(temp_sub_range) >= 3:

            for selected_sub in itertools.combinations(temp_sub_range, 3):
                result.append((main_stat, *selected_sub))

            for selected_sub in itertools.combinations(temp_sub_range, 3):
                for complement_sub in itertools.combinations(temp_complement, 1):
                    result.append((main_stat, *selected_sub, *complement_sub))

        if len(temp_sub_range) >= 4:
            for selected_sub in itertools.combinations(temp_sub_range, 4):
                result.append((main_stat, *selected_sub))

    return result


# 获得该配置下所有有意义的词条组合的出现概率
def get_probability_distribution_for_config(config_index):
    config = XZSConfig(config_index)
    prob_dist_for_config = {}
    for artifact_type in artifact_types:
        exclusive_combinations = get_combinations_with_target_substats(config.target_stats, artifact_type)
        prob_dist_for_combinations = {}
        for combination in exclusive_combinations:
            score = 0
            score += config.get_expected_score(combination)
            score = half_up(score, 2)
            prob = get_probability_for_combination(combination, artifact_type)
            if score not in prob_dist_for_combinations.keys():
                prob_dist_for_combinations[score] = prob
            else:
                prob_dist_for_combinations[score] += prob
        other_comb_prob = 1 - sum(prob_dist_for_combinations.values())
        if 0.0 not in prob_dist_for_combinations.keys():
            prob_dist_for_combinations[0.0] = other_comb_prob
        else:
            prob_dist_for_combinations[0.0] += other_comb_prob
        prob_dist_for_config[artifact_type] = prob_dist_for_combinations
    return prob_dist_for_config


# 画出给定配置的有效圣遗物的概率分布图，以及随机圣遗物分级概率
def plot_probability_distribution_for_config(config_index: int):
    prob_dist_for_config = get_probability_distribution_for_config(config_index)
    score_standards = get_criteria(config_index)
    num_artifact_types = len(prob_dist_for_config)
    print(num_artifact_types)
    fig, axes = plt.subplots(num_artifact_types, 2, figsize=(15, 4 * num_artifact_types))

    for idx, (artifact_type, prob_dist) in enumerate(prob_dist_for_config.items()):
        intervals = score_standards[artifact_type]
        print(intervals)

        print(f'Probability Distribution for {artifact_type}:')
        print(f'Interval Probability Distribution:')
        interval_probabilities = []

        lower_bound_prob = sum([prob_dist[score] for score in prob_dist if score < intervals[0]])
        upper_bound_prob = sum([prob_dist[score] for score in prob_dist if score >= intervals[-1]])

        print(f'Score less than {intervals[0]}: Probability: {lower_bound_prob:.2f}')
        for idx2, interval in enumerate(intervals[:-1]):
            interval_prob = sum(
                [prob_dist[score] for score in prob_dist if interval <= score < intervals[idx2 + 1]])
            interval_probabilities.append(interval_prob)
            print(f'Score Interval: {interval}-{intervals[idx2 + 1]}, Probability: {interval_prob:.2f}')
        print(f'Score greater or equal to {intervals[-1]}: Probability: {upper_bound_prob:.2f}')
        print()

        # 绘制原始概率分布
        x_raw = [score for score in prob_dist.keys() if score != 0]
        y_raw = [prob_dist[score] for score in x_raw]
        axes[idx, 0].bar(x_raw, y_raw, align='center', alpha=0.5)
        axes[idx, 0].set_title(f'Original Probability Distribution for {artifact_type}', fontsize=10)
        axes[idx, 0].set_xlabel('Score', fontsize=8)
        axes[idx, 0].set_ylabel('Probability', fontsize=8)

        # 绘制落入区间的概率分布
        x_interval = [f'<{intervals[0]}'] + [f'{intervals[i]}-{intervals[i + 1]}' for i in
                                             range(len(intervals) - 1)] + [f'>={intervals[-1]}']
        interval_probabilities = [lower_bound_prob] + interval_probabilities + [upper_bound_prob]
        bars = axes[idx, 1].bar(x_interval, interval_probabilities, align='center', alpha=0.5)
        axes[idx, 1].set_title(f'Interval Probability Distribution for {artifact_type}', fontsize=10)
        axes[idx, 1].set_xlabel('Score Interval', fontsize=8)
        axes[idx, 1].set_ylabel('Probability', fontsize=8)

        # 标记概率值
        for bar in bars:
            height = bar.get_height()
            axes[idx, 1].text(bar.get_x() + bar.get_width() / 2., height, f'{height:.2f}', ha='center', va='bottom',
                              fontsize=8)

    # 显示图形
    plt.tight_layout()
    plt.show()


# 通过蒙特卡洛模拟获取给定样本空间下n次抽取的上确界期望值
def get_upper_bound_expectation_by_monte_carlo(sample: dict, num_samples: int, num_repeats: int):
    samples = np.random.choice(list(sample), size=(num_samples, num_repeats), p=list(sample.values()))
    upper_bounds = np.max(samples, axis=1)
    mean_upper_bound = half_up(float(np.mean(upper_bounds)), 1)
    return mean_upper_bound


# 通过蒙特卡洛模拟获取指定配置的毕业标准
def get_graduation_criteria_for_all_setting(config_index: int, num_samples: int, time_threshold):
    # 10天、20天、40天、120天
    lock.acquire()
    prob_dist_for_all_setting = get_probability_distribution_for_config(config_index)
    graduation_criteria_for_all_setting = {}
    for artifact_type in artifact_types:
        graduation_criteria = []
        artifact_sample = prob_dist_for_all_setting[artifact_type]
        for time in time_threshold:
            graduation_criteria.append(get_upper_bound_expectation_by_monte_carlo(artifact_sample, num_samples, time))
        graduation_criteria_for_all_setting[artifact_type] = graduation_criteria
    lock.release()
    return graduation_criteria_for_all_setting


# 获得所有配置的毕业标准
def get_all_graduation_criteria(num_samples: int, time_threshold=[9, 18, 36, 108]):
    graduation_criteria_for_config = {}
    with mp.Pool() as pool:
        async_results = [pool.apply_async(get_graduation_criteria_for_all_setting, (i, num_samples, time_threshold)) for
                         i in range(len(xzs_configs))]
        for i, res in enumerate(async_results):
            graduation_criteria_for_config[i] = res.get()

    with open(os.path.join(parent_dir, "data\\XZSGraduationCriteria.json"), "w", encoding='utf-8-sig') as f:
        json.dump(graduation_criteria_for_config, f)

    return graduation_criteria_for_config


if __name__ == '__main__':
    # plot_probability_distribution_for_config(28)
    pass
