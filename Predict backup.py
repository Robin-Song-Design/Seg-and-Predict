# app.py  
import subprocess  
import threading  
import os  
import sys  
import time  
import signal  
import multiprocessing  
import webbrowser  
import numpy as np  
import joblib  

from flask import Flask, request, jsonify, send_file  
from flask_cors import CORS  
from color_mapper import ColorMapper  

# 全局变量  
current_dir = os.path.dirname(os.path.abspath(__file__))  
color_mapper = None  
model = None  
feature_names = None  

def initialize_app():  
    """  
    统一的初始化函数  
    """  
    global color_mapper, model, feature_names  
    try:  
        # 加载颜色映射器  
        color_mapper = ColorMapper(os.path.join(current_dir, 'color_coding_semantic_segmentation_classes - Sheet1.xlsx'))  
        
        # 加载模型  
        model = joblib.load(os.path.join(current_dir, 'rf_model.pkl'))  
        
        # 加载特征名称  
        with open(os.path.join(current_dir, 'feature_names_142.txt'), 'r') as f:  
            feature_names = [line.strip() for line in f.readlines()]  
        
        print("模型和颜色映射加载成功")  
        print(f"特征数量: {len(feature_names)}")  
        return True  
    except Exception as e:  
        print(f"初始化错误: {str(e)}")  
        return False  

def start_segmentation_server():  
    """  
    启动图像分割服务器的函数  
    """  
    anaconda_python = r"C:\Users\robin\anaconda3\envs\py7env\python.exe"  
    seg_script_path = r"C:\Users\robin\OneDrive - University College London\AC\Studio\First stage\htmlscript\seg.py"  
    
    try:  
        process = multiprocessing.Process(  
            target=run_seg_script,   
            args=(anaconda_python, seg_script_path)  
        )  
        process.start()  
        time.sleep(2)  
        return process  
    except Exception as e:  
        print(f"启动分割服务器失败: {e}")  
        return None  

def run_seg_script(python_path, script_path):  
    """  
    实际运行 seg.py 的函数
    """  
    try:  
        subprocess.run([python_path, script_path], check=True)  
    except subprocess.CalledProcessError as e:  
        print(f"seg.py 运行出错: {e}")  

# Flask 应用  
app = Flask(__name__)  
CORS(app)  

def process_features(rgb_ratios):  
    """  
    处理RGB特征，转换为类别占比  
    """  
    feature_dict = {name: 0.0 for name in feature_names}  
    
    for feature in rgb_ratios:  
        rgb_array = np.array([feature['r'], feature['g'], feature['b']], dtype=np.uint8)  
        category = color_mapper.get_color_category(rgb_array)  
        
        if category and category in feature_dict:  
            feature_dict[category] += feature['ratio']  
    
    feature_vector = np.array([feature_dict[name] for name in feature_names])  
    
    return feature_vector  

@app.route('/')  
def serve_html():  
    """  
    直接提供HTML文件
    """  
    return send_file(os.path.join(current_dir, 'MAIN.html'))

@app.route('/predict', methods=['POST'])  
def predict():  
    try:
        # 打印接收到的数据，用于调试  
        print("收到预测请求:", request.json)  
        
        data = request.json  
        rgb_ratios = data['features']  
        
        feature_vector = process_features(rgb_ratios)  
        feature_vector = feature_vector.reshape(1, -1)  
        
        prediction = model.predict(feature_vector)[0]  
        
        importance_dict = dict(zip(feature_names, model.feature_importances_))  
        top_features = dict(sorted(  
            importance_dict.items(),  
            key=lambda x: x[1],  
            reverse=True  
        )[:5])  
        
        response = {  
            'status': 'success',  
            'prediction': float(prediction),  
            'crime_rate': float(np.exp(prediction)),  
            'feature_importance': top_features,  
            'category_ratios': {  
                name: float(ratio)  
                for name, ratio in zip(feature_names, feature_vector[0])  
                if ratio > 0  
            }  
        }  
        
        print("预测响应:", response)  
        return jsonify(response)  
        
    except Exception as e:  
        print(f"预测错误: {str(e)}")  
        return jsonify({  
            'status': 'error',  
            'message': str(e)  
        }), 500  

# 全局变量存储分割服务进程  
segmentation_process = None  

def main():  
    global segmentation_process  
    
    # 初始化应用  
    if not initialize_app():  
        print("应用初始化失败")  
        return  
    
    # 启动分割服务器  
    segmentation_process = start_segmentation_server()  
    
    try:  
        # 运行 Flask 应用  
        app.run(debug=True, port=5000, host='0.0.0.0')  
    except Exception as e:  
        print(f"应用启动失败: {e}")  
    finally:  
        # 清理进程  
        if segmentation_process:  
            segmentation_process.terminate()  

if __name__ == '__main__':  
    multiprocessing.freeze_support()  
    main()