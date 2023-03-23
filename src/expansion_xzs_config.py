import io

from src.basic_data import get_config_of_xzs, char_data, stats_data, set_config, id_chs, xzs_multi_factor, \
    get_allowed_main_stats, sub_stats_for_all, sub_weights, get_criteria


class XZSConfig:

    def __init__(self, config_id: int):
        config = get_config_of_xzs(config_id)
        self.id = config['index']
        self.name = f"xzs_{config_id + 1}"
        self.char_chs = config['char_chs']
        char_data_item = next((data for data in char_data if data['chs'] == self.char_chs), None)
        self.char = char_data_item['id']
        element_data = next((data for data in stats_data if data['en'] == char_data_item['element']), None)
        self.element_chs = element_data['chs']
        self.element = element_data['id']
        self.sets_range = {set_config(config['set1'])['id']}
        self.sets_chs = {id_chs(set_config(config['set1'])['id'])}
        if config['set2'] is not None:
            self.sets_range.add(set_config(config['set2'])['id'])
            self.sets_chs.add(id_chs(set_config(config['set2'])['id']))
        self.weight = {
            'hp%': config['hp%'], 'atk%': config['atk%'], 'def%': config['def%'],
            'cr': config['cr'], 'cd': config['cd'], 'em': config['em'], 'er': config['er'],
            'atk': config['atk'], 'hp': config['hp'], 'def': config['def']
        }
        self.target_stats = {key for key, value in self.weight.items() if value != 0}
        self.target_stats.add(self.element)
        if char_data_item['is_heal']:
            self.target_stats.add('hb')
        # 排序参数，用来确定分配圣遗物时的先后顺序
        self.ranking = (char_data_item['usage_ranking'], len(self.target_stats), self.name)
        self.target_stats_weight = sorted([(key, value) for key, value in self.weight.items() if value != 0],
                                          key=lambda data: data[1], reverse=True)
        self.target_count = len(self.target_stats_weight)

        sands_main_stats = get_allowed_main_stats('sands') & self.target_stats
        goblet_main_stats = get_allowed_main_stats('goblet') & self.target_stats
        circlet_main_stats = get_allowed_main_stats('circlet') & self.target_stats

        self.standard = {
            "flower": {"main_stats": {'hp'},
                       "score_thresholds": get_criteria(self.id)['flower']},
            "plume": {"main_stats": {'atk'},
                      "score_thresholds": get_criteria(self.id)['plume']},
            "sands": {"main_stats": sands_main_stats,
                      "score_thresholds": get_criteria(self.id)['sands']},
            "goblet": {"main_stats": goblet_main_stats,
                       "score_thresholds": get_criteria(self.id)['goblet']},
            "circlet": {"main_stats": circlet_main_stats,
                        "score_thresholds": get_criteria(self.id)['circlet']},
        }

    def __str__(self):
        output = io.StringIO()
        output.write(
            f"配置名: {self.name.capitalize()} | 适用角色: {self.char_chs} | 可选套装: {self.sets_chs} | 适用元素: {self.element_chs}\n")
        output.write(f"目标词条: {self.target_stats}\n")
        output.write(f"目标词条权重: {self.target_stats_weight}\n")
        output.write("配置标准:\n")
        for artifact_type, artifact_standard in self.standard.items():
            output.write(f"{id_chs(artifact_type)}: {artifact_standard}\n")
        return output.getvalue()

    def get_expected_score(self, stats_type: tuple):
        main_stat = stats_type[0]
        sub_stats = stats_type[1:]
        allowed_sub_stats = sub_stats_for_all.copy()
        allowed_sub_stats.discard(main_stat)
        sub_weight = sub_weights.copy()
        sub_weight.pop(main_stat, None)

        max_level_expected_score = 0
        for stat in sub_stats:
            max_level_expected_score += xzs_multi_factor[stat] * self.weight[stat]
            allowed_sub_stats.discard(stat)
            sub_weight.pop(stat)
        # 计算第四词条的期望
        if len(sub_stats) == 3:
            for stat in allowed_sub_stats:
                p = sub_weight[stat] / sum(sub_weight.values())
                max_level_expected_score += p * xzs_multi_factor[stat] * self.weight[stat]
            max_level_expected_score *= 2
        else:
            max_level_expected_score *= 2.25
        return max_level_expected_score


if __name__ == "__main__":
    pass
