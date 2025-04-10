import streamlit as st
import pandas as pd
import os
from datetime import datetime
import json
import plotly.express as px
import sqlite3
from utils.db import (
    get_history, delete_record, clear_history, get_history_count, 
    batch_delete_records, get_class_statistics, get_categories,
    get_history_by_category, get_history_count_by_category
)
import html
from utils.styles import tooltip_css, feedback_css

# 导入数据库路径常量
from utils.db import DB_PATH

def show_history():
    """显示历史记录页面，包含搜索、筛选和详情查看功能"""
    # 添加自定义CSS，为长文本创建更好的工具提示效果
    st.markdown(f"<style>{tooltip_css}</style>", unsafe_allow_html=True)
    
    st.subheader("📜 预测历史记录")
    
    # 初始化会话状态
    if 'page' not in st.session_state:
        st.session_state.page = 0
    if 'records_per_page' not in st.session_state:
        st.session_state.records_per_page = 20
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ""
    if 'sort_by' not in st.session_state:
        st.session_state.sort_by = "timestamp"
    if 'sort_order' not in st.session_state:
        st.session_state.sort_order = "DESC"
    if 'selected_records' not in st.session_state:
        st.session_state.selected_records = []
    if 'history_view' not in st.session_state:
        st.session_state.history_view = "全部记录"
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = None
    if 'view_redirect' not in st.session_state:
        st.session_state.view_redirect = None
    
    # 处理重定向（如果需要从类别概览切换到类别视图）
    if st.session_state.view_redirect:
        action, params = st.session_state.view_redirect
        if action == "switch_to_category":
            st.session_state.selected_category = params
            st.session_state.page = 0
            st.session_state.history_view = "按类别查看"
            # 清除重定向，避免循环
            st.session_state.view_redirect = None
    
    # 获取所有类别
    categories = ["全部"] + get_categories()
    available_categories = categories[1:]  # 排除"全部"选项
    
    st.radio(
        "查看方式",
        ["全部记录", "按类别查看"],
        key="history_view",
        horizontal=True,
        on_change=lambda: setattr(st.session_state, 'page', 0)
    )
    
    if st.session_state.history_view == "按类别查看":
        # 安全检查：如果选择的类别不在可用类别列表中，重置为第一个可用类别
        original_category = st.session_state.selected_category  # 保存原始类别名称
        
        if original_category not in available_categories:
            if available_categories:
                # 在更新类别前先显示警告
                st.warning(f"之前选择的类别'{original_category}'不可用，已切换到'{available_categories[0]}'")
                st.session_state.selected_category = available_categories[0]
            else:
                st.warning(f"之前选择的类别'{original_category}'不可用，且当前没有可用的类别")
                st.session_state.selected_category = None
        
        # 类别选择器
        if available_categories:
            selected_index = 0
            if st.session_state.selected_category in available_categories:
                selected_index = available_categories.index(st.session_state.selected_category)
                
            selected_category = st.selectbox(
                "选择类别",
                options=available_categories,
                index=selected_index,
                on_change=lambda: setattr(st.session_state, 'page', 0)
            )
            st.session_state.selected_category = selected_category
            
            # 显示类别浏览器
            show_category_browser(selected_category)
        else:
            st.info("暂无可用类别数据")
    else:
        # 重置选择的类别
        st.session_state.selected_category = None
        
        # 显示全部记录
        show_all_history()

