from collections import UserDict

class SingleInsertDict(UserDict):
    def __setitem__(self, key, value):
        if key in self.data:
            raise KeyError(f"Повторное добавление ключа запрещено: {key}")
        super().__setitem__(key, value)


dct = {'Value': '1'}
dct['Value'] = 2
new_dct = SingleInsertDict(dct)
new_dct['Value'] = 2
print(type(new_dct), new_dct)