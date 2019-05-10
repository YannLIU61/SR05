import pickle

class Decoder:
    def __init__(self, split_str=' ', split_list=' '):
        self.split_str = split_str
        self.split_list = split_list

    def decode(self, content):
        contents = content.split(self.split_str)
        return dict((i, contents[i]) for i in range(len(contents)))


class Encoder:
    def __init__(self, split_str=' ', split_list=' '):
        self.split_str = split_str
        self.split_list = split_list

    def encode(self, *args):
        return self.split_str.join(args)


class SR05Decoder(Decoder):
    def __init__(self, split_str='^&&^', split_list='&'):
        super(Decoder, self).__init__()
        self.split_str = split_str
        self.split_list = split_list

    def decode(self, content):
        contents = content.split(self.split_str)
        if len(contents) < 5:
            return None

        values = dict()
        values.update({\
                "identity": contents[0],\
                "destination": contents[1],\
                "protocol": contents[2],\
                "content": contents[3],\
                "message_counter": contents[4]
        })
        return values


class SR05Encoder(Encoder):
    def __init__(self, split_str='^&&^', split_list='&'):
        super(Encoder, self).__init__()
        self.split_str = split_str
        self.split_list = split_list

    def encode(self, *args):
        # des,res,prot,contenue, id
        des         = str(args[0]) if len(args) > 0 else ""
        res         = str(args[1]) if len(args) > 1 else ""
        prot        = str(args[2]) if len(args) > 2 else ""
        contenue    = str(args[3]) if len(args) > 3 else ""
        mid         = str(args[4]) if len(args) > 4 else ""
        arglist = [des, res, prot, contenue, mid]

        return self.split_str.join(arglist)


# pck='1^&&^2^&&^1^&&^qweqweq'
# if not IfAlreadySend(pck,0):
#         print("Yes")
# print(pck.find("^&^"))