def show_category_browser(category):
    """显示指定类别的历史记录"""
    if not category:
        st.info("请选择一个类别")
        return
    
    # 视图选择器
    view_options = ["表格视图", "图片视图"]
    view_mode = st.radio(
        "查看方式",
        view_options,
        horizontal=True,
        key="category_view_mode"
    )
    
    if view_mode == "图片视图":
        show_category_gallery(category)
        return
    
    # 搜索和过滤控件
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search = st.text_input("🔍 搜索记录", value=st.session_state.search_term, key="category_search")
        if search != st.session_state.search_term:
            st.session_state.search_term = search
            st.session_state.page = 0  # 重置页码
    
    with col2:
        sort_options = {
            "timestamp": "时间",
            "id": "ID"
        }
        sort_by = st.selectbox(
            "排序依据", 
            options=list(sort_options.keys()),
            format_func=lambda x: sort_options[x],
            index=list(sort_options.keys()).index(st.session_state.sort_by),
            key="category_sort_by"
        )
        if sort_by != st.session_state.sort_by:
            st.session_state.sort_by = sort_by
            st.session_state.page = 0  # 重置页码
    
    with col3:
        order_options = {
            "DESC": "降序",
            "ASC": "升序"
        }
        sort_order = st.selectbox(
            "排序方式", 
            options=list(order_options.keys()),
            format_func=lambda x: order_options[x],
            index=list(order_options.keys()).index(st.session_state.sort_order),
            key="category_sort_order"
        )
        if sort_order != st.session_state.sort_order:
            st.session_state.sort_order = sort_order
            st.session_state.page = 0  # 重置页码
    
    # 获取该类别总记录数
    total_records = get_history_count(st.session_state.search_term, category)
    
    if total_records == 0:
        st.info(f"暂无「{category}」类别的历史记录")
        return
    
    # 管理控件
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 批量删除类别记录按钮
        if st.button(f"🗑️ 删除全部「{category}」类别记录"):
            st.warning(f"确定要删除全部「{category}」类别记录吗？此操作不可撤销！")
            delete_confirm = st.button("确认删除", key="confirm_delete_category")
            if delete_confirm:
                # 获取该类别所有记录ID
                all_records = get_history_by_category(category, limit=10000)
                record_ids = [r['id'] for r in all_records]
                if record_ids:
                    deleted = batch_delete_records(record_ids)
                    st.success(f"已删除 {deleted} 条「{category}」类别记录")
                    st.session_state.page = 0
                    st.session_state.selected_records = []
                    st.rerun()
    
    with col2:
        # 批量删除按钮
        if st.session_state.selected_records:
            if st.button(f"🗑️ 删除选中的 {len(st.session_state.selected_records)} 条记录", key="delete_selected_category"):
                st.warning("确定要删除选中的记录吗？此操作不可撤销！")
                delete_confirm = st.button("确认删除", key="confirm_delete_selected_category")
                if delete_confirm:
                    deleted = batch_delete_records(st.session_state.selected_records)
                    st.success(f"已删除 {deleted} 条记录")
                    st.session_state.selected_records = []
                    st.rerun()
    
    # 分页控件
    total_pages = (total_records - 1) // st.session_state.records_per_page + 1
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("◀️ 上一页", disabled=st.session_state.page <= 0, key="prev_category"):
            st.session_state.page -= 1
            st.rerun()
    
    with col2:
        st.write(f"「{category}」类别 - 第 {st.session_state.page + 1} 页，共 {total_pages} 页，总计 {total_records} 条记录")
    
    with col3:
        if st.button("下一页 ▶️", disabled=st.session_state.page >= total_pages - 1, key="next_category"):
            st.session_state.page += 1
            st.rerun()
    
    # 每页显示记录数
    st.session_state.records_per_page = st.select_slider(
        "每页显示记录数", 
        options=[10, 20, 50, 100],
        value=st.session_state.records_per_page,
        key="records_per_page_category"
    )
    
    # 计算偏移量
    offset = st.session_state.page * st.session_state.records_per_page
    
    # 获取历史记录
    history = get_history(
        limit=st.session_state.records_per_page,
        offset=offset,
        search_term=st.session_state.search_term,
        sort_by=st.session_state.sort_by,
        sort_order=st.session_state.sort_order,
        category=category
    )
    
    # 显示历史记录表格
    display_history_table(history)
    
    # 显示统计信息
    with st.expander(f"📊 「{category}」类别统计"):
        st.info(f"类别「{category}」总共有 {total_records} 条记录")
        show_category_statistics(category)

