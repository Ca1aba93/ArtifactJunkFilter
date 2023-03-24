import itertools
import json
import os
from decimal import Decimal, ROUND_HALF_UP

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)

# 不可更改游戏配置数据
with open(os.path.join(parent_dir, "data\\CharactersData.json"), 'r', encoding='utf-8-sig') as file:
    char_data = json.load(file)
with open(os.path.join(parent_dir, "data\\SetsData.json"), 'r', encoding='utf-8-sig') as file:
    sets_data = json.load(file)
with open(os.path.join(parent_dir, "data\\StatsData.json"), 'r', encoding='utf-8-sig') as file:
    stats_data = json.load(file)
with open(os.path.join(parent_dir, "data\\XiaoZhuShouConfig.json"), 'r', encoding='utf-8-sig') as file:
    xzs_configs = json.load(file)
with open(os.path.join(parent_dir, "data\\ArtifactTypeConfig.json"), 'r', encoding='utf-8-sig') as file:
    type_config = json.load(file)

# 计算生成
with open(os.path.join(parent_dir, "data\\XZSGraduationCriteria.json"), 'r', encoding='utf-8-sig') as file:
    xzs_criteria = json.load(file)

# 随圣遗物改变
with open(os.path.join(parent_dir, "data\\StandardizedArtifactsData.json"), 'r', encoding='utf-8-sig') as file:
    std_artifacts = json.load(file)
with open(os.path.join(parent_dir, "data\\ArtifactsNameByType.json"), 'r', encoding='utf-8-sig') as file:
    artifacts_name_by_type = json.load(file)

# 小助手速算乘数:
# 小助手的评分算法是：副词条得分 = 数值 * 均衡乘数 * 收益权重，例如暴击的均衡乘数是2，收益权重是100
# 现改为 得分 = (数值/词条均值) * (均衡乘数*词条均值) * 收益权重 即 归一化值 * 速算乘数 * 收益权重
# 将词条归一化后乘以对应速算乘数 再加权即可得到最终评分
xzs_multi_factor = {'atk': 0.03290465, 'atk%': 0.0659015, 'cd': 0.06605, 'cr': 0.0661,
                    'def': 0.043501424999999996, 'def%': 0.065667, 'em': 0.0653895,
                    'er': 0.065944395, 'hp': 0.043576104, 'hp%': 0.0659015}

sub_weights = {'hp': 150, 'atk': 150, 'def': 150, 'hp%': 100, 'atk%': 100,
               'def%': 100, 'er': 100, 'em': 100, 'cr': 75, 'cd': 75}

all_substats = {'atk%', 'def', 'atk', 'hp', 'em', 'def%', 'hp%', 'cr', 'er', 'cd'}

main_weights = {
    "flower": {'hp': 1000},
    "plume": {'atk': 1000},
    "sands": {'hp%': 1334, 'atk%': 1333, 'def%': 1333, 'em': 500, 'er': 500},
    "goblet": {'hp%': 767, 'atk%': 766, 'def%': 767, 'em': 100, 'pyro%': 200, 'electro%': 200, 'cryo%': 200,
               'hydro%': 200, 'dendro%': 200, 'anemo%': 200, 'geo%': 200, 'physical%': 200},
    "circlet": {'hp%': 1100, 'atk%': 1100, 'def%': 1100, 'em': 200, 'cr': 500, 'cd': 500, 'hb': 500}}

artifact_types = {'flower', 'plume', 'sands', 'goblet', 'circlet'}

substat_average = {'hp': 253.94000244140625, 'hp%': 0.04954999964684248, 'atk': 16.535000324249268,
                   'atk%': 0.04954999964684248, 'def': 19.675000190734863, 'def%': 0.06194999907165766,
                   'cr': 0.03304999973624945, 'cd': 0.06604999862611294, 'er': 0.05505000054836273,
                   'em': 19.8149995803833}


# 由副词条数值推断强化次数
def find_enhancement_count(substat_id: str, given_value: float or int):
    if substat_id == 'null':
        return [0]
    tiers = ['tier1', 'tier2', 'tier3', 'tier4']
    # 找到副词条对应的数值词典，其中有一二三四档可生成值，仅限五星圣遗物
    substat_values = [data for data in stats_data if data['id'] == substat_id][0]['sub_value']
    enhancement_counts_and_values = {}
    # 构造词典
    for enhancement_count in range(1, 7):
        # 构造强化n次的所有可能的组合，单个词条强化次数上限为6次，所以取1-6次
        enhancement_value_set = set()
        all_combinations = list(itertools.combinations_with_replacement(tiers, enhancement_count))
        for combination in all_combinations:
            combined_sum = set_decimal(sum(substat_values[tier] for tier in combination))
            enhancement_value_set.add(combined_sum)
        enhancement_counts_and_values[enhancement_count] = enhancement_value_set

    # 进行查询
    temp_value = set_decimal(given_value)
    min_difference = float('inf')
    closest_counts = []

    for count, values_set in enhancement_counts_and_values.items():
        for value in values_set:
            difference = abs(temp_value - value)
            if difference < min_difference:
                min_difference = difference
                closest_counts = [count]
            elif difference == min_difference:
                closest_counts.append(count)

    return sorted(closest_counts)


