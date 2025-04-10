import streamlit as st
from utils.db import export_history
import base64
from datetime import datetime

def export_data():
    """优化后的导出历史数据功能"""
    st.subheader("📤 导出预测历史")
    
    # 添加说明信息
    st.markdown("""
    <div style="background-color:#e8f4f8; padding:10px; border-radius:8px; margin-bottom:20px;">
    <p>您可以将所有预测历史记录导出为CSV或JSON格式文件，方便进行后续分析或存档。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 选择导出格式
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        export_format = st.radio(
            "选择导出格式:",
            ["CSV", "JSON"],
            horizontal=True,
            help="CSV格式适合在Excel等电子表格软件中打开，JSON格式适合程序处理"
        )
    
    # 导出按钮
    if st.button("📥 生成导出文件", use_container_width=True):
        with st.spinner("正在准备导出文件..."):
            format_lower = export_format.lower()
            
            try:
                # 导出数据
                if format_lower == 'csv':
                    data = export_history(format='csv')
                    mime_type = "text/csv"
                    file_ext = "csv"
                    icon = "📊"
                elif format_lower == 'json':
                    data = export_history(format='json')
                    mime_type = "application/json"
                    file_ext = "json"
                    icon = "📝"
                else:
                    st.error(f"不支持的格式: {format_lower}")
                    return
                
                # 生成文件名
                current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"cifar100_predictions_{current_time}.{file_ext}"
                
                # 创建下载链接
                b64 = base64.b64encode(data.encode()).decode()
                href = f'<div style="text-align:center; margin-top:20px;"><a href="data:{mime_type};base64,{b64}" download="{filename}" style="background-color:#4CAF50; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">{icon} 下载 {export_format} 文件</a></div>'
                st.markdown(href, unsafe_allow_html=True)
                
                st.success(f"{export_format} 格式的预测历史已准备好下载")
                
            except Exception as e:
                st.error(f"导出失败: {str(e)}")
    
    # 添加帮助信息
    with st.expander("导出文件包含哪些信息?"):
        st.markdown("""
        导出的文件包含以下信息:
        - 预测ID
        - 预测时间
        - 图片路径
        - 预测结果(类别和概率)
        - 用户反馈(如果有)
        
        这些数据可以用于:
        - 分析模型预测性能
        - 建立预测记录档案
        - 进行更深入的数据分析
        """)

# 保留此函数以避免导入错误，但实际上不再使用
def data_visualization():
    pass 