def show_category_gallery(category):
    """以图片库方式显示特定类别的图片"""
    # 获取该类别总记录数
    total_records = get_history_count_by_category(category)
    
    if total_records == 0:
        st.info(f"暂无「{category}」类别的历史记录")
        return
    
    st.subheader(f"「{category}」类别图片库 - 共 {total_records} 张图片")
    
    # 每行显示的图片数
    cols_per_row = st.slider("每行显示图片数", min_value=2, max_value=6, value=4)
    
    # 每页显示的图片数
    st.session_state.gallery_per_page = st.select_slider(
        "每页显示图片数", 
        options=[12, 24, 36, 48],
        value=24,
        key=f"gallery_per_page_{category}"
    )
    
    # 分页控件
    total_pages = (total_records - 1) // st.session_state.gallery_per_page + 1
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("◀️ 上一页", disabled=st.session_state.page <= 0, key=f"gallery_prev_{category}"):
            st.session_state.page -= 1
            st.rerun()
    
    with col2:
        st.write(f"第 {st.session_state.page + 1} 页，共 {total_pages} 页")
    
    with col3:
        if st.button("下一页 ▶️", disabled=st.session_state.page >= total_pages - 1, key=f"gallery_next_{category}"):
            st.session_state.page += 1
            st.rerun()
    
    # 计算偏移量
    offset = st.session_state.page * st.session_state.gallery_per_page
    
    # 获取历史记录
    history = get_history(
        limit=st.session_state.gallery_per_page,
        offset=offset,
        sort_by="timestamp",
        sort_order="DESC",
        category=category
    )
    
    if not history:
        st.warning("无法加载图片")
        return
    
    # 显示图片网格
    rows = []
    current_row = []
    
    for i, record in enumerate(history):
        if i % cols_per_row == 0 and current_row:
            rows.append(current_row)
            current_row = []
        
        current_row.append(record)
    
    if current_row:
        rows.append(current_row)
    
    # 显示每一行的图片
    for row in rows:
        cols = st.columns(cols_per_row)
        
        for i, record in enumerate(row):
            with cols[i]:
                if os.path.exists(record['image_path']):
                    # 显示图片
                    st.image(record['image_path'], caption=f"ID: {record['id']}", use_container_width=True)
                    
                    # 显示主要预测结果
                    top1_class = record['prediction_result'][0]['class_name'] if record['prediction_result'] else "未知"
                    top1_prob = record['prediction_result'][0]['probability'] if record['prediction_result'] else 0
                    st.caption(f"{top1_class} ({top1_prob:.2f}%)")
                    
                    # 避免使用嵌套列，直接显示按钮
                    view_btn = st.button("查看详情", key=f"view_{record['id']}")
                    if view_btn:
                        st.session_state.view_record_id = record['id']
                        st.rerun()
                    
                    delete_btn = st.button("🗑️ 删除", key=f"gallery_delete_{record['id']}")
                    if delete_btn:
                        with st.spinner(f"删除记录 #{record['id']}..."):
                            delete_record(record['id'])
                            # 如果该记录在选中记录中，移除它
                            if record['id'] in st.session_state.selected_records:
                                st.session_state.selected_records.remove(record['id'])
                            st.success(f"记录 #{record['id']} 已删除")
                            st.rerun()
                else:
                    st.info("图片已删除")
    
    # 显示选中图片的详细信息
    if 'view_record_id' in st.session_state and st.session_state.view_record_id:
        show_record_detail(st.session_state.view_record_id)

