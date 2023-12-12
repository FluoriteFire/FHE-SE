import numpy as np
from PIL import Image

def Noise(select,n,m,img):
    # 椒盐噪声，随机往img中的任意位置添加n个纯黑的噪点
    if(select == 0):
        for k in range(n):
            i = int(np.random.random() * img.shape[1])
            j = int(np.random.random() * img.shape[0])
            # 如果图片是深色系可以将0改成255，即白点
            if img.ndim == 2:
                img[j,i] = 0
            elif img.ndim == 3:
                img[j,i,0]= 0
                img[j,i,1]= 0
                img[j,i,2]= 0
        return img
    
    # 给数据加指定SNR的高斯噪声
    elif(select == 1):
        noise = np.random.normal(n, m, img.shape)
        return img + noise
        
if __name__ == "__main__":
    path = "./test.jpg"
    select = 1      # 0
    n = 0          # 65535       
    m = 10

    im  =  Image.open(path)  
    img =  np.array(im)
    img = Noise(select,n,m,img)
    img = Image.fromarray(img.astype('uint8')).convert('RGB')
    img.show()