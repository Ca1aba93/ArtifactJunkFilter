import itertools
import multiprocessing as mp
import os

import numpy as np
import pandas as pd

from src.artifact_data_processing import Artifact
from src.basic_data import xzs_multi_factor, half_up, sub_weights, std_artifacts, \
    xzs_configs, artifact_types, get_artifacts_name_by_type
from src.expansion_xzs_config import XZSConfig

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)

lock = mp.Lock()

# 显示所有列
pd.set_option('display.max_columns', None)

# 显示所有行
pd.set_option('display.max_rows', None)


def check_main_stat(artifact_id: int, config_id: int):
    artifact = Artifact(artifact_id)
    config = XZSConfig(config_id)
    if artifact.main_stat in config.standard[artifact.type]['main_stats']:
        return True
    else:
        return False


def check_set(artifact_id: int, config_id: int):
    artifact = Artifact(artifact_id)
    config = XZSConfig(config_id)
    if artifact.set in config.sets_range:
        return True
    else:
        return False


def check_element(artifact_id: int, config_id: int):
    artifact = Artifact(artifact_id)
    config = XZSConfig(config_id)
    if artifact.main_stat == config.element:
        return True
    else:
        return False


def rule_decorator(rule_func):
    rule_decorator.rules.append(rule_func)
    return rule_func


rule_decorator.rules = []


@rule_decorator
def rule_1(artifact_id: int, config_id: int, evaluation_level):
    # 规则 1: 维持原样
    artifact = Artifact(artifact_id)
    config = XZSConfig(config_id)
    return evaluation_level


@rule_decorator
def rule_2(artifact_id: int, config_id: int, evaluation_level):
    # 规则 2: （除杯外）主属性与套装必须正确，否则评级降为0，其中冠的主属性必须是双爆
    # 杯的套装可以不正确，但是主属性必须是元素，并且评级大于1
    artifact = Artifact(artifact_id)
    if artifact.type != 'goblet':
        # print("artifact.type != 'goblet'")
        if not check_main_stat(artifact_id, config_id) or not check_set(artifact_id, config_id):
            # print("not check_main_stat or not check_set")
            evaluation_level = 0
    else:
        # print("type=='goblet'")
        if evaluation_level < 1 or not check_element(artifact_id, config_id):
            # print("evaluation_level < 1 or not check_element")
            evaluation_level = 0
    return evaluation_level


# 对圣遗物-配置对进行定级
def evaluate_artifact_with_xzs_config(artifact_id: int, config_id: int, rule_ids: list):
    def apply_rules(_artifact_id: int, _config_id: int, _evaluation_level: int, _rule_ids: list):
        for rule_id in _rule_ids:
            if 0 <= rule_id < len(rule_decorator.rules):
                _evaluation_level = rule_decorator.rules[rule_id](_artifact_id, _config_id, _evaluation_level)
            return _evaluation_level

    lock.acquire()
    artifact = Artifact(artifact_id)
    config = XZSConfig(config_id)

    sub_stats = artifact.sub_stats
    sub_norms = artifact.norms

    base_score, actual_score = 0, 0
    for i, stat in enumerate(sub_stats):
        stat_score = xzs_multi_factor[stat] * config.weight[stat]
        base_score += stat_score
        actual_score += sub_norms[i] * stat_score

    num_sub_stats = len(artifact.sub_stats)
    available_enhancements = (5 if num_sub_stats == 4 else 4) - artifact.level // 4
    stat_weights = sub_weights.copy()

    for stat in set(sub_stats) | {artifact.main_stat}:
        stat_weights.pop(stat, None)

    if num_sub_stats == 3:
        generatable_stats = set(stat_weights.keys())
        sub_stat4_base = sum(
            (xzs_multi_factor[stat] * config.weight[stat] * stat_weights[stat]) for stat in
            generatable_stats) / sum(
            stat_weights.values())
        base_score += sub_stat4_base
        actual_score += sub_stat4_base

    max_level_expected_score = half_up(actual_score + (available_enhancements / 4) * base_score, 1)
    score_thresholds = config.standard[artifact.type]['score_thresholds']

    for evaluation_level, threshold in enumerate(score_thresholds):
        if max_level_expected_score < threshold:
            break
    else:
        evaluation_level = len(score_thresholds)

    # 利用规则对结果进行微调
    evaluation_level = apply_rules(artifact_id, config_id, evaluation_level, rule_ids)
    lock.release()

    return evaluation_level


# 定义一个辅助函数，用于将参数打包到一个元组中
def evaluate_artifact_with_xzs_config_helper(args):
    return evaluate_artifact_with_xzs_config(*args)


# 获得所有圣遗物-配置的评分矩阵
def evaluate_all_artifacts_and_configs(rule_ids: list):
    artifacts = []
    for art_id in range(len(std_artifacts)):
        artifacts.append(Artifact(art_id).name)

    configs = []
    for config_id in range(len(xzs_configs)):
        configs.append(XZSConfig(config_id).name)

    evaluation_matrix = np.ones((len(artifacts), len(configs)), dtype=int)

    with mp.Pool() as pool:
        arg_list = [(art_id, config_id, rule_ids) for art_id, config_id in
                    itertools.product(range(len(std_artifacts)), range(len(xzs_configs)))]
        results = pool.map(evaluate_artifact_with_xzs_config_helper, arg_list)

        # 将结果填充到评估矩阵中
        for idx, (art_id, config_id) in enumerate(
                itertools.product(range(len(std_artifacts)), range(len(xzs_configs)))):
            evaluation_matrix[art_id][config_id] = results[idx]

    evaluation_df = pd.DataFrame(evaluation_matrix, index=artifacts, columns=configs)

    return evaluation_df


