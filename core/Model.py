import json
import xmltodict
import xml.etree.ElementTree as ET
from datetime import datetime
from .DatabaseValidator import DatabaseValidator

class Model:

    __database, __layout = None, None
    __database_index = {}
    __layout_index = {}
    __DATABASE_NAMING = {'data': __database, 'meta': __layout, 'data_index':__database_index, 'meta_index':__layout_index}

    def __init__(self):
        self.__load_database()
        self.__indexing()
        self.__dbValidator = DatabaseValidator(self.__database, self.__layout)

    def __load_database(self):
        self.__database_tree = ET.parse('database/db.xml')
        self.__layout_tree = ET.parse('database/layout.xml')
        self.__database = self.__database_tree.getroot()
        self.__layout = self.__layout_tree.getroot()

    def __indexing(self):
        for item in self.__database.findall(".//*[@id]"):
            if item.attrib['id'] in self.__database_index.keys():
                print("Warning, database is not inconsistant")
            self.__database_index[item.attrib['id']] = item
        for item in self.__layout.findall(".//*[@id]"):
            if item.attrib['id'] in self.__layout_index.keys():
                print("Warning, layout database is not inconsistant")
            self.__layout_index[item.attrib['id']] = item

    def get_list_of_databases(self):
        result = {}
        for base in self.__database:
            result[base.tag] = [len(base), base.attrib['layoutId']]

        return result

    def get_container_for(self, record):
        return self.__database.find(".//"+ record.upper())

    def get_all_records(self, record, json=False):
        if json:
            root = self.__database.find(".//"+ record.upper())
            dic = xmltodict.parse(ET.tostring(root))
            return dic
        return self.__database.findall(".//"+ record[:-1].upper())

    def search_records(self, record, query):
        root = ET.Element('RESULT')
        result = self.__database.findall(".//" + record[:-1].upper()+'[@name="'+ query +'"]')
        if result == None:
            result = self.__database.findall(".//" + record[:-1].upper()+'[@id="'+ id +'"]')
        for item in result:
            root.append(item)
        json_acceptable_string = str(xmltodict.parse(ET.tostring(root))).replace("@", "").replace("'", "\"")
        return json.loads(json_acceptable_string)

    def get_container_with_layout_id(self, id):
        return self.__database.find('.//*[@layoutId="' + id + '"]')

    def get_layout_for(self, record):
        return self.__layout.find('.//LAYOUT[@for="' + record.upper() + '"]')

    def get_layout_by_id(self, id):
        return self.__layout.find('.//LAYOUT[@id="' + id + '"]')

    def update_layout_by_id(self, data, id):
        layout = self.get_layout_by_id(id)
        for element in data:
            if not self.__field_exists(element, layout):
                field = ET.SubElement(layout, "FIELD")
                field.attrib['name'] = element
                field.attrib['type'] = data[element][0]
                if data[element][0] in ['select', 'link']:
                    self.__manage_complex_type(data[element], field)
            elif self.__fields_type_changed(element, data[element][0], layout):
                for field in layout:
                    if field.attrib['name'] == element:
                        field.attrib['type'] = data[element]
            self.__update_field_visibility(layout, element, data[element])
        self.__update_records_by_new_fields(data, id)
        self.__save("layout")

    def __manage_complex_type(self, data, element):
        if data[0] == 'select':
            for item in data:
                if item not in ['listview', 'detailsview', 'select']:
                    option = ET.SubElement(element, 'OPTION')
                    option.attrib['id'] = self.__generate_id('meta_index')
                    option.attrib['name'] = item
                    option.attrib['value'] = item
        elif data[0] == 'link':

            for item in data:
                if item not in ['listview', 'detailsview', 'link']:
                    link = ET.SubElement(element, "LINK")
                    link.attrib['id'] = self.__generate_id('meta_index')
                    link.attrib['value'] = item

    def __update_field_visibility(self,layout, field, data):
        element = layout.find('.//FIELD[@name="'+field+'"]')
        if 'listview' in data:
            element.attrib['listview'] = "True"
        else:
            element.attrib['listview'] = "False"
        if "detailsview" in data:
            element.attrib['details'] = "True"
        else:
            element.attrib['details'] = "False"


    def __field_exists(self, name, layout):
        for field in layout:
            if field.attrib['name'] == name:
                return True
        return False

    def __fields_type_changed(self, name, type, layout):
        for field in layout:
            if field.attrib['name'] == name and field.attrib['type'] != type:
                return True
        return False

    def __update_records_by_new_fields(self, data, id):
        container = self.get_container_with_layout_id(id)

        for record in container:
            for field in data:
                if field not in record.attrib:
                    record.attrib[field] = ""


    def remove_field_from_layout(self, layoutId, name):
        layout = self.get_layout_by_id(layoutId)
        toBeRemoved = None
        for field in layout:
            if field.attrib['name'] == name:
                toBeRemoved = field
        layout.remove(toBeRemoved)
        self.__remove_field_from_records(layoutId, name)
        self.__save("layout")

    def __remove_field_from_records(self, layoutId, name):
        container = self.get_container_with_layout_id(layoutId)
        for record in container:
            record.attrib.pop(name, None)

    def create_database(self, data):
        base = ET.SubElement(self.__database, data['dbName'].upper())
        layout = ET.SubElement(self.__layout, "LAYOUT")
        layout.attrib['id'] = self.__generate_id('meta_index')
        layout.attrib['for'] = data['dbName'].upper()
        self.__create_id_field_for_new_layout(layout)
        base.attrib['layoutId'] = layout.attrib['id']
        base.attrib['layout'] = 'layout.xml'
        self.__save('layout')

    def __create_id_field_for_new_layout(self, layout):
        field = ET.SubElement(layout, "FIELD")
        field.attrib['name'] = 'id'
        field.attrib['type'] = 'link'
        field.attrib['listview'] = 'True'
        field.attrib['details'] = 'True'
        link = ET.SubElement(field, "LINK")
        link.attrib['id'] = self.__generate_id('meta_index')
        link.attrib['value'] = layout.attrib['for']

    def remove_database_and_layout(self, id):
        self.__layout.remove(self.__layout_index[id])
        base = self.__database.find('.//*[@layoutId="'+ id + '"]')
        self.__database.remove(base)
        self.__save('layout')


    def create_record(self, data, database):
        root = self.__database.find(database)
        record = ET.SubElement(root, database[:-1])
        record.attrib['id'] = self.__generate_id('data_index')
        for element in data:
            record.attrib[element] = data[element]
        self.__save('db')


    def __generate_id(self, db):
        candidate = int(datetime.now().strftime("%Y%m%d%H%M%S"))
        while self.__check_in_index(candidate, db):
            candidate = int(candidate) + 1
        return str(candidate)

    def __check_in_index(self, candidate, db):
        if str(candidate) in self.__DATABASE_NAMING[db].keys():
            return True
        return False

    def __save(self, file):
        if file == 'db':
            self.__database_tree.write('database/db.xml')
        elif file == 'layout':
            self.__database_tree.write('database/db.xml')
            self.__layout_tree.write('database/layout.xml')