import sublime

class CMakeDict(dict):  # dicts take a mapping or iterable as their optional first argument
    __slots__ = () # no __dict__ - that would be redundant
    def __init__(self, mapping=(), **kwargs):
        super(CMakeDict, self).__init__(mapping, **kwargs)
    def __getitem__(self, k):
        if self.__contains__(sublime.platform()):
            p = super(CMakeDict, self).__getitem__(sublime.platform())
            if k in p:
                return p[k]
        if self.__contains__(k):
            return super(CMakeDict, self).__getitem__(k)
        return super(CMakeDict, self).__getitem__(k)
    def __setitem__(self, k, v):
        return super(CMakeDict, self).__setitem__(k, v)
    def __delitem__(self, k):
        return super(CMakeDict, self).__delitem__(k)
    def get(self, k, default=None):
        return super(CMakeDict, self).get(k, default)
    def setdefault(self, k, default=None):
        return super(CMakeDict, self).setdefault(k, default)
    def pop(self, k):
        return super(CMakeDict, self).pop(k)
    def update(self, mapping=(), **kwargs):
        super(CMakeDict, self).update(mapping, **kwargs)
    def __contains__(self, k):
        return super(CMakeDict, self).__contains__(k)
    @classmethod
    def fromkeys(cls, keys):
        return super(CMakeDict, cls).fromkeys(k for k in keys)
