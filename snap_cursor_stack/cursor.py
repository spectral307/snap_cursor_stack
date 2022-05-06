class Cursor:
    def __init__(self, xdata, xdata_ind, axes, **kwargs):
        figures = []
        for ax in axes:
            if ax.figure not in figures:
                figures.append(ax.figure)
        if len(figures) > 1:
            raise BaseException("All axes must belong to one figure")

        self.__canvas = figures[0].canvas
        self.__xdata_ind = xdata_ind
        self.__xdata = xdata
        self.__axes = axes
        self.axvlines = []
        self.points = []
        self.__annotations = {}
        self.__cids = {}

        for ax in axes:
            axvline = ax.axvline(
                self.__xdata[xdata_ind], pickradius=2, picker=True, **kwargs)
            self.axvlines.append(axvline)
            ydata = ax.lines[0].get_ydata()
            point = ax.scatter(
                self.__xdata[xdata_ind], ydata[xdata_ind], **kwargs)
            self.points.append(point)

        self.__axvline_zorder = self.axvlines[0].get_zorder()
        self.__annotation_zorder = None

    def annotate(self, text, **kwargs):
        for ann in self.__annotations.values():
            ann.remove()
        self.__annotations.clear()

        self.__disconnect_ylim_changed_handlers()

        if text == None:
            return

        renderer = self.__canvas.get_renderer()

        for ax in self.__axes:
            ylim = ax.get_ylim()[1]
            ann = ax.annotate(
                text,
                (self.get_xdata(), ylim),
                textcoords="offset pixels",
                xytext=(0., 0.),
                bbox={"facecolor": "white",
                      "edgecolor": "black",
                      "boxstyle": "round,pad=.2"},
                zorder=self.__axvline_zorder,
                **kwargs)
            self.__annotations[ax] = ann

            extent = ann.get_window_extent(renderer)

            text_x = -(extent.width / 2)
            text_y = 7.0

            ann.set_position((text_x, text_y))

            cid = ax.callbacks.connect(
                "ylim_changed", self.__refresh_annotation_y_pos)
            self.__cids[ax] = cid

        self.__annotation_zorder = list(self.__annotations.values())[
            0].get_zorder()

    def __disconnect_ylim_changed_handlers(self):
        for ax, cid in self.__cids.items():
            ax.callbacks.disconnect(cid)
        self.__cids.clear()

    def __del__(self):
        self.__disconnect_ylim_changed_handlers()

    def __refresh_annotation_y_pos(self, ax):
        ann = self.__annotations[ax]
        ann.xy = (ann.xy[0], ax.get_ylim()[1])

    def __refresh_annotation_x_pos(self):
        for ann in self.__annotations.values():
            ann.xy = (self.get_xdata(), ann.xy[1])

    def __hash__(self):
        ret = 0
        for axvline in self.axvlines:
            ret += hash(axvline)
        return ret

    def enable_focus(self):
        for axvline in self.axvlines:
            axvline.set_zorder(1000)
        for ann in self.__annotations.values():
            ann.set_zorder(1000)

    def disable_focus(self):
        for axvline in self.axvlines:
            axvline.set_zorder(self.__axvline_zorder)
        for ann in self.__annotations.values():
            ann.set_zorder(self.__annotation_zorder)

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
        for point in self.points:
            ydata = point.axes.lines[0].get_ydata()
            point.set_offsets((self.__xdata[value], ydata[value]))
        self.__xdata_ind = value
        self.__refresh_annotation_x_pos()

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
