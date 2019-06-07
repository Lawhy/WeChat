# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.4'
#       jupytext_version: 1.1.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # WeChat
#
# ### 微信自动回复小程序Demo

#coding=utf8
import itchat
from itchat.content import TEXT
from itchat.content import *
import sys
import time
import re
import requests, json
import aiml
import os
import re


def get_room_ID(room_name):
    global myUserName
    chat_rooms = itchat.get_chatrooms()
    for room in chat_rooms:
        if room['NickName'] == room_name:
            print('Found the desired chat room: ', room['NickName'])
            return room['UserName']
    return None


# +
def check_auto_sign_up_mode(from_user, to_user, content):
    global myUserName, commands, group_reply
    # 在自己的对话框里开启关闭自动报名功能
    if from_user == myUserName and to_user == myUserName:
        mode = ''
        for k in commands.keys():
            if commands[k] == content:
                mode = str(k)
                break
        # 如果某个模式被激活, 机器人模式只能在非离线模式打开
        if mode == 'auto_sign_up_mode_on':
            print('自动报名模式启动...')
            itchat.send_msg(u"[自动报名]已经打开。\n", 'filehelper')
            group_reply = True
        elif mode == 'auto_sign_up_mode_off':
            print('自动报名模式关闭...')
            itchat.send_msg(u"[自动报名]已经关闭。\n", 'filehelper')
            group_reply = False
    
def check_robot_mode(from_user, to_user, content):
    global myUserName, peer_list, commands, robot_reply
    # 机器人模式
    if content == commands["robot_mode_add"] and from_user == myUserName:
        print('机器人模式添加，对象为用户: ' + str(to_user))
        itchat.send_msg('机器人模式添加，对象为用户: ' + str(to_user), 'filehelper')
        peer_list.append(to_user)
        robot_reply = True
    elif content == commands["robot_mode_remove"] and from_user == myUserName:
        print('机器人模式移除，对象为用户: ' + str(to_user))
        itchat.send_msg('机器人模式移除，对象为用户: ' + str(to_user), 'filehelper')
        peer_list.remove(to_user)
    elif content == commands['robot_mode_off'] and from_user == myUserName:
        itchat.send_msg('机器人模式全关闭')
        peer_list = []
        robot_reply = False


# +
def turing_reply(from_user, content):
    global peer_list, robot_reply
    if robot_reply and from_user in peer_list:
        # Sleep 1 second is not necessary. Just cheat human.  
        time.sleep(2)
           
        cont = requests.get('http://www.tuling123.com/openapi/api?key=18747f51219b4c6e82ad780a624b4883&info=%s' % content).content
        m = json.loads(cont)
        itchat.send(m['text'], from_user)
        if m['code'] == 200000:
            itchat.send(m['url'], from_user)
        if m['code'] == 302000:
            itchat.send(m['list'], from_user)
        if m['code'] == 308000:
            itchat.send(m['list'], from_user)
        
