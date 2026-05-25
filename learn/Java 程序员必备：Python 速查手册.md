# Java 程序员必备：Python 速查手册

# Java 程序员专属・Python 速查手册

（对标 Java，只记常用，直接复制可用，避开语法坑）

## 一、基础语法对照（必背）

|Java|Python|备注|
|---|---|---|
|`int a=1;`|`a = 1`|不用声明类型|
|`String s=\&\#34;xxx\&\#34;;`|`s = \&\#34;xxx\&\#34;` 或 `s=\&\#39;xxx\&\#39;`|单双引号一样|
|`boolean b=true;`|`b = True / False`|**首字母大写**|
|`null`|`None`|空值|
|`i\+\+`|`i \+= 1`|无自增运算符|
|`System\.out\.println\(\)`|`print\(\)`|打印|
|`// 注释`|`\# 注释`|单行|
|`/\* 块注释 \*/`|`\&\#34;\&\#34;\&\#34;多行注释\&\#34;\&\#34;\&\#34;`|多行|

### 缩进规则（最重要）

- Java：`\{\}` 包代码块

- Python：**冒号 ****`:`**** \+ 4 空格缩进**，不能乱

### 1\. 变量类型指定（核心补充：Java静态类型 → Python类型注解）

Python 3\.5\+ 支持**类型注解（Type Hint）**，对标 Java 静态变量声明，可主动指定变量类型，规避动态类型隐患，适配企业级规范开发。仅做语法校验，不影响程序运行，完全贴合Java程序员强类型编码习惯。

**核心规则**：变量名: 类型 = 值

**Java vs Python 类型指定对标（全场景示例）**

```python
# 【整数】Java：int num = 10;
num: int = 10

# 【浮点数】Java：double price = 99.9;
price: float = 99.9

# 【字符串】Java：String name = "test";
name: str = "test"

# 【布尔值】Java：boolean flag = true;
flag: bool = True

# 【空值】Java：Object obj = null;
obj: None = None

```

```python
# 【列表 List】对标 ArrayList
list_data: list[int] = [1, 2, 3]  # 仅存储int
list_str: list[str] = ["a", "b"] # 仅存储str

# 【字典 Dict】对标 HashMap
# dict[键类型, 值类型]
user_info: dict[str, int] = {"age": 18, "id": 1001}

# 【集合 Set】对标 HashSet
set_data: set[int] = {1, 2, 3}

# 【元组 Tuple】对标 不可变数组
tuple_data: tuple[int, str, bool] = (1, "test", True)

```

```python
# 1. 任意类型（对标Java Object）
any_data: any = 123
any_data = "任意类型切换"

# 2. 可选类型（允许为空，对标Java包装类可空）
from typing import Optional
age: Optional[int] = None  # 可以是int或None
age = 20

# 3. 自定义类类型（对标Java自定义对象）
class User:
    pass
user: User = User()  # 指定变量为User对象类型

```

```python
# Java：public static int calc(int a, int b)
def calc(a: int, b: int) -> int:
    return a + b

# 无返回值指定 -> None
def print_msg(msg: str) -> None:
    print(msg)

```

### 2\. 类型注解补充说明

- Python 类型注解**仅用于代码提示、静态校验**，运行时不会强制校验类型（和Java编译强制校验不同）

- 如需强制类型校验，可配合工具 `mypy` 做静态代码检查

- 企业级Python项目（后端、数据分析）**强制推荐加类型注解**，适配Java开发严谨编码习惯

## 二、判断 \&amp; 循环

### if 判断

```python
if a > 10:
    pass
elif a > 5:
    pass
else:
    pass
```

> Java：`else if` → Python：`elif`
> 
> 

### for 循环

```python
# Java for(int i=0;i<10;i++)
for i in range(10):
    pass

# Java 增强for
arr = [1,2,3]
for num in arr:
    pass

# 带索引遍历
for i,num in enumerate(arr):
    pass
```

### while

```python
i=0
while i<10:
    i +=1
```

## 三、常用数据结构（对标 Java 容器）

### 1\. list 列表 = ArrayList

```python
# 初始化
li = [1,2,3,"java"]

# 增
li.append(4)       # add
li.insert(0,0)     # 插入

# 查
li[0]
li[-1]             # 最后一个

# 删
li.pop()           # 删末尾
del li[0]

# 遍历
for x in li: pass
```

### 2\. dict 字典 = HashMap

```python
# 初始化
d = {"name":"zs","age":18}

# 取值
d["name"]
d.get("age",0)     # 安全取值，不存在给默认值

# 增改
d["gender"] = "男"

# 遍历key/value
for k in d: pass
for k,v in d.items(): pass
```

### 3\. set 集合 = HashSet

```python
s = {1,2,3,3}   # 自动去重
s.add(4)
s.remove(2)
```

### 4\. tuple 元组 = 不可变 List

```python
t = (1,2,3)
# t[0]=9 报错，不可修改
```

## 四、函数（对标 Java 方法）

```python
# Java: public static int add(int a,int b)
def add(a, b):
    return a + b

# 调用
res = add(1,2)

# 默认参数
def hello(name="javaer"):
    print(name)
```

## 五、面向对象 OOP（对标 Java 类）

```python
class User:
    # 构造方法 = 构造函数
    def __init__(self, name, age):
        self.name = name   # self = this
        self.age = age

    # 成员方法
    def say(self):
        print(self.name)

# 实例化 = new
u = User("张三",20)
u.say()

# 继承
class Student(User):
    def __init__(self,name,age,cls):
        super().__init__(name,age)
        self.cls = cls
```

> 重点：`self` 必须写，放在方法第一个参数
> 
> 

## 六、字符串操作（高频）

```python
s = "hello java"

# 拼接
s2 = s + " python"

# 格式化（推荐，对标String.format）
name = "张三"
age = 20
info = f"姓名:{name},年龄:{age}"

# 分割 split
arr = s.split(" ")

# 替换
s.replace("java","python")
```

## 七、文件 IO（对标 Java IO）

```python
# 读文件
with open("test.txt","r",encoding="utf-8") as f:
    text = f.read()

# 写文件
with open("test.txt","w",encoding="utf-8") as f:
    f.write("hello")
```

> `with` 自动关闭流，不用手动 close
> 
> 

## 八、异常处理（try\-catch）

```python
try:
    1/0
except Exception as e:
    print(e)
finally:
    pass
```

## 九、Javaer 必避坑清单

1. 缩进不对直接报错，不要用 tab，用**4 个空格**

2. `True/False/None` 首字母大写

3. 没有 `\+\+/\-\-`，只能 `\+= \-=`

4. 字典取值优先用 `\.get\(\)`，避免键不存在抛异常

5. 函数、类名规范：类大驼峰 `UserInfo`，函数小写下划线 `get\_user\(\)`

6. Python默认动态类型，企业开发建议加**类型注解**，还原Java强类型严谨性，减少类型报错

## 十、常用库速查（对标 Java 框架）

- Web 接口：**FastAPI/Flask** ≈ SpringBoot

- 数据处理：**pandas** ≈ EasyExcel \+ 工具类

- 爬虫：**requests** ≈ OkHttp

- 数据库：**pymysql/redis\-py** ≈ JDBC

> （注：文档部分内容可能由 AI 生成）
