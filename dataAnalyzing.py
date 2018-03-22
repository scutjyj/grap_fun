# coding = utf-8
import sys

def findInvalidUser(user_name):
    ret = []
    src_file_name = 'E:\\{user_name}_isFollowing_info.txt'
    with open(src_file_name.format(user_name=user_name), 'r') as fp:
        lines = fp.readlines()
    for line in lines:
        _tmp = line.split('|')
        if '-1' in _tmp:
            ret.append(_tmp[0])
    return ret
    
if __name__ == '__main__':
    if len(sys.argv) == 2:
        invalid_user_list = findInvalidUser(sys.argv[1])
        print "the invalid user list(total:%s):%s" % (len(invalid_user_list), ','.join(invalid_user_list))
        ret_file = 'E:\\{user_name}_invalid_users.txt'
        with open(ret_file.format(user_name=sys.argv[1]), 'w+') as fp:
            for _user in invalid_user_list:
                line = '%s\n' % _user
                fp.write(line)
    else:
        print "invalid parameter!!!"