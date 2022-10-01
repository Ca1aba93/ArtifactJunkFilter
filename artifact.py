import json
import os

import pandas as pd
from jsonpath import jsonpath

from dict import set_dict, attribute_dict, position_dict
from rarity import rarity

proDir = os.path.split(os.path.realpath(__file__))[0]

with open(proDir + '/mona.json', 'r', encoding='utf8') as jd:
    art_data = json.load(jd)

artifacts = jsonpath(art_data, "$.flower[*]") + jsonpath(art_data, "$.feather[*]") + \
            jsonpath(art_data, "$.sand[*]") + jsonpath(art_data, "$.cup[*]") + jsonpath(art_data, "$.head[*]")
positions = ['flower', 'feather', 'sand', 'cup', 'head']


class Artifact:
    def __init__(self):
        self.abstract = None
        self.star = None
        self.set = None
        self.set_chs = None
        self.position = None
        self.position_chs = None
        self.level = None
        self.main = pd.Series([], dtype='float64')
        self.raw_sec = pd.Series([], dtype='float64')
        self.main_chs = None
        self.sec_chs = None
        self.sec = pd.Series([], dtype='float64')  # 副词条归一化
        self.rarity = 0

    def read(self, art_dict: dict):
        self.star = art_dict['star']
        self.set = art_dict['setName']
        self.set_chs = jsonpath(set_dict, "$.{}".format(self.set))[0]["chs"]
        self.position = art_dict['position']
        self.position_chs = position_dict[self.position]
        self.level = art_dict['level']
        self.abstract = '{}星 {} {}; 等级:{}'.format(self.star, self.set_chs, self.position_chs, self.level)
        self.main[jsonpath(art_dict, "$.mainTag.name")[0]] = 1
        self.raw_sec = pd.Series(jsonpath(art_dict, "$.normalTags[*].value"),
                                 index=jsonpath(art_dict, "$.normalTags[*].name"))
        self.main_chs = '主属性为:' + '【{}】'.format(jsonpath(attribute_dict, "$.{}.chs".format(self.main.index[0]))[0])
        sec_index = []
        for i in range(len(self.raw_sec.index.tolist())):
            sec_index += [jsonpath(attribute_dict, "$.{}.chs".format(self.raw_sec.index[i]))[0]]
        temp_sec_chs = pd.Series(self.raw_sec.values, index=sec_index)
        self.sec_chs = '副属性为: '
        for i in range(len(temp_sec_chs)):
            if temp_sec_chs[i] < 1:
                self.sec_chs += '{}--{}; '.format(temp_sec_chs.index[i], '{:.1%}'.format(temp_sec_chs[i]))
            else:
                self.sec_chs += '{}--{}; '.format(temp_sec_chs.index[i], '{:.0f}'.format(temp_sec_chs[i]))
        for i in range(len(self.raw_sec)):
            self.sec[self.raw_sec.index[i]] = \
                self.raw_sec[i] / jsonpath(attribute_dict, "$.{}.average".format(self.raw_sec.index[i]))[0]
        if self.level < 8 and self.star >= 4:  # 筛选合格的胚子
            if len(self.sec) == 3:  # 初始3词缀
                rarity_list = [self.position, 3] + self.main.index.tolist() + self.sec.index.tolist()
                self.rarity = rarity(rarity_list)
            elif len(self.sec) == 4:
                if self.star < 4:  # 初始4词缀
                    rarity_list = [self.position, 3] + self.main.index.tolist() + self.sec.index.tolist()
                    self.rarity = rarity(rarity_list)
                elif self.star >= 4:
                    max_normalize = self.sec.max()  # 归一值中的最大值
                    if max_normalize > 1.2:  # 大于1.2，初始4词条
                        rarity_list = [self.position, 4] + self.main.index.tolist() + self.sec.index.tolist()
                        self.rarity = rarity(rarity_list)
                    else:  # 小于1.2，初始3词条
                        rarity_list = [self.position, 4] + self.main.index.tolist() + self.sec.index.tolist()
                        self.rarity = rarity(rarity_list)


if __name__ == '__main__':
    pass
