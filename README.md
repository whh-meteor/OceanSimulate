# OceanSimulate

使用 Python-Flask 作为系统后台处理 mesh 文件和 geojson、专题图

# 默认端口号 5000

# 目录结构

```
OceanSimulate
├── app.py  # 程序入口
├── config.ini # 程序环境配置
├── requirements.txt
├── static #  静态资源文件-如dem，全球岸线
├── tempfile # 临时文件，中间数据文件，专题图
└── utils # 程序配置
```

# 功能概要

### 1. mesh 文件处理

### 2. geojson 文件处理

### 3. 专题图处理

### 4. 网格裁剪、区域裁剪

### 5. 水深赋值

### 6. 风场裁剪

### 7. mesh 索引重排

# 运行方式

## 1. 下载代码到本地

## 2. 安装依赖包

    ```
    pip install -r requirements.txt
    ```

### GDAL 需要单独安装，请参考 [GDAL 安装指南](https://gdal.org/download.html)

## 3. 启动服务

```
python app.py
```

    或者

```
python app.py --config "config.ini"
```