def show_record_detail(record_id):
    """显示记录详情"""
    # 获取记录详情
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM prediction_history WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    
    if not row:
        st.error(f"找不到ID为 {record_id} 的记录")
        return
    
    record = dict(row)
    record['prediction_result'] = json.loads(record['prediction_result'])
    
    conn.close()
    
    # 显示详情对话框
    with st.expander("图片详情", expanded=True):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if os.path.exists(record['image_path']):
                st.image(record['image_path'], caption=f"图片 ID: {record_id}", use_container_width=True)
            else:
                st.warning("图片文件不存在或已被删除")
        
        with col2:
            st.markdown(f"**记录ID:** {record['id']}")
            st.markdown(f"**时间:** {record['timestamp']}")
            st.markdown(f"**类别:** {record['category'] if 'category' in record else '未知'}")
            st.markdown(f"**图片路径:** {record['image_path']}")
            
            # 显示预测结果
            st.markdown("**预测结果:**")
            for result in record['prediction_result']:
                st.markdown(f"- {result['class_name']}: {result['probability']:.2f}%")
            
            # 显示反馈
            if record['feedback']:
                try:
                    feedback_data = json.loads(record['feedback'])
                    st.write("📝 **用户反馈:**")
                    
                    # 添加反馈卡片样式
                    st.markdown(f"<style>{feedback_css}</style>", unsafe_allow_html=True)
                    
                    st.markdown('<div class="feedback-detail-card">', unsafe_allow_html=True)
                    
                    if isinstance(feedback_data, dict):
                        # 显示评分
                        if 'rating' in feedback_data:
                            rating = feedback_data['rating']
                            rating_html = "⭐" * rating + "☆" * (5 - rating)
                            st.markdown(f"**评分:** {rating_html} ({rating}/5)")
                        
                        # 显示正确类别（如果用户提供）
                        if 'correct_class' in feedback_data and feedback_data['correct_class']:
                            st.markdown(f"**正确类别:** {feedback_data['correct_class']}")
                            
                        # 显示评论
                        if 'comment' in feedback_data and feedback_data['comment']:
                            st.markdown(f"**评论:** {feedback_data['comment']}")
                        
                        # 显示批量反馈特有字段
                        if 'overall_rating' in feedback_data:
                            st.markdown("**批量分类反馈:**")
                            
                            overall_rating = feedback_data['overall_rating']
                            overall_rating_html = "⭐" * overall_rating + "☆" * (5 - overall_rating)
                            st.markdown(f"**整体准确性评分:** {overall_rating_html} ({overall_rating}/5)")
                            
                            if 'performance_rating' in feedback_data:
                                perf_rating = feedback_data['performance_rating']
                                perf_rating_html = "⭐" * perf_rating + "☆" * (5 - perf_rating)
                                st.markdown(f"**性能评分:** {perf_rating_html} ({perf_rating}/5)")
                            
                            if 'least_accurate_class' in feedback_data and feedback_data['least_accurate_class']:
                                st.markdown(f"**最不准确的类别:** {feedback_data['least_accurate_class']}")
                            
                            if 'batch_size' in feedback_data:
                                st.markdown(f"**批量大小:** {feedback_data['batch_size']}张图片")
                                
                            if 'timestamp' in feedback_data:
                                st.markdown(f"**反馈时间:** {feedback_data['timestamp']}")
                    else:
                        # 处理旧格式或其他格式的反馈
                        st.json(feedback_data)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                except json.JSONDecodeError:
                    # 如果反馈不是JSON格式，直接显示
                    st.text(record['feedback'])
        
        # 删除记录按钮
        if st.button(f"删除记录 #{record_id}", key=f"delete_detail_{record_id}"):
            delete_record(record_id)
            st.success(f"记录 #{record_id} 已删除")
            st.session_state.view_record_id = None
            st.rerun()
        
        # 关闭详情按钮
        if st.button("关闭详情", key="close_detail"):
            st.session_state.view_record_id = None
            st.rerun()

def show_all_history():
    """显示全部历史记录"""
    # 搜索和过滤控件
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search = st.text_input("🔍 搜索记录", value=st.session_state.search_term)
        if search != st.session_state.search_term:
            st.session_state.search_term = search
            st.session_state.page = 0  # 重置页码
    
    with col2:
        sort_options = {
            "timestamp": "时间",
            "id": "ID"
        }
        sort_by = st.selectbox(
            "排序依据", 
            options=list(sort_options.keys()),
            format_func=lambda x: sort_options[x],
            index=list(sort_options.keys()).index(st.session_state.sort_by)
        )
        if sort_by != st.session_state.sort_by:
            st.session_state.sort_by = sort_by
            st.session_state.page = 0  # 重置页码
    
    with col3:
        order_options = {
            "DESC": "降序",
            "ASC": "升序"
        }
        sort_order = st.selectbox(
            "排序方式", 
            options=list(order_options.keys()),
            format_func=lambda x: order_options[x],
            index=list(order_options.keys()).index(st.session_state.sort_order)
        )
        if sort_order != st.session_state.sort_order:
            st.session_state.sort_order = sort_order
            st.session_state.page = 0  # 重置页码
    
    # 获取总记录数
    total_records = get_history_count(st.session_state.search_term)
    
    if total_records == 0:
        st.info("暂无历史记录")
        return
    
    # 管理控件
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # 清空历史按钮
        if st.button("🗑️ 清空所有历史记录"):
            st.warning("确定要清空所有历史记录吗？此操作不可撤销！")
            clear_confirm = st.button("确认清空")
            if clear_confirm:
                clear_history()
                st.success("历史记录已清空")
                st.session_state.page = 0
                st.session_state.selected_records = []
                st.rerun()
    
    with col2:
        # 批量删除按钮
        if st.session_state.selected_records:
            if st.button(f"🗑️ 删除选中的 {len(st.session_state.selected_records)} 条记录"):
                st.warning("确定要删除选中的记录吗？此操作不可撤销！")
                delete_confirm = st.button("确认删除")
                if delete_confirm:
                    deleted = batch_delete_records(st.session_state.selected_records)
                    st.success(f"已删除 {deleted} 条记录")
                    st.session_state.selected_records = []
                    st.rerun()
    
    # 分页控件
    total_pages = (total_records - 1) // st.session_state.records_per_page + 1
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("◀️ 上一页", disabled=st.session_state.page <= 0):
            st.session_state.page -= 1
            st.rerun()
    
    with col2:
        st.write(f"第 {st.session_state.page + 1} 页，共 {total_pages} 页，总计 {total_records} 条记录")
    
    with col3:
        if st.button("下一页 ▶️", disabled=st.session_state.page >= total_pages - 1):
            st.session_state.page += 1
            st.rerun()
    
    # 每页显示记录数
    st.session_state.records_per_page = st.select_slider(
        "每页显示记录数", 
        options=[10, 20, 50, 100],
        value=st.session_state.records_per_page
    )
    
    # 计算偏移量
    offset = st.session_state.page * st.session_state.records_per_page
    
    # 获取历史记录
    history = get_history(
        limit=st.session_state.records_per_page,
        offset=offset,
        search_term=st.session_state.search_term,
        sort_by=st.session_state.sort_by,
        sort_order=st.session_state.sort_order
    )
    
    # 显示历史记录表格
    display_history_table(history)
    
    # 显示统计信息
    with st.expander("📊 预测统计"):
        history_statistics()

