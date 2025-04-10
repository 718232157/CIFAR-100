import streamlit as st
from utils.image_utils import save_uploaded_image, is_valid_image, get_image_preview
from utils.styles import get_upload_info_style, get_image_info_style
import time
import os

def single_image_upload():
    """单张图片上传组件
    
    提供用户友好的单张图片上传界面，支持拖放，带有预览和验证功能
    
    Returns:
        str: 保存的图片路径或None
    """
    # 添加上传说明
    st.markdown(get_upload_info_style("single"), unsafe_allow_html=True)
    
    # 创建上传区
    uploaded_file = st.file_uploader(
        "选择或拖放图片到此处", 
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        help="选择一张要分类的图片"
    )
    
    if uploaded_file is not None:
        # 创建进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 验证图片
        if not is_valid_image(uploaded_file):
            st.error("❌ 无效的图片文件，请上传正确格式的图片")
            return None
            
        # 显示处理信息
        for i in range(100):
            # 更新进度条
            progress_bar.progress(i + 1)
            status_text.text(f"处理中... {i+1}%")
            time.sleep(0.01)
        
        # 保存图片
        file_path = save_uploaded_image(uploaded_file)
        status_text.text("✅ 图片已成功上传!")
        
        # 显示图片预览
        preview_container = st.container()
        with preview_container:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(uploaded_file, caption="预览图片", use_container_width=True)
            with col2:
                st.markdown(get_image_info_style(uploaded_file, file_path), unsafe_allow_html=True)
        
        return file_path
    else:
        # 显示示例图片区域
        with st.expander("没有图片? 查看示例", expanded=False):
            st.markdown("""
            您可以尝试上传以下物体的图片：
            - 动物：猫、狗、鸟、鱼等
            - 交通工具：汽车、飞机、船等
            - 植物：花、树、水果等
            - 日常物品：椅子、桌子、电话等
            
            CIFAR-100数据集包含100个不同类别，上传图片后系统将尝试将其分类到最接近的类别。
            """)
    
    return None

def multiple_image_upload():
    """多张图片上传组件
    
    提供用户友好的多张图片上传界面，支持拖放，带有预览和批量处理功能
    
    Returns:
        list: 保存的图片路径列表
    """
    # 添加上传说明
    st.markdown(get_upload_info_style("multiple"), unsafe_allow_html=True)
    
    # 创建上传区
    uploaded_files = st.file_uploader(
        "选择或拖放多张图片到此处", 
        type=["jpg", "jpeg", "png", "bmp", "webp"], 
        accept_multiple_files=True,
        help="选择多张图片进行批量分类"
    )
    
    file_paths = []
    
    if uploaded_files:
        # 限制图片数量
        if len(uploaded_files) > 20:
            st.warning("⚠️ 一次最多处理20张图片，系统将仅处理前20张")
            uploaded_files = uploaded_files[:20]
        
        # 创建进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text("正在处理图片...")
        
        # 处理上传的图片
        valid_files = []
        invalid_files = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            # 更新进度
            progress = int((i + 1) / len(uploaded_files) * 100)
            progress_bar.progress(progress)
            status_text.text(f"处理中... {progress}%")
            
            # 验证图片
            if not is_valid_image(uploaded_file):
                invalid_files.append(uploaded_file.name)
                continue
            
            # 保存图片
            file_path = save_uploaded_image(uploaded_file)
            file_paths.append(file_path)
            valid_files.append(uploaded_file)
            
            # 小延迟使处理看起来更自然
            time.sleep(0.05)
        
        # 处理完成后显示信息
        if invalid_files:
            st.warning(f"⚠️ {len(invalid_files)}个文件无效: {', '.join(invalid_files)}")
        
        status_text.text(f"✅ 成功上传 {len(valid_files)} 张图片!")
        
        # 显示图片预览网格
        if file_paths:
            st.write("### 图片预览")
            
            # 动态确定每行显示的图片数量
            if len(file_paths) <= 3:
                cols_per_row = len(file_paths)
            elif len(file_paths) <= 8:
                cols_per_row = 4
            else:
                cols_per_row = 5
            
            # 创建网格布局
            rows = [file_paths[i:i+cols_per_row] for i in range(0, len(file_paths), cols_per_row)]
            
            for row in rows:
                cols = st.columns(cols_per_row)
                for i, file_path in enumerate(row):
                    with cols[i]:
                        # 获取文件名
                        filename = os.path.basename(file_path)
                        # 显示缩略图
                        st.image(
                            file_path, 
                            caption=f"{filename[:15]}..." if len(filename) > 15 else filename, 
                            use_container_width=True
                        )
    
    return file_paths 