def get_selected_configs(config_indices: set):
    tuples_list = []
    for config_id in config_indices:
        tuples_list.append(XZSConfig(config_id).ranking)
    sorted_tuples = sorted(tuples_list, key=lambda x: (x[0], -x[1]))
    sorted_names = [t[2] for t in sorted_tuples]
    return sorted_names


# 给配置的部位分配圣遗物
def assign_artifact_to_config_slot(config_name, artifact_type, evaluation_df, available_artifacts, assigned_artifacts,
                                   type_counters):
    artifacts_name_by_type = get_artifacts_name_by_type(artifact_type)
    available_indices = available_artifacts.index.intersection(artifacts_name_by_type)

    if not available_indices.empty:
        type_evaluation_series = evaluation_df.loc[available_indices, config_name]
        max_rating = type_evaluation_series.max()

        if max_rating > 0:
            max_rating_indices = type_evaluation_series[type_evaluation_series == max_rating].index
            selected_index = max_rating_indices.to_series().sample(n=1).iloc[0]
            artifact_index = selected_index
            assigned_artifacts[config_name][artifact_type].append(artifact_index)
            available_artifacts.loc[artifact_index] = False
            evaluation_df.loc[artifact_index, :] = 0
            type_counters[config_name][artifact_type] += 1
            return True

    return False


# 为配置分配圣遗物
def assign_artifacts_to_selected_configs(evaluation_df, selected_configs, threshold):
    configs_name = []
    for config_id in range(len(xzs_configs)):
        configs_name.append(XZSConfig(config_id).name)
    if not selected_configs:
        selected_configs = configs_name

    selected_evaluation_df = evaluation_df[selected_configs].copy()

    assigned_artifacts = {config_name: {artifact_type: [] for artifact_type in artifact_types} for config_name in
                          selected_configs}
    type_counters = {config_name: {artifact_type: 0 for artifact_type in artifact_types} for config_name in
                     selected_configs}
    type_limits = {config_name: {artifact_type: 1 for artifact_type in artifact_types} for config_name in
                   selected_configs}

    max_ratings = selected_evaluation_df.max(axis=1)
    available_artifacts = max_ratings >= threshold

    while available_artifacts.any():
        any_artifact_assigned = False

        for config_name, artifact_type in itertools.product(selected_configs, artifact_types):
            if type_counters[config_name][artifact_type] < type_limits[config_name][artifact_type]:
                artifact_assigned = assign_artifact_to_config_slot(config_name, artifact_type, selected_evaluation_df,
                                                                   available_artifacts, assigned_artifacts,
                                                                   type_counters)
                any_artifact_assigned |= artifact_assigned

        if not any_artifact_assigned:
            for config_name in selected_configs:
                for artifact_type in artifact_types:
                    if type_counters[config_name][artifact_type] == type_limits[config_name][artifact_type]:
                        type_limits[config_name][artifact_type] += 1

    return assigned_artifacts


def artifacts_above_threshold(evaluation_df, threshold):
    max_artifact_ratings = evaluation_df.max(axis=1)
    qualified_artifacts = max_artifact_ratings[max_artifact_ratings >= threshold]

    artifact_summary = {}
    for score in range(5):
        artifact_summary[score] = {
            '数量': (max_artifact_ratings == score).sum(),
            '占比': f"{100 * (max_artifact_ratings == score).mean():.1f}%"
        }

    print("圣遗物评分统计：")
    for score in range(5):
        print(f"评分 {score}: 数量={artifact_summary[score]['数量']}, 占比={artifact_summary[score]['占比']}")

    qualified_config_results = {}
    for artifact_name, artifact_rating in qualified_artifacts.items():
        configs = evaluation_df.loc[artifact_name][evaluation_df.loc[artifact_name] >= threshold].index.tolist()
        if configs:
            qualified_config_results[artifact_name] = {
                'final_score': artifact_rating,
                'configs': configs
            }

    print("符合条件的圣遗物及其配置：")
    for artifact_name, artifact_data in qualified_config_results.items():
        print(f"圣遗物 {artifact_name}: 最终评分={artifact_data['final_score']}, 配置={artifact_data['configs']}")

    return qualified_config_results


def configs_with_qualified_artifacts(evaluation_df, threshold):
    qualified_artifacts_mask = evaluation_df >= threshold

    qualified_artifacts_by_config = {}
    for config_name in evaluation_df.columns:
        artifacts = evaluation_df.index[qualified_artifacts_mask[config_name]].tolist()
        if artifacts:
            qualified_artifacts_by_config[config_name] = artifacts

    print("各配置下符合条件的圣遗物：")
    for config_name, artifacts in qualified_artifacts_by_config.items():
        print(f"配置 {config_name}: 圣遗物={artifacts}")

    return qualified_artifacts_by_config


if __name__ == "__main__":
    pass
