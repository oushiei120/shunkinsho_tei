import os
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

# 文件路径
person_file = "/Users/oushiei/Documents/GitHub/shunkinsho_tei/春琴抄_PERSON.txt"

city_file = "/Users/oushiei/Documents/GitHub/shunkinsho_tei/春琴抄_City.txt"

# 读取文件内容
def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

# 创建 <listPerson> 节点
def create_list_person(persons):
    list_person = Element("listPerson")
    for person in persons:
        person_element = SubElement(list_person, "person", {"xml:id": person})
        pers_name = SubElement(person_element, "persName")
        pers_name.text = person
    return list_person

# 创建 <listPlace> 节点
def create_list_place(places):
    list_place = Element("listPlace")
    for place in places:
        place_element = SubElement(list_place, "place", {"xml:id": place})
        place_name = SubElement(place_element, "placeName")
        place_name.text = place
    return list_place

# 主函数
def main():
    # 读取文件内容
    persons = read_file(person_file)
    cities = read_file(city_file)

    # 直接创建 listPerson 和 listPlace 元素
    list_person = create_list_person(persons)
    list_place = create_list_place(cities)

    # 格式化输出 listPerson 和 listPlace
    person_xml = parseString(tostring(list_person, encoding="unicode")).toprettyxml(indent="    ")
    place_xml = parseString(tostring(list_place, encoding="unicode")).toprettyxml(indent="    ")

    # 去掉 XML 声明
    person_xml = person_xml.replace('<?xml version="1.0" ?>\n', '')
    place_xml = place_xml.replace('<?xml version="1.0" ?>\n', '')
    
    # 保存到文件
    output_file = "/Users/oushiei/Documents/GitHub/shunkinsho_tei/春琴抄_output.xml"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(person_xml)
        f.write(place_xml)

    print(f"XML 文件已生成: {output_file}")

if __name__ == "__main__":
    main()