import pandas as pd  
import numpy as np  
import ast  

class ColorMapper:  
    def __init__(self, xlsx_path):  
        """初始化颜色映射器"""  
        # 读取Excel文件  
        self.df = pd.read_excel(xlsx_path)  
        
        # 初始化颜色映射字典  
        self.category_colors = {}  
        self.color_to_category = {}  
        
        #print("\=== 开始处理颜色映射 ===")  
        # 处理每一行  
        for _, row in self.df.iterrows():  
            try:  
                # 获取RGB值（第6列）并转换为numpy数组  
                rgb_str = str(row.iloc[5]).strip('[]() ').replace(' ', '')  
                rgb_values = [int(x) for x in rgb_str.split(',')]  
                rgb_array = np.array(rgb_values, dtype=np.uint8)  
                
                # 获取类别名称（第9列）  
                category_name = str(row.iloc[8])  
                
                # 打印调试信息  
                #print(f"\n处理类别: {category_name}")  
                #print(f"原始RGB字符串: {row.iloc[5]}")  
                #print(f"处理后RGB值: {rgb_array}")  
                #print(f"RGB数组形状: {rgb_array.shape}")  
                
                # 存储映射  
                self.category_colors[category_name] = rgb_array  
                self.color_to_category[tuple(rgb_array)] = category_name  
                
            except Exception as e:  
                print(f"处理行时出错: {row.iloc[8]}, 错误: {str(e)}")  
                continue  
        
        # 打印所有颜色映射进行验证  
        #print("\=== 颜色映射验证 ===")  
        #for category, color in self.category_colors.items():  
            #print(f"类别: {category:<30} RGB值: {color}")  
    
    def get_category_color(self, category):  
        """获取类别对应的颜色"""  
        return self.category_colors.get(category)  
    
    def get_color_category(self, color):  
        """获取颜色对应的类别"""  
        return self.color_to_category.get(tuple(color))
