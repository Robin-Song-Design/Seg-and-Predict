import os  
import sys  
import base64  
import io  
import numpy as np  
import joblib  
import webbrowser  
import threading  
import multiprocessing  

# Flask 相关  
from flask import Flask, request, jsonify  
from flask_cors import CORS  

# 图像分割相关  
import mxnet as mx  
from mxnet.gluon.data.vision import transforms  
from PIL import Image  
import gluoncv  
from gluoncv.utils.viz import get_color_pallete  

# 颜色映射  
from color_mapper import ColorMapper  

# 创建主应用  
app = Flask(__name__)  
CORS(app)  

# 全局变量存储模型和配置  
current_dir = os.path.dirname(os.path.abspath(__file__))  

# 颜色映射器  
color_mapper = ColorMapper(os.path.join(current_dir, 'color_coding_semantic_segmentation_classes - Sheet1.xlsx'))  

# 犯罪率预测模型  
model = joblib.load(os.path.join(current_dir, 'rf_model.pkl'))  

# 特征名称  
with open(os.path.join(current_dir, 'feature_names_142.txt'), 'r') as f:  
    feature_names = [line.strip() for line in f.readlines()]  

# 图像分割模型  
class ImageSegmentation:  
    def __init__(self):  
        # 使用 CPU 上下文  
        self.ctx = mx.cpu(0)  
        try:  
            # 加载预训练模型  
            self.model = gluoncv.model_zoo.get_model('psp_resnet101_ade', pretrained=True, ctx=self.ctx)  
            print("图像分割模型加载成功")  
        except Exception as e:  
            print(f"图像分割模型加载失败: {e}")  
            self.model = None  

    def process_image(self, image_data):  
        if self.model is None:  
            return None, "模型未成功加载"  

        try:  
            # 处理 base64 编码的图像  
            if image_data.startswith('data:image'):  
                image_data = image_data.split(',')[1]  
            
            # 解码图像  
            img_bytes = base64.b64decode(image_data)  
            pil_img = Image.open(io.BytesIO(img_bytes))  
            
            # 转换为 numpy 数组  
            img_array = np.array(pil_img)  

            # 转换为 MXNet 图像  
            mx_img = mx.nd.array(img_array)  

            # 预处理图像  
            transform_fn = transforms.Compose([  
                transforms.ToTensor(),  
                transforms.Normalize([.485, .456, .406], [.229, .224, .225])  
            ])  
            
            img = transform_fn(mx_img)  
            img = img.expand_dims(0).as_in_context(self.ctx)  

            # 模型推理  
            output = self.model.demo(img)  
            predict = mx.nd.squeeze(mx.nd.argmax(output, 1)).asnumpy()  

            # 获取颜色映射  
            mask = get_color_pallete(predict, 'ade20k')  
            
            # 编码为 base64  
            buffer = io.BytesIO()  
            mask.save(buffer, format='PNG')  
            seg_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')  

            return seg_base64, None  

        except Exception as e:  
            print(f"处理图像时发生错误: {e}")  
            import traceback  
            traceback.print_exc()  
            return None, str(e)  

# 创建图像分割模型实例  
segmentation_model = ImageSegmentation()  

def process_features(rgb_ratios):  
    """  
    处理RGB特征，转换为类别占比  
    """  
    # 创建一个与训练数据相同结构的特征字典  
    feature_dict = {name: 0.0 for name in feature_names}  
    
    # 处理每个RGB值  
    for feature in rgb_ratios:  
        rgb_array = np.array([feature['r'], feature['g'], feature['b']], dtype=np.uint8)  
        category = color_mapper.get_color_category(rgb_array)  
        
        if category and category in feature_dict:  
            # 累加该类别的占比  
            feature_dict[category] += feature['ratio']  
    
    # 转换为与训练数据相同顺序的特征向量  
    feature_vector = np.array([feature_dict[name] for name in feature_names])  
    
    return feature_vector  

@app.route('/predict', methods=['POST'])  
def predict():  
    try:  
        # 获取请求数据  
        data = request.json  
        rgb_ratios = data['features']  
        
        # 处理特征  
        feature_vector = process_features(rgb_ratios)  
        feature_vector = feature_vector.reshape(1, -1)  
        
        # 进行预测  
        prediction = model.predict(feature_vector)[0]  # 回归预测  
        
        # 获取特征重要性  
        importance_dict = dict(zip(feature_names, model.feature_importances_))  
        top_features = dict(sorted(  
            importance_dict.items(),  
            key=lambda x: x[1],  
            reverse=True  
        )[:5])  
        
        # 构建响应  
        response = {  
            'status': 'success',  
            'prediction': float(prediction),  # log_crime_rate的预测值  
            'crime_rate': float(np.exp(prediction)),  # 转换回原始尺度  
            'feature_importance': top_features,  
            'category_ratios': {  
                name: float(ratio)  
                for name, ratio in zip(feature_names, feature_vector[0])  
                if ratio > 0  
            }  
        }  
        
        return jsonify(response)  
        
    except Exception as e:  
        print(f"预测错误: {str(e)}")  
        return jsonify({  
            'status': 'error',  
            'message': str(e)  
        }), 500  

@app.route('/segment', methods=['POST'])  
def segment_image():  
    try:  
        # 获取请求中的图像数据  
        request_data = request.json  
        image_data = request_data.get('image', None)  
        
        if not image_data:  
            return jsonify({  
                'status': 'error',  
                'message': '未收到图像数据'  
            }), 400  
        
        # 处理图像分割  
        seg_base64, error = segmentation_model.process_image(image_data)  
        
        if error:  
            return jsonify({  
                'status': 'error',  
                'message': error  
            }), 500  
        
        return jsonify({  
            'status': 'success',  
            'segmented_image': seg_base64  
        })  
        
    except Exception as e:  
        print(f"路由处理异常: {e}")  
        import traceback  
        traceback.print_exc()  
        return jsonify({  
            'status': 'error',  
            'message': str(e)  
        }), 500  

def open_browser():  
    # 获取当前文件的目录  
    current_dir = os.path.dirname(os.path.abspath(__file__))  
    # 构建HTML文件的完整路径  
    html_path = os.path.join(current_dir, 'MAIN.html')  
    # 将文件路径转换为URL格式  
    url = 'file:///' + html_path.replace('\\', '/')  
    # 打开浏览器  
    webbrowser.open(url)  

def run_flask_app():  
    # 在单独的线程中打开浏览器  
    threading.Timer(1.5, open_browser).start()  
    
    # 运行 Flask 应用  
    app.run(debug=False, port=5000, host='0.0.0.0')  

if __name__ == '__main__':  
    # 使用多进程确保稳定性  
    multiprocessing.freeze_support()  
    
    # 启动 Flask 应用  
    run_flask_app()