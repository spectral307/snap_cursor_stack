import matplotlib.pyplot as plt
import numpy as np
from bisect import insort, bisect_left
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from matplotlib.backend_bases import MouseButton
from .cursor import Cursor


class SnapCursorStack:
    def __init__(self, axes, xdata: np.array, ydata):
        self.__axes = axes
        self.__xdata = xdata
        self.__ydata = ydata

        figures = []
        for ax in self.__axes:
            if ax.figure not in figures:
                figures.append(ax.figure)
        if len(figures) > 1:
            raise BaseException("All axes must belong to one figure")

        self.__canvas = figures[0].canvas

        self.__cursors = []
        self.__size_hor_cursor = None
        self.__pick_list = []
        self.__picked_cursor = None
        self.__xdata_move_range_left_lim_ind = None
        self.__xdata_move_range_right_lim_ind = None

        self.__transform_mouse_pointer_over_cursor_cid = None
        self.__drag_cursor_cid = None

        self.__cursors_moved_handlers = []
        self.__prev_cursor_xdata = None

        self.__transform_mouse_pointer_over_cursor_cid = self.__canvas.mpl_connect(
            "motion_notify_event", self.__transform_mouse_pointer_over_cursor)
        self.__canvas.mpl_connect(
            "pick_event", self.__handle_pick_event)
        self.__canvas.mpl_connect(
            "button_press_event", self.__handle_button_press_event)
        self.__canvas.mpl_connect(
            "button_release_event", self.__handle_button_release_event)

    def get_cursor_xdata(self):
        return [cursor.get_xdata() for cursor in self.__cursors]

    def get_cursor_xdata_inds(self):
        return [cursor.get_xdata_ind() for cursor in self.__cursors]

    def add_cursors_moved_handler(self, handler):
        if handler not in self.__cursors_moved_handlers:
            self.__cursors_moved_handlers.append(handler)

    def remove_cursors_moved_handler(self, handler):
        if handler in self.__cursors_moved_handlers:
            self.__cursors_moved_handlers.remove(handler)

    def annotate(self, texts):
        if len(texts) != len(self.__cursors):
            raise ValueError(
                "Number of texts must be same as number of cursors")
        for i, text in enumerate(texts):
            self.__cursors[i].annotate(text)

    def add_cursor(self, xdata_ind, **kwargs):
        if not isinstance(xdata_ind, (int, np.int32, np.int64)):
            raise TypeError("xdata_ind must be int")

        if xdata_ind < 0:
            raise ValueError("xdata_ind must be non-negative")

        for cursor in self.__cursors:
            if cursor.get_xdata_ind() == xdata_ind:
                raise ValueError("There is already cursor with same xdata_ind")

        cursor = Cursor(
            self.__xdata, xdata_ind, self.__ydata, self.__axes, **kwargs)
        insort(self.__cursors, cursor)

    def draw_idle(self):
        self.__canvas.draw_idle()

    def clear(self):
        for cursor in self.__cursors:
            cursor.remove()

    def __enable_size_hor(self, cursor):
        QApplication.setOverrideCursor(Qt.CursorShape.SizeHorCursor)
        self.__size_hor_cursor = cursor

    def __disable_size_hor(self):
        QApplication.restoreOverrideCursor()
        self.__size_hor_cursor = None

    def __transform_mouse_pointer_over_cursor(self, event):
        if self.__canvas.cursor().shape() != Qt.CursorShape.ArrowCursor:
            return

        if event.inaxes not in self.__axes:
            if self.__is_size_hor_enabled():
                self.__disable_size_hor()
            return

        if self.__is_size_hor_enabled():
            if self.__size_hor_cursor.contains(event):
                return
            self.__disable_size_hor()

        for cursor in self.__cursors:
            if cursor.contains(event):
                self.__enable_size_hor(cursor)
                return

    def __is_size_hor_enabled(self):
        if self.__size_hor_cursor is None:
            return False
        return True

    def __handle_pick_event(self, event):
        self.__pick_list.append(event.artist)

    def __handle_button_press_event(self, event):
        if event.button != MouseButton.LEFT:
            return

        if len(self.__pick_list) == 0:
            return

        if len(self.__pick_list) > 1:
            self.__pick_list.sort(
                key=lambda item: item.get_zorder(), reverse=True)

        picked_axvline = self.__pick_list[0]

        for cursor in self.__cursors:
            if picked_axvline in cursor.axvlines:
                self.__picked_cursor = cursor

        self.__pick_list.clear()

        picked_cursor_ind = self.__cursors.index(self.__picked_cursor)

        self.__calculate_xdata_move_range(picked_cursor_ind)

        self.__prev_cursor_xdata = self.get_cursor_xdata()

        self.__picked_cursor.enable_focus()
        self.draw_idle()

        self.__canvas.mpl_disconnect(
            self.__transform_mouse_pointer_over_cursor_cid)
        self.__transform_mouse_pointer_over_cursor_cid = None

        self.__drag_cursor_cid = self.__canvas.mpl_connect(
            "motion_notify_event", self.__drag_cursor)

    def __calculate_xdata_move_range(self, picked_cursor_ind):
        if picked_cursor_ind == 0:
            self.__xdata_move_range_left_lim_ind = 0
            next_cursor = self.__cursors[picked_cursor_ind+1]
            self.__xdata_move_range_right_lim_ind = next_cursor.get_xdata_ind() - 1
        elif picked_cursor_ind == (len(self.__cursors) - 1):
            self.__xdata_move_range_right_lim_ind = len(self.__xdata) - 1
            prev_cursor = self.__cursors[picked_cursor_ind-1]
            self.__xdata_move_range_left_lim_ind = prev_cursor.get_xdata_ind() + 1
        else:
            next_cursor = self.__cursors[picked_cursor_ind+1]
            prev_cursor = self.__cursors[picked_cursor_ind-1]
            self.__xdata_move_range_left_lim_ind = prev_cursor.get_xdata_ind() + 1
            self.__xdata_move_range_right_lim_ind = next_cursor.get_xdata_ind() - 1

    def __handle_button_release_event(self, event):
        if self.__picked_cursor is None:
            return
        self.__disable_drag_mode(event.x, event.y)

    def __disable_drag_mode(self, x, y):
        if self.__prev_cursor_xdata != self.get_cursor_xdata():
            for handler in self.__cursors_moved_handlers:
                handler()
        self.__prev_cursor_xdata = None

        self.__picked_cursor.disable_focus()

        self.__picked_cursor = None
        self.__xdata_move_range_left_lim_ind = None
        self.__xdata_move_range_right_lim_ind = None

        self.__canvas.mpl_disconnect(self.__drag_cursor_cid)
        self.__drag_cursor_cid = None

        self.__transform_mouse_pointer_over_cursor_cid = self.__canvas.mpl_connect(
            "motion_notify_event", self.__transform_mouse_pointer_over_cursor)

        self.__canvas.motion_notify_event(x, y)

    def __drag_cursor(self, event):
        if event.inaxes not in self.__axes:
            self.__disable_drag_mode(event.x, event.y)
            return

        closest_xdata_ind = self.__get_closest_sorted_xdata_ind(
            event.xdata, lo=self.__xdata_move_range_left_lim_ind+1,
            hi=self.__xdata_move_range_right_lim_ind)

        closest_xdata_ind = self.__get_closest_xdata_ind(event.xdata)

        self.__picked_cursor.set_xdata_ind(closest_xdata_ind)
        self.draw_idle()

    def __get_closest_xdata_ind(self, x):
        if x < self.__xdata[self.__xdata_move_range_left_lim_ind]:
            return self.__xdata_move_range_left_lim_ind

        if x > self.__xdata[self.__xdata_move_range_right_lim_ind]:
            return self.__xdata_move_range_right_lim_ind

        distance = np.abs(x - self.__xdata)
        return np.argmin(distance)

    def __get_closest_sorted_xdata_ind(self, x, **kwargs):
        pos = bisect_left(self.__xdata, x, **kwargs)
        if pos == 0 or pos == len(self.__xdata):
            return pos
        before = self.__xdata[pos - 1]
        after = self.__xdata[pos]
        if after - x < x - before:
            return pos
        else:
            return pos - 1
