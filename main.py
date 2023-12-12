import tenseal as ts
import numpy as np
from PIL import Image
import os
import time

class Server():
    def __init__(self):
        self.data = []  # 数据库索引
        self.tag = []   # 标签 -> 数据
    
    # 将客户端发送的数据写入数据库中
    def WriteData(self,data,tag):
        self.data.append(data)
        self.tag.append(tag)
    
    # 通过索引搜索得到数据
    def Search(self,data):
        output = []
        time_start = time.time()
        for i in self.data:
            output.append(i - data)
        time_end = time.time()  
        time_sum = time_end - time_start
        print("服务端搜索数据用时为%s秒\n" % time_sum)
        return output

    # 通过发送的标签获取数据
    def SendTag(self,tag):
        return self.tag[tag]

class Client():
    def __init__(self,select,Noise_n,Noise_m,algorithm):
        self.select = select
        self.Noise_n = Noise_n
        self.Noise_m = Noise_m
        self.algorithm = algorithm

        if self.algorithm == "CKKS":
            self.context = ts.context(
                ts.SCHEME_TYPE.CKKS,
                poly_modulus_degree=32768,
                coeff_mod_bit_sizes=[60, 40, 40, 40, 40, 60],
            )
        elif self.algorithm == "BFV":
            self.context = ts.context(ts.SCHEME_TYPE.BFV, poly_modulus_degree=32768, plain_modulus=65537, coeff_mod_bit_sizes=[60, 40, 40, 40, 40, 60])

        self.context.generate_galois_keys()
        self.context.global_scale = 2**40

    # 读取图片加密后发送数据
    def SendData(self,path):
        dirname, filename = os.path.split(path)
        tag, extension = os.path.splitext(filename)

        # 读取图片至数组
        im  =  Image.open(path)  
        img =  np.array(im)

        # 记录开始时间
        time_start = time.time()  

        # 为数组添加噪声
        img = self.Noise(self.select,self.Noise_n,self.Noise_m,img)

        # 展平数组
        img = img.flatten()

        # 将数组加密
        if self.algorithm == "CKKS":
            data = ts.ckks_vector(self.context,img)
        elif self.algorithm == "BFV":
            data = ts.bfv_vector(self.context,img)

        # 记录结束时间
        time_end = time.time()  
        # 计算的时间差为程序的执行时间，单位为秒/s
        time_sum = time_end - time_start 
        return data,tag,time_sum

    def Noise(self,select,n,m,img):
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

    # 解密数据并排序找到最小值
    def GetTag(self,input):
        datas = []
        time_start = time.time()
        for i in input:
            data = i.decrypt()
            dist = np.sqrt(np.sum(np.square(data).astype('int64')))
            datas.append(dist)
        # print(datas)
        tag = datas.index(min(datas))
        time_end = time.time()  
        time_sum = time_end - time_start
        print("解密数据计算距离最小值用时为%s秒\n" % time_sum)
        return tag


if __name__ == "__main__":
    select = 1          # 0是椒盐噪声，1是高斯噪声
    n = 0               # 椒盐噪声是噪声点个数(需要大)，高斯噪声是中心值(尽量小)
    m = 10               # 高斯噪声中的标准差(越大影响越大)
    tags = []
    timecounts = []

    img_path = "./imgs/"
    test_img = "./search.jpg"

    clinet = Client(select,n,m,"CKKS")   # 选择算法为 CKKS 或 BFV
    server = Server()
    
    # 遍历文件夹读取图片然后上传数据库
    for imgname in os.listdir(img_path):
        data, tag, timecount = clinet.SendData(img_path+imgname)
        tags.append(tag)
        timecounts.append(timecount)
        server.WriteData(data,tag)

    data, tag, timecount = clinet.SendData(test_img)

    print('\n')
    for i in range(0,len(tags)):
        print("上传%s的执行时间为%f秒" % (tags[i],timecounts[i]))
    print("\n上传%s的执行时间为%f秒\n" % (tag,timecount))
    output = server.Search(data)
    tag = clinet.GetTag(output)
    print("查询到的数据为: ",end='')
    print(server.SendTag(tag))