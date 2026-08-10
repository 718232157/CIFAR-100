# CIFAR-100 ConvNeXt–ViT Hybrid Image Classifier

> 在校期间完成的计算机视觉实践项目：从模型训练、权重保存和推理封装，到 Streamlit 交互应用，形成一套可运行的 CIFAR-100 图像分类流程。

本项目采用 **ConvNeXt-Tiny + Vision Transformer** 双分支架构，对两路分类结果进行融合，支持单张图片预测、多图片预测、历史记录、结果导出、类别导航与用户反馈。训练过程在 Kaggle GPU 环境完成，应用端代码与推理逻辑保存在本仓库。

## 项目入口

| 内容 | 地址 | 说明 |
| --- | --- | --- |
| 在线演示 | [Streamlit Community Cloud](https://dream-ten.streamlit.app/) | 免费实例长时间无访问会休眠，进入后可手动唤醒 |
| 训练源码与日志 | [Kaggle Notebook](https://www.kaggle.com/code/hepingyang/pjone-sort-vit) | 可查看模型结构、训练策略、运行日志与版本记录 |
| 模型权重 | [Kaggle Output](https://www.kaggle.com/code/hepingyang/pjone-sort-vit/output) | `best_model.pth`，约 455.4 MB |

## 模型与训练

### 模型结构

- **ConvNeXt-Tiny 分支**：使用 ImageNet 预训练权重，负责提取局部纹理和层次化视觉特征。
- **Vision Transformer 分支**：使用 12 层、12 头 Transformer 建模全局信息。
- **结果融合层**：拼接两路 100 类分类输出，通过包含 BatchNorm、GELU 与 Dropout 的 MLP 生成最终预测。

这里采用的是分类结果层融合，而不是简单宣称“特征融合”。完整实现可在 [`model.py`](./model.py) 和公开的 [Kaggle Notebook](https://www.kaggle.com/code/hepingyang/pjone-sort-vit) 中查看。

### 训练策略

- CIFAR-100 数据增强：随机裁剪、水平翻转、随机旋转、ColorJitter 与 RandAugment
- MixUp 与 CutMix 混合增强
- Label Smoothing
- AdamW 优化器与 OneCycleLR 学习率策略
- AMP 混合精度训练
- 梯度累积，降低大模型训练时的显存压力
- 按评估准确率持续保存最佳权重

### 公开运行记录

| 项目 | 记录 |
| --- | --- |
| 数据集 | CIFAR-100 |
| 输入尺寸 | 160 × 160 |
| 实际完成轮数 | 45 Epochs |
| 最佳 Top-1 Accuracy | **87.25%** |
| 云端运行时间 | 约 12 小时 |
| 训练环境 | Kaggle GPU / PyTorch AMP |

该次 Notebook 原计划继续训练，但 Kaggle 单次 GPU 运行达到 12 小时时长上限后被平台终止。公开运行元数据显示任务没有代码异常，并在结束前完成第 45 轮训练；训练过程中持续保存最佳权重，因此现有模型来自有效训练阶段。

以上数据来自一次公开运行记录，用于说明本项目的实际训练过程，不作为跨模型、跨硬件的通用性能承诺。项目未提供严格的单模型消融实验，因此不宣称融合架构一定优于所有单一模型。

## 应用功能

- **单张图片预测**：展示 Top-K 类别、置信度和可视化结果。
- **多图片预测**：连续处理多张图片，并汇总分类结果。
- **历史记录**：使用 SQLite 保存预测记录，支持查询与筛选。
- **结果导出**：将历史数据导出为 CSV 或 JSON。
- **类别导航**：浏览 CIFAR-100 的 100 个细分类别。
- **用户反馈**：记录用户对预测结果的反馈。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 深度学习 | PyTorch、Torchvision、timm |
| 模型 | ConvNeXt-Tiny、Vision Transformer |
| 图像处理 | Pillow、NumPy |
| 应用界面 | Streamlit |
| 数据存储 | SQLite、JSON |
| 训练环境 | Kaggle GPU |

## 本地运行

### 1. 克隆项目

```bash
git clone https://github.com/718232157/CIFAR-100.git
cd CIFAR-100
```

### 2. 安装依赖

建议使用 Python 3.10 环境：

```bash
pip install -r requirements.txt
```

### 3. 下载模型权重

从 [Kaggle Output](https://www.kaggle.com/code/hepingyang/pjone-sort-vit/output) 下载 `best_model.pth`，放到项目根目录。也可以使用 Kaggle CLI：

```bash
kaggle kernels output hepingyang/pjone-sort-vit -p .
```

仓库使用 Git LFS 记录模型文件，但当前 GitHub LFS 下载不可用，因此推荐从 Kaggle 获取完整权重。普通 Git 克隆得到的 `best_model.pth` 可能只是 LFS 指针文件。

### 4. 启动应用

```bash
streamlit run app.py
```

默认访问地址为 `http://localhost:8501`。

## 项目结构

```text
CIFAR-100/
├── app.py                  # Streamlit 应用入口
├── model.py                # 模型定义、权重加载与预测逻辑
├── components/             # 上传、预测、历史、导出、反馈等 UI 组件
├── utils/                  # 数据库、图像处理和样式工具
├── data/                   # 应用运行数据目录
├── requirements.txt        # Python 依赖
└── best_model.pth          # 模型权重（Git LFS 指针）
```

## 项目定位与边界

这是一个在校期间完成的深度学习与应用开发实践，重点是验证完整的模型训练和产品化展示流程。当前版本仍有进一步提升空间：

- 尚未补充 ConvNeXt、ViT 与融合模型之间的完整消融实验。
- 当前多图片功能以交互完整性为主，尚未进行生产级吞吐优化。
- 模型体积和计算量较大，更适合 GPU 环境；免费 Streamlit 实例可能因资源不足或休眠而暂时不可用。

## 数据集

CIFAR-100 包含 100 个类别、共 60,000 张 32 × 32 彩色图像，其中 50,000 张用于训练、10,000 张用于测试。数据集介绍见 [CIFAR-100 官方页面](https://www.cs.toronto.edu/~kriz/cifar.html)。

## 联系方式

如需交流项目实现或获取模型文件，可联系：`718232157@qq.com`
