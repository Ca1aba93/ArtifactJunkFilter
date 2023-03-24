import json
import os

from src.basic_data import stats_data, type_config, sets_data, substat_average, find_enhancement_count, \
    adjust_enhancement_counts, char_data, set_decimal_for_good

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)

# good格式数据
with open(os.path.join(parent_dir, 'good.json'), 'r', encoding='utf-8-sig') as file:
    raw_good_data = json.load(file)

good_artifacts = raw_good_data['artifacts']


# 从good格式到id的查找函数
def good_id(search_key: str):
    good_to_id_raw_data = stats_data + type_config + sets_data + char_data
    try:
        result_dict = next((item for item in good_to_id_raw_data if item['good_format'] == search_key))
        result = result_dict['id']
    except StopIteration:
        result = ""
    return result


# 将单个good格式的圣遗物数据转化为标准格式
def convert_good_to_standard_format(idx):
    good_art = good_artifacts[idx]
    std_artifact = {
        "index": idx,
        "name": f"artifact_{idx + 1}",
        "set": good_id(good_art['setKey']),
        "type": good_id(good_art['slotKey']),
        "level": good_art['level'],
        "rarity": good_art['rarity'],
        "locked": good_art['lock'],
        "equipped": good_art['location'],
        "main_stat": good_id(good_art['mainStatKey']),
        "sub_stats": [],
        "sub_values": []
    }
    sub_stats_data = good_art['substats']
    for sub_stat in sub_stats_data:
        std_artifact['sub_stats'].append(good_id(sub_stat['key']))
        std_artifact['sub_values'].append(set_decimal_for_good(good_id(sub_stat['key']), sub_stat['value']))

    norms = []
    enhancement_count_list = []
    for stat_idx, sub_stat in enumerate(std_artifact['sub_stats']):
        norms.append(std_artifact['sub_values'][stat_idx] / substat_average[sub_stat])
        enhancement_count_list.append(find_enhancement_count(sub_stat, std_artifact['sub_values'][stat_idx]))

    std_artifact['norms'] = norms
    std_artifact['initial_num'], std_artifact['enhancement_count'] = adjust_enhancement_counts(enhancement_count_list,
                                                                                               std_artifact['level'])
    return std_artifact


# 将全部good格式圣遗物数据转化为标准格式并储存
def convert_good_to_standard_for_all():
    standard_artifacts = []
    names_by_type = {
        'flower': [],
        'plume': [],
        'sands': [],
        'goblet': [],
        'circlet': []
    }
    for idx, good_art in enumerate(good_artifacts):
        if good_art['rarity'] != 5:
            continue  # Exclude 4-star artifacts
        standard_artifacts.append(convert_good_to_standard_format(idx))
        names_by_type[good_id(good_art['slotKey'])].append(convert_good_to_standard_format(idx)['name'])
    with open(os.path.join(parent_dir, "data\\StandardizedArtifactsData.json"), "w", encoding='utf-8-sig') as f:
        json.dump(standard_artifacts, f)
    with open(os.path.join(parent_dir, "data\\ArtifactsNameByType.json"), "w", encoding='utf-8-sig') as f:
        json.dump(names_by_type, f)
    print("已将good.json数据转化为标准格式！")
    return


if __name__ == "__main__":
    convert_good_to_standard_for_all()
