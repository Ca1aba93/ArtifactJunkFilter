import json
import os

from src.basic_data import stats_data, type_config, sets_data, set_decimal, substat_average, find_enhancement_count, \
    adjust_enhancement_counts

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)

# mona格式数据
with open(os.path.join(parent_dir, 'mona.json'), 'r', encoding='utf-8-sig') as file:
    raw_mona_data = json.load(file)
mona_artifacts = raw_mona_data.get("flower") + raw_mona_data.get("feather") + raw_mona_data.get("sand") + \
                 raw_mona_data.get("cup") + raw_mona_data.get("head")


# 从mona格式到id的查找函数
def mona_id(mona_format: str):
    mona_to_id_raw_data = stats_data + type_config + sets_data
    result_dict = [d for d in mona_to_id_raw_data if d['mona_format'] == mona_format][0]
    result = result_dict['id']
    return result


# 将单个mona格式的圣遗物数据转化为标准格式
def convert_mona_to_standard_format(idx):
    mona_art = mona_artifacts[idx]
    std_artifact = {
        "index": idx,
        "name": f"artifact_{idx + 1}",
        "set": mona_id(mona_art['setName']),
        "type": mona_id(mona_art['position']),
        "level": mona_art['level'],
        "rarity": mona_art['star'],
        "locked": mona_art['omit'],
        "equipped": "",
        "main_stat": mona_id(mona_art['mainTag']['name']),
        "sub_stats": [],
        "sub_values": []
    }
    sub_stats_data = mona_art['normalTags']
    for sub_stat in sub_stats_data:
        std_artifact['sub_stats'].append(mona_id(sub_stat['name']))
        std_artifact['sub_values'].append(set_decimal(sub_stat['value']))

    norms = []
    enhancement_count_list = []
    for stat_idx, sub_stat in enumerate(std_artifact['sub_stats']):
        norms.append(std_artifact['sub_values'][stat_idx] / substat_average[sub_stat])
        enhancement_count_list.append(find_enhancement_count(sub_stat, std_artifact['sub_values'][stat_idx]))

    std_artifact['norms'] = norms
    std_artifact['initial_num'], std_artifact['enhancement_count'] = adjust_enhancement_counts(enhancement_count_list,
                                                                                               std_artifact['level'])
    return std_artifact


# 将全部mona格式圣遗物数据转化为标准格式并储存
def convert_mona_to_standard_for_all():
    standard_artifacts = []
    names_by_type = {
        'flower': [],
        'plume': [],
        'sands': [],
        'goblet': [],
        'circlet': []
    }
    for idx, mona_art in enumerate(mona_artifacts):
        if mona_art['star'] != 5:
            continue  # Exclude 4-star artifacts
        standard_artifacts.append(convert_mona_to_standard_format(idx))
        names_by_type[mona_id(mona_art['position'])].append(convert_mona_to_standard_format(idx)['name'])
    with open(os.path.join(parent_dir, "data", "StandardizedArtifactsData.json"), "w", encoding='utf-8-sig') as f:
        json.dump(standard_artifacts, f)
    with open(os.path.join(parent_dir, "data", "ArtifactsNameByType.json"), "w", encoding='utf-8-sig') as f:
        json.dump(names_by_type, f)
    print("已将mona.json数据转化为标准格式")
    return


if __name__ == "__main__":
    pass
