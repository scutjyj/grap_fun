# coding=utf-8
import sys
import urllib3
import re
import time

def getIsFollowedInfo(user_name):
    http_pm = urllib3.PoolManager()
    _user_url = 'https://www.zhihu.com/people/{username}/following?page={page_num}'
    ret_list = []
    page_count = 1
    while True:
        a = []
        user_url = _user_url.format(username=user_name, page_num=page_count)
        print user_url
        r = http_pm.request('GET', user_url)
        if r.status == 200:
            # firstly, we should do some preprocessing to get rid of the part including the information of user_name in r.data.
            t_str = 'urlToken&quot;:&quot;{user_name}&quot;'.format(user_name=user_name)
            data_list = r.data.split(t_str)
            non_zero_count = 0
            for t_data in data_list:
                a = re.findall(r'urlToken&quot;:&quot;([A-Za-z0-9-_.]+?)&quot;.*?articlesCount.*?name&quot;:&quot;(.*?)&quot;.*?followerCount&quot;:(\S+?),&quot;', t_data)
                print a, len(a)
                if len(a) != 0:
                    ret_list.extend(a)
                    non_zero_count += 1
                else:
                    pass
            if non_zero_count != 0:
                page_count += 1
                time.sleep(1)
            else:
            # No more data.
                break
        else:
            print 'grap page:%s failed!!!' % page_count
            break
            
    # Order the ret_list by follower numbers.
    _ret_list = sorted(ret_list, cmp=lambda x,y : cmp(int(x[2]),int(y[2])), reverse=True)
    # convert every tuple in ret_list to list.
    ret_list = map(lambda x:list(x), _ret_list)
    # get thankedCount,voteupCount,answerCount,favoritedCount of the users.
    _user_url = 'https://www.zhihu.com/people/{user_name}/activities'
    rl_len = len(ret_list)
    rl_count = 0
    no_data_default_value = [-1,-1,-1,-1]
    while rl_count < rl_len:
        user_url = _user_url.format(user_name=ret_list[rl_count][0])
        r = http_pm.request('GET', user_url)
        if r.status == 200:
            """
            a = re.findall(r'"zhihu:voteupCount" content="(\d+)".*?"zhihu:thankedCount" content="(\d+)".*?"zhihu:answerCount" content="(\d+)".*?favoritedCount&quot;:(\d+),&quot;', r.data)
            #print a, len(a)
            if a:
                # get the detail info successfully!
                ret_list[rl_count].extend(a[0])
                print ret_list[rl_count]
            else:
                ret_list[rl_count].extend(no_data_default_value)
            """
                
            voteupCount = re.findall(r'"zhihu:voteupCount" content="(\d+)"', r.data)
            thankedCount = re.findall(r'"zhihu:thankedCount" content="(\d+)"', r.data)
            answerCount = re.findall(r'"zhihu:answerCount" content="(\d+)"', r.data)
            favoritedCount = re.findall(r'favoritedCount&quot;:(\d+),&quot', r.data)
            if len(voteupCount) > 1 or len(thankedCount) > 1 or len(answerCount) > 1 or len(favoritedCount) > 1:
                print 'Your regular expression is invalid!!!user_id=%s' % ret_list[rl_count][0]
                return
            else:
                """
                if len(voteupCount) == 0 or len(thankedCount) == 0 or len(answerCount) == 0 or len(favoritedCount) == 0:
                    print 'can not get the parameter!!!user_id=%s' % ret_list[rl_count][0]
                    return
                else:
                    ret_list[rl_count].append(voteupCount[0])
                    ret_list[rl_count].append(thankedCount[0])
                    ret_list[rl_count].append(answerCount[0])
                    ret_list[rl_count].append(favoritedCount[0])
                """
                
                ret_list[rl_count].append(voteupCount[0] if len(voteupCount) == 1 else '-1')
                ret_list[rl_count].append(thankedCount[0] if len(thankedCount) == 1 else '-1')
                ret_list[rl_count].append(answerCount[0] if len(answerCount) == 1 else '-1')
                ret_list[rl_count].append(favoritedCount[0] if len(favoritedCount) == 1 else '-1')
                
        else:
            print 'Get the user detail info failed!!!!'
            ret_list[rl_count].extend(no_data_default_value)
        rl_count += 1
    # and we just save the data into file for now.
    file_name = 'E:\\{username}_isFollowing_info.txt'
    with open(file_name.format(username=user_name), 'w+') as fp:
        fp.write('用户ID|用户名|关注者数|获赞次数|感谢次数|回答数|被收藏次数\n')
        for item in ret_list:
            try:
                _line = '|'.join(item)
            except TypeError:
                print 'joining error!!!item:%s' % item
                return
            line = '%s\n' % _line
            fp.write(line)
    print 'Done!'

if __name__ == '__main__':
    if len(sys.argv) == 2:
        getIsFollowedInfo(sys.argv[1])
    else:
        print 'invalid parameter!'