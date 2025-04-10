import torch
import torch.nn as nn
import torchvision
from torchvision import transforms
from timm.models.vision_transformer import VisionTransformer
import numpy as np
from PIL import Image
import io
import functools
import time

# CIFAR-100类别名称
CIFAR100_CLASSES = [
    'apple', 'aquarium_fish', 'baby', 'bear', 'beaver', 'bed', 'bee', 'beetle', 'bicycle', 'bottle', 
    'bowl', 'boy', 'bridge', 'bus', 'butterfly', 'camel', 'can', 'castle', 'caterpillar', 'cattle', 
    'chair', 'chimpanzee', 'clock', 'cloud', 'cockroach', 'couch', 'crab', 'crocodile', 'cup', 'dinosaur', 
    'dolphin', 'elephant', 'flatfish', 'forest', 'fox', 'girl', 'hamster', 'house', 'kangaroo', 'keyboard', 
    'lamp', 'lawn_mower', 'leopard', 'lion', 'lizard', 'lobster', 'man', 'maple_tree', 'motorcycle', 'mountain', 
    'mouse', 'mushroom', 'oak_tree', 'orange', 'orchid', 'otter', 'palm_tree', 'pear', 'pickup_truck', 'pine_tree', 
    'plain', 'plate', 'poppy', 'porcupine', 'possum', 'rabbit', 'raccoon', 'ray', 'road', 'rocket', 
    'rose', 'sea', 'seal', 'shark', 'shrew', 'skunk', 'skyscraper', 'snail', 'snake', 'spider', 
    'squirrel', 'streetcar', 'sunflower', 'sweet_pepper', 'table', 'tank', 'telephone', 'television', 'tiger', 'tractor', 
    'train', 'trout', 'tulip', 'turtle', 'wardrobe', 'whale', 'willow_tree', 'wolf', 'woman', 'worm'
]

# 模型类定义
class EfficientHybrid(nn.Module):
    def __init__(self, img_size=160, num_classes=100):
        super().__init__()
        # 使用ConvNeXt作为特征提取器
        self.convnext = torchvision.models.convnext_tiny(weights=None)
        self.convnext.classifier[2] = nn.Linear(768, num_classes)
        
        # 使用Vision Transformer提取全局特征
        self.vit = VisionTransformer(
            img_size=img_size,
            patch_size=16,
            embed_dim=768,
            depth=12,
            num_heads=12,
            num_classes=num_classes
        )
        
        # 融合层 - 结合两个模型的输出
        self.fusion = nn.Sequential(
            nn.Linear(num_classes * 2, 384),
            nn.BatchNorm1d(384),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(384, num_classes)
        )

    def forward(self, x):
        # 并行处理提高效率
        x1 = self.convnext(x)
        x2 = self.vit(x)
        # 融合两个模型的输出
        return self.fusion(torch.cat([x1, x2], dim=1))

# 性能计时装饰器
def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 执行时间: {(end_time - start_time)*1000:.2f} ms")
        return result
    return wrapper

# 加载模型并缓存
@timing_decorator
def load_model(model_path, device=None):
    """加载模型并将其移动到指定设备上
    
    Args:
        model_path: 模型文件路径
        device: 计算设备，None时自动选择
        
    Returns:
        加载的模型和使用的设备
    """
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    print(f"正在加载模型到 {device} 设备...")
    
    # 创建模型实例
    model = EfficientHybrid().to(device)
    
    # 加载模型权重
    try:
        model.load_state_dict(torch.load(model_path, map_location=device))
        print("模型加载成功!")
    except Exception as e:
        print(f"模型加载失败: {str(e)}")
        raise e
    
    # 设置为评估模式
    model.eval()
    return model, device

# 图像预处理转换器 - 预先定义并重用
def get_transform(img_size=160):
    """获取预处理转换器
    
    Args:
        img_size: 输入图像大小
        
    Returns:
        预处理转换器
    """
    return transforms.Compose([
        transforms.Resize(img_size + 32),  # 略大一些再裁剪，增加鲁棒性
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        # CIFAR-100数据集的均值和标准差
        transforms.Normalize(mean=[0.5071, 0.4867, 0.4408],
                           std=[0.2675, 0.2565, 0.2761])
    ])

# 预处理转换器缓存
_transform_cache = {}

# 图像预处理
def preprocess_image(image, img_size=160):
    """预处理输入图像
    
    Args:
        image: PIL.Image或二进制图像数据
        img_size: 图像大小
        
    Returns:
        处理后的张量
    """
    # 从缓存获取转换器，不存在则创建
    global _transform_cache
    if img_size not in _transform_cache:
        _transform_cache[img_size] = get_transform(img_size)
    transform = _transform_cache[img_size]
    
    # 处理不同类型的输入
    if isinstance(image, bytes):
        image = Image.open(io.BytesIO(image)).convert('RGB')
    elif not isinstance(image, Image.Image):
        raise TypeError("图像必须是PIL.Image或bytes类型")
    
    # 应用转换并增加批次维度
    return transform(image).unsqueeze(0)

# 预测函数
@torch.no_grad()  # 禁用梯度计算提高性能
def predict(model, image, device, top_k=5):
    """预测图像类别
    
    Args:
        model: 预训练模型
        image: 输入图像
        device: 计算设备
        top_k: 返回前k个预测结果
        
    Returns:
        预测结果列表，包含类别ID、名称和概率
    """
    # 预处理图像
    processed_image = preprocess_image(image).to(device)
    
    # 模型推理
    output = model(processed_image)
    probabilities = torch.nn.functional.softmax(output, dim=1)
    
    # 获取top-k结果
    top_prob, top_class = torch.topk(probabilities, top_k, dim=1)
    
    # 格式化结果
    result = []
    for i in range(top_k):
        class_idx = top_class[0][i].item()
        result.append({
            'class_id': class_idx,
            'class_name': CIFAR100_CLASSES[class_idx],
            'probability': round(top_prob[0][i].item() * 100, 2)  # 转为百分比并保留两位小数
        })
    
    return result

# 批量预测函数
@torch.no_grad()  # 禁用梯度计算提高性能
def batch_predict(model, images, device, top_k=5, batch_size=16):
    """批量预测多张图像
    
    Args:
        model: 预训练模型
        images: 图像列表
        device: 计算设备
        top_k: 每张图像返回前k个预测结果
        batch_size: 批处理大小
        
    Returns:
        每张图像的预测结果列表
    """
    results = []
    
    # 按批次处理图像
    for i in range(0, len(images), batch_size):
        batch_images = images[i:i+batch_size]
        batch_results = []
        
        # 处理每张图像
        for image in batch_images:
            result = predict(model, image, device, top_k)
            batch_results.append(result)
        
        results.extend(batch_results)
    
    return results 