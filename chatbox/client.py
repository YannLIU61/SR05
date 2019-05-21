#coding=utf-8
# 本机上运行, server addr == client addr
import socket,select,threading,sys
host = socket.gethostname()
client_addr = (host,5963)  # equals server_addr()

# listening
def listening(cs):
    inputs = [cs]
    while True:
        rlist,wlist,elist = select.select(inputs, [], [])
        # client socket就是用来收发数据的, 由于只有这个waitable 对象, 所以不必迭代
        if cs in rlist:
            try:
                # 打印从服务器收到的数据
                print (cs.recv(1024))
            except socket.error:
                print ("socket is error")
                exit()

# speak
def speak(cs):
    while True:
        try:
            data = raw_input()
        except Exception as e:
            print (r"can't input")
            exit()
        try:
            cs.send(data)
            if data == "exit":
                cs.close()
                exit()
        except Exception as e:
            exit()


def main():
    # client socket
    cs = socket.socket()
    cs.connect(client_addr)
    # 分别启动听和说线程
    t = threading.Thread(target=listening,args=(cs,))  # 注意当元组中只有一个元素的时候需要这样写, 否则会被认为是其原来的类型
    t.start()

    t1 = threading.Thread(target=speak,args=(cs,))
    t1.start()

if __name__ == "__main__":
    main()