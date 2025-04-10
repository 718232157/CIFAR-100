import os
import uuid
from PIL import Image, ExifTags
import io
import base64
import tempfile
from datetime import datetime

def save_uploaded_image(uploaded_file):
    """保存上传的图像到临时目录，并返回路径
    
    Args:
        uploaded_file: Streamlit上传的文件对象
        
    Returns:
        str: 保存的文件路径
    """
    # 创建临时目录
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'uploads')
    os.makedirs(temp_dir, exist_ok=True)
    
    # 生成唯一文件名 - 添加时间戳以便更好地跟踪
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = os.path.splitext(uploaded_file.name)[1]
    original_name = os.path.splitext(uploaded_file.name)[0]
    # 使用原始文件名的前20个字符 + 时间戳 + UUID的前8个字符，可读性更好
    filename = f"{original_name[:20]}_{current_time}_{str(uuid.uuid4())[:8]}{file_ext}"
    file_path = os.path.join(temp_dir, filename)
    
    # 保存图片
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def get_image_preview(image, max_size=(300, 300)):
    """获取图片的base64编码，用于预览
    
    Args:
        image: 图片路径或文件对象
        max_size: 预览图片的最大尺寸（宽，高）
        
    Returns:
        str: base64编码的图片数据
    """
    try:
        if isinstance(image, str) and os.path.exists(image):
            img = Image.open(image).convert('RGB')
        elif hasattr(image, 'read'):
            img = Image.open(image).convert('RGB')
        else:
            return None
        
        # 调整大小以适应预览，保持纵横比
        img.thumbnail(max_size, Image.LANCZOS)
        
        # 转换为base64编码
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=85, optimize=True)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        print(f"图片预览生成错误: {str(e)}")
        return None

def get_file_extension(filename):
    """获取文件扩展名
    
    Args:
        filename: 文件名
        
    Returns:
        str: 文件扩展名（小写）
    """
    return os.path.splitext(filename)[1].lower()

def is_valid_image(file):
    """检查文件是否为有效的图像文件
    
    Args:
        file: 文件对象
        
    Returns:
        bool: 文件是否为有效图像
    """
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
    extension = get_file_extension(file.name)
    
    if extension not in valid_extensions:
        return False
    
    try:
        # 创建临时文件并保存上传的内容
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
            tmp_path = tmp.name
            # 保存文件内容
            file.seek(0)
            tmp.write(file.read())
        
        # 尝试打开并验证图像
        try:
            with Image.open(tmp_path) as img:
                # 验证图像数据
                img.verify()
                return True
        except Exception:
            return False
        finally:
            # 删除临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            # 重置文件指针，这样文件可以再次读取
            file.seek(0)
    except Exception:
        return False

def get_image_exif(image_path):
    """获取图片的EXIF信息
    
    提取图片的EXIF元数据，如拍摄时间、相机型号等
    
    Args:
        image_path: 图片路径
        
    Returns:
        dict: EXIF信息字典
    """
    try:
        img = Image.open(image_path)
        
        # 检查图片是否有EXIF信息
        if hasattr(img, '_getexif') and img._getexif():
            exif = img._getexif()
            exif_data = {}
            
            # 只保留常用的EXIF标签
            useful_tags = {
                'DateTime': '拍摄时间',
                'Make': '相机制造商',
                'Model': '相机型号',
                'Software': '软件',
                'ExifImageWidth': '图片宽度',
                'ExifImageHeight': '图片高度',
                'XResolution': '水平分辨率',
                'YResolution': '垂直分辨率',
                'ResolutionUnit': '分辨率单位',
                'Flash': '闪光灯'
            }
            
            # 转换EXIF标签编号为名称
            exif_tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items() if k in ExifTags.TAGS}
            
            # 提取有用的标签
            for tag, value in exif_tags.items():
                if tag in useful_tags:
                    # 转换标签名称为中文
                    exif_data[useful_tags[tag]] = value
            
            return exif_data
        else:
            # 如果没有EXIF信息，返回基本图片信息
            return {
                '宽度': img.width,
                '高度': img.height,
                '格式': img.format,
                '颜色模式': img.mode
            }
    except Exception as e:
        print(f"获取EXIF信息错误: {str(e)}")
        return None

def optimize_image(image_path, max_size=(800, 800), quality=85):
    """优化图像大小和质量
    
    对大图像进行缩放和压缩，以提高性能
    
    Args:
        image_path: 图片路径
        max_size: 最大尺寸（宽，高）
        quality: JPEG压缩质量（1-100）
        
    Returns:
        str: 优化后的图片路径
    """
    try:
        img = Image.open(image_path)
        
        # 检查图像是否需要缩放
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, Image.LANCZOS)
        
        # 文件名添加优化标记
        filename, ext = os.path.splitext(image_path)
        optimized_path = f"{filename}_optimized{ext}"
        
        # 保存优化后的图像
        img.save(optimized_path, quality=quality, optimize=True)
        
        return optimized_path
    except Exception as e:
        print(f"图像优化错误: {str(e)}")
        return image_path  # 如果优化失败，返回原始路径 