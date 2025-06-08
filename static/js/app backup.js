function CrimeRateEditor() {  
            const [brushSize, setBrushSize] = React.useState(10);
            const [selectedColor, setSelectedColor] = React.useState(null);
            const [crimeRate, setCrimeRate] = React.useState(null);
            const [isDrawing, setIsDrawing] = React.useState(false);
            const [hasImage, setHasImage] = React.useState(false);
            const [currentTool, setCurrentTool] = React.useState('brush');
            const [canvasSize, setCanvasSize] = React.useState({ width: 1000, height: 600 });
            const canvasRef = React.useRef(null);
            const contextRef = React.useRef(null);
            const imageRef = React.useRef(null);
            const containerRef = React.useRef(null);
            
            const [isPredicting, setIsPredicting] = React.useState(false);
            const [prediction, setPrediction] = React.useState(null);
            const [predictionError, setPredictionError] = React.useState(null);
            const [predictionDetails, setPredictionDetails] = React.useState(null);
            const [isSegmenting, setIsSegmenting] = React.useState(false);
            const [hasoriginalImage, setHasOriginalImage] = React.useState(false);
            const [originalImage, setOriginalImage] = React.useState(null);
            const [segmentedImage, setSegmentedImage] = React.useState(null);
            const fileInputRef = React.useRef(null);

            const preSegmentedImageUrl = "/test.jpg";  

            // 初始化画布
            const initializeCanvas = (width, height) => {
                const canvas = canvasRef.current;  
                if (!canvas) return;  

                // 设置画布的实际尺寸  
                canvas.width = width;  
                canvas.height = height;
                setCanvasSize({ width, height });

                const context = canvas.getContext('2d');
                context.lineCap = 'round';  
                context.strokeStyle = currentTool === 'brush' ? (selectedColor?.color || 'black') : 'white';
                context.lineWidth = brushSize;  
                contextRef.current = context;  

                // 设置白色背景  
                context.fillStyle = 'white';  
                context.fillRect(0, 0, canvas.width, canvas.height);

                // 设置画布的CSS尺寸  
                updateCanvasStyle();
            };  

            // 更新画布的CSS尺寸以保持宽高比  
            const updateCanvasStyle = () => {
                const canvas = canvasRef.current;
                const container = containerRef.current;
                if (!canvas || !container) return;

                const containerWidth = container.clientWidth;
                const containerHeight = container.clientHeight;
                const containerRatio = containerWidth / containerHeight;
                const imageRatio = canvas.width / canvas.height;  

                let newWidth, newHeight;  
                if (imageRatio > containerRatio) {  
                    newWidth = containerWidth;  
                    newHeight = containerWidth / imageRatio;  
                } else {  
                    newHeight = containerHeight;  
                    newWidth = containerHeight * imageRatio;  
                }  

                canvas.style.width = `${newWidth}px`;  
                canvas.style.height = `${newHeight}px`;  
            };  

            React.useEffect(() => {
                initializeCanvas(1000, 600);
                document.getElementById('loading').style.display = 'none';  

                window.addEventListener('resize', updateCanvasStyle);  
                return () => window.removeEventListener('resize', updateCanvasStyle);  
            }, []);  

            // 处理图片上传
            const handleImageUpload = (e) => {  
                const file = e.target.files[0];  
                
                if (file) {  
                    const reader = new FileReader();  
                    reader.onloadend = () => {  
                        setOriginalImage(reader.result); 
                        // 重置分割图像  
                        setSegmentedImage(null); 
                        setHasOriginalImage(true);   
                    };  
                    reader.readAsDataURL(file); 
                }     
            };
            
            //分割函数
            const handleSegmentation = async () => {  
                if (!originalImage) return;
                
                setIsSegmenting(true);  
                try {  
                    
                    console.log('发送的图像数据长度:', originalImage.length);  
                    console.log('图像数据前缀:', originalImage.slice(0, 50));  
                    
                    const response = await fetch('http://127.0.0.1:5001/segment', {  
                        method: 'POST',  
                        headers: {  
                            'Content-Type': 'application/json',  
                        },  
                        body: JSON.stringify({ image: originalImage })  
                    });  

                    // 检查响应状态  
                    if (!response.ok) {  
                        const errorText = await response.text();  
                        console.error('Server Response Error:', {  
                            status: response.status,  
                            statusText: response.statusText,  
                            errorText: errorText  
                        });  
                        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);  
                    }  
                    
                    const data = await response.json();  
                    
                    // 详细的错误处理  
                    if (data.status !== 'success') {  
                        console.error('Segmentation error:', data.message);  
                        alert(`Segmentation failed: ${data.message}`);  
                        return;  
                    }  

                    console.log('接收到的分割图像数据长度:', data.segmented_image.length);  
                    console.log('分割图像数据前缀:', data.segmented_image.slice(0, 50));

                    if (data.status === 'success') {  
                        // 创建分割图像  
                        const segmentedImg = new Image();  
                        segmentedImg.src = `data:image/png;base64,${data.segmented_image}`;  
                        segmentedImg.onload = () => {  
                            // 可以在这里处理分割图像，例如显示或进一步处理 
                            // 获取画布上下文  
                            initializeCanvas(segmentedImg.width, segmentedImg.height); 
                            
                            const canvas = canvasRef.current;  
                            const context = canvas.getContext('2d');  
                
                            // 清除画布  
                            //context.clearRect(0, 0, canvas.width, canvas.height);  
                
                            // 调整画布尺寸以匹配分割图像  
                            //canvas.width = segmentedImg.width;  
                            //canvas.height = segmentedImg.height;  
                
                            // 绘制分割图像到画布  
                            context.drawImage(segmentedImg, 0, 0); 
                            
                            imageRef.current = {  
                                element: segmentedImg,  
                                width: segmentedImg.width,  
                                height: segmentedImg.height  
                            };  
                            setHasImage(true);  
                            
                            // 设置分割图像状态  
                            setSegmentedImage(canvas.toDataURL('image/png')); 

                            setSegmentedImage(segmentedImg.src);  
                            console.log('Segmentation complete', {  
                                width: canvas.width,  
                                height: canvas.height}
                        )};  
                    } else {  
                        console.error('Segmentation failed:', data.message); 
                        // 可以添加错误提示  
                        alert('Segmentation failed: ' + data.message);   
                    }  
                } catch (error) {  
                    console.error('Segmentation error details:', {  
                        name: error.name,  
                        message: error.message,  
                        stack: error.stack  
                    });  
                    alert('分割过程发生错误：' + error.message);   
                } finally {  
                    setIsSegmenting(false);  
                }  
            };  

            // 获取鼠标在画布上的实际坐标  
            const getMousePos = (e) => {  
                const canvas = canvasRef.current;  
                const rect = canvas.getBoundingClientRect();  
                const scaleX = canvas.width / rect.width;  
                const scaleY = canvas.height / rect.height;  
                return {  
                    x: (e.clientX - rect.left) * scaleX,  
                    y: (e.clientY - rect.top) * scaleY  
                };  
            };  

            // 工具函数  
            const tools = {  
                brush: {  
                    draw: (e) => {  
                        if (!isDrawing || !selectedColor) return;  
                        const pos = getMousePos(e);  
                        contextRef.current.lineTo(pos.x, pos.y);  
                        contextRef.current.stroke();  
                    },  
                    start: (e) => {  
                        if (!selectedColor) return;  
                        setIsDrawing(true);  
                        const pos = getMousePos(e);  
                        contextRef.current.beginPath();  
                        contextRef.current.moveTo(pos.x, pos.y);  
                    }  
                },  
                eraser: {  
                    draw: (e) => {  
                        if (!isDrawing) return;  
                        const pos = getMousePos(e);  
                        contextRef.current.clearRect(  
                            pos.x - brushSize/2,  
                            pos.y - brushSize/2,  
                            brushSize,  
                            brushSize  
                        );  
                    },  
                    start: (e) => {  
                        setIsDrawing(true);  
                        tools.eraser.draw(e);  
                    }  
                }  
            };  

            const startDrawing = (e) => {  
                tools[currentTool].start(e);  
            };  

            const draw = (e) => {  
                tools[currentTool].draw(e);  
            };  

            const stopDrawing = () => {  
                setIsDrawing(false);  
                contextRef.current?.closePath();  
            };  

            // 重置画布  
            const handleReset = () => {  
                if (!imageRef.current) return;
                
                const canvas = canvasRef.current;
                const context = contextRef.current;
                const img = imageRef.current;
                
                initializeCanvas(img.width, img.height);
                context.drawImage(img.element, 0, 0);
            };  

            // 更新画笔样式  
            React.useEffect(() => {  
                if (contextRef.current) {  
                    contextRef.current.strokeStyle = currentTool === 'brush' ? (selectedColor?.color || 'black') : 'white';  
                    contextRef.current.lineWidth = brushSize;  
                }  
            }, [currentTool, brushSize, selectedColor]);  

            //计算像素
            const calculatePixelRatios = () => {  
                const canvas = canvasRef.current;  
                const context = canvas.getContext('2d');  
                const imageData = context.getImageData(0, 0, canvas.width, canvas.height);  
                const pixels = imageData.data;  
    
                // 创建RGB计数对象  
                const rgbCounts = new Map();  
                const totalPixels = pixels.length / 4; // 总像素数 
    
                // 统计每个颜色的像素数量  
                for (let i = 0; i < pixels.length; i += 4) {  
                    const r = pixels[i];  
                    const g = pixels[i + 1];  
                    const b = pixels[i + 2];  
                    const key = `${r},${g},${b}`;  
        
                    rgbCounts.set(key, (rgbCounts.get(key) || 0) + 1);  
                }  
    
                // 计算每个RGB值的占比并转换为数组格式  
                const features = Array.from(rgbCounts.entries()).map(([key, count]) => {  
                    const [r, g, b] = key.split(',').map(Number);  
                    return {  
                        r: r,  
                        g: g,  
                        b: b,  
                        ratio: count / totalPixels  
                    };  
                });     
    
                // 按占比降序排序  
                features.sort((a, b) => b.ratio - a.ratio); 
    
                console.log('RGB ratios:', features);  
                return features;   
            };  
            
            
            // 实际预测函数  
            const handlePredict = async () => {  
                
                if (!hasImage) return;  
                
                try {  
                    setIsPredicting(true);  // 开始预测  
                    setPredictionError(null); // 清除之前的错误  
                    
                    const canvas = canvasRef.current;  
                    const imageData = canvas.toDataURL('image/png'); 
                    
                    // 计算像素占比  
                    const rgbRatios = calculatePixelRatios();  
                    
                    // 发送预测请求到后端   
                    const response = await fetch('http://127.0.0.1:5000/predict', {  
                        method: 'POST',  
                        headers: {  
                            'Content-Type': 'application/json',  
                            // 添加CORS头  
                            'Access-Control-Allow-Origin': '*'  
                        },  
                        body: JSON.stringify({  
                            features: rgbRatios 
                        })  
                    });  
                    
                    if (!response.ok) {  
                        throw new Error(`HTTP error! status: ${response.status}`);   
                    }  
                    
                    const data = await response.json();  
                    setCrimeRate(data.crime_rate);
                    setPredictionDetails(data); 

                } catch (error) {  
                    console.error('Prediction failed:', error);  
                    setPredictionError(error.message);
                    setCrimeRate(null); 
                } finally {  
                    setIsPredicting(false);   
                }  
            };  
                // 修改结果显示部分  
            const renderPredictionResult = () => {  
                if (isPredicting) {  
                    return (  
                        <div className="mt-4 p-3 bg-gray-100 rounded">  
                            <div className="text-center text-gray-600">  
                                Predicting...  
                            </div>  
                        </div>  
                    );  
                }  

                if (predictionError) {  
                    return (  
                        <div className="mt-4 p-3 bg-red-100 rounded">  
                            <div className="text-red-600">  
                                {predictionError}  
                            </div>  
                        </div>  
                    );  
                }  

                if (crimeRate !== null) {  
                    return (  
                        <div className="mt-4 space-y-3">  
                            <div className="p-3 bg-gray-100 rounded">  
                                <h3 className="font-medium">Predict Result</h3>  
                                <div className="text-2xl font-bold text-blue-600">  
                                    {crimeRate.toFixed(4)}  
                                </div>  
                            </div>  
                    
                            {predictionDetails?.feature_importance && (  
                                <div className="p-3 bg-gray-100 rounded">  
                                    <h3 className="font-medium">Main Factors</h3>  
                                    <div className="text-sm space-y-1 mt-2">  
                                        {Object.entries(predictionDetails.feature_importance)  
                                            .slice(0, 5) // 只显示前三个最重要的特征  
                                            .map(([feature, importance]) => (  
                                                <div key={feature} className="flex justify-between">  
                                                    <span>{feature}</span>  
                                                    <span>{(importance * 100).toFixed(1)}%</span>  
                                                </div>  
                                            ))  
                                        }  
                                    </div>  
                                </div>  
                            )}  
                        </div>  
                    );  
                }  

                return null;  
            }; 
            return (  
                <div className="p-10 mx-auto max-w-6xl h-screen">  
                    <div className="flex-1 flex gap-8 h-full">  
                        <div className="w-48 space-y-4">  
                            <div className="space-y-2">  
                                <h3 className="font-medium">Upload Image</h3>  
                                <input  
                                    type="file"  
                                    accept="image/*"  
                                    onChange={handleImageUpload}  
                                    className="w-full text-sm"  
                                />  
                            </div>  

                            {/* 分割按钮 */}  
                            <button  
                                onClick={handleSegmentation}  
                                disabled={!hasoriginalImage || isSegmenting}  
                                className={`mt-4 w-full py-2 rounded ${  
                                    !hasoriginalImage || isSegmenting  
                                        ? 'bg-gray-300 cursor-default'  
                                        : 'bg-blue-500 text-white hover:bg-blue-600'  
                                }`}  
                            >  
                                {isSegmenting ? 'Segmenting...' : 'Segment'}  
                            </button>  

                            <div className="space-y-2">  
                                <h3 className="font-medium">Tool</h3>  
                                <div className="flex gap-2">  
                                    <button  
                                        className={`px-3 py-1 rounded ${currentTool === 'brush' ? 'bg-cyan-400 text-white' : 'bg-gray-200'}`}  
                                        onClick={() => setCurrentTool('brush')}  
                                    >  
                                        Brush  
                                    </button>  
                                    <button  
                                        className={`px-3 py-1 rounded ${currentTool === 'eraser' ? 'bg-cyan-500 text-white' : 'bg-gray-200'}`}  
                                        onClick={() => setCurrentTool('eraser')}  
                                    >  
                                        Eraser 
                                    </button>  
                                </div>  
                            </div>  

                            <div className="space-y-2">  
                                <h3 className="font-medium">Brush Size</h3>  
                                <input  
                                    type="range"  
                                    value={brushSize}  
                                    onChange={(e) => setBrushSize(Number(e.target.value))}  
                                    min="1"  
                                    max="100"  
                                    className="w-full
                                        appearance-none   
                                        bg-pink-200   
                                        h-2   
                                        rounded-full   
                                        outline-none   
                                        opacity-70   
                                        hover:opacity-100 "  
                                />
                                <div className="text-sm text-gray-600">
                                    Current Size: {brushSize}px
                                </div>
                            </div>
                            
                            <div className="space-y-2">
                                <h3 className="font-medium">Scene Elements</h3>
                                <div className="px-1 py-2 grid grid-cols-2 gap-2 max-h-64 overflow-y-auto">
                                    {Object.entries(CITYSCAPES_COLORS).map(([key, item]) => (
                                        <button
                                            key={key}
                                            className={`p-2 rounded border ${
                                                selectedColor?.id === item.id ? 'ring-2 ring-[#ff00ff]' : ''
                                            }`}
                                            onClick={() => setSelectedColor(item)}
                                        >
                                            <div
                                                className="w-full h-6 rounded"
                                                style={{ backgroundColor: item.color }}
                                            />
                                            <div className="text-xs mt-1">{item.label}</div>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <button
                                className="w-full px-4 py-2 bg-gray-300 text-white rounded hover:bg-gray-400"
                                onClick={handleReset}
                                //disabled={!hasImage}
                            >
                                Reset
                            </button>

                            {/* <button
                                className="w-full px-4 py-2 bg-cyan-300 text-white rounded hover:bg-cyan-400"
                                onClick={handleReset}
                                disabled={!hasImage}
                            >
                                Generate
                            </button> */}

                            <button  
                                className={`w-full px-4 py-2 text-white rounded  
                                    ${isPredicting   
                                        ? 'bg-gray-500 cursor-not-allowed'  
                                        : 'bg-[#ff00ff] hover:bg-pink-600'  
                                    } disabled:opacity-50`}  
                                onClick={handlePredict}  
                                disabled={!hasImage || isPredicting}  
                            >  
                                {isPredicting ? 'Predicting...' : 'Predict'}  
                            </button>  

                            {/* 添加预测结果显示 */}  
                            {renderPredictionResult()}  
                        </div>

                        <div className="flex-1 flex flex-col w-full h-full">     
                            {/* 新增：原始图像显示区域 */}  
                            
                                <div className="mb-4 w-full h-[200px] border rounded-lg overflow-hidden">  
                                    {hasoriginalImage && originalImage && (  
                                    <img   
                                        src={originalImage}   
                                        alt="Original"   
                                        className="w-full h-full object-contain"  
                                    />  
                                    )}
                                </div>  
                             
                            <div 
                                ref={containerRef} 
                                className="flex-1 border rounded-lg overflow-hidden flex h-full items-center justify-center bg-pink-50 
                                            min-h-[200px] max-h-[400px]" 
                            >
                                <canvas
                                    ref={canvasRef}
                                    style={{
                                        width: '100%',
                                        height: '100%',
                                        objectFit: 'contain'
                                    }}
                                    onMouseDown={startDrawing}
                                    onMouseMove={draw}
                                    onMouseUp={stopDrawing}
                                    onMouseLeave={stopDrawing}
                                />
                            </div> 
                            
                            <div className="mb-4 w-full h-[200px] border-4 rounded-lg overflow-hidden">  
                                    {hasoriginalImage && originalImage && (  
                                    <img   
                                        src={originalImage}   
                                        alt="Original"   
                                        className="w-full h-full object-contain"  
                                    />  
                                    )}
                            </div>  
                        </div>
                    </div>
                </div>
            );
        }
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(<CrimeRateEditor />);