def auto_sign_up(from_user, content, asset_nick_name, asset_ID):
    global room_ID, room_name, myUserName, group_reply
    
    # special boolean for testing use
    special_entry = False
    
    if not room_ID:
        print('Fail to retrieve the room ID!')
        return
    
    if group_reply and from_user == room_ID:
        # 如果消息来自指定群聊
        print("[" + room_name + ", " + asset_nick_name + "]: " + str(content))
        itchat.send_msg("[" + room_name + ", " + asset_nick_name + "]: " + str(content), 'filehelper')
        # 自动回复指定人物信息
        if asset_nick_name == '大黄油' or asset_nick_name == 'LEO':
            print("[ECBC]: Asset is on the move!")
            if not replace_msg(content) == content:
                # 这样了话日常话语不会被包进去
                itchat.send_msg(replace_msg(content), room_ID)
                print("[ECBC]: 报名成功!")
                itchat.send_msg("[ECBC]: 报名成功!", 'filehelper')
                group_reply = False
            else:
                print('[ECBC]: Asset的日常话语...')
        # backup plan, 万一大黄油的消息被错过
        elif (u'报名表' in content) and (u'周' in content) and (not u'Lawrence' in content):
            print(u"[ECBC]:报名表出来了！速度抢报名啦！")
            itchat.send_msg(u"[ECBC]:报名表出来了！速度抢报名啦！", 'filehelper')
            # plab B execution
            itchat.send_msg(replace_msg(content), room_ID)
            itchat.send_msg("[ECBC]: 报名成功!", 'filehelper')
            group_reply = False
    
    # Demo listener
    if group_reply and (from_user == demo_ID or asset_ID == myUserName):
        print("[Demo, " + asset_nick_name + "]: " + str(content))
        if asset_nick_name == '小小小小小' or special_entry:
            print("[Demo]: Asset is on the move!")
            if not replace_msg(content) == content:
                # 这样了话日常话语不会被包进去
                itchat.send_msg(replace_msg(content), demo_ID)
                print('[Demo]: 报名成功!')
                itchat.send_msg("[Demo]: 报名成功!", 'filehelper')
                group_reply = False
            else:
                print('[Demo]: Asset的日常话语...')
        # backup plan, 万一大黄油的消息被错过
        elif u'报名表' in content and u'周' in content and u'Lawrence' not in content:
            print(u"[Demo]:报名表出来了！速度抢报名啦！")
            itchat.send_msg(u"[Demo]:报名表出来了！速度抢报名啦！", 'filehelper')
            # plab B execution
            itchat.send_msg(replace_msg(content), demo_ID)
            print('[Demo]: 报名成功!')
            group_reply = False
            

def replace_msg(content):
    pa = re.compile(r'周[三六].+?training Session 报名表[\s\S]+?Waiting list:')
    sessions = re.findall(pa, content)
    for before in sessions:
        after = before.replace('3.', '3. Lawrence ')
        content = content.replace(before, after)
    return content


# -

# When recieve the following msg types, trigger the auto replying.
@itchat.msg_register([TEXT, PICTURE, FRIENDS, CARD, MAP, SHARING, RECORDING, ATTACHMENT, VIDEO], isGroupChat=True, isFriendChat=True, isMpChat=True)
def text_reply(msg):
    global robot_reply, group_reply, asset_nick_name, asset_ID
    
    if 'ActualNickName' in msg.keys() and 'ActualUserName' in msg.keys():
        asset_nick_name = msg['ActualNickName']
        asset_ID = msg['ActualUserName']
        print('A group message from actual user: ' + asset_nick_name + ' with ID: ' + asset_ID )
    
    # 检查是否自动回复
    check_auto_sign_up_mode(msg['FromUserName'], msg['ToUserName'], msg['Content'])
    check_robot_mode(msg['FromUserName'], msg['ToUserName'], msg['Content'])
    
    # Let Turing reply the msg.
    turing_reply(msg['FromUserName'], msg['Content'])
    auto_sign_up(msg['FromUserName'], msg['Content'],  asset_nick_name, asset_ID)
    
    return


if __name__ == '__main__':
    # Set the hot login
    itchat.auto_login(hotReload=True)
    # Get your own UserName
    myUserName = itchat.get_friends(update=True)[0]["UserName"]
    print('[MyUserID]: ' + myUserName)

    # Set the default variables
    robot_reply = False
    group_reply = False
    peer_list = []
    room_name = 'ECBC open session'
    room_ID = get_room_ID(room_name)
    demo_ID = get_room_ID('Demo')
    print('[Room ID]: ' + room_ID)
    print('[Demo ID]: ' + demo_ID)
    asset_nick_name = ''
    asset_ID = ''
    commands = {
        "robot_mode_add": u'巴啦啦小魔仙 变身机器人',
        "robot_mode_remove": u'巴啦啦小魔仙 变回本人',
        "robot_mode_off": u'巴啦啦小魔仙 全部关掉',
        'auto_sign_up_mode_on': '启动自动报名',
        'auto_sign_up_mode_off': '解除自动报名'
    }
    itchat.run()

    # room_name = 'ECBC open session'
    # room_ID = get_room_ID(room_name)
    # for member in itchat.update_chatroom(room_ID)['MemberList']:
    #     if member['NickName'] == '大黄油':
    #         print(member)
