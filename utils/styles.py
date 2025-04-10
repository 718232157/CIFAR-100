"""
样式模块 - 包含所有应用的CSS样式定义

提供统一的样式管理，使主应用代码更加清晰
"""
import os

# 主要CSS样式
main_css = """
/* 全局样式 */
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

* {
    font-family: 'Roboto', sans-serif;
}

/* 标题样式 */
.main-header {
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(90deg, #1E88E5 0%, #1565C0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 1.5rem;
    padding: 1rem 0;
}

.sub-header {
    font-size: 1.7rem;
    font-weight: 500;
    color: #0D47A1;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
    padding-bottom: 0.3rem;
    border-bottom: 2px solid #E3F2FD;
}

/* 卡片样式 */
.card {
    background-color: #FFFFFF;
    border-radius: 0.8rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    padding: 1.5rem;
    margin: 0.8rem 0;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

/* 信息框样式 */
.info-box {
    background-color: #E3F2FD;
    border-left: 4px solid #1E88E5;
    padding: 0.8rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}

.success-box {
    background-color: #E8F5E9;
    border-left: 4px solid #4CAF50;
    padding: 0.8rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}

.warning-box {
    background-color: #FFF8E1;
    border-left: 4px solid #FFC107;
    padding: 0.8rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}

/* 按钮样式 */
.stButton button {
    width: 100%;
    border-radius: 0.5rem;
    font-weight: 500;
    transition: all 0.3s ease;
}

.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

/* 自定义侧边栏样式 */
.sidebar-content {
    padding: 1rem;
}

/* 页脚样式 */
.footer {
    margin-top: 3rem;
    padding: 0.5rem 0;
    color: #A8A8A8;
    font-size: 0.75rem;
    background-color: transparent;
}

.footer-table {
    width: 100%;
    max-width: 1024px;
    margin: 0 auto;
    border-collapse: collapse;
    border: 1px solid #eee;
}

.footer-table td {
    padding: 10px 15px;
    text-align: center;
    border: 1px solid #eee;
}

.footer-table tr:first-child td {
    border-bottom: 1px solid #eee;
    font-weight: normal;
    color: #666;
}

.footer-table h5 {
    margin: 0;
    font-weight: normal;
    font-size: 0.9rem;
    color: #666;
}

.footer-table p {
    margin: 0;
    font-size: 0.85rem;
}

.footer-table a {
    color: #4FC3F7;
    text-decoration: none;
}

.footer-table a:hover {
    text-decoration: underline;
}

.footer-copyright {
    margin-top: 0.5rem;
    font-size: 0.65rem;
    text-align: center;
    color: #CCCCCC;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .footer {
        padding: 0.4rem 0;
    }
    
    .footer-table {
        width: 95%;
    }
}
"""

# 反馈相关样式
feedback_css = """
.feedback-detail-card {
    background-color: #f8f9fa;
    border-left: 4px solid #1E88E5;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 15px;
}

.feedback-card {
    background-color: #f8f9fa;
    border-left: 4px solid #4CAF50;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 15px;
}

.record-feedback-card {
    background-color: #f0f7ff;
    border-left: 4px solid #1976D2;
    padding: 15px;
    border-radius: 5px;
    margin-top: 10px;
}
"""

# 工具提示样式
tooltip_css = """
.tooltip-container {
    position: relative;
    display: inline-block;
    max-width: 100%;
    margin-bottom: 5px;
}

.tooltip-content {
    max-width: 100%;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
}

.full-text {
    visibility: hidden;
    width: 300px;
    background-color: #333;
    color: #fff;
    text-align: left;
    border-radius: 6px;
    padding: 8px;
    position: absolute;
    z-index: 9999;
    bottom: 125%;
    left: 0;
    opacity: 0;
    transition: opacity 0.3s;
    white-space: pre-wrap;
    word-wrap: break-word;
    box-shadow: 0 3px 10px rgba(0,0,0,0.2);
    font-size: 14px;
    line-height: 1.4;
}

/* 确保在小屏幕上提示框不会超出可视区域 */
@media (max-width: 768px) {
    .full-text {
        width: 200px;
        left: -50px;
    }
}

/* 在底部和右侧添加小箭头指向文本 */
.full-text::after {
    content: "";
    position: absolute;
    top: 100%;
    left: 15px;
    border-width: 5px;
    border-style: solid;
    border-color: #333 transparent transparent transparent;
}

.tooltip-container:hover .full-text {
    visibility: visible;
    opacity: 1;
}
"""

# 图片上传组件样式
image_upload_css = """
.upload-info-box {
    padding: 8px;
    margin-bottom: 8px;
    border-radius: 5px;
    background-color: #f8f9fa;
}

.image-info-container {
    padding: 12px;
    border-radius: 5px;
    background-color: #f0f7ff;
    height: 100%;
}
"""

# 预测结果展示样式
prediction_css = """
.result-card {
    background-color: #f8f9fa; 
    padding: 20px; 
    border-radius: 10px; 
    border-left: 5px solid #4CAF50;
}

.batch-result-card {
    border: 1px solid #e0e0e0; 
    border-radius: 8px; 
    overflow: hidden; 
    margin-bottom: 15px;
}

.batch-result-header {
    padding: 8px 12px; 
    background-color: #f5f5f5; 
    border-bottom: 1px solid #e0e0e0;
}
"""

# 获取所有CSS样式
def get_all_css():
    """返回所有CSS样式的组合"""
    return main_css + feedback_css + tooltip_css + image_upload_css + prediction_css

# 生成内联样式的函数
def get_result_card_style(top_result):
    """生成预测结果卡片的内联样式HTML"""
    return f"""
    <div class="result-card">
        <h2 style="color: #2E7D32; margin-top: 0;">分类结果</h2>
        <div style="margin: 15px 0;">
            <p style="font-size: 13px; color: #757575; margin: 0;">识别为</p>
            <h1 style="font-size: 32px; margin: 5px 0;">{top_result['class_name']}</h1>
            <p style="color: #1976D2; font-size: 18px; margin: 5px 0;">置信度: {top_result['probability']:.2f}%</p>
        </div>
        <p style="margin-top: 20px; padding-top: 10px; border-top: 1px solid #ddd;">
            系统基于CIFAR-100数据集的100个预定义类别进行识别。
        </p>
    </div>
    """

def get_image_info_style(uploaded_file, file_path):
    """生成图片信息展示的内联样式HTML"""
    return f"""
    <div class="image-info-container">
        <h4 style="margin-top: 0;">图片信息</h4>
        <p><strong>文件名:</strong> {uploaded_file.name}</p>
        <p><strong>文件大小:</strong> {uploaded_file.size / 1024:.1f} KB</p>
        <p><strong>保存路径:</strong> {os.path.basename(file_path)}</p>
    </div>
    """

def get_batch_result_header(result_idx):
    """生成批量结果头部的内联样式HTML"""
    return f"""
    <div class="batch-result-card">
        <div class="batch-result-header">
            <span style="font-size: 0.9rem; font-weight: bold;">图片 {result_idx + 1}</span>
        </div>
    </div>
    """

def get_upload_info_style(upload_type="single"):
    """生成上传信息提示的内联样式HTML
    
    Args:
        upload_type: 'single'表示单张上传，'multiple'表示多张上传
    """
    if upload_type == "single":
        return """
        <div class="upload-info-box">
            <p style="margin: 0;"><strong>支持格式:</strong> JPG, JPEG, PNG, BMP, WEBP</p>
            <p style="margin: 5px 0 0 0;"><strong>提示:</strong> 您可以直接将图片拖放到上传区域</p>
        </div>
        """
    else:
        return """
        <div class="upload-info-box">
            <p style="margin: 0;"><strong>支持格式:</strong> JPG, JPEG, PNG, BMP, WEBP</p>
            <p style="margin: 5px 0 0 0;"><strong>提示:</strong> 您可以选择多个文件或直接将多张图片一起拖放到上传区域</p>
            <p style="margin: 5px 0 0 0;"><strong>批量处理:</strong> 一次最多处理20张图片</p>
        </div>
        """ 