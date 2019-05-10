
class Clock:
    def __init__(self):
        self.clocks = dict()

    def __gt__(self, other):
        """
        None: not defined
        True: greater
        False: less
        """
        if not isinstance(other, Clock):
            return None

        at_least_one_greater = False
        for node in self.clocks.keys():
            if node in other.clocks.keys():
                if self.clocks[node] < other.clocks[node]:
                    return False
                elif self.clocks[node] > other.clocks[node]:
                    at_least_one_greater = True
            else:
                # Not in other, but in this
                if self.clocks[node] > 0:
                    at_least_one_greater = True

        for node in other.clocks.keys():
            if node not in self.clocks.keys():
                if other.clocks[node] != 0:
                    return None

        return at_least_one_greater
        

    def __lt__(self, other):
        if not isinstance(other, Clock):
            return None

        gt = self.__gt__(other)
        if gt != None:
            return not gt
        else:
            return None

    def clear(self):
        self.clocks.clear()

    def sync(self, other):
        if not isinstance(other, Clock):
            return
        
        for node in other.clocks.keys():
            if node not in self.clocks.keys():
                self.clocks.update({node: other.clocks[node]})
            else:
                self.clocks[node] = max(self.clocks[node], other.clocks[node])