def display_history_table(history):
    """显示历史记录表格"""
    # 转换数据为表格显示
    table_data = []
    
    for record in history:
        # 获取top1预测结果
        top1_class = record['prediction_result'][0]['class_name'] if record['prediction_result'] else "未知"
        top1_prob = record['prediction_result'][0]['probability'] if record['prediction_result'] else 0
        
        # 检查图片是否存在
        image_exists = os.path.exists(record['image_path'])
        
        # 处理反馈数据，提供简洁摘要
        feedback_summary = "无"
        if record['feedback']:
            try:
                feedback_data = json.loads(record['feedback'])
                if isinstance(feedback_data, dict):
                    if 'rating' in feedback_data:
                        rating = feedback_data['rating']
                        feedback_summary = f"⭐ 评分: {rating}/5"
                        if feedback_data.get('comment'):
                            feedback_summary += " (含评论)"
                    elif 'overall_rating' in feedback_data:
                        overall_rating = feedback_data['overall_rating']
                        feedback_summary = f"🔢 批量评分: {overall_rating}/5"
                        if feedback_data.get('least_accurate_class'):
                            feedback_summary += " (含详情)"
            except:
                feedback_summary = "📝 已提供"
        
        table_data.append({
            "选择": record['id'],
            "ID": record['id'],
            "时间": record['timestamp'],
            "预测类别": top1_class,
            "置信度": f"{top1_prob:.2f}%",
            "图片状态": "可查看" if image_exists else "已删除",
            "反馈": feedback_summary
        })
    
    # 创建DataFrame
    df = pd.DataFrame(table_data)
    
    # 多选框
    selected_ids = st.multiselect(
        "选择记录",
        options=df["选择"].tolist(),
        default=st.session_state.selected_records,
        format_func=lambda x: f"ID: {x}"
    )
    st.session_state.selected_records = selected_ids
    
    # 显示表格，不显示选择列
    display_df = df.drop(columns=["选择"])
    st.dataframe(display_df, use_container_width=True)
    
    # 添加查看反馈功能
    st.markdown("---")
    st.subheader("📋 反馈详情查看器")
    
    # 添加引导信息
    st.info("""
    **在表格中，反馈列显示了简要信息。要查看完整反馈内容，您可以：**
    1. 在表格右侧的快速操作中点击 📝 按钮
    2. 或在下方选择一条记录查看详细反馈
    
    ⭐ 表示单张图片的反馈，🔢 表示批量分类的反馈
    """)
    
    # 会话状态初始化
    if 'viewing_feedback_id' not in st.session_state:
        st.session_state.viewing_feedback_id = None
    
    # 创建反馈查看标签页
    feedback_tabs = st.tabs(["选择记录", "反馈详情"])
    
    with feedback_tabs[0]:
        st.write("选择记录ID查看详细反馈：")
        records_with_feedback = [r for r in history if r['feedback']]
        
        if not records_with_feedback:
            st.info("没有包含反馈的记录")
        else:
            feedback_record_ids = [r['id'] for r in records_with_feedback]
            selected_feedback_id = st.selectbox(
                "包含反馈的记录",
                options=feedback_record_ids,
                format_func=lambda x: f"ID: {x}"
            )
            
            if st.button("显示反馈详情"):
                st.session_state.viewing_feedback_id = selected_feedback_id
                st.rerun()
    
    with feedback_tabs[1]:
        if st.session_state.viewing_feedback_id:
            selected_feedback_record = next((r for r in history if r['id'] == st.session_state.viewing_feedback_id), None)
            
            if selected_feedback_record and selected_feedback_record['feedback']:
                st.write(f"#### 记录 #{selected_feedback_record['id']} 的反馈详情")
                
                # 显示记录基本信息
                st.write(f"**预测类别:** {selected_feedback_record['prediction_result'][0]['class_name']}")
                st.write(f"**时间:** {selected_feedback_record['timestamp']}")
                
                # 解析并显示反馈
                try:
                    feedback_data = json.loads(selected_feedback_record['feedback'])
                    
                    if isinstance(feedback_data, dict):
                        st.write("##### 用户反馈:")
                        
                        # 使用卡片样式显示反馈
                        st.markdown(f"<style>{feedback_css}</style>", unsafe_allow_html=True)
                        
                        st.markdown('<div class="feedback-card">', unsafe_allow_html=True)
                        
                        # 单条反馈
                        if 'rating' in feedback_data:
                            rating = feedback_data['rating']
                            rating_html = "⭐" * rating + "☆" * (5 - rating)
                            st.markdown(f"**评分:** {rating_html} ({rating}/5)")
                            
                            if 'correct_class' in feedback_data and feedback_data['correct_class']:
                                st.markdown(f"**正确类别:** {feedback_data['correct_class']}")
                                
                            if 'comment' in feedback_data and feedback_data['comment']:
                                st.markdown(f"**评论:** {feedback_data['comment']}")
                        
                        # 批量反馈
                        if 'overall_rating' in feedback_data:
                            st.markdown("#### 批量分类反馈:")
                            
                            overall_rating = feedback_data['overall_rating']
                            overall_rating_html = "⭐" * overall_rating + "☆" * (5 - overall_rating)
                            st.markdown(f"**整体准确性评分:** {overall_rating_html} ({overall_rating}/5)")
                            
                            if 'performance_rating' in feedback_data:
                                perf_rating = feedback_data['performance_rating']
                                perf_rating_html = "⭐" * perf_rating + "☆" * (5 - perf_rating)
                                st.markdown(f"**性能评分:** {perf_rating_html} ({perf_rating}/5)")
                                
                            if 'least_accurate_class' in feedback_data and feedback_data['least_accurate_class']:
                                st.markdown(f"**最不准确的类别:** {feedback_data['least_accurate_class']}")
                                
                            if 'batch_size' in feedback_data:
                                st.markdown(f"**批量大小:** {feedback_data['batch_size']}张图片")
                                
                            if 'timestamp' in feedback_data:
                                st.markdown(f"**反馈时间:** {feedback_data['timestamp']}")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        # 处理旧格式反馈
                        st.json(feedback_data)
                except json.JSONDecodeError:
                    st.text(selected_feedback_record['feedback'])
            else:
                st.info("请选择一条包含反馈的记录")
        else:
            st.info('请在"选择记录"标签页中选择要查看的反馈记录')
    
    # 快速操作部分
    st.subheader("快速操作")
    
    # 设置每行显示几个记录
    num_cols = 3
    record_chunks = [history[i:i + num_cols] for i in range(0, len(history), num_cols)]
    
    # 对每一行记录进行处理
    for chunk in record_chunks:
        cols = st.columns(num_cols)
        
        for i, record in enumerate(chunk):
            with cols[i]:
                record_id = record['id']
                top1_class = record['prediction_result'][0]['class_name'] if record['prediction_result'] else "未知"
                
                # 显示记录基本信息
                st.write(f"ID: {record_id} - {top1_class}")
                
                # 删除按钮
                delete_button = st.button("🗑️", key=f"quick_delete_{record_id}")
                if delete_button:
                    with st.spinner(f"删除记录 #{record_id}..."):
                        delete_record(record_id)
                        if record_id in st.session_state.selected_records:
                            st.session_state.selected_records.remove(record_id)
                        st.success(f"记录 #{record_id} 已删除")
                        st.rerun()
                
                # 查看反馈按钮
                if record['feedback']:
                    view_button = st.button("📝", key=f"view_feedback_{record_id}", help="查看反馈")
                    if view_button:
                        st.session_state.viewing_feedback_id = record_id
                        st.rerun()
                else:
                    st.write("　")  # 使用全角空格作为占位符
    
    # 详细记录查看部分
    with st.expander("查看详细记录"):
        if not history:
            st.info("无记录可查看")
            return
            
        selected_id = st.selectbox("选择记录ID", [r['id'] for r in history], key="detail_record_select")
        
        if selected_id:
            # 找到选中的记录
            selected_record = next((r for r in history if r['id'] == selected_id), None)
            
            if selected_record:
                detail_tabs = st.tabs(["图片", "记录信息", "预测结果", "反馈信息"])
                
                with detail_tabs[0]:
                    if os.path.exists(selected_record['image_path']):
                        st.image(selected_record['image_path'], caption=f"图片 ID: {selected_id}", width=250)
                    else:
                        st.warning("图片文件不存在或已被删除")
                
                with detail_tabs[1]:
                    st.markdown(f"**记录ID:** {selected_record['id']}")
                    st.markdown(f"**时间:** {selected_record['timestamp']}")
                    st.markdown(f"**类别:** {selected_record['category'] if 'category' in selected_record else '未知'}")
                    st.markdown(f"**图片路径:** {selected_record['image_path']}")
                    
                with detail_tabs[2]:
                    st.markdown("**预测结果:**")
                    for result in selected_record['prediction_result']:
                        st.markdown(f"- {result['class_name']}: {result['probability']:.2f}%")
                    
                with detail_tabs[3]:
                    if selected_record['feedback']:
                        try:
                            feedback_data = json.loads(selected_record['feedback'])
                            st.write("📝 **用户反馈:**")
                            
                            st.markdown(f"<style>{feedback_css}</style>", unsafe_allow_html=True)
                            
                            st.markdown('<div class="record-feedback-card">', unsafe_allow_html=True)
                            
                            if isinstance(feedback_data, dict):
                                # 显示单条反馈
                                if 'rating' in feedback_data:
                                    rating = feedback_data['rating']
                                    rating_html = "⭐" * rating + "☆" * (5 - rating)
                                    st.markdown(f"**评分:** {rating_html} ({rating}/5)")
                                    
                                    if 'correct_class' in feedback_data and feedback_data['correct_class']:
                                        st.markdown(f"**正确类别:** {feedback_data['correct_class']}")
                                        
                                    if 'comment' in feedback_data and feedback_data['comment']:
                                        st.markdown(f"**评论:** {feedback_data['comment']}")
                                
                                # 显示批量反馈
                                if 'overall_rating' in feedback_data:
                                    st.markdown("**批量分类反馈:**")
                                    
                                    overall_rating = feedback_data['overall_rating']
                                    overall_rating_html = "⭐" * overall_rating + "☆" * (5 - overall_rating)
                                    st.markdown(f"**整体准确性评分:** {overall_rating_html} ({overall_rating}/5)")
                                    
                                    if 'performance_rating' in feedback_data:
                                        perf_rating = feedback_data['performance_rating']
                                        perf_rating_html = "⭐" * perf_rating + "☆" * (5 - perf_rating)
                                        st.markdown(f"**性能评分:** {perf_rating_html} ({perf_rating}/5)")
                                    
                                    if 'least_accurate_class' in feedback_data and feedback_data['least_accurate_class']:
                                        st.markdown(f"**最不准确的类别:** {feedback_data['least_accurate_class']}")
                                    
                                    if 'batch_size' in feedback_data:
                                        st.markdown(f"**批量大小:** {feedback_data['batch_size']}张图片")
                                        
                                    if 'timestamp' in feedback_data:
                                        st.markdown(f"**反馈时间:** {feedback_data['timestamp']}")
                            else:
                                st.json(feedback_data)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        except json.JSONDecodeError:
                            st.text(selected_record['feedback'])
                    else:
                        st.info("此记录没有反馈信息")
                
                # 操作按钮
                st.write("---")
                button_cols = st.columns(2)
                
                with button_cols[0]:
                    delete_button = st.button(f"删除记录 #{selected_id}", key=f"delete_detail_{selected_id}")
                    if delete_button:
                        delete_record(selected_id)
                        st.success(f"记录 #{selected_id} 已删除")
                        st.session_state.view_record_id = None
                        st.rerun()
                
                with button_cols[1]:
                    close_button = st.button("关闭详情", key="close_detail") 
                    if close_button:
                        st.session_state.view_record_id = None
                        st.rerun()

