import os
import numpy as np
import joblib
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from color_mapper import ColorMapper

# 全局变量
current_dir = os.path.dirname(os.path.abspath(__file__))
color_mapper = None
model = None
feature_names = None

def initialize_app():

    global color_mapper, model, feature_names
    try:
        # load the color mapping
        color_mapper = ColorMapper(os.path.join(current_dir, 'color_coding_semantic_segmentation_classes - Sheet1.xlsx'))
        
        # load the pre-trained model
        model = joblib.load(os.path.join(current_dir, 'rf_model.pkl'))
        
        # load the feature names
        with open(os.path.join(current_dir, 'feature_names_142.txt'), 'r') as f:
            feature_names = [line.strip() for line in f.readlines()]
        
        print("model and color mapper initialized successfully.")
        print(f"features amount: {len(feature_names)}")
        return True
    except Exception as e:
        print(f"initialization error: {str(e)}")
        return False

# Flask app setup
app = Flask(__name__)
CORS(app)

def process_features(rgb_ratios):
    """
    Process RGB ratios into a feature vector based on color categories.
    """
    feature_dict = {name: 0.0 for name in feature_names}
    
    for feature in rgb_ratios:
        rgb_array = np.array([feature['r'], feature['g'], feature['b']], dtype=np.uint8)
        category = color_mapper.get_color_category(rgb_array)
        
        if category and category in feature_dict:
            feature_dict[category] += feature['ratio']
    
    feature_vector = np.array([feature_dict[name] for name in feature_names])
    
    return feature_vector

# static file serving routes
@app.route('/')
def index():
    """
    Main html page route
    """
    return send_from_directory('static', 'index.html')

@app.route('/js/<path:filename>')
def serve_js(filename):
    """
    js files route
    """
    return send_from_directory('static/js', filename)

@app.route('/images/<path:filename>')
def serve_images(filename):
    """
    images files route
    """
    return send_from_directory('static/images', filename)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Print the request data for debugging
        print("received requests:", request.json)
        
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
        
        print("Predict response:", response)
        return jsonify(response)
        
    except Exception as e:
        print(f"Predict error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# initialize the app
if not initialize_app():
    print("app initialization failed, exiting.")
    exit(1)

if __name__ == '__main__':
    # environment variable for Flask app
    app.run(debug=True, port=5000, host='0.0.0.0')