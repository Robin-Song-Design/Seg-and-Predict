import torch  
import numpy as np  
import diffusers
from PIL import Image  
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
import cv2  

class ImageGenerator:  
    def __init__(self):  
        # 加载 ControlNet 模型  
        controlnet = ControlNetModel.from_pretrained(  
            "lllyasviel/control_v11p_sd15_seg",   
            torch_dtype=torch.float16  
        )  

        # 加载 Stable Diffusion 管道  
        self.pipeline = StableDiffusionControlNetPipeline.from_pretrained(  
            "runwayml/stable-diffusion-v1-5",   
            controlnet=controlnet,  
            torch_dtype=torch.float16  
        )  
        
        # 移动到 GPU  
        self.pipeline.to("cuda")  
        
        # 优化设置  
        self.pipeline.enable_model_cpu_offload()  
        self.pipeline.enable_xformers_memory_efficient_attention()  

    def preprocess_mask(self, segmentation_mask):  
        """  
        预处理分割掩码  
        - 确保掩码为单通道  
        - 调整大小与原图一致  
        - 转换为 ControlNet 可接受的格式  
        """  
        # 确保是 numpy 数组  
        if isinstance(segmentation_mask, Image.Image):  
            segmentation_mask = np.array(segmentation_mask)  
        
        # 如果是彩色图，转为灰度  
        if len(segmentation_mask.shape) == 3:  
            segmentation_mask = cv2.cvtColor(segmentation_mask, cv2.COLOR_RGB2GRAY)  
        
        # 二值化处理  
        _, binary_mask = cv2.threshold(segmentation_mask, 0, 255, cv2.THRESH_BINARY)  
        
        # 转换为 PIL 图像  
        control_image = Image.fromarray(binary_mask).convert("RGB")  
        
        return control_image  

    def generate_image(self, original_image, segmentation_mask, prompt,   
                       num_inference_steps=50, guidance_scale=7.5):  
        """  
        生成图像  
        
        参数:  
        - original_image: 原始图像 (PIL Image)  
        - segmentation_mask: 分割掩码  
        - prompt: 生成文本提示  
        - num_inference_steps: 推理步数  
        - guidance_scale: 引导比例  
        """  
        try:  
            # 预处理掩码  
            processed_mask = self.preprocess_mask(segmentation_mask)  
            
            # 生成图像  
            generator = torch.Generator("cuda").manual_seed(42)  
            
            output = self.pipeline(  
                prompt=prompt,  
                image=processed_mask,  
                original_image=original_image,  # 保留未分割区域  
                num_inference_steps=num_inference_steps,  
                guidance_scale=guidance_scale,  
                generator=generator,  
                control_guidance_start=0.0,  
                control_guidance_end=1.0,  
            )  
            
            # 返回生成的图像  
            return output.images[0]  
        
        except Exception as e:  
            print(f"图像生成错误: {e}")  
            return None  

    def save_image(self, image, filepath):  
        """  
        保存生成的图像  
        """  
        if image:  
            image.save(filepath)  
            return True  
        return False  

# 使用示例  
def main():  
    # 初始化生成器  
    generator = ImageGenerator()  
    
    # 加载图像和掩码  
    original_image = Image.open("original.jpg")  
    segmentation_mask = Image.open("mask.png")  
    
    # 生成新图像  
    prompt = "A vibrant street scene with modern architecture"  
    new_image = generator.generate_image(  
        original_image,   
        segmentation_mask,   
        prompt  
    )  
    
    # 保存图像  
    if new_image:  
        generator.save_image(new_image, "generated_image.png")  

if __name__ == "__main__":  
    main()