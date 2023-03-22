import io
import os

from src.basic_data import stats_data, std_artifacts, sets_data, id_chs, output_value

current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)


class Artifact:

    def __init__(self, artifact_id: int):
        artifact = std_artifacts[artifact_id]
        self.id = artifact['index']
        self.name = artifact['name']
        self.set = artifact['set']
        self.type = artifact['type']
        self.level = artifact['level']
        self.rarity = artifact['rarity']
        self.main_stat = artifact['main_stat']
        self.main_value = [d for d in stats_data if d['id'] == self.main_stat][0]['main_value'][str(self.level)]
        self.sub_stats = artifact['sub_stats']
        self.sub_values = artifact['sub_values']
        self.initial_num = artifact['initial_num']
        self.enhancement_count = artifact['enhancement_count']
        self.norms = artifact['norms']

    def __str__(self):
        output = io.StringIO()
        set_data = [d for d in sets_data if d['id'] == self.set][0]
        the_type_chs = set_data[f"{self.type}_chs"]

        output.write(f"=== {self.name.capitalize()} ===".center(26))
        output.write(f"\n部位: {id_chs(self.type):7}\t{the_type_chs:8}")
        output.write(f"\n套装: {id_chs(self.set):7}\t等级: {self.level}")
        output.write(f"\n初始词条数: {self.initial_num}")
        output.write("\n------ 主属性 ------".center(31))
        mainstat_chs = id_chs(self.main_stat)
        mainstat_value_str = output_value(self.main_value)
        output.write(f"\n{mainstat_chs:<8}\t{mainstat_value_str:>6}".center(31))
        output.write("\n---------- 副属性 ----------")
        output.write("\n{:6}\t{:^6}\t{:^7}".format('副词条', '数值', '额外强化'))
        substats = [
            (self.sub_stats[0], self.sub_values[0], self.enhancement_count[0][1]),
            (self.sub_stats[1], self.sub_values[1], self.enhancement_count[1][1]),
            (self.sub_stats[2], self.sub_values[2], self.enhancement_count[2][1])
        ]
        if len(self.sub_stats) == 4:
            substats.append((self.sub_stats[3], self.sub_values[3], self.enhancement_count[3][1]))
        for substat in substats:
            substat_chs = id_chs(substat[0])
            substat_value_str = output_value(substat[1])
            enhancement_count = substat[2]
            output.write(f"\n{substat_chs:6}\t{substat_value_str:>6}\t{enhancement_count:>7}")
        output.write('\n')

        return output.getvalue()


if __name__ == "__main__":
    pass
