import streamlit as st
from utils.db import save_feedback
import uuid
import json
import os
import datetime
import pandas as pd

# 添加保存反馈到本地文件的功能
def save_general_feedback_to_file(feedback_data):
    """将通用反馈保存到本地文件"""
    # 确保data/feedback目录存在
    feedback_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'feedback')
    os.makedirs(feedback_dir, exist_ok=True)
    
    # 生成带时间戳的反馈记录
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    feedback_with_time = {
        "timestamp": timestamp,
        **feedback_data
    }
    
    # 反馈文件路径
    feedback_file = os.path.join(feedback_dir, 'user_feedback.json')
    
    # 读取现有反馈
    existing_feedback = []
    if os.path.exists(feedback_file):
        try:
            with open(feedback_file, 'r', encoding='utf-8') as f:
                existing_feedback = json.load(f)
        except json.JSONDecodeError:
            # 如果文件存在但格式不正确，就从头开始
            existing_feedback = []
    
    # 添加新反馈
    existing_feedback.append(feedback_with_time)
    
    # 保存到文件
    with open(feedback_file, 'w', encoding='utf-8') as f:
        json.dump(existing_feedback, f, ensure_ascii=False, indent=2)
    
    # 返回反馈文件路径，方便用户查看
    return feedback_file

def collect_feedback(record_id):
    """收集用户对预测结果的反馈"""
    
    # 初始化会话状态，用于跟踪此记录的反馈状态
    feedback_key = f"feedback_submitted_{record_id}"
    if feedback_key not in st.session_state:
        st.session_state[feedback_key] = False
    
    # 如果已提交反馈，显示感谢信息
    if st.session_state[feedback_key]:
        st.success("✅ 感谢您的反馈！您的意见对我们很重要。")
        
        # 添加重新提交按钮
        if st.button("提交新的反馈", key=f"new_feedback_{record_id}"):
            st.session_state[feedback_key] = False
            st.rerun()
        
        return True
    
    # 如果尚未提交反馈，显示反馈表单
    st.write("### 对预测结果的评价")
    
    # 使用唯一键创建表单，避免冲突
    form_key = f"prediction_feedback_form_{record_id}"
    
    with st.form(key=form_key):
        # 评分
        rating = st.slider("准确性评分", 1, 5, 3, 1, 
                        help="1=完全不准确，5=非常准确")
        
        # 正确类别
        correct_class = st.text_input("如果预测错误，请输入正确的类别:", 
                                  help="如果您知道图片的实际类别，请在此处输入")
        
        # 其他反馈
        comment = st.text_area("其他评论或反馈:")
        
        # 提交按钮
        submit_button = st.form_submit_button(label="提交反馈", use_container_width=True)
        
    # 表单外处理提交
    if submit_button:
        # 构造反馈信息
        feedback_data = {
            "rating": rating,
            "correct_class": correct_class if correct_class else None,
            "comment": comment
        }
        
        # 保存到数据库
        try:
            save_feedback(record_id, json.dumps(feedback_data))
            
            # 更新会话状态，标记为已提交
            st.session_state[feedback_key] = True
            
            # 显示成功消息
            st.success("✅ 感谢您的反馈！您的意见对我们很重要。")
            
            # 触发UI刷新
            st.rerun()
            
            return True
        except Exception as e:
            st.error(f"提交反馈时出错: {str(e)}")
            return False
    
    return False

