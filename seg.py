import os  
import base64  
import io  
import numpy as np  
import mxnet as mx  
from mxnet import image  
from mxnet.gluon.data.vision import transforms  
from flask import Flask, request, jsonify  
from flask_cors import CORS  
from PIL import Image  
import gluoncv  
from gluoncv.utils.viz import get_color_pallete  

app = Flask(__name__)  
CORS(app)  

class ImageSegmentation:  
    def __init__(self):  
        # 使用 CPU 上下文  
        self.ctx = mx.cpu(0)  
        try:  
            # 加载预训练模型  
            self.model = gluoncv.model_zoo.get_model('psp_resnet101_ade', pretrained=True, ctx=self.ctx)  
            print("模型加载成功")  
        except Exception as e:  
            print(f"模型加载失败: {e}")  
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

# 创建分割模型实例  
segmentation_model = ImageSegmentation()  

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

if __name__ == '__main__':  
    app.run(port=5001, debug=True, host='0.0.0.0')