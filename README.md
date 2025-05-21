# software_project
nku software project

### Vue项目配置记录
```
npm install webpack -g //安装webpack
npm install vue-cli -g //安装脚手架工具
vue init webpack project-name<项目名字不能用中文> //初始化项目
npm run dev //启动项目
```

修改src目录中的文件：
- src/route/index.js中配置路由
- src/comonents/views/新建vue文件代表网页
- src/App.vue中配置全局样式，也需要修改

导入手势：
`npm install axios@1.5.0 --save`

python后端文件注意导入：
```
from flask import Flask, jsonify
from flask_cors import CORS  # 导入 CORS
```

导入音频：
在src/assets添加名为music.mp3的音乐

导入动态背景库（vue项目根目录下执行）：
```
npm install vanta@0.5.24
npm install three@0.121.0
```
