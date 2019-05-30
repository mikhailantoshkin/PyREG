#!/usr/bin/python
# -- coding: utf-8 --
from __future__ import print_function
from __future__ import unicode_literals
from Registry import Registry
from Registry import RegistryParse
RegSZ = 0x0001
RegExpandSZ = 0x0002
RegBin = 0x0003
RegDWord = 0x0004
RegMultiSZ = 0x0007
RegQWord = 0x000B
RegNone = 0x0000
RegBigEndian = 0x0005
RegLink = 0x0006
RegResourceList = 0x0008
RegFullResourceDescriptor = 0x0009
RegResourceRequirementsList = 0x000A
RegFileTime = 0x0010
import hexdump
import sys
import codecs
import argparse
sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
reload(sys)
sys.setdefaultencoding('utf-8')


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs='?', help='Registry Hive Path')
    parser.add_argument('-k', '--key',  help='show values and subkeys of a specific key. Use \'ROOT\\Keyname\\Keyname\\...\'', type = str)
    parser.add_argument('-d', '--depth', help='set the recursion depth for lookup of subkeys. If none is given - shows subkeys of a given key and their values (equal to 1)', type=int, default=1, choices=range(1, 11))
    parser.add_argument('--deleted', action='store_const', const=True, default=False, help='add deleted hive values to the end of the output. If -k is not given, show all delited hive keys and values')
    return parser


def all_cells(buf):  # get all cells for all HBIN blocks, returns list of all cells
    cells = []
    regf = RegistryParse.REGFBlock(buf, 0, False)  # HIVE header block
    hbins = regf.hbins()  # list of HBINs for this HIVE
    try:  # sometimes you get StructureDoesNotExist exception with final cell creation
        for hbin in hbins:
            for cell in hbin.cells():
                    cells.append(cell)
        return cells
    except Registry.RegistryParse.RegistryStructureDoesNotExist:
        return cells


def del_rec(key, depth, current_depth, cells, buf):  #find all subkeys of a given key
        current_depth += 1  # how deep we are in subkeys
        subkeylist=[]
        # setting up custom subkey list
        if type(key) is RegistryParse.NKRecord:  # we check if the given key was deleted. if it was - it's going to be a nkrecord
            for cell in cells:  # check all the cells if its a subkey of given key
                if cell.data_id() == b"nk":  # if it's a nkrecord
                    nk = RegistryParse.NKRecord(buf, cell.data_offset(), cell)  # create nkrecord
                    if nk. has_parent_key() and nk.parent_key().path() == key.path():
                        subkeylist.append(nk)  # add child to the list
        else:
            for subkey in key.subkeys():  # if it's a RegistryValue we just add RegistryKeys to a list
                subkeylist.append(subkey)
            for cell in cells:  # check for deleted subkeys in all cells
                if cell.data_id() == b"nk":  # if it's a nkrecord
                    if cell.is_free():  #if it was deleted it won't show in subkyelist of given key
                        nk = RegistryParse.NKRecord(buf, cell.data_offset(), cell)  # create nkrecord
                        if nk.has_parent_key() and nk.parent_key().path() == key.path():  # check child
                            subkeylist.append(nk)

        for key in subkeylist:  # printing the info for each key
            print(key_info(key))
            if current_depth < depth:  # recursion if we are not deep enough.
                # If there is no subkeys for a key subkeylist will be empty
                del_rec(key, depth, current_depth + 1, cells, buf)


def key_info(key):  # returns string consisting of a info about given key
    string = 'Key:'  # string for key related info
    valstr = ''  # string for value related info
    val_cnt = 0
    if type(key) is RegistryParse.NKRecord:  # if the key was deleted
        string += ' (DELETED KEY) '  # forming an outut string
        string += key.path() + '\nClass Name:  %s\nMTIME:  %s\n\n' \
                  % (key.classname(), key.timestamp().strftime("%Y-%m-%d %H:%M:%S"))
        try:  # if no values is given for a key error flag is raised
            for v in key.values_list().values():  # for each value in value list of this nkrecord
                val_cnt += 1
                valstr += data2str(v, val_cnt)  # form an output string
        except RegistryParse.RegistryStructureDoesNotExist:
            valstr += 'Key has no values\n'  # if there is no values for this key
    else:  # if we dealing with "live" key
        string += 5 * ' '  # alignment padding
        string += key.path() + '\nClass Name:  %s\nMTIME:  %s\n\n' \
                  % (key._nkrecord.classname(), key.timestamp().strftime("%Y-%m-%d %H:%M:%S"))
        if key.values():
            for val in key.values():
                val_cnt += 1
                valstr += data2str(val._vkrecord, val_cnt)  # forming an output string with every value from value list
        else:
            valstr += 'Key has no values\n'
    return (string + valstr)  # return the output for key and its values