# 根据4个词条的强化次数推断初始分布（总是选取最低次数）
def adjust_enhancement_counts(count_list: list, level: int):
    if len(count_list) == 3:
        count_list.append([0])

    min_count = 0
    for count in count_list:
        min_count += count[0]
    initial_count = min_count - level // 4

    if initial_count < 3:
        for count in count_list:
            if len(count) == 2:
                count.pop(0)
                initial_count += 1
                if initial_count == 3:
                    break
    result_list = []
    for count in count_list[:-1]:
        result_list.append([1, count[0] - 1])
    if initial_count == 3 and count_list[3][0] == 0:
        result_list.append([0, 0])
    else:
        result_list.append([1, count_list[3][0] - 1])
    return initial_count, result_list


# 将id格式到中文的查找函数
def id_chs(the_id: str):
    id_to_chs_raw_data = char_data + sets_data + stats_data + type_config
    result_dict = [d for d in id_to_chs_raw_data if d['id'] == the_id][0]
    result = result_dict['chs']
    return result


# 根据套装中文名获得套装的配置
def set_config(set_name_chs: str):
    result = [d for d in sets_data if d['chs'] == set_name_chs][0]
    return result


# 根据部位获取该部位允许的主词条
def get_allowed_main_stats(equip_type: str):
    result = [d for d in type_config if d['id'] == equip_type][0]['allow_main_stats']
    return set(result)


# 优化数据输出格式
def output_value(the_value: int or float):
    if the_value > 1:
        result = str(int(Decimal(str(the_value)).quantize(Decimal("0"), rounding=ROUND_HALF_UP)))
    else:
        result = str(float(Decimal(str(the_value * 100)).quantize(Decimal("0.0"), rounding=ROUND_HALF_UP))) + '%'
    return result


# 根据装备类型获得该类型的所有圣遗物编号
def get_artifacts_name_by_type(equip_type: str):
    return artifacts_name_by_type[equip_type]


# 获得小助手对应序列号的原始配置
def get_config_of_xzs(config_index: int):
    result = [d for d in xzs_configs if d['index'] == config_index][0]
    return result


# 根据索引名获得小助手的毕业标准
def get_criteria(config_index: int):
    result = xzs_criteria[str(config_index)]
    return result


# 获得正确的四舍五入值
def half_up(the_value: float, digit: int):
    temp = f"0.{digit * '0'}"
    result = float(Decimal(str(the_value)).quantize(Decimal(temp), rounding=ROUND_HALF_UP))
    return result


# 精度处理
def set_decimal(stat_value: float):
    if stat_value >= 1:
        temp2 = Decimal(str(stat_value)).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
        res = int(Decimal(str(temp2)).quantize(Decimal("0"), rounding=ROUND_HALF_UP))
    else:
        temp5 = Decimal(str(stat_value)).quantize(Decimal("0.00000"), rounding=ROUND_HALF_UP)
        temp4 = Decimal(str(temp5)).quantize(Decimal("0.0000"), rounding=ROUND_HALF_UP)
        res = float(Decimal(str(temp4)).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP))
    return res


def set_decimal_for_good(stat_id: str, temp_res: float):
    if stat_id in {'atk%', 'def%', 'hp%', 'cr', 'er', 'cd'}:
        temp_res = temp_res / 100
    else:
        temp_res = temp_res
    if temp_res >= 1:
        temp2 = Decimal(str(temp_res)).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
        res = int(Decimal(str(temp2)).quantize(Decimal("0"), rounding=ROUND_HALF_UP))
    else:
        temp5 = Decimal(str(temp_res)).quantize(Decimal("0.00000"), rounding=ROUND_HALF_UP)
        temp4 = Decimal(str(temp5)).quantize(Decimal("0.0000"), rounding=ROUND_HALF_UP)
        res = float(Decimal(str(temp4)).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP))
    return res


if __name__ == "__main__":
    pass
