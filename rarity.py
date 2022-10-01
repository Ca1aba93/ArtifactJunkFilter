import copy
import math
import os
from itertools import combinations, permutations

import pandas as pd

proDir = os.path.split(os.path.realpath(__file__))[0]

with open(proDir + '/config/weight.csv', 'r', encoding='utf8') as file:
    weight_temp = pd.read_csv(file)
weights_df = weight_temp.set_index('position')  # 重设索引，获得权重DataFrame二维数据表
raw_sec_weights = weights_df.loc['secondary'].dropna(inplace=False)  # 得到原始副属性权重列


def probability_of_sec(sec_attribute: list, corresponded_sec: pd.Series):
    """
    副属性词条出现概率计算
    sec_attribute: 需要计算的副属性词条
    corresponding_sec: 【对应的】的可选副属性权重词条，只能在全部副属性权重中排除主属性
    """
    all_comb = list(permutations(sec_attribute, len(sec_attribute)))  # 求出所有的排列
    p_comb = 0  # 该排列概率从零开始计算
    for attributeComb in all_comb:
        p_ind = 1  # 对应特定排列，概率从1开始计算
        sec = copy.deepcopy(corresponded_sec)  # 深copy，防止数据污染
        for attribute in attributeComb:  # 按顺序不放回计算
            p_ind *= sec[attribute] / sec.values.sum()
            sec = sec.drop(attribute)  # 不放回
        p_comb += p_ind  # 将特定排列加总到最后的概率上
    return p_comb


def expect_of_artifact(artifact_attribute: list):
    """
    输入圣遗物的属性，计算该圣遗物的稀有度
    [部位，初始词条数，主属性，副属性1，副属性2，...]
    """
    p = 1  # 圣遗物初始概率为1
    main_weight = weights_df.loc[artifact_attribute[0]].dropna(inplace=False)  # 读取对应部位主属性权重
    p *= main_weight[artifact_attribute[2]] / main_weight.values.sum()  # 获得主属性出现概率
    sec_weight = copy.deepcopy(raw_sec_weights)  # 深copy
    if artifact_attribute[2] in sec_weight.index:  # 检测主属性是否在原始副属性列表中
        sec_weight = sec_weight.drop(artifact_attribute[2])  # 如果是，则去除
    p *= probability_of_sec(artifact_attribute[3:], sec_weight)  # 计算副属性出现概率
    # 初始词条数也要折算为概率
    if artifact_attribute[1] == 4:
        p *= 0.2
    elif artifact_attribute[1] == 3:
        p *= 0.8
    elif artifact_attribute[1] == 2:
        p = 1
    return 1 / p


artifact_standard = 3.023554709325051  # 3.02为cup难度系数


def rarity(artifact_attribute: list):
    """接受导出的圣遗物词条，输出圣遗物的稀有度"""
    r = 1
    if artifact_attribute[0] == "flower" or artifact_attribute[0] == "feather":
        r *= math.log(expect_of_artifact(artifact_attribute), artifact_standard)
    elif artifact_attribute[0] == "sand":
        r *= math.log(expect_of_artifact(artifact_attribute), artifact_standard)
    elif artifact_attribute[0] == "cup":
        r *= math.log(expect_of_artifact(artifact_attribute), artifact_standard)
    elif artifact_attribute[0] == "head":
        r *= math.log(expect_of_artifact(artifact_attribute), artifact_standard)
    return r


def probably_sec(valid_sec_attribute: list, corresponded_sec: pd.Series):
    """
    输入处理好的副词条属性（既已经删除掉出现过得主属性），获取在初始3、4词条下毕业的概率
    processed_sec：经过处理的build所需要的副词条（需要去掉主属性已经存在的）
    corresponding_sec: 【对应的】的可选副属性权重词条
    """
    # 首先将有效词条从可选词条中排出
    optional_sec = corresponded_sec.index.tolist()  # 从这里选择补充的词条组
    for validAttribute in valid_sec_attribute:
        if validAttribute in optional_sec:
            optional_sec.remove(validAttribute)
    p = 0
    if len(valid_sec_attribute) == 0:
        p = 1
    elif len(valid_sec_attribute) < 4:
        # 首先计算三词条概率
        add_esc_comb = list(combinations(optional_sec, 3 - len(valid_sec_attribute)))  # 为了达成3词条要添加的词条组合
        temp = 0
        for addComb in add_esc_comb:
            three_word_comb = valid_sec_attribute + list(addComb)  # 所有可能的三词条组合
            temp += 0.8 * probability_of_sec(three_word_comb, corresponded_sec)
        p += temp / len(add_esc_comb)
        # 其次计算四词条概率
        add_esc_comb = list(combinations(optional_sec, 4 - len(valid_sec_attribute)))  # 为了达成3词条要添加的词条组合
        temp = 0
        for addComb in add_esc_comb:
            four_word_comb = valid_sec_attribute + list(addComb)  # 所有可能的4词条组合
            temp += 0.2 * probability_of_sec(four_word_comb, corresponded_sec)
        p += temp / len(add_esc_comb)
    elif len(valid_sec_attribute) == 4:
        p = probability_of_sec(valid_sec_attribute, corresponded_sec)
    elif len(valid_sec_attribute) > 4:
        # 大于四有效词条的build选取最小的四个权重词条即可
        sorted_sec = corresponded_sec.filter(valid_sec_attribute).sort_values()  # 以有效属性筛选权重并排序
        pointer = 0  # 指针，若5个属性权重均为100，则从第一个开始
        for i in range(len(sorted_sec) - 1):
            if sorted_sec[i] < sorted_sec[i + 1]:  # 指出权重变为100的点
                pointer = i + 1
                break
        add_esc_comb = list(combinations(sorted_sec[pointer:].index, 4 - pointer))  # 为了达成4词条要添加的词条组合
        temp = 0
        for addComb in add_esc_comb:
            four_word_comb = sorted_sec[0:pointer].index.tolist() + list(addComb)  # 所有可能的4词条组合
            temp += 0.2 * probability_of_sec(four_word_comb, corresponded_sec)
        p += temp / len(add_esc_comb)
    return p


def rarity_of_build(eff_main: list, eff_sec: list):
    """
    输入build有效词条，分部位输出完美毕业所需的稀有度
    eff_main:[部位，主属性1，...]
    eff_sec:[副属性1，副属性2，...]
    """
    p = 1  # 圣遗物初始概率为1
    main_weight = weights_df.loc[eff_main[0]].dropna(inplace=False)  # 读取对应部位主属性权重
    p *= main_weight[eff_main[1]] / main_weight.values.sum()  # 主属性权重
    if len(eff_main) > 2:
        p *= 2
    sec = copy.deepcopy(eff_sec)
    sec_weight = copy.deepcopy(raw_sec_weights)
    if eff_main[1] in sec:  # 检测主属性是否在有效副属性列表中
        sec.remove(eff_main[1])  # 如果是，则删除
    if eff_main[1] in sec_weight:  # 检测主属性是否在有效副属性列表中
        sec_weight = sec_weight.drop(eff_main[1])  # 如果是，则删除
    p *= probably_sec(sec, sec_weight)  # 计算副属性出现概率
    e = 1 / p
    r = 1
    if eff_main[0] == "flower" or eff_main[0] == "feather":
        r *= math.log(e, artifact_standard)
    elif eff_main[0] == "sand":
        r *= math.log(e, artifact_standard)
    elif eff_main[0] == "cup":
        r *= math.log(e, artifact_standard)
    elif eff_main[0] == "head":
        r *= math.log(e, artifact_standard)
    return r


if __name__ == '__main__':
    pass