def del_vals(buf, cells):
    vkstr=''
    for cell in cells:
        vk = RegistryParse.VKRecord(buf, cell.data_offset(), cell)  # create a vkrecord
        vkstr = vkstr + data2str(vk, 0) + '\n'  # form a string with info about deleted vkrecords
    return vkstr


def data2str(value, val_cnt):  # riped from VKRecord __str__. It would be easier just to modify RegistryParse though
    if value.has_name():
        name = value.name()
    else:
        name = "(default)"
    data = ""
    data_type = value.data_type()
    if data_type == RegSZ or data_type == RegExpandSZ:
        data = value.data()
    elif data_type == RegMultiSZ:
        string = "\tValue %s \n\tName: %s \n\tType: %s, \n\tData:\n" % \
                 (str(val_cnt), name, value.data_type_str())
        if value.data():
            for p in value.data(): string = string + (' ' + p + '\n')
        return string + '\n'  # string has all the stings from RegMultiSZ
    elif data_type == RegDWord or data_type == RegQWord:
        data = str(value.data())
    elif data_type == RegNone:
        data = "(none)"
    elif data_type == RegFileTime:
        data = value.data().isoformat(str("T")) + "Z"
    else:  # if its regbin or any other type of binary data just hexdump it
        data = hexdump.hexdump(value.data(), result='return')
        return "\tValue %s \n\tName: %s \n\tType: %s \n\tData:\n%s\n\n" % (str(val_cnt), name, value.data_type_str(), data)
    return "\tValue %s \n\tName: %s \n\tType: %s \n\tData: %s\n\n" % (str(val_cnt), name, value.data_type_str(), data)


if __name__ == '__main__':

    parser = createParser()
    namespace = parser.parse_args(sys.argv[1:])
    reg = Registry.Registry(namespace.path)
    f = open(namespace.path)
    buf = f.read()
    cells = all_cells(buf)
    nk_cells = []
    vk_cells = []

    for cell in cells:  # populate lists with corresponding cells
        if cell.data_id() == b"nk":
            nk_cells.append(cell)
        if cell.data_id() == b"vk" and cell.is_free():
            vk_cells.append(cell)

    if namespace.deleted and not namespace.key:  # if only --deleted is given
        string = 'DELETED HIVE KEYS'
        print('\n\n' + len(string) * '-' + '\n%s\n' % string + len(string) * '-' + '\n\n\n')
        for cell in nk_cells:  # check for all deleted nk records and print their info
            if cell.is_free():
                print(key_info(RegistryParse.NKRecord(buf, cell.data_offset(), cell)))
        string = 'DELETED HIVE VALUES WITCH CAN NOT BE LINKED TO ANY KEY'
        print('\n\n' + len(string) * '-' + '\n%s\n' % string + len(string) * '-' + '\n\n\n')
        print(del_vals(buf, vk_cells))  #print all deleted values

    elif namespace.key:  # if -k is given
        for cell in nk_cells:  # check if the cell is holding a given key
            nk = RegistryParse.NKRecord(buf, cell.data_offset(), cell)
            if nk.path() == namespace.key:  # check if it's a valid nkrecord
                if cell.is_free():  # if the key was deleted - it's NKRecord object
                    key = nk
                else:
                    key = Registry.RegistryKey(nk)  # if the key is "live" - it's RegistryKey object
        try:  # try to print key info, if key was not found - NameError
            print(key_info(key))
        except NameError:
            print('Specified key not found')
            sys.exit(-1)

        del_rec(key, namespace.depth, 0, nk_cells, buf)  # start the recursive metod
        if namespace.deleted:  # if --deleted is passed along with -k print all deleted values of the HIVE
            string = 'DELETED HIVE VALUES'
            print('\n\n'+len(string)*'-'+'\n%s\n' % string +len(string)*'-'+'\n\n\n')
            print(del_vals(buf, vk_cells))

