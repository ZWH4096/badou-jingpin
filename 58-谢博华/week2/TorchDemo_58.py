# coding:utf8

import torch
import torch.nn as nn
import numpy as np
import random
import json
import matplotlib.pyplot as plt

"""

基于pytorch框架编写模型训练
实现一个自行构造的找规律(机器学习)任务
规律：x是一个4维向量，如果第2,3数在1,4数区间内，则为正样本，反之为负样本

"""


class TorchModel(nn.Module):
    def __init__(self, input_size):
        super(TorchModel, self).__init__()
        self.linear1 = nn.Linear(input_size, 16)  # 线性层
        self.linear2 = nn.Linear(16, 1)
        self.activation = torch.sigmoid  # sigmoid归一化函数
        self.loss = nn.BCELoss()  # loss函数采用二分类交叉熵损失函数

    # 当输入真实标签，返回loss值；无真实标签，返回预测值
    def forward(self, x, y=None):
        x = self.linear1(x)     # (batch_size, input_size) -> (batch_size, 16)
        x = self.linear2(x)
        y_pred = self.activation(x)  # (batch_size, 1) -> (batch_size, 1)
        if y is not None:
            return self.loss(y_pred, y)  # 预测值和真实值计算损失
        else:
            return y_pred  # 输出预测结果


# 生成一个样本, 样本的生成方法，代表了我们要学习的规律
# 随机生成一个4维向量，如果第2,3在1,4之间，认为是正样本，反之为负样本
def build_sample():
    x = np.random.random(4)
    if x[0] > x[3]:
        if (x[0] > x[1] > x[3]) & (x[0] > x[2] > x[3]):
            return x, 1
        else:
            return x, 0
    elif x[3] > x[0]:
        if (x[0] < x[1] < x[3]) & (x[0] < x[2] < x[3]):
            return x, 1
        else:
            return x, 0
    else:
        return x, 0


# 随机生成一批样本
# 正负样本均匀生成
def build_dataset(total_sample_num):
    X = []
    Y = []
    while 1:
        x, y = build_sample()
        if y==1:
            X.append(x)
            Y.append([y])
        if len(Y)==(total_sample_num//2):
            break
    while 1:
        x, y = build_sample()
        if y==0:
            X.append(x)
            Y.append([y])
        if len(Y)==(total_sample_num):
            break
        combined = list(zip(X, Y))  # 将向量组合在一起
        random.shuffle(combined)  # 随机打乱向量顺序
        X[:], Y[:] = zip(*combined)  # 将顺序打乱后的X和Y重新分割开来
    return torch.FloatTensor(X), torch.FloatTensor(Y)

# 测试代码
# 用来测试每轮模型的准确率
def evaluate(model):
    model.eval()
    test_sample_num = 100
    x, y = build_dataset(test_sample_num)
    print("本次预测集中共有%d个正样本，%d个负样本" % (sum(y), test_sample_num - sum(y)))
    correct, wrong = 0, 0
    with torch.no_grad():
        y_pred = model(x)  # 模型预测
        for y_p, y_t in zip(y_pred, y):  # 与真实标签进行对比
            if float(y_p) < 0.5 and int(y_t) == 0:
                correct += 1  # 负样本判断正确
            elif float(y_p) >= 0.5 and int(y_t) == 1:
                correct += 1  # 正样本判断正确
            else:
                wrong += 1
    print("正确预测个数：%d, 正确率：%f" % (correct, correct / (correct + wrong)))
    return correct / (correct + wrong)


def main():
    # 配置参数
    epoch_num = 60  # 训练轮数
    batch_size = 200  # 每次训练样本个数
    train_sample = 10000  # 每轮训练总共训练的样本总数
    input_size = 4  # 输入向量维度
    learning_rate = 0.01  # 学习率
    # 建立模型
    model = TorchModel(input_size)
    # 选择优化器
    optim = torch.optim.Adam(model.parameters(), lr=learning_rate)
    log = []
    # 创建训练集，正常任务是读取训练集
    train_x, train_y = build_dataset(train_sample)
    # 训练过程
    for epoch in range(epoch_num):
        model.train()
        watch_loss = []
        for batch_index in range(train_sample // batch_size):
            x = train_x[batch_index * batch_size : (batch_index + 1) * batch_size]
            y = train_y[batch_index * batch_size : (batch_index + 1) * batch_size]
            loss = model(x, y)  # 计算loss
            loss.backward()  # 计算梯度
            if batch_index % 2 == 0:
                optim.step()  # 更新权重
                optim.zero_grad()  # 梯度归零
            watch_loss.append(loss.item())
        print("=========\n第%d轮平均loss:%f" % (epoch + 1, np.mean(watch_loss)))
        acc = evaluate(model)  # 测试本轮模型结果
        log.append([acc, float(np.mean(watch_loss))])
    # 保存模型
    torch.save(model.state_dict(), "model.pth")
    # 画图
    print(log)
    plt.plot(range(len(log)), [l[0] for l in log], label="acc")  # 画acc曲线
    plt.plot(range(len(log)), [l[1] for l in log], label="loss")  # 画loss曲线
    plt.legend()
    plt.show()
    return


# 使用训练好的模型做预测
def predict(model_path, input_vec):
    input_size = 4
    model = TorchModel(input_size)
    model.load_state_dict(torch.load(model_path))  # 加载训练好的权重
    print(model.state_dict())

    model.eval()  # 测试模式
    with torch.no_grad():  # 不计算梯度
        result = model.forward(torch.FloatTensor(input_vec))  # 模型预测
    for vec, res in zip(input_vec, result):
        print("输入：%s, 预测类别：%d, 概率值：%f" % (vec, round(float(res)), res))  # 打印结果


if __name__ == "__main__":
    main()
    test_vec = [[1,3,5,7],  #1
                [8,6,4,2],    #1
                [0.94963533,0.95758807,0.95520434,0.84890681],  #0
                [0.78797868,0.13625847,0.34675372,0.09871392],  #1
                [0.89349776,0.92579291,0.41567412,0.7358894]]   #0
    predict("model.pth", test_vec)
