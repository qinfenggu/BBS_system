"""
一个用户插入数据：
无任何限制。只需在下面明确相关的路径和名字
"""
import os
import shutil
import pandas as pd


class Replace_Operation(object):
    # rxconfig_1600_0文件类型转换
    def Change_type(self, decode_file_path):
        files = os.listdir(decode_file_path)  # decode文件夹目录下的所有文件
        # print(files)
        for i, file in enumerate(files):
            # print(file)
            if file == replace_data_filename:
                NewName = os.path.join(decode_file_path, 'Replace.txt')  # 组合成新的文件名
                OldName = os.path.join(decode_file_path, file)  # 旧的文件名
                os.rename(OldName, NewName)  # 重命名
            elif file == 'Replace.txt':
                NewName = os.path.join(decode_file_path, replace_data_filename)  # 组合成新的文件名
                OldName = os.path.join(decode_file_path, file)  # 旧的文件名
                os.rename(OldName, NewName)  # 重命名

    # 插入数据
    def Replace_data(self, j, decode_file_path):
        fields = self.get_insert_fields(decode_file_path)     # 从表里面获取到所有字段后进行筛选出需要插入的字段
        # print(fields)
        # print('这是第{}'.format(j))
        # print(fields)
        for keyword in fields:
            file = open(r"{}\Replace.txt".format(decode_file_path), 'r')
            content = file.read()
            keyword1 = '/' + keyword
            if keyword == 'nTBSize':
                value = ''
                self.Insert_data(content, keyword, keyword1, value, decode_file_path, file)
            else:
                values = str(data.loc[j, keyword])  # 取值
                if values == 'nan':
                    file.close()
                else:
                    value = str(int(data.loc[j, keyword]))
                    self.Insert_data(content, keyword, keyword1, value, decode_file_path, file)
            if keyword == 'nNrOfLayers':
                file_n = open(r"{}\Replace.txt".format(decode_file_path), 'r')
                content_n = file_n.read()
                keyword_n = 'nNrOfAntennaPorts'
                keyword_n1 = '/nNrOfAntennaPorts'
                value_n = str(int(data.loc[j, keyword]))
                post_n = content_n.find(keyword_n)  # 查找字段
                post1_n = content_n.find(keyword_n1)
                content = content[:post_n] + keyword_n + '>' + value_n + '<' + content[post1_n:]
                file = open(r"{}\Replace.txt".format(decode_file_path), 'w')
                file.write(content)
                file.close()

    # 得到value后插入数据
    def Insert_data(self, content, keyword, keyword1, value, decode_file_path, file):
        post = content.find(keyword)  # 查找字段
        post1 = content.find(keyword1)
        if post != -1:
            content = content[:post] + keyword + '>' + value + '<' + content[post1:]
            file = open(r"{}\Replace.txt".format(decode_file_path), 'w')
        file.write(content)
        file.close()

    # 从表里面获取到所有字段后进行筛选出需要插入的字段
    def get_insert_fields(self, decode_file_path):
        # Change_type(decode_file)
        fp = open(r"{}\Replace.txt".format(decode_file_path), 'r')
        lines = []
        for line in fp:
            lines.append(line)
        fp.close()
        # Change_type(decode_file)
        fields = ['nTBSize']

        for i in keys:  # keys从表里面获取到的所有字段
            for j in lines:
                if i in j:
                    fields.append(i)
        return fields

    def main_function(self):
        j = 1

        for i in range(len(data)):  # decode一共多少条数据
            # print(i)
            if not os.path.exists('replace_data/{}{}'.format(decode_name,j)):  # 判断文件存不存在
                os.mkdir(replace_file_path + '\\' + decode_name + '{}'.format(j))  # 创建decode_1文件夹
                decode_file_path = os.path.join(replace_file_path, decode_name + '{}'.format(j))  # decode_1文件夹路径
            else:
                decode_file_path ='replace_data\{}{}'.format(decode_name,j)

            ref_files = os.listdir(ref_file_path)  # 把ref文件夹下面的所有文件组成list

            # 把ref文件夹下面的文件复制到decode_1文件夹那边
            for file_name in ref_files:
                full_file_name = os.path.join(ref_file_path, file_name)
                if os.path.isfile(full_file_name):  # 判断文件是否存在
                    shutil.copy(full_file_name, decode_file_path)  # 把ref文件夹下面的文件复制到decode文件夹那边
            self.Change_type(decode_file_path)
            self.Replace_data(j, decode_file_path)
            self.Change_type(decode_file_path)

            j += 1


if __name__ == '__main__':
    zcompiledcode_path = 'replace_data/zcompiledcode1.xlsx'  # zcompiledcode路径
    ref_file_path = 'replace_data\decode_ref'  # ref文件夹的路径
    replace_file_path = 'replace_data'  # 创建decode文件夹的父文件夹路径
    decode_name = 'Eecode_'  # 取创建decode文件夹名字
    replace_data_filename = 'rxconfig_1600_0.cfg'  # 在decode下更换数据的cfg文件名

    data = pd.read_excel(zcompiledcode_path, sheet_name='decode', index_col='编号')  # 打开excel文件读取数据。
    keys = data.loc[1].keys()  # 获取表里面所有的字段
    RO = Replace_Operation()
    RO.main_function()
