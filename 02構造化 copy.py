import re
import os
from bs4 import BeautifulSoup, Tag
import xml.etree.ElementTree as ET
from collections import defaultdict

# ==================== 設定と初期化 ====================
# ファイルパス設定
person_file = "/Users/oushiei/Documents/GitHub/shunkinsho_tei/春琴抄_PERSON.txt"  # 人名リストファイル
city_file = "/Users/oushiei/Documents/GitHub/shunkinsho_tei/春琴抄_City.txt"      # 地名リストファイル
xml_file = "/Users/oushiei/Documents/GitHub/shunkinsho_tei/56866_58169.xml"      # 処理対象のXMLファイル

# ==================== エンティティ読み込み関数 ====================
# 人名と地名ファイルを読み込む関数、各行の内容をリスト項目として読み込む
def read_entities(file_path):
    """
    テキストファイルからエンティティリスト（人名または地名）を読み込む
    パラメータ:
        file_path: エンティティリストファイルのパス
    戻り値:
        リスト: クリーニング後のエンティティリスト、空行と空白を除去
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        # 空行と空白を除去し、各エンティティが有効であることを確認
        return [line.strip() for line in f.readlines() if line.strip()]

# ==================== エンティティデータ処理 ====================
# 人名と地名リストの読み込み
persons = read_entities(person_file)  # ファイルからすべての人名を読み込む
places = read_entities(city_file)     # ファイルからすべての地名を読み込む

# デバッグ情報の出力、地名データが正しく読み込まれたことを確認
print(f"読み込まれた地名の数: {len(places)}")
print(f"地名サンプル: {places[:5] if places else '地名なし'}")

# 長さでソート、最も長い名前を先にマッチングする（部分マッチングの問題を回避）
# 例えば：「春琴女」は「春琴」よりも優先してマッチングする必要がある、そうしないと誤ったマークアップが発生する
persons.sort(key=len, reverse=True)
places.sort(key=len, reverse=True)

# ==================== XMLファイル処理 ====================
# XMLファイルから内容を読み込む
with open(xml_file, 'r', encoding='utf-8') as f:
    xml_content = f.read()

# BeautifulSoupを使用して解析（元の形式を保持）
# 'xml'パーサーを選択してXML構造と特性を維持
soup = BeautifulSoup(xml_content, 'xml')

# ==================== エンティティID生成 ====================
# エンティティインデックスの作成（XML ID参照用）
# 各人名と地名に一意のIDが割り当てられ、マークアップと後続の参照に使用される
person_dict = {name: f"person_{i}" for i, name in enumerate(persons, 1)}
place_dict = {name: f"place_{i}" for i, name in enumerate(places, 1)}

# 出現回数を記録する辞書の作成、各エンティティがテキスト内で出現する回数を記録
person_occurrences = defaultdict(int)  # 人名の出現回数
place_occurrences = defaultdict(int)   # 地名の出現回数

# ==================== 文書本体の特定 ====================
# 文書のbody部分を検索
body = soup.find('body')
if not body:
    body = soup.find('text')  # 一部のTEI文書ではtext要素を直接使用する場合がある

# ==================== コア処理関数 ====================
# 処理関数の修正、ノード置換の問題を解決
def process_content(node):
    """
    DOMノードを再帰的に処理し、テキストノード内の人名と地名にマークアップを追加
    パラメータ:
        node: 処理対象のDOMノード
    """
    if isinstance(node, Tag):
        # ノードに子ノードがある場合、まずrubyタグ（日本語の振り仮名用）かどうかを確認
        if node.name == 'seg' and node.get('type') == 'ruby':
            # rubyタグの場合、内部処理をスキップして構造を保護
            return
        
        # 子ノードのコピーを作成、処理中にリストが変更されるのを防ぐ
        # DOMを変更すると子ノードリストが動的に変化するため
        children = list(node.children)
        for child in children:
            if isinstance(child, Tag):
                # 子タグノードを再帰的に処理
                process_content(child)
            elif isinstance(child, str) and child.strip() and child.parent is not None:
                # テキストノードが空でなく、まだDOMツリー内にあることを確認
                # まず人名を処理 - 競合を避けるため2段階で処理
                processed_child = process_entities(child, persons, person_dict, person_occurrences, "persName")
                if processed_child and child.parent is not None:
                    # 処理後のノードで元のテキストノードを置換
                    child.replace_with(*processed_child)
        
        # 2回目の走査で地名を処理
        # 人名処理後にDOM構造が変更されているため、テキストノードを再取得する必要がある
        new_children = list(node.children)
        for child in new_children:
            if isinstance(child, str) and child.strip() and child.parent is not None:
                processed_node = process_entities(child, places, place_dict, place_occurrences, "placeName")
                if processed_node:
                    try:
                        # ノードの置換を試みる
                        child.replace_with(*processed_node)
                    except ValueError:
                        # ノードがすでにツリー内にない場合、適切にスキップ
                        pass

# エンティティ（人名または地名）を処理するヘルパー関数
def process_entities(text, entities, entity_dict, occurrences, tag_name):
    """
    テキスト内でエンティティを検索し、マークアップする
    パラメータ:
        text: 処理対象のテキスト
        entities: エンティティリスト（人名または地名）
        entity_dict: エンティティID辞書
        occurrences: エンティティ出現回数辞書
        tag_name: タグ名（"persName"または"placeName"）
    戻り値:
        処理後のノードリスト、マッチングがない場合はNone
    """
    for entity in entities:
        if entity in text:
            # エンティティの出現回数を記録
            occurrences[entity] += 1
            
            # テキストを分割し、エンティティの前後にタグを追加
            parts = text.split(entity)
            new_elements = []
            
            for i in range(len(parts)):
                if parts[i]:
                    # 分割後の通常テキストを保持
                    new_elements.append(parts[i])
                
                # 各分割点にエンティティタグを追加（最後の分割点を除く）
                if i < len(parts) - 1:
                    # 新しいエンティティタグを作成
                    entity_tag = soup.new_tag(tag_name)
                    # corresp属性を追加し、エンティティIDを参照
                    entity_tag['corresp'] = f"#{entity_dict[entity]}"
                    # タグ内のテキストをエンティティ名に設定
                    entity_tag.string = entity
                    # タグを結果リストに追加
                    new_elements.append(entity_tag)
            
            # 元のテキストを置き換えるための新しいノードリストを準備
            if new_elements:
                return new_elements
    
    # エンティティが見つからない場合はNoneを返す
    return None

# ==================== 文書処理の開始 ====================
# bodyノードが見つかった場合、内容の処理を開始
if body:
    process_content(body)

# ==================== TEI追加情報の作成 ====================
# back部分の作成（存在しない場合）- エンティティリストとメタデータを格納するため
back = soup.find('back')
if not back:
    back = soup.new_tag('back')
    soup.TEI.append(back)

# listPerson部分の作成 - TEI標準で文書内に登場する人物をリストアップするため
list_person = soup.new_tag('listPerson')
for person, person_id in person_dict.items():
    if person_occurrences[person] > 0:  # 文書内で実際に出現する人物のみを追加
        person_entry = soup.new_tag('person')
        person_entry['xml:id'] = person_id  # 一意のIDを設定
        
        persName = soup.new_tag('persName')
        persName.string = person  # 人名を設定
        person_entry.append(persName)
        
        list_person.append(person_entry)

# listPlace部分の作成 - TEI標準で文書内に登場する場所をリストアップするため
list_place = soup.new_tag('listPlace')
for place, place_id in place_dict.items():
    if place_occurrences[place] > 0:  # 文書内で実際に出現する場所のみを追加
        place_entry = soup.new_tag('place')
        place_entry['xml:id'] = place_id  # 一意のIDを設定
        
        placeName = soup.new_tag('placeName')
        placeName.string = place  # 地名を設定
        place_entry.append(placeName)
        
        list_place.append(place_entry)

# listPersonとlistPlaceをback部分に追加
back.append(list_person)
back.append(list_place)

# ==================== デバッグ情報出力 ====================
# デバッグ情報を出力し、処理結果のサンプルを表示
print(f"処理された人名サンプル: {list(person_occurrences.items())[:5] if person_occurrences else 'マッチングする人名なし'}")
print(f"処理された地名サンプル: {list(place_occurrences.items())[:5] if place_occurrences else 'マッチングする地名なし'}")

# ==================== 処理結果の保存 ====================
# 元のファイルを上書きせず、新しいファイルに出力
output_xml_file = "/Users/oushiei/Documents/GitHub/shunkinsho_tei/56866_58169_tagged_places_fixed.xml"

# 修正後のXMLファイルを新しいファイルに保存
with open(output_xml_file, 'w', encoding='utf-8') as f:
    f.write(str(soup))

# 処理結果の総括
print(f"処理完了。マークアップされた人名：{sum(person_occurrences.values())}個、地名：{sum(place_occurrences.values())}個")
print(f"結果は新しいファイルに保存されました: {output_xml_file}")