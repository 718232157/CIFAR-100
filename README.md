# CIFAR-100 图像分类应用

这是一个基于CIFAR-100数据集的图像分类应用程序，使用Streamlit构建用户界面，结合ConvNeXt和Vision Transformer的混合模型进行图像分类。

## 功能特点

- **单张图片分类**：上传单张图片并获取分类结果，附带详细的可视化分析
- **多张图片分类**：批量上传多张图片并获取分类结果，支持统计分析
- **历史记录管理**：查看和管理历史预测记录，支持搜索和筛选
- **数据导出**：将预测历史导出为CSV或JSON格式，便于进一步分析
- **类别导航**：浏览CIFAR-100数据集中的100个类别及其详情
- **用户反馈**：提供对预测结果的反馈意见和改进建议

## 新增特性与优化

- **改进UI设计**：全新的响应式界面设计，支持不同设备屏幕尺寸
- **可视化分析**：使用交互式图表展示分类结果和置信度分布
- **批处理优化**：支持大批量图像的高效处理和结果展示
- **模型性能提升**：优化了模型加载和推理过程，提高响应速度
- **数据统计分析**：添加了多维度的结果统计和可视化功能
- **用户体验改进**：添加了进度指示、详细提示和直观的结果展示

## 环境要求

- 其他依赖见`requirements.txt`



## 运行应用
拉取代码到本地按照运行以下命令
```bash
cd cifar100_app
streamlit run app.py
```

应用将在本地启动，访问浏览器中的`http://localhost:8501`即可使用。
或访问：https://dream-ten.streamlit.app/ (注：此网站由于是免费资源提供，模型较大，所用内存较多，提供的免费资源如下：1个cpu核心，1G内存。请错峰使用)



## 项目结构

```
cifar100_app/
├── app.py                # 主应用程序，负责初始化和运行Streamlit应用
├── model.py              # 模型定义和预测功能，使用预训练的ConvNeXt和ViT模型
├── README.md             # 项目说明文档，提供项目概述和使用指南
├── requirements.txt      # 依赖包列表，便于环境搭建
├── components/           # UI组件模块
│   ├── image_upload.py   # 图片上传组件，支持单张和多张图片上传
│   ├── prediction.py     # 预测结果显示组件，展示分类结果
│   ├── history.py        # 历史记录组件，管理和显示预测历史
│   ├── export.py         # 数据导出组件，支持CSV和JSON格式
│   ├── feedback.py       # 用户反馈组件，收集和显示反馈
│   └── navigation.py     # CIFAR-100类别导航组件，浏览类别信息
├── utils/                # 工具函数模块
│   ├── db.py             # 数据库操作，处理历史记录存储和检索
│   ├── image_utils.py    # 图像处理工具，提供实用函数
│   └── styles.py         # 样式管理，定义应用的CSS样式
├── data/                 # 数据存储
│   ├── uploads/          # 上传图片存储
│   └── history.db        # SQLite数据库文件
└── assets/               # 静态资源
```

## 关于CIFAR-100

CIFAR-100是一个包含100个类别的图像分类数据集，每个类别有600张32x32的彩色图像，其中500张用于训练，100张用于测试。它是计算机视觉研究和教学中广泛使用的基准数据集。

详情参考：[CIFAR-100数据集](https://www.cs.toronto.edu/~kriz/cifar.html)

## 模型说明

本应用使用混合模型架构，结合了ConvNeXt和Vision Transformer的优点：

- **ConvNeXt**：提供强大的局部特征提取能力，擅长处理纹理和细节
- **Vision Transformer (ViT)**：提供良好的全局上下文理解能力，擅长捕捉长距离依赖关系
- **混合架构**：通过特征融合机制，结合两种模型的优势，提高分类准确率

通过同时利用CNN和Transformer的优势，该混合模型在CIFAR-100数据集上展现出优于单一模型的性能表现。

## 性能优化

本应用中实施了多项性能优化：

1. **模型推理优化**：
   - 使用缓存机制减少重复计算
   - 禁用梯度计算优化推理速度
   - 批量处理提高吞吐量

2. **图像处理优化**：
   - 智能图像缩放和压缩
   - 异步加载提高响应速度
   - 临时文件管理防止内存泄漏

3. **UI响应优化**：
   - 懒加载减少初始加载时间
   - 优化页面刷新逻辑
   - 使用缓存避免重复渲染


