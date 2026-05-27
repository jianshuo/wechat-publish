我写了个ccglass，看看Claude Code向大模型发了什么
原来的claude trace等很多工具当claude code 从node升级到二进制文件以后，全都用不了了，只好自己写了一个工具。把昨天晚上的工具直接包装好了一个node包，大家可以直接这么安装：
npm i ccglass
然后在命令行输入 ccglass，选择claude就可以看到Claude code 发给服务器的所有细节的内容
大家可以试试。
