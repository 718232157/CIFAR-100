import sqlite3
import json
import os
import pandas as pd
from datetime import datetime

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'history.db')

def init_db():
    """初始化数据库，创建必要的表"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 历史记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prediction_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_path TEXT,
        prediction_result TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        feedback TEXT,
        category TEXT
    )
    ''')
    
    conn.commit()
    conn.close()
    
    # 确保数据目录结构
    categories_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'categories')
    os.makedirs(categories_dir, exist_ok=True)
    
    # 确保数据库结构
    ensure_db_structure()

def save_prediction(image_path, prediction_result):
    """保存预测结果到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 将预测结果转换为JSON字符串
    prediction_json = json.dumps(prediction_result)
    
    # 获取top1预测类别，用于分类
    top1_class = prediction_result[0]['class_name'] if prediction_result else "未知"
    
    # 创建类别文件夹
    category_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'categories', top1_class)
    os.makedirs(category_folder, exist_ok=True)
    
    # 重新保存图片到类别文件夹
    new_image_path = None
    if os.path.exists(image_path):
        # 提取原始文件名
        base_filename = os.path.basename(image_path)
        # 生成新路径
        new_image_path = os.path.join(category_folder, base_filename)
        
        # 如果文件已存在，在文件名前添加时间戳避免冲突
        if os.path.exists(new_image_path):
            filename, ext = os.path.splitext(base_filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            new_image_path = os.path.join(category_folder, f"{filename}_{timestamp}{ext}")
        
        # 拷贝图片
        try:
            from shutil import copy2
            copy2(image_path, new_image_path)
        except Exception as e:
            print(f"图片拷贝失败: {str(e)}")
            new_image_path = image_path  # 失败时使用原路径
    else:
        new_image_path = image_path
    
    cursor.execute(
        "INSERT INTO prediction_history (image_path, prediction_result, timestamp, category) VALUES (?, ?, ?, ?)",
        (new_image_path, prediction_json, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), top1_class)
    )
    
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    
    return last_id

def get_history(limit=100, offset=0, search_term=None, sort_by="timestamp", sort_order="DESC", category=None):
    """获取预测历史记录
    
    参数:
        limit: 每页显示的记录数
        offset: 起始偏移量(用于分页)
        search_term: 搜索关键词(在类别名称和反馈中搜索)
        sort_by: 排序字段(id, timestamp, top1_class)
        sort_order: 排序顺序(ASC或DESC)
        category: 筛选特定类别
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 构建查询语句
    query = "SELECT * FROM prediction_history"
    params = []
    
    # 添加筛选条件
    conditions = []
    
    if category:
        conditions.append("category = ?")
        params.append(category)
    
    if search_term:
        conditions.append("(prediction_result LIKE ? OR feedback LIKE ?)")
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # 添加排序
    sort_column = "timestamp"  # 默认按时间戳排序
    if sort_by == "id":
        sort_column = "id"
    
    query += f" ORDER BY {sort_column} {sort_order}"
    
    # 添加分页
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    
    results = []
    for row in cursor.fetchall():
        record = dict(row)
        record['prediction_result'] = json.loads(record['prediction_result'])
        results.append(record)
    
    conn.close()
    return results

def get_history_count(search_term=None, category=None):
    """获取历史记录总数(用于分页)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 构建查询语句
    query = "SELECT COUNT(*) FROM prediction_history"
    params = []
    
    # 添加筛选条件
    conditions = []
    
    if category:
        conditions.append("category = ?")
        params.append(category)
    
    if search_term:
        conditions.append("(prediction_result LIKE ? OR feedback LIKE ?)")
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

def get_class_statistics():
    """获取类别统计信息"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT prediction_result FROM prediction_history")
    
    class_counts = {}
    for row in cursor.fetchall():
        prediction_result = json.loads(row['prediction_result'])
        if prediction_result:
            top1_class = prediction_result[0]['class_name']
            class_counts[top1_class] = class_counts.get(top1_class, 0) + 1
    
    conn.close()
    
    # 按频率排序
    sorted_counts = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_counts

def batch_delete_records(record_ids):
    """批量删除历史记录"""
    if not record_ids:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    placeholders = ','.join(['?'] * len(record_ids))
    cursor.execute(f"DELETE FROM prediction_history WHERE id IN ({placeholders})", record_ids)
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted_count

def save_feedback(record_id, feedback):
    """保存用户反馈
    
    Args:
        record_id: 记录ID
        feedback: 反馈内容（JSON字符串或Python字典）
        
    Returns:
        bool: 保存是否成功
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 确保feedback是JSON字符串
        if not isinstance(feedback, str):
            feedback = json.dumps(feedback)
        
        cursor.execute(
            "UPDATE prediction_history SET feedback = ? WHERE id = ?",
            (feedback, record_id)
        )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"保存反馈失败: {str(e)}")
        return False

def export_history(format='csv'):
    """导出历史记录为CSV或JSON格式"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM prediction_history ORDER BY timestamp DESC")
    
    results = []
    for row in cursor.fetchall():
        record = dict(row)
        record['prediction_result'] = json.loads(record['prediction_result'])
        # 提取top1预测结果和概率
        if record['prediction_result']:
            record['top1_class'] = record['prediction_result'][0]['class_name']
            record['top1_probability'] = record['prediction_result'][0]['probability']
        results.append(record)
    
    conn.close()
    
    if format == 'csv':
        df = pd.DataFrame(results)
        return df.to_csv(index=False)
    elif format == 'json':
        return json.dumps(results, indent=2)
    else:
        raise ValueError(f"Unsupported format: {format}")

def delete_record(record_id):
    """删除历史记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM prediction_history WHERE id = ?", (record_id,))
    
    conn.commit()
    conn.close()

def clear_history():
    """清空历史记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM prediction_history")
    
    conn.commit()
    conn.close()

# 添加初始化函数，确保数据库表结构包含category字段
def ensure_db_structure():
    """确保数据库表结构包含所需字段"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查是否存在category列
    cursor.execute("PRAGMA table_info(prediction_history)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "category" not in columns:
        cursor.execute("ALTER TABLE prediction_history ADD COLUMN category TEXT")
        
        # 更新现有记录的category字段
        cursor.execute("SELECT id, prediction_result FROM prediction_history")
        for row in cursor.fetchall():
            record_id, prediction_result = row
            prediction_data = json.loads(prediction_result)
            if prediction_data:
                top1_class = prediction_data[0]['class_name']
                cursor.execute("UPDATE prediction_history SET category = ? WHERE id = ?", (top1_class, record_id))
    
    conn.commit()
    conn.close()

def get_categories():
    """获取所有预测类别"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT category FROM prediction_history WHERE category IS NOT NULL")
    categories = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return categories

def get_history_by_category(category, limit=100, offset=0, sort_by="timestamp", sort_order="DESC"):
    """获取指定类别的历史记录"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 构建查询语句
    query = "SELECT * FROM prediction_history WHERE category = ?"
    params = [category]
    
    # 添加排序
    sort_column = "timestamp"  # 默认按时间戳排序
    if sort_by == "id":
        sort_column = "id"
    
    query += f" ORDER BY {sort_column} {sort_order}"
    
    # 添加分页
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    
    results = []
    for row in cursor.fetchall():
        record = dict(row)
        record['prediction_result'] = json.loads(record['prediction_result'])
        results.append(record)
    
    conn.close()
    return results

def get_history_count_by_category(category):
    """获取指定类别的历史记录数量"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM prediction_history WHERE category = ?", (category,))
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

# 初始化数据库
init_db() 