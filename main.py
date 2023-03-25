from src.artifact_data_analysis import evaluate_all_artifacts_and_configs, artifacts_above_threshold, \
    configs_with_qualified_artifacts, assign_artifacts_to_selected_configs, \
    get_selected_configs, show_assigned_result, get_locked_for_yas
from src.good_to_standard_converter import convert_good_to_standard_for_all
from src.mona_to_standard_converter import convert_mona_to_standard_for_all
from src.xzs_graduation_criteria_calculation import get_all_graduation_criteria

if __name__ == "__main__":
    """1、在这里调整毕业标准"""
    # time_threshold = [9, 18, 36, 108]  # 毕业标准阈值，例如十天可换算为10*180 /40 /5 =9
    # get_all_graduation_criteria(10000, time_threshold)  # 使用蒙特卡洛模拟计算小助手毕业标准,毕业阈值可不添加，默认为10/20/40/120天

    """2、在这里导入自己的圣遗物数据"""
    # convert_mona_to_standard_for_all()  # 从mona.json中导入圣遗物数据
    convert_good_to_standard_for_all()  # 从good.json中导入圣遗物数据

    """3、在这里对圣遗物进行评分"""
    rules = [1]  # 评分规则，目前就两个：0为不做任何调整，1为主属性圣遗物都必须正确的严苛版，后期可给出规则自由搭配
    evaluate_df = evaluate_all_artifacts_and_configs(rules)  # 所有圣遗物对所有配置的评分结果，评分为0-4, 1为10天毕业标准（体力价值论）

    """3.5、圣遗物评分展示"""
    # 以下参数与函数用来展示高标准下的极品圣遗物，即使不使用某些配置，但是也不会遗漏极品胚子
    # order = 3  # 展示标准为等级3
    # artifacts_above_threshold(evaluate_df, order)
    # configs_with_qualified_artifacts(evaluate_df, order, True)  # 删除True默认不展示细节

    """4、在这里对圣遗物进行分配（分配给不同配置）"""
    target_config = set()  # 目标配置，输入目标配置序号即可自动排序，排序规则为深渊使用率&词缀要求量，配置可在csv里查看，空集为所有配置，若要输入则输入index
    assign_threshold = 1  # 分配阈值，大于等于阈值的圣遗物才会被自动分配
    # 自动分配，按照配置顺序一件一件变量循环，保证每个配置都能分配到，且最好的圣遗物能分配给排名最高的配置
    result = assign_artifacts_to_selected_configs(evaluate_df, get_selected_configs(target_config), assign_threshold)

    """4.5、分配结果展示"""
    print(result)
    show_assigned_result(result)

    """5、对圣遗物进行上锁解锁"""
    get_locked_for_yas(result)  # 获得yas-lock的lock.json文件
    # 其余功能正在开发中
