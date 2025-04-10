import streamlit as st
from model import CIFAR100_CLASSES

# 添加中英文映射字典
CIFAR100_CHINESE_MAPPING = {
    'apple': '苹果',
    'aquarium_fish': '观赏鱼',
    'baby': '婴儿',
    'bear': '熊',
    'beaver': '海狸',
    'bed': '床',
    'bee': '蜜蜂',
    'beetle': '甲虫',
    'bicycle': '自行车',
    'bottle': '瓶子',
    'bowl': '碗',
    'boy': '男孩',
    'bridge': '桥',
    'bus': '公交车',
    'butterfly': '蝴蝶',
    'camel': '骆驼',
    'can': '罐头',
    'castle': '城堡',
    'caterpillar': '毛毛虫',
    'cattle': '牛',
    'chair': '椅子',
    'chimpanzee': '黑猩猩',
    'clock': '时钟',
    'cloud': '云',
    'cockroach': '蟑螂',
    'couch': '沙发',
    'crab': '螃蟹',
    'crocodile': '鳄鱼',
    'cup': '杯子',
    'dinosaur': '恐龙',
    'dolphin': '海豚',
    'elephant': '大象',
    'flatfish': '比目鱼',
    'forest': '森林',
    'fox': '狐狸',
    'girl': '女孩',
    'hamster': '仓鼠',
    'house': '房子',
    'kangaroo': '袋鼠',
    'keyboard': '键盘',
    'lamp': '台灯',
    'lawn_mower': '割草机',
    'leopard': '豹子',
    'lion': '狮子',
    'lizard': '蜥蜴',
    'lobster': '龙虾',
    'man': '男人',
    'maple_tree': '枫树',
    'motorcycle': '摩托车',
    'mountain': '山',
    'mouse': '老鼠',
    'mushroom': '蘑菇',
    'oak_tree': '橡树',
    'orange': '橙子',
    'orchid': '兰花',
    'otter': '水獭',
    'palm_tree': '棕榈树',
    'pear': '梨',
    'pickup_truck': '皮卡车',
    'pine_tree': '松树',
    'plain': '平原',
    'plate': '盘子',
    'poppy': '罂粟花',
    'porcupine': '豪猪',
    'possum': '负鼠',
    'rabbit': '兔子',
    'raccoon': '浣熊',
    'ray': '鳐鱼',
    'road': '道路',
    'rocket': '火箭',
    'rose': '玫瑰',
    'sea': '海洋',
    'seal': '海豹',
    'shark': '鲨鱼',
    'shrew': '鼩鼱',
    'skunk': '臭鼬',
    'skyscraper': '摩天大楼',
    'snail': '蜗牛',
    'snake': '蛇',
    'spider': '蜘蛛',
    'squirrel': '松鼠',
    'streetcar': '有轨电车',
    'sunflower': '向日葵',
    'sweet_pepper': '甜椒',
    'table': '桌子',
    'tank': '坦克',
    'telephone': '电话',
    'television': '电视',
    'tiger': '老虎',
    'tractor': '拖拉机',
    'train': '火车',
    'trout': '鳟鱼',
    'tulip': '郁金香',
    'turtle': '乌龟',
    'wardrobe': '衣柜',
    'whale': '鲸鱼',
    'willow_tree': '柳树',
    'wolf': '狼',
    'woman': '女人',
    'worm': '蠕虫'
}

# 反向映射，用于中文搜索
CIFAR100_REVERSE_MAPPING = {v: k for k, v in CIFAR100_CHINESE_MAPPING.items()}

# 定义类别的语义分组
CATEGORY_GROUPS = {
    "动物类": [
        'aquarium_fish', 'bear', 'beaver', 'bee', 'beetle', 'butterfly', 'camel', 'caterpillar', 'cattle', 
        'chimpanzee', 'cockroach', 'crab', 'crocodile', 'dinosaur', 'dolphin', 'elephant', 'flatfish', 'fox', 
        'hamster', 'kangaroo', 'leopard', 'lion', 'lizard', 'lobster', 'mouse', 'otter', 'porcupine', 'possum', 
        'rabbit', 'raccoon', 'ray', 'seal', 'shark', 'shrew', 'skunk', 'snail', 'snake', 'spider', 'squirrel', 
        'tiger', 'trout', 'turtle', 'whale', 'wolf', 'worm'
    ],
    "植物类": [
        'apple', 'forest', 'maple_tree', 'mushroom', 'oak_tree', 'orange', 'orchid', 'palm_tree', 'pear', 
        'pine_tree', 'poppy', 'rose', 'sunflower', 'sweet_pepper', 'tulip', 'willow_tree'
    ],
    "交通工具类": [
        'bicycle', 'bus', 'motorcycle', 'pickup_truck', 'rocket', 'streetcar', 'tank', 'tractor', 'train'
    ],
    "自然景观类": [
        'cloud', 'mountain', 'plain', 'sea'
    ],
    "建筑及设施类": [
        'bridge', 'castle', 'house', 'road', 'skyscraper'
    ],
    "日常物品类": [
        'bed', 'bottle', 'bowl', 'can', 'chair', 'clock', 'couch', 'cup', 'keyboard', 'lamp', 
        'lawn_mower', 'plate', 'table', 'telephone', 'television', 'wardrobe'
    ],
    "人物类": [
        'baby', 'boy', 'girl', 'man', 'woman'
    ]
}

# 设置类别组的中文名和图标
CATEGORY_ICONS = {
    "动物类": "🐾",
    "植物类": "🌱",
    "交通工具类": "🚗",
    "自然景观类": "🏞️",
    "建筑及设施类": "🏢",
    "日常物品类": "🛋️",
    "人物类": "👤"
}

def class_navigation():
    """CIFAR-100类别导航栏"""
    st.subheader("🔍 CIFAR-100 类别导航")
    
    # 搜索框
    search_query = st.text_input("搜索类别:", placeholder="输入中文或英文类别名称...")
    
    # 获取所有类别
    all_classes = sorted(CIFAR100_CLASSES)
    
    # 过滤搜索结果（支持中英文搜索）
    if search_query:
        search_query_lower = search_query.lower()
        filtered_classes = []
        
        for cls in all_classes:
            # 检查英文名称
            if search_query_lower in cls.lower():
                filtered_classes.append(cls)
                continue
                
            # 检查中文名称
            chinese_name = CIFAR100_CHINESE_MAPPING.get(cls, "")
            if chinese_name and search_query_lower in chinese_name:
                filtered_classes.append(cls)
                
        # 如果有搜索结果，显示搜索结果
        if filtered_classes:
            st.write(f"### 搜索结果: {len(filtered_classes)}个类别")
            display_classes_in_grid(filtered_classes)
        else:
            st.info(f"没有找到匹配 '{search_query}' 的类别")
    else:
        # 没有搜索查询时，显示类别分组
        show_category_groups()

def show_category_groups():
    """显示按语义分组的类别"""
    # 为每个类别组创建一个可展开的部分
    for category, classes in CATEGORY_GROUPS.items():
        icon = CATEGORY_ICONS.get(category, "")
        with st.expander(f"{icon} {category} ({len(classes)}个类别)", expanded=False):
            display_classes_in_grid(classes)

def display_classes_in_grid(classes):
    """在网格中显示类别列表"""
    # 创建3列网格来显示类别
    cols = st.columns(3)
    
    for i, cls in enumerate(sorted(classes)):
        # 显示中英文名称
        chinese_name = CIFAR100_CHINESE_MAPPING.get(cls, "")
        display_name = f"{cls} ({chinese_name})" if chinese_name else cls
        cols[i % 3].write(f"- {display_name}")