def show_category_statistics(category):
    """显示特定类别的统计信息"""
    # 获取该类别的记录数量
    count = get_history_count_by_category(category)
    
    # 获取所有类别的统计信息
    all_stats = get_class_statistics()
    total_count = sum([count for _, count in all_stats])
    
    # 计算该类别占总记录的百分比
    if total_count > 0:
        percentage = (count / total_count) * 100
        st.write(f"该类别占总记录的 {percentage:.2f}%")
    
    # 获取该类别的所有记录
    records = get_history_by_category(category, limit=1000)
    
    # 统计反馈情况
    feedback_counts = {}
    for record in records:
        if record['feedback']:
            feedback = record['feedback']
            feedback_counts[feedback] = feedback_counts.get(feedback, 0) + 1
    
    if feedback_counts:
        st.subheader("反馈统计")
        feedback_df = pd.DataFrame(
            [(fb, cnt) for fb, cnt in feedback_counts.items()], 
            columns=["反馈内容", "次数"]
        )
        
        # 使用饼图显示反馈分布
        fig = px.pie(
            feedback_df,
            values="次数",
            names="反馈内容",
            title="反馈分布",
            hole=0.3
        )
        st.plotly_chart(fig, use_container_width=True)

def history_statistics():
    """显示历史记录统计信息"""
    
    # 获取类别统计信息
    class_stats = get_class_statistics()
    
    if not class_stats:
        st.info("暂无数据，无法生成统计信息")
        return
    
    # 转换为DataFrame用于显示
    df = pd.DataFrame(class_stats, columns=["类别", "次数"])
    
    # 类别导航链接
    st.subheader("类别快速导航")
    col_count = 4  # 每行显示的类别数
    categories = df["类别"].tolist()
    
    # 按行分组显示类别
    for i in range(0, len(categories), col_count):
        cols = st.columns(col_count)
        for j in range(col_count):
            idx = i + j
            if idx < len(categories):
                with cols[j]:
                    if st.button(f"{categories[idx]} ({df.iloc[idx]['次数']})", key=f"cat_{categories[idx]}"):
                        # 使用browse_category函数进行导航
                        browse_category(categories[idx])
    
    # 限制显示的类别数量
    display_limit = st.slider("显示前N个类别", min_value=5, max_value=min(50, len(class_stats)), value=10)
    display_df = df.head(display_limit)
    
    # 使用plotly创建交互式图表
    fig = px.bar(
        display_df, 
        x="类别", 
        y="次数",
        title="预测类别分布",
        labels={"类别": "预测类别", "次数": "出现次数"},
        color="次数",
        color_continuous_scale="Viridis"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 饼图显示比例
    pie_fig = px.pie(
        display_df,
        values="次数",
        names="类别",
        title="预测类别比例分布",
        hole=0.3
    )
    
    st.plotly_chart(pie_fig, use_container_width=True)
    
    # 显示统计数据表格
    st.subheader("详细统计数据")
    st.dataframe(display_df, use_container_width=True)

def browse_category(category):
    """浏览特定类别的图片（设置重定向）"""
    # 使用重定向机制而不是直接修改history_view
    st.session_state.view_redirect = ("switch_to_category", category)
    st.rerun()

def display_truncated_text(label, text, max_length=50):
    """创建显示截断文本的函数，当鼠标悬停时显示完整文本
    
    Args:
        label: 文本标签（例如"评论"）
        text: 完整文本内容
        max_length: 显示的最大长度
    """
    if text is None:
        return st.markdown(f"<div><strong>{label}:</strong> 无</div>", unsafe_allow_html=True)
    
    escaped_text = html.escape(str(text))
    
    # 检查文本是否需要截断
    if len(str(text)) > max_length:
        display_text = escaped_text[:max_length] + "..."
        st.markdown(f"""
        <div class="tooltip-container">
            <div><strong>{label}:</strong> <span class="tooltip-content">{display_text}</span>
            <span style="color: #888; font-size: 0.8em;">(鼠标悬停查看全部)</span></div>
            <div class="full-text">{escaped_text}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 如果文本不需要截断，直接显示
        st.markdown(f"<div><strong>{label}:</strong> {escaped_text}</div>", unsafe_allow_html=True) 