import copy
import os

import pandas as pd

from dict import set_simple, main_simple, eff_simple
from rarity import rarity_of_build

proDir = os.path.split(os.path.realpath(__file__))[0]

with open(proDir + '/config/build.csv', 'r', encoding='utf8') as file:
    raw_build_data = pd.read_csv(file)
with open(proDir + '/config/position_weights.csv', 'r', encoding='utf8') as file:
    raw_position_weights = pd.read_csv(file)
score_weights = raw_position_weights.set_index('position')  # 评分权重
positions = ['flower', 'feather', 'sand', 'cup', 'head']


def expand(build: pd.Series):
    temp = build.fillna(value=0)
    # 获得buildName
    if temp[3] == 0:
        set_name = temp[2]
    else:
        set_name = '{}、{}'.format(temp[2], temp[3])
    if temp[1] == 0:
        build_name = '{}--{}--<{}{}{}>'.format(temp[0], set_name, temp[4], temp[5], temp[6])
    else:
        build_name = '{}--{}--{}--<{}{}{}>'.format(temp[0], temp[1], set_name, temp[4], temp[5], temp[6])
    expanded_build = pd.Series(build_name, index=['buildName'])
    # 获得sets
    sets = []
    sets += set_simple[temp[2]]
    if temp[3] != 0:
        sets += set_simple[temp[3]]
    expanded_build['sets'] = sets
    # 获得各部位主属性列表
    flower_main_att = ['flower', 'lifeStatic']
    feather_main_att = ['feather', 'attackStatic']
    sand_main_att = ['sand'] + main_simple[build[4]]
    cup_main_att = ['cup'] + main_simple[build[5]]
    head_main_att = ['head'] + main_simple[build[6]]
    # 生成有效属性列表
    temp = build[7:14].dropna(inplace=False).index.tolist()
    eff_attribute = []
    for simple in temp:
        eff_attribute.append(eff_simple[simple])
    # 生成build毕业难度列表
    expanded_build['flowerDifficulty'] = rarity_of_build(flower_main_att, eff_attribute)
    expanded_build['featherDifficulty'] = rarity_of_build(feather_main_att, eff_attribute)
    expanded_build['sandDifficulty'] = rarity_of_build(sand_main_att, eff_attribute)
    expanded_build['cupDifficulty'] = rarity_of_build(cup_main_att, eff_attribute)
    expanded_build['headDifficulty'] = rarity_of_build(head_main_att, eff_attribute)
    # 生成各部位主属性评分权重 *5
    expanded_build['flowerMainWeights'] = pd.Series([1, 0], index=flower_main_att)
    expanded_build['featherMainWeights'] = pd.Series([1, 0], index=feather_main_att)
    expanded_build['sandMainWeights'] = pd.Series([1, 3.3], index=sand_main_att)
    expanded_build['cupMainWeights'] = pd.Series([1, 3.3], index=cup_main_att)
    if len(head_main_att) == 2:
        expanded_build['headMainWeights'] = pd.Series([1, 3.3], index=head_main_att)
    else:
        expanded_build['headMainWeights'] = pd.Series([1, 3.3, 3.3], index=head_main_att)
    # 各部位主属性评分权重补完 *3
    for position in positions[2:]:
        temp = '{}MainWeights'.format(position)
        inborn = copy.deepcopy(score_weights.loc[position]).dropna()
        for eff in eff_attribute:  # 对于每一个有效属性
            if eff in expanded_build[temp]:  # drop掉存在于已有权重中的对应【固有】主属性
                inborn.drop(eff, inplace=True)
        for att in inborn.index.tolist():  # 对每一个固有主属性（已经去掉已有权重的）
            if att not in eff_attribute:  # 如果它不存在于有效属性中，则drop掉
                inborn.drop(att, inplace=True)
        expanded_build[temp] = pd.concat([expanded_build[temp], inborn])
    # 生成副属性评分权重
    temp_sec = copy.deepcopy(score_weights.loc['sec']).dropna()
    for att in temp_sec.index.tolist():
        if att not in eff_attribute:  # 如果它不存在于有效属性中，则drop掉
            temp_sec.drop(att, inplace=True)
    expanded_build['secWeights'] = temp_sec
    # 计算最佳得分
    for position in positions:
        temp = '{}MainWeights'.format(position)
        eff_main = expanded_build[temp][1:2]
        sec = copy.deepcopy(score_weights.loc['sec']).dropna()
        for att in sec.index.tolist():  # 对每一个固有主属性（已经去掉已有权重的）
            if att not in eff_attribute:  # 如果它不存在于有效属性中，则drop掉
                sec.drop(att, inplace=True)
        for att in sec.index.tolist():  # 对每一个固有主属性（已经去掉已有权重的）
            if att in eff_main:  # 如果它存在于主属性中，则drop掉
                sec.drop(att, inplace=True)
        if len(sec) > 4:
            full_sec = sec.sort_values(ascending=False)[0:4]
        else:
            full_sec = sec.sort_values(ascending=False)
        best_att = pd.concat([eff_main, full_sec])
        best_score = eff_main[0] + 1.176 * full_sec.sum()
        expanded_build['best_{}'.format(position)] = best_score
    # 返回
    return expanded_build


all_build_amount = 0
for i in raw_build_data.index:
    if type(raw_build_data.iloc[i]['角色']) != str:
        all_build_amount = i
        break


print('正在展开build......')
d = {}
build_amount = 0
for i in range(all_build_amount):
    if raw_build_data.iloc[i]['启用'] == 'yes':
        d[build_amount] = expand(raw_build_data.iloc[i])
        build_amount += 1
build_df = pd.DataFrame(d)
build_df.to_json(path_or_buf=proDir + '/config/expend_build.json', force_ascii=False)
print('展开完成.')

if __name__ == '__main__':
    pass