def collect_batch_feedback(record_ids):
    """收集用户对批量预测结果的整体反馈
    
    Args:
        record_ids: 记录ID列表，对应于批量分类的多个结果
        
    Returns:
        bool: 表示反馈是否已提交
    """
    if not record_ids:
        st.info("没有可评价的批量分类记录")
        return False
    
    # 将列表转换为字符串作为唯一键
    records_key = "_".join([str(id) for id in record_ids])
    
    # 初始化会话状态，用于跟踪此批次的反馈状态
    feedback_key = f"batch_feedback_submitted_{records_key}"
    if feedback_key not in st.session_state:
        st.session_state[feedback_key] = False
    
    # 如果已提交反馈，显示感谢信息
    if st.session_state[feedback_key]:
        st.success("✅ 感谢您的批量分类反馈！您的意见对我们很重要。")
        
        # 添加重新提交按钮
        if st.button("提交新的批量反馈", key=f"new_batch_feedback_{records_key}"):
            st.session_state[feedback_key] = False
            st.rerun()
        
        return True
    
    # 如果尚未提交反馈，显示批量反馈表单
    st.write("### 对批量分类结果的整体评价")
    
    # 使用唯一键创建表单，避免冲突
    form_key = f"batch_feedback_form_{records_key}"
    
    with st.form(key=form_key):
        # 整体评分
        overall_rating = st.slider("整体准确性评分", 1, 5, 3, 1, 
                               help="1=完全不准确，5=非常准确")
        
        # 批量分类算法评分
        performance_rating = st.slider("批量处理性能评分", 1, 5, 3, 1,
                                   help="1=非常慢，5=非常快")
        
        # 最不准确的类别
        least_accurate_class = st.text_input("哪个类别的预测最不准确?", 
                                         help="如果有特定类别的预测不准确，请在此处输入")
        
        # 其他反馈
        batch_comment = st.text_area("其他评论或反馈:")
        
        # 提交按钮
        submit_button = st.form_submit_button(label="提交批量反馈", use_container_width=True)
    
    # 表单外处理提交
    if submit_button:
        try:
            # 构造批量反馈数据
            batch_feedback_data = {
                "overall_rating": overall_rating,
                "performance_rating": performance_rating,
                "least_accurate_class": least_accurate_class if least_accurate_class else None,
                "comment": batch_comment,
                "batch_size": len(record_ids),
                "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 为批次中的每个记录保存相同的批量反馈
            success = True
            for record_id in record_ids:
                feedback_result = save_feedback(record_id, json.dumps(batch_feedback_data))
                if not feedback_result:
                    success = False
            
            if success:
                # 更新会话状态，标记为已提交
                st.session_state[feedback_key] = True
                
                # 显示成功消息
                st.success(f"✅ 感谢您的批量反馈！已成功保存对{len(record_ids)}张图片的评价。")
                
                # 触发UI刷新
                st.rerun()
                
                return True
            else:
                st.error("部分反馈提交失败，请重试")
                return False
        except Exception as e:
            st.error(f"提交批量反馈时出错: {str(e)}")
            return False
    
    return False

def feedback_form():
    """优化后的反馈表单页面"""
    st.subheader("📢 意见反馈")
    
    # 初始化会话状态以跟踪表单提交
    if "feedback_submitted" not in st.session_state:
        st.session_state.feedback_submitted = False
    
    if "form_key" not in st.session_state:
        st.session_state.form_key = str(uuid.uuid4())
    
    # 使用卡片样式的容器
    with st.container():
        st.markdown("""
        <div style="background-color:#f0f2f6; padding:15px; border-radius:10px; margin-bottom:15px">
        <h3 style="color:#1E88E5">您的反馈对我们很重要！</h3>
        <p>请告诉我们您对应用的看法，或报告您遇到的问题。</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 如果尚未提交表单，显示表单
    if not st.session_state.feedback_submitted:
        # 使用简化的表单
        with st.form(key=f"simplified_feedback_form_{st.session_state.form_key}"):
            # 选择反馈类型
            feedback_type = st.radio(
                "反馈类型:",
                ["功能建议", "错误报告", "分类准确度问题", "界面体验", "其他"],
                horizontal=True
            )
            
            # 满意度评分
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write("满意度:")
            with col2:
                satisfaction = st.select_slider(
                    "",
                    options=["非常不满意", "不满意", "一般", "满意", "非常满意"],
                    value="满意"
                )
            
            # 反馈内容
            feedback_content = st.text_area(
                "请详细描述您的反馈:",
                height=120,
                placeholder="请在此输入您的问题、建议或想法..."
            )
            
            # 联系信息（可选）
            with st.expander("留下联系方式（可选）"):
                email = st.text_input("电子邮件:", placeholder="your.email@example.com")
            
            # 提交按钮
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submit_button = st.form_submit_button(
                    label="提交反馈",
                    use_container_width=True,
                )
            
        # 表单外处理提交（这样可以避免一些Streamlit的状态问题）
        if submit_button:
            if not feedback_content:
                st.error("请输入反馈内容后再提交")
            else:
                # 创建反馈数据结构
                feedback_data = {
                    "feedback_type": feedback_type,
                    "satisfaction": satisfaction,
                    "content": feedback_content,
                    "email": email if email else None
                }
                
                # 保存到本地文件
                feedback_file = save_general_feedback_to_file(feedback_data)
                
                # 更新会话状态
                st.session_state.feedback_submitted = True
                st.session_state.feedback_data = feedback_data
                st.session_state.feedback_file = feedback_file
                
                # 刷新页面以显示成功消息
                st.rerun()
    
    # 如果已提交表单，显示成功消息
    else:
        st.success("🎉 感谢您的反馈！我们会认真考虑您的建议。")
        
        # 显示提交的反馈摘要
        if hasattr(st.session_state, 'feedback_data'):
            with st.expander("您提交的反馈", expanded=True):
                st.write(f"**类型:** {st.session_state.feedback_data['feedback_type']}")
                st.write(f"**满意度:** {st.session_state.feedback_data['satisfaction']}")
                st.write(f"**内容:** {st.session_state.feedback_data['content']}")
                
                # 显示反馈文件的保存位置
                if hasattr(st.session_state, 'feedback_file'):
                    st.info(f"您的反馈已保存至: {st.session_state.feedback_file}")
        
        # 添加气球动画
        st.balloons()
        
        # 添加重置按钮，允许用户提交新的反馈
        if st.button("提交新的反馈"):
            st.session_state.feedback_submitted = False
            st.session_state.form_key = str(uuid.uuid4())  # 生成新的表单键
            st.rerun()

def view_feedback_records():
    """查看已保存的反馈记录"""
    st.subheader("📋 反馈记录")
    
    # 反馈文件路径
    feedback_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'feedback')
    feedback_file = os.path.join(feedback_dir, 'user_feedback.json')
    
    if not os.path.exists(feedback_file):
        st.info("暂无反馈记录")
        return
    
    try:
        with open(feedback_file, 'r', encoding='utf-8') as f:
            feedback_records = json.load(f)
        
        if not feedback_records:
            st.info("暂无反馈记录")
            return
        
        # 显示反馈记录总数
        st.write(f"共有 {len(feedback_records)} 条反馈记录")
        
        # 创建数据框
        df = pd.DataFrame(feedback_records)
        
        # 选择显示特定类型的反馈
        if 'feedback_type' in df.columns:
            feedback_types = ["全部"] + sorted(df['feedback_type'].unique().tolist())
            selected_type = st.selectbox("按类型筛选:", feedback_types)
            
            if selected_type != "全部":
                df = df[df['feedback_type'] == selected_type]
        
        # 按时间排序
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp', ascending=False)
        
        # 显示记录
        for i, record in df.iterrows():
            with st.expander(f"反馈 #{i+1} - {record.get('timestamp', '未知时间')}", expanded=False):
                for key, value in record.items():
                    if key not in ['timestamp', 'email']:
                        st.write(f"**{key}:** {value}")
                
                # 如果有联系方式，单独显示
                if 'email' in record and record['email']:
                    st.write(f"**联系方式:** {record['email']}")
    
    except Exception as e:
        st.error(f"读取反馈记录时出错: {str(e)}")
        st.write("请检查反馈文件格式是否正确。") 