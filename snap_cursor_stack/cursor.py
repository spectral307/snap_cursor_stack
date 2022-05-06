class Cursor:
    def __init__(self, xdata, xdata_ind, axes, **kwargs):
        self.__xdata_ind = xdata_ind
        self.__xdata = xdata
        self.axvlines = []

        for ax in axes:
            axvline = ax.axvline(
                self.__xdata[xdata_ind], pickradius=2, picker=True, **kwargs)
            self.axvlines.append(axvline)

    def contains(self, event):
        for axvline in self.axvlines:
            if axvline.contains(event)[0]:
                return True
        return False

    def set_xdata_ind(self, value):
        if value == self.__xdata_ind:
            return
        for axvline in self.axvlines:
            axvline.set_xdata(self.__xdata[value])
        self.__xdata_ind = value

    def get_xdata_ind(self):
        return self.__xdata_ind

    def get_xdata(self):
        return self.__xdata[self.__xdata_ind]

    def __eq__(self, other):
        if (isinstance(other, Cursor)):
            return self.__xdata_ind == other.__xdata_ind
        raise TypeError("other")

    def __ne__(self, other):
        if (isinstance(other, Cursor)):
            return self.__xdata_ind != other.__xdata_ind
        raise TypeError("other")

    def __lt__(self, other):
        if (isinstance(other, Cursor)):
            return self.__xdata_ind < other.__xdata_ind
        raise TypeError("other")

    def __gt__(self, other):
        if (isinstance(other, Cursor)):
            return self.__xdata_ind > other.__xdata_ind
        raise TypeError("other")

    def __le__(self, other):
        if (isinstance(other, Cursor)):
            return self.__xdata_ind >= other.__xdata_ind
        raise TypeError("other")

    def __ge__(self, other):
        if (isinstance(other, Cursor)):
            return self.__xdata_ind <= other.__xdata_ind
        raise TypeError("other")
