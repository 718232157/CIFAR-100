import streamlit as st
import os
import hashlib
import urllib.request
import torch
from PIL import Image

# 导入自定义模块
from model import load_model, predict, batch_predict
from components.image_upload import single_image_upload, multiple_image_upload
from components.prediction import display_prediction_result, display_batch_predictions
from components.history import show_history
from components.feedback import collect_feedback, feedback_form, view_feedback_records, collect_batch_feedback
from components.export import export_data, data_visualization
from components.navigation import class_navigation
from utils.styles import get_all_css

# 页面配置
st.set_page_config(
    page_title="CIFAR-100 图像分类应用",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 应用全局CSS样式
st.markdown(f"<style>{get_all_css()}</style>", unsafe_allow_html=True)

MODEL_PATH = "best_model.pth"
MODEL_URL = "https://github.com/718232157/CIFAR-100/releases/download/v1.0.0/best_model.pth"
MODEL_SIZE = 455397781
MODEL_SHA256 = "a5bd01d6e8cc0227094b88421256037059b1c3cef29e62143190fa94be2729ea"


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as model_file:
        for chunk in iter(lambda: model_file.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_model_file():
    """Download and verify the public release checkpoint when it is absent."""
    if (
        os.path.exists(MODEL_PATH)
        and os.path.getsize(MODEL_PATH) == MODEL_SIZE
        and _sha256(MODEL_PATH) == MODEL_SHA256
    ):
        return MODEL_PATH

    temporary_path = f"{MODEL_PATH}.download"
    if os.path.exists(temporary_path):
        os.remove(temporary_path)

    urllib.request.urlretrieve(MODEL_URL, temporary_path)

    if os.path.getsize(temporary_path) != MODEL_SIZE or _sha256(temporary_path) != MODEL_SHA256:
        os.remove(temporary_path)
        raise RuntimeError("模型文件完整性校验失败，请稍后重试。")

    os.replace(temporary_path, MODEL_PATH)
    return MODEL_PATH


@st.cache_resource(show_spinner=False)
def get_cached_model():
    model_path = ensure_model_file()
    return load_model(model_path)


# 模型在进程内只加载一次，避免 Streamlit 重跑重复占用内存。
if 'model' not in st.session_state:
    try:
        with st.spinner("首次启动正在下载并加载模型，约 455 MB，请稍候……"):
            st.session_state.model, st.session_state.device = get_cached_model()
        st.session_state.model_loaded = True
        st.session_state.model_error = None
    except Exception as error:
        st.session_state.model_loaded = False
        st.session_state.model_error = str(error)

if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "单张图片分类"

if 'last_prediction_record_id' not in st.session_state:
    st.session_state.last_prediction_record_id = None

# 侧边栏菜单 - 改进布局
with st.sidebar:
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    
    # Logo和标题
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
        <span style="font-size: 2rem; margin-right: 0.5rem;">🖼️</span>
        <h1 style="margin: 0; color: #1E88E5; font-size: 1.8rem;">CIFAR-100<br><span style="font-size: 1.2rem; color: #757575;">图像分类</span></h1>
    </div>
    """, unsafe_allow_html=True)
    
    # 设备信息
    if 'model_loaded' in st.session_state and st.session_state.model_loaded:
        device_info = "GPU" if torch.cuda.is_available() else "CPU"
        st.markdown(f"""
        <div class="info-box">
            <strong>运行状态：</strong>正常<br>
            <strong>使用设备：</strong>{device_info}<br>
            <strong>模型类型：</strong>ConvNeXt + ViT 混合模型
        </div>
        """, unsafe_allow_html=True)
    
    # 主菜单
    st.markdown("<h3 style='margin-top: 1.5rem;'>主功能</h3>", unsafe_allow_html=True)
    
    tab_options = [
        {"name": "单张图片分类", "icon": "🔍"},
        {"name": "多张图片分类", "icon": "📑"},
        {"name": "历史记录", "icon": "📊"},
        {"name": "数据导出", "icon": "💾"},
        {"name": "类别导航", "icon": "🧭"},
        {"name": "用户反馈", "icon": "📝"}
    ]
    
    # 改进菜单按钮
    col1, col2 = st.columns(2)
    
    with col1:
        for i in range(0, len(tab_options), 2):
            tab = tab_options[i]
            if st.button(f"{tab['icon']} {tab['name']}", key=f"btn_{tab['name']}"):
                st.session_state.current_tab = tab['name']
                st.session_state.last_prediction_record_id = None
    
    with col2:
        for i in range(1, len(tab_options), 2):
            tab = tab_options[i]
            if st.button(f"{tab['icon']} {tab['name']}", key=f"btn_{tab['name']}"):
                st.session_state.current_tab = tab['name']
                st.session_state.last_prediction_record_id = None
    
    # 关于信息
    st.markdown("---")
    with st.expander("📖 关于应用"):
        st.markdown("""
        **CIFAR-100图像分类应用**使用混合模型架构（ConvNeXt + Vision Transformer）对CIFAR-100数据集中的100种不同物体类别进行分类。
        
        本应用可以帮助您：
        - 对单张或多张图像进行分类识别
        - 管理和分析历史分类记录
        - 导出数据进行进一步分析
        - 浏览和了解CIFAR-100中的各种类别
        
        [CIFAR-100 数据集详情](https://www.cs.toronto.edu/~kriz/cifar.html)
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)

# 主界面
st.markdown("<h1 class='main-header'>CIFAR-100 图像分类应用</h1>", unsafe_allow_html=True)

# 如果模型未加载，显示错误信息
if 'model_loaded' in st.session_state and not st.session_state.model_loaded:
    st.error("模型下载或加载失败。")
    if st.session_state.get('model_error'):
        st.code(st.session_state.model_error)
    st.warning("请稍后刷新重试；模型权重也可以从项目的 GitHub Release 手动下载。")
    st.stop()

# 根据当前选择的标签显示内容 - 改进显示逻辑
if st.session_state.current_tab == "单张图片分类":
    st.markdown("<h2 class='sub-header' style='margin-bottom: 0.5rem;'>单张图片分类</h2>", unsafe_allow_html=True)
    
    # 添加使用指南
    st.markdown("""
    <div class="info-box">
        <strong>使用指南：</strong>上传一张图片（JPG、PNG或JPEG格式），系统将对其进行分类，并显示前最可能的类别。
    </div>
    """, unsafe_allow_html=True)
    
    # 上传单张图片
    file_path = single_image_upload()
    
    if file_path:
        # 进行预测
        classify_btn = st.button("📊 开始分类", key="single_classify_btn", use_container_width=True)
        if classify_btn:
            with st.spinner("正在进行分类分析..."):
                try:
                    # 读取图片
                    image = Image.open(file_path).convert('RGB')
                    
                    # 预测
                    prediction_result = predict(
                        st.session_state.model, 
                        image, 
                        st.session_state.device
                    )
                    
                    # 显示预测结果
                    record_id = display_prediction_result(file_path, prediction_result)
                    st.session_state.last_prediction_record_id = record_id
                    
                    # 添加成功消息
                    st.markdown("""
                    <div class="success-box">
                        <strong>分类完成！</strong> 可以在下方查看分类结果和提供反馈。
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"分类过程中出错: {str(e)}")
    
    # 显示反馈表单
    if st.session_state.last_prediction_record_id:
        with st.expander("📝 提供反馈", expanded=True):
            feedback_result = collect_feedback(st.session_state.last_prediction_record_id)
            if feedback_result:
                # 如果反馈已提交，显示链接到历史记录页面
                st.markdown("""
                <div style="padding: 10px; margin-top: 10px; border-radius: 5px; background-color: #f0f7ff;">
                    <p>您可以在<strong>历史记录</strong>页面中查看所有分类记录和反馈。</p>
                </div>
                """, unsafe_allow_html=True)

elif st.session_state.current_tab == "多张图片分类":
    st.markdown("<h2 class='sub-header' style='margin-bottom: 0.5rem;'>多张图片分类</h2>", unsafe_allow_html=True)
    
    # 添加使用指南
    st.markdown("""
    <div class="info-box">
        <strong>使用指南：</strong>上传多张图片（JPG、PNG或JPEG格式），系统将对所有图片进行批量分类，并显示每张图片前5个最可能的类别及其概率。
    </div>
    """, unsafe_allow_html=True)
    
    # 初始化会话状态
    if 'batch_record_ids' not in st.session_state:
        st.session_state.batch_record_ids = None
    
    # 上传多张图片
    file_paths = multiple_image_upload()
    
    if file_paths:
        # 显示已上传文件数量
        st.markdown(f"""
        <div class="info-box">
            <strong>已上传：</strong> {len(file_paths)}张图片
        </div>
        """, unsafe_allow_html=True)
        
        # 进行预测
        batch_btn = st.button("📊 开始批量分类", key="batch_classify_btn", use_container_width=True)
        if batch_btn:
            with st.spinner("正在进行批量分类分析..."):
                try:
                    # 读取图片
                    images = [Image.open(path).convert('RGB') for path in file_paths]
                    
                    # 批量预测
                    batch_results = batch_predict(
                        st.session_state.model, 
                        images, 
                        st.session_state.device
                    )
                    
                    # 显示预测结果
                    record_ids = display_batch_predictions(file_paths, batch_results)
                    
                    # 保存记录ID到会话状态，用于批量反馈
                    st.session_state.batch_record_ids = record_ids
                    
                    # 添加成功消息
                    st.markdown("""
                    <div class="success-box">
                        <strong>批量分类完成！</strong> 可以在下方查看分类结果和提供反馈。
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"批量分类过程中出错: {str(e)}")
    
    # 显示批量反馈表单
    if st.session_state.batch_record_ids and len(st.session_state.batch_record_ids) > 0:
        with st.expander("📝 提供批量分类反馈", expanded=True):
            feedback_result = collect_batch_feedback(st.session_state.batch_record_ids)
            if feedback_result:
                # 如果反馈已提交，显示链接到历史记录页面
                st.markdown("""
                <div style="padding: 10px; margin-top: 10px; border-radius: 5px; background-color: #f0f7ff;">
                    <p>感谢您的反馈！您可以在<strong>历史记录</strong>页面中查看所有分类记录和反馈。</p>
                </div>
                """, unsafe_allow_html=True)

elif st.session_state.current_tab == "历史记录":
    st.markdown("<h2 class='sub-header' style='margin-bottom: 0.5rem;'>历史记录</h2>", unsafe_allow_html=True)
    
    # 添加使用指南
    st.markdown("""
    <div class="info-box">
        <strong>使用指南：</strong>在此页面查看、搜索和管理所有历史分类记录。可以按类别筛选、按时间排序，并查看详细的分类结果。
    </div>
    """, unsafe_allow_html=True)
    
    # 显示历史记录，统计功能已集成到show_history函数中
    show_history()

elif st.session_state.current_tab == "数据导出":
    st.markdown("<h2 class='sub-header' style='margin-bottom: 0.5rem;'>数据导出</h2>", unsafe_allow_html=True)
    
    # 添加使用指南
    st.markdown("""
    <div class="info-box">
        <strong>使用指南：</strong>导出历史分类记录为CSV或JSON格式，以便进行进一步分析或备份数据。
    </div>
    """, unsafe_allow_html=True)
    
    # 直接显示数据导出功能
    export_data()

elif st.session_state.current_tab == "类别导航":
    st.markdown("<h2 class='sub-header' style='margin-bottom: 0.5rem;'>CIFAR-100 类别导航</h2>", unsafe_allow_html=True)
    
    # 添加使用指南
    st.markdown("""
    <div class="info-box">
        <strong>使用指南：</strong>浏览CIFAR-100数据集中的100个类别，了解每个类别的详细信息和示例图像。
    </div>
    """, unsafe_allow_html=True)
    
    # 直接显示类别导航
    class_navigation()

elif st.session_state.current_tab == "用户反馈":
    st.markdown("<h2 class='sub-header' style='margin-bottom: 0.5rem;'>用户反馈</h2>", unsafe_allow_html=True)
    
    # 添加使用指南
    st.markdown("""
    <div class="info-box">
        <strong>使用指南：</strong>在此页面提交对系统的反馈和建议，或查看已提交的反馈记录。
    </div>
    """, unsafe_allow_html=True)
    
    # 创建提交反馈和查看反馈的选项卡
    feedback_tab1, feedback_tab2 = st.tabs(["提交反馈", "查看反馈记录"])
    
    with feedback_tab1:
        feedback_form()
    
    with feedback_tab2:
        view_feedback_records()

# 页脚
st.markdown('<div class="footer">', unsafe_allow_html=True)
st.markdown("""
<table class="footer-table">
    <tr>
        <td>CIFAR-100 应用</td>
        <td>技术支持</td>
        <td>数据来源</td>
    </tr>
    <tr>
        <td>深度学习图像分类</td>
        <td>ConvNeXt+ViT</td>
        <td><a href="https://www.cs.toronto.edu/~kriz/cifar.html" target="_blank">CIFAR-100</a></td>
    </tr>
</table>
<div class="footer-copyright">© 2025 CIFAR-100 分类应用 | v1.0.0</div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
