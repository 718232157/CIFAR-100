import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import pandas as pd
from PIL import Image
from datetime import datetime
from utils.db import save_prediction
from utils.image_utils import get_image_exif
from utils.styles import get_result_card_style, get_batch_result_header

def display_prediction_result(image_path, prediction_result):
    """显示单张图片的预测结果
    
    创建美观、信息丰富的预测结果展示，包括置信度图表和详细分析
    
    Args:
        image_path: 图片路径
        prediction_result: 预测结果列表，包含类别和概率
        
    Returns:
        int: 记录ID
    """
    if not prediction_result:
        st.error("❌ 预测失败，无法获取结果")
        return
    
    # 保存预测结果到数据库
    record_id = save_prediction(image_path, prediction_result)
    
    # 只获取最可能的结果
    top_result = prediction_result[0]
    
    # 创建结果容器
    st.markdown("### 📊 分类结果")
    
    # 使用卡片样式展示主要结果
    main_result_container = st.container()
    with main_result_container:
        # 创建两列布局
        col1, col2 = st.columns([1, 1.2])
        
        with col1:
            # 图片容器
            img_container = st.container()
            with img_container:
                # 显示图片
                try:
                    img = Image.open(image_path)
                    st.image(img, caption="分类图片", use_container_width=True)
                    
                    # 提取图片信息
                    img_info = get_image_exif(image_path)
                    
                    # 显示图片基本信息
                    with st.expander("查看图片信息", expanded=False):
                        st.markdown(f"""
                        **文件名**: {os.path.basename(image_path)}  
                        **图片尺寸**: {img.width} x {img.height} 像素  
                        **文件大小**: {os.path.getsize(image_path) / 1024:.1f} KB  
                        **添加时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        """)
                        
                        # 显示EXIF信息
                        if img_info:
                            st.markdown("**EXIF信息**:")
                            for key, value in img_info.items():
                                st.markdown(f"- **{key}**: {value}")
                except Exception as e:
                    st.error(f"图片显示错误: {str(e)}")
        
        with col2:
            # 创建样式化的结果卡片
            st.markdown(get_result_card_style(top_result), unsafe_allow_html=True)
            
            # 显示预测结果详情
            st.markdown("#### 详细分析")
            
            # 创建预测结果数据框
            results_df = pd.DataFrame(prediction_result)
            
            # 使用plotly创建可视化图表
            fig = px.bar(
                results_df, 
                x='probability', 
                y='class_name',
                orientation='h',
                labels={'probability': '置信度 (%)', 'class_name': '类别'},
                title='前5个最可能的类别',
                color='probability',
                color_continuous_scale='Viridis',
                height=300
            )
            
            # 自定义图表
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(autorange="reversed"),
                xaxis=dict(range=[0, 100]),
                coloraxis_showscale=False,
                margin=dict(l=0, r=0, t=40, b=0)
            )
            
            # 显示图表
            st.plotly_chart(fig, use_container_width=True)
    
    # 添加分析结果
    with st.expander("📝 分类分析", expanded=True):
        # 计算前两个结果之间的差距
        if len(prediction_result) > 1:
            confidence_gap = prediction_result[0]['probability'] - prediction_result[1]['probability']
            
            # 分析置信度情况
            if prediction_result[0]['probability'] > 90:
                confidence_status = "非常高"
                analysis = "系统对此分类有很高的确信度。"
            elif prediction_result[0]['probability'] > 70:
                confidence_status = "高"
                analysis = "系统对此分类有较高的确信度。"
            elif prediction_result[0]['probability'] > 50:
                confidence_status = "中等"
                analysis = "系统对此分类有中等确信度。"
            else:
                confidence_status = "低"
                analysis = "系统对此分类的确信度较低，图像可能包含混合特征或不在训练数据集中。"
            
            # 分析与第二可能结果的差距
            if confidence_gap > 50:
                gap_analysis = "与第二可能类别差距显著，分类结果可信度高。"
            elif confidence_gap > 20:
                gap_analysis = "与第二可能类别有明显差距。"
            elif confidence_gap > 10:
                gap_analysis = "与第二可能类别差距适中。"
            else:
                gap_analysis = "与第二可能类别差距较小，图像可能同时具有多个类别的特征。"
            
            # 显示分析
            st.markdown(f"""
            #### 置信度分析
            - **最高置信度**: {prediction_result[0]['probability']:.2f}% ({confidence_status})
            - **第二可能类别**: {prediction_result[1]['class_name']} ({prediction_result[1]['probability']:.2f}%)
            - **置信度差距**: {confidence_gap:.2f}%
            
            #### 分析结论
            {analysis} {gap_analysis}
            """)
            
            # 可视化置信度差距
            col1, col2 = st.columns(2)
            with col1:
                fig = go.Figure()
                
                # 添加置信度对比
                categories = [r['class_name'] for r in prediction_result]
                values = [r['probability'] for r in prediction_result]
                
                fig.add_trace(go.Pie(
                    labels=categories,
                    values=values,
                    hole=.3,
                    textinfo='label+percent',
                    insidetextorientation='radial'
                ))
                
                fig.update_layout(
                    title_text="置信度分布",
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                # 创建雷达图
                categories = [r['class_name'] for r in prediction_result]
                values = [r['probability'] for r in prediction_result]
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name='置信度分布'
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )
                    ),
                    title="特征分布",
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0),
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # 提供分享选项
    st.markdown("""
    <div style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin-top: 20px;">
        <p style="margin: 0;">您可以在"历史记录"页面中查看此分类记录，或使用"数据导出"功能导出分析结果。</p>
    </div>
    """, unsafe_allow_html=True)
    
    return record_id

def display_batch_predictions(image_paths, batch_results):
    """显示多张图片的预测结果
    
    创建美观、信息丰富的批量预测结果展示，包括网格视图和统计分析
    
    Args:
        image_paths: 图片路径列表
        batch_results: 预测结果列表
        
    Returns:
        list: 记录ID列表
    """
    if not batch_results or len(batch_results) != len(image_paths):
        st.error("❌ 批量预测失败，结果数量与图片数量不匹配")
        return []
    
    # 标题
    st.markdown("### 📊 批量分类结果")
    
    # 保存所有预测结果
    record_ids = []
    top_classes = []
    top_probabilities = []
    
    for img_path, result in zip(image_paths, batch_results):
        record_id = save_prediction(img_path, result)
        record_ids.append(record_id)
        top_classes.append(result[0]['class_name'])
        top_probabilities.append(result[0]['probability'])
    
    # 显示总览信息
    st.markdown(f"""
    <div style="padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
            <div style="min-width: 200px; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #1976D2;">批量处理总览</h4>
                <p style="margin: 5px 0 0 0;">共处理 <strong>{len(image_paths)}</strong> 张图片</p>
            </div>
            <div style="min-width: 200px; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #1976D2;">平均置信度</h4>
                <p style="margin: 5px 0 0 0;"><strong>{sum(top_probabilities) / len(top_probabilities):.2f}%</strong></p>
            </div>
            <div style="min-width: 200px; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #1976D2;">最常见类别</h4>
                <p style="margin: 5px 0 0 0;"><strong>{max(set(top_classes), key=top_classes.count)}</strong></p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 添加统计分析选项卡
    tab1, tab2 = st.tabs(["图片网格视图", "统计分析"])
    
    with tab1:
        # 创建网格显示
        num_images = len(image_paths)
        cols_per_row = min(4, len(image_paths))
        
        # 计算每行应该有多少列
        rows = []
        for i in range(0, num_images, cols_per_row):
            rows.append(image_paths[i:i+cols_per_row])
        
        # 逐行创建列
        for row_idx, row_images in enumerate(rows):
            cols = st.columns(cols_per_row)
            
            for col_idx, img_path in enumerate(row_images):
                result_idx = row_idx * cols_per_row + col_idx
                if result_idx < num_images:
                    with cols[col_idx]:
                        # 当前图片的预测结果
                        result = batch_results[result_idx]
                        top_result = result[0]
                        
                        # 创建卡片布局
                        st.markdown(get_batch_result_header(result_idx), unsafe_allow_html=True)
                        
                        # 显示图片
                        st.image(img_path, use_container_width=True)
                        
                        # 显示主要预测结果
                        confidence_color = "#4CAF50" if top_result['probability'] > 70 else "#FF9800" if top_result['probability'] > 50 else "#F44336"
                        st.markdown(f"<p style='margin: 5px 0; font-weight: bold;'>{top_result['class_name']}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='margin: 5px 0; color: {confidence_color};'>置信度: {top_result['probability']:.2f}%</p>", unsafe_allow_html=True)
                        
                        # 显示次要结果
                        if len(result) > 1:
                            with st.expander("其他可能类别", expanded=False):
                                for i, r in enumerate(result[1:], 2):
                                    st.markdown(f"{i}. {r['class_name']}: {r['probability']:.2f}%")
    
    with tab2:
        # 创建数据框
        analysis_data = pd.DataFrame({
            '图片序号': range(1, len(image_paths) + 1),
            '图片名称': [os.path.basename(path) for path in image_paths],
            '预测类别': top_classes,
            '置信度': top_probabilities
        })
        
        # 显示数据表格
        st.dataframe(analysis_data, use_container_width=True)
        
        # 创建类别统计
        col1, col2 = st.columns(2)
        
        with col1:
            # 统计类别频率
            class_counts = pd.Series(top_classes).value_counts().reset_index()
            class_counts.columns = ['类别', '数量']
            
            # 创建饼图
            fig = px.pie(
                class_counts, 
                values='数量', 
                names='类别',
                title='预测类别分布',
                hole=0.3
            )
            
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            # 置信度分布直方图
            fig = px.histogram(
                analysis_data, 
                x='置信度', 
                nbins=10,
                title='置信度分布',
                color_discrete_sequence=['#1976D2']
            )
            
            fig.update_layout(
                xaxis_title='置信度 (%)',
                yaxis_title='图片数量',
                margin=dict(l=0, r=0, t=40, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 汇总统计
        st.markdown("#### 汇总统计")
        
        # 计算统计数据
        avg_conf = np.mean(top_probabilities)
        median_conf = np.median(top_probabilities)
        min_conf = np.min(top_probabilities)
        max_conf = np.max(top_probabilities)
        
        # 创建统计卡片
        stat_cols = st.columns(4)
        
        with stat_cols[0]:
            st.metric("平均置信度", f"{avg_conf:.2f}%")
        
        with stat_cols[1]:
            st.metric("中位数置信度", f"{median_conf:.2f}%")
        
        with stat_cols[2]:
            st.metric("最低置信度", f"{min_conf:.2f}%")
        
        with stat_cols[3]:
            st.metric("最高置信度", f"{max_conf:.2f}%")
    
    # 提供导出选项
    st.markdown("""
    <div style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin-top: 20px;">
        <p style="margin: 0;">批量分类结果已保存到历史记录中。您可以在"历史记录"页面查看所有分类，或使用"数据导出"功能导出分析结果。</p>
    </div>
    """, unsafe_allow_html=True)
    
    return record